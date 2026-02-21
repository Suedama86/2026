from __future__ import annotations

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
    const checked = ('checked' in el) ? !!el.checked : null;
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
    ) -> tuple[list[UIElement], Plan, list[ActionLog]]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await page.wait_for_timeout(300)

                elements = await self._extract_elements(page)
                plan = plan_actions(goal, elements)
                logs = await self._execute_plan(page, plan, dry_run=dry_run)

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
                    checked: ('checked' in el) ? !!el.checked : null
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
