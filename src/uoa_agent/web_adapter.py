from __future__ import annotations

import re
from typing import Any

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, async_playwright

from uoa_agent.models import ActionLog, ActionStep, Plan, UIElement
from uoa_agent.planner import plan_actions

_EXTRACT_ELEMENTS_SCRIPT = """
() => {
  const selectors = [
    'button',
    'input',
    'select',
    'textarea',
    '[role="button"]',
    '[role="switch"]',
    '[role="checkbox"]',
    '[role="menuitem"]',
    '[aria-pressed]',
    '[contenteditable="true"]'
  ];

  const visible = (el) => {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style &&
      style.visibility !== 'hidden' &&
      style.display !== 'none' &&
      rect.width > 0 &&
      rect.height > 0;
  };

  const uniq = new Set();
  const nodes = [];
  for (const selector of selectors) {
    for (const el of document.querySelectorAll(selector)) {
      if (!uniq.has(el)) {
        uniq.add(el);
        nodes.push(el);
      }
    }
  }

  const out = [];
  let uid = 0;
  for (const el of nodes) {
    if (!visible(el)) {
      continue;
    }

    el.setAttribute('data-uoa-id', String(uid));
    const tag = (el.tagName || '').toLowerCase();
    const role = (el.getAttribute('role') || '').toLowerCase();
    const type = (el.getAttribute('type') || '').toLowerCase();
    const placeholder = el.getAttribute('placeholder') || '';
    const ariaLabel = el.getAttribute('aria-label') || '';
    let label = ariaLabel;

    if (!label && el.id) {
      const escapedId = el.id.replace(/"/g, '\\"');
      const labelEl = document.querySelector('label[for="' + escapedId + '"]');
      if (labelEl) {
        label = (labelEl.innerText || labelEl.textContent || '').trim();
      }
    }
    if (!label) {
      const parentLabel = el.closest('label');
      if (parentLabel) {
        label = (parentLabel.innerText || parentLabel.textContent || '').trim();
      }
    }

    const text = (el.innerText || el.textContent || '').trim();
    let checked = ('checked' in el) ? !!el.checked : null;
    if (checked === null) {
      const ariaPressed = el.getAttribute('aria-pressed');
      const ariaChecked = el.getAttribute('aria-checked');
      if (ariaPressed !== null) {
        checked = ariaPressed === 'true';
      } else if (ariaChecked !== null) {
        checked = ariaChecked === 'true';
      }
    }
    const value = ('value' in el && el.value !== undefined && el.value !== null) ? String(el.value) : null;
    const options = tag === 'select'
      ? Array.from(el.options || []).map(opt => (opt.text || '').trim()).filter(Boolean)
      : [];

    out.push({
      uid,
      tag,
      role,
      type,
      label,
      text,
      placeholder,
      checked,
      value,
      options
    });
    uid += 1;
  }

  return out;
}
"""

FINALIZE_KEYWORDS = {
    "save": 4,
    "apply": 4,
    "update": 3,
    "confirm": 3,
    "done": 2,
    "finish": 2,
    "submit": 2,
}
FINALIZE_NEGATIVE_KEYWORDS = {"cancel", "close", "discard", "reset", "delete", "remove", "back"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _element_text(el: UIElement) -> str:
    return _normalize(" ".join(part for part in [el.label, el.text, el.placeholder] if part))


def _is_clickable(el: UIElement) -> bool:
    return el.tag.lower() == "button" or el.role.lower() in {"button", "menuitem"}


def _pick_finalize_uid(elements: list[UIElement]) -> int | None:
    best_uid: int | None = None
    best_score = 0
    for el in elements:
        if not _is_clickable(el):
            continue

        text = _element_text(el)
        if not text:
            continue
        if any(token in text for token in FINALIZE_NEGATIVE_KEYWORDS):
            continue

        score = 0
        for token, weight in FINALIZE_KEYWORDS.items():
            if token in text:
                score += weight

        if score > best_score:
            best_score = score
            best_uid = el.uid
    return best_uid


class PlaywrightWebAdapter:
    def __init__(self, timeout_ms: int = 20000) -> None:
        self.timeout_ms = timeout_ms

    async def inspect(self, url: str, *, headless: bool = True) -> list[UIElement]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await page.wait_for_timeout(300)
                return await self._extract_elements(page)
            finally:
                await browser.close()

    async def run_goal(
        self,
        url: str,
        goal: str,
        *,
        dry_run: bool = False,
        headless: bool = True,
        safe_mode: bool = True,
        auto_finalize: bool = True,
    ) -> tuple[list[UIElement], Plan, list[ActionLog]]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await page.wait_for_timeout(300)

                elements = await self._extract_elements(page)
                plan = plan_actions(goal, elements, safe_mode=safe_mode)
                logs = await self._execute_plan(page, plan, dry_run=dry_run)
                if not dry_run and auto_finalize:
                    logs.extend(await self._auto_finalize(page, has_planned_steps=bool(plan.steps)))

                return elements, plan, logs
            finally:
                await browser.close()

    async def _extract_elements(self, page: Page) -> list[UIElement]:
        raw: list[dict[str, Any]] = await page.evaluate(_EXTRACT_ELEMENTS_SCRIPT)
        return [UIElement.model_validate(item) for item in raw]

    async def _execute_plan(self, page: Page, plan: Plan, *, dry_run: bool) -> list[ActionLog]:
        logs: list[ActionLog] = []
        for step in plan.steps:
            if dry_run:
                logs.append(
                    ActionLog(
                        uid=step.uid,
                        action=step.action,
                        status="planned",
                        detail=f"Dry run: {step.reason}",
                    )
                )
                continue

            try:
                log = await self._apply_step(page, step)
            except PlaywrightError as exc:
                log = ActionLog(
                    uid=step.uid,
                    action=step.action,
                    status="failed",
                    detail=f"Playwright error: {exc}",
                )
            logs.append(log)

        return logs

    async def _auto_finalize(self, page: Page, *, has_planned_steps: bool) -> list[ActionLog]:
        if not has_planned_steps:
            return [
                ActionLog(
                    uid=-1,
                    action="click",
                    status="skipped",
                    detail="Skipped auto-finalize because plan had no actionable steps.",
                )
            ]

        elements = await self._extract_elements(page)
        finalize_uid = _pick_finalize_uid(elements)
        if finalize_uid is None:
            return [
                ActionLog(
                    uid=-1,
                    action="click",
                    status="skipped",
                    detail="No save/apply control found for auto-finalize.",
                )
            ]

        log = await self._apply_step(
            page,
            ActionStep(
                uid=finalize_uid,
                action="click",
                reason="Auto-finalize by clicking save/apply control.",
            ),
        )
        return [log]

    async def _apply_step(self, page: Page, step: ActionStep) -> ActionLog:
        locator = page.locator(f'[data-uoa-id="{step.uid}"]')
        count = await locator.count()
        if count == 0:
            return ActionLog(
                uid=step.uid,
                action=step.action,
                status="failed",
                detail="Element not found; page likely changed.",
            )

        target = locator.first
        detail = step.reason

        if step.action == "click":
            await target.click(timeout=self.timeout_ms)
            return ActionLog(uid=step.uid, action=step.action, status="applied", detail=detail)

        if step.action in {"toggle_on", "toggle_off"}:
            desired = step.action == "toggle_on"
            state = await target.evaluate(
                """(el) => ({
                    type: (el.getAttribute('type') || '').toLowerCase(),
                    role: (el.getAttribute('role') || '').toLowerCase(),
                    checked: (() => {
                        if ('checked' in el) {
                            return !!el.checked;
                        }
                        const ariaPressed = el.getAttribute('aria-pressed');
                        if (ariaPressed !== null) {
                            return ariaPressed === 'true';
                        }
                        const ariaChecked = el.getAttribute('aria-checked');
                        if (ariaChecked !== null) {
                            return ariaChecked === 'true';
                        }
                        return null;
                    })()
                })"""
            )
            checked = state.get("checked", None)

            if checked is desired:
                return ActionLog(
                    uid=step.uid,
                    action=step.action,
                    status="skipped",
                    detail="Already in desired state.",
                )

            is_native_checkbox = state.get("type") == "checkbox"
            if is_native_checkbox:
                if desired:
                    await target.check(timeout=self.timeout_ms)
                else:
                    await target.uncheck(timeout=self.timeout_ms)
            else:
                await target.click(timeout=self.timeout_ms)

            return ActionLog(uid=step.uid, action=step.action, status="applied", detail=detail)

        if step.action == "fill":
            await target.fill(step.value or "", timeout=self.timeout_ms)
            return ActionLog(uid=step.uid, action=step.action, status="applied", detail=detail)

        if step.action == "select":
            if not step.value:
                return ActionLog(
                    uid=step.uid,
                    action=step.action,
                    status="failed",
                    detail="No select value provided by planner.",
                )
            try:
                await target.select_option(label=step.value, timeout=self.timeout_ms)
            except PlaywrightError:
                await target.select_option(value=step.value, timeout=self.timeout_ms)
            return ActionLog(uid=step.uid, action=step.action, status="applied", detail=detail)

        return ActionLog(
            uid=step.uid,
            action=step.action,
            status="failed",
            detail=f"Unsupported action '{step.action}'.",
        )
