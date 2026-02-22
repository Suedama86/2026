from __future__ import annotations

import re
from dataclasses import dataclass

from uoa_agent.models import ActionStep, IntentSummary, Plan, UIElement

ADVANCED_KEYWORDS = {
    "advanced",
    "expert",
    "pro",
    "power",
    "full mode",
    "developer",
    "high",
    "max",
}

ALL_FEATURES_KEYWORDS = {
    "all features",
    "everything",
    "all options",
    "full feature",
    "max features",
    "all settings",
}

DISABLE_KEYWORDS = {
    "disable",
    "turn off",
    "deactivate",
    "stop",
    "remove",
}

ADVANCED_OPTION_PRIORITY = ["expert", "advanced", "pro", "full", "max", "high", "developer"]
BASIC_OPTION_PRIORITY = ["beginner", "light", "basic", "standard", "default"]
NEGATIVE_TOGGLE_PATTERNS = [
    re.compile(r"\bdisable\b"),
    re.compile(r"\bturn off\b"),
    re.compile(r"\boff\b"),
    re.compile(r"\bwithout\b"),
    re.compile(r"\bexclude\b"),
    re.compile(r"\bhide\b"),
    re.compile(r"\bblock\b"),
    re.compile(r"\bsuppress\b"),
    re.compile(r"\bdo not\b"),
    re.compile(r"\bno\b"),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _contains_any(haystack: str, needles: set[str]) -> bool:
    return any(token in haystack for token in needles)


def _display_name(el: UIElement) -> str:
    return el.label or el.text or el.placeholder or f"{el.tag}#{el.uid}"


def _element_text(el: UIElement) -> str:
    parts = [el.label, el.text, el.placeholder, " ".join(el.options), el.type, el.role]
    return _normalize(" ".join(part for part in parts if part))


def _is_toggle(el: UIElement) -> bool:
    role = el.role.lower()
    typ = el.type.lower()
    return el.checked is not None or typ in {"checkbox"} or role in {"switch", "checkbox"}


def _is_select(el: UIElement) -> bool:
    return el.tag.lower() == "select"


def _is_clickable(el: UIElement) -> bool:
    return el.tag.lower() == "button" or el.role.lower() in {"button", "menuitem"}


def _select_option_by_priority(options: list[str], priorities: list[str]) -> str | None:
    normalized = [_normalize(opt) for opt in options]
    for keyword in priorities:
        for idx, option in enumerate(normalized):
            if keyword in option:
                return options[idx]
    return None


def _select_advanced_option(options: list[str]) -> str | None:
    return _select_option_by_priority(options, ADVANCED_OPTION_PRIORITY)


def _select_basic_option(options: list[str]) -> str | None:
    return _select_option_by_priority(options, BASIC_OPTION_PRIORITY)


def _extract_feature_phrases(goal: str) -> list[str]:
    normalized = _normalize(goal)
    normalized = re.sub(r"\b(enable|turn on|activate|set|with|and|plus)\b", ",", normalized)
    phrases = [piece.strip() for piece in normalized.split(",")]
    return [phrase for phrase in phrases if len(phrase.split()) >= 2]


@dataclass
class _Candidate:
    score: float
    uid: int
    action: str
    reason: str
    value: str | None = None


def _token_overlap_score(needle: str, haystack: str) -> float:
    n_tokens = set(re.findall(r"[a-z0-9]+", needle))
    h_tokens = set(re.findall(r"[a-z0-9]+", haystack))
    if not n_tokens:
        return 0.0
    return len(n_tokens & h_tokens) / len(n_tokens)


def _select_option_for_phrase(phrase: str, options: list[str]) -> str | None:
    best_score = 0.0
    best_option: str | None = None
    for option in options:
        score = _token_overlap_score(phrase, _normalize(option))
        if score > best_score:
            best_score = score
            best_option = option
    if best_score >= 0.5:
        return best_option
    return None


def _looks_negative_toggle(text: str) -> bool:
    return any(pattern.search(text) for pattern in NEGATIVE_TOGGLE_PATTERNS)


def plan_actions(goal: str, elements: list[UIElement], *, safe_mode: bool = True) -> Plan:
    goal_normalized = _normalize(goal)
    wants_disable = _contains_any(goal_normalized, DISABLE_KEYWORDS)
    wants_advanced = _contains_any(goal_normalized, ADVANCED_KEYWORDS)
    wants_all_features = _contains_any(goal_normalized, ALL_FEATURES_KEYWORDS) or "all" in goal_normalized

    intents = IntentSummary(
        wants_advanced=wants_advanced,
        wants_all_features=wants_all_features,
        wants_disable=wants_disable,
        raw_goal=goal,
    )

    steps: list[ActionStep] = []
    warnings: list[str] = []
    used_uids: set[int] = set()

    def add_step(uid: int, action: str, reason: str, value: str | None = None) -> None:
        if uid in used_uids:
            return
        steps.append(ActionStep(uid=uid, action=action, value=value, reason=reason))
        used_uids.add(uid)

    # Broad action for "all features": flip all toggles consistently.
    if wants_all_features:
        desired_action = "toggle_off" if wants_disable else "toggle_on"
        for el in elements:
            if not _is_toggle(el):
                continue
            text = _element_text(el)
            if safe_mode and desired_action == "toggle_on" and _looks_negative_toggle(text):
                warnings.append(f'Safe mode skipped toggle "{_display_name(el)}".')
                continue
            if desired_action == "toggle_on" and el.checked is True:
                continue
            if desired_action == "toggle_off" and el.checked is False:
                continue
            add_step(el.uid, desired_action, 'Goal indicates "all features".')

    # Targeted advanced controls.
    if wants_advanced:
        desired_toggle_action = "toggle_off" if wants_disable else "toggle_on"
        for el in elements:
            text = _element_text(el)
            mentions_advanced = _contains_any(text, ADVANCED_KEYWORDS)
            if not mentions_advanced:
                continue

            if _is_toggle(el):
                if safe_mode and desired_toggle_action == "toggle_on" and _looks_negative_toggle(text):
                    warnings.append(f'Safe mode skipped advanced toggle "{_display_name(el)}".')
                    continue
                add_step(el.uid, desired_toggle_action, "Found advanced-like toggle.")
            elif _is_select(el):
                selected = _select_basic_option(el.options) if wants_disable else _select_advanced_option(el.options)
                if selected:
                    add_step(el.uid, "select", "Found advanced option in select.", selected)
            elif _is_clickable(el):
                if not wants_disable:
                    add_step(el.uid, "click", "Found advanced-like action button.")

    # Feature phrases: "enable dark mode and analytics", etc.
    phrases = _extract_feature_phrases(goal_normalized)
    for phrase in phrases:
        candidates: list[_Candidate] = []
        for el in elements:
            text = _element_text(el)
            score = _token_overlap_score(phrase, text)
            if score < 0.6:
                continue
            if _is_toggle(el):
                desired_toggle_action = "toggle_off" if wants_disable else "toggle_on"
                if safe_mode and desired_toggle_action == "toggle_on" and _looks_negative_toggle(text):
                    warnings.append(f'Safe mode skipped phrase-match toggle "{_display_name(el)}".')
                    continue
                candidates.append(
                    _Candidate(
                        score=score,
                        uid=el.uid,
                        action=desired_toggle_action,
                        reason=f'Matched phrase "{phrase}" to toggle.',
                    )
                )
            elif _is_select(el):
                selected_value: str | None
                if wants_advanced:
                    selected_value = _select_basic_option(el.options) if wants_disable else _select_advanced_option(
                        el.options
                    )
                else:
                    selected_value = _select_option_for_phrase(phrase, el.options)

                if not selected_value:
                    continue
                candidates.append(
                    _Candidate(
                        score=score,
                        uid=el.uid,
                        action="select",
                        reason=f'Matched phrase "{phrase}" to select.',
                        value=selected_value,
                    )
                )
            elif _is_clickable(el):
                candidates.append(
                    _Candidate(
                        score=score,
                        uid=el.uid,
                        action="click",
                        reason=f'Matched phrase "{phrase}" to button.',
                    )
                )
        if candidates:
            top = sorted(candidates, key=lambda item: item.score, reverse=True)[0]
            add_step(top.uid, top.action, top.reason, top.value)

    # Final fallback: if user asks advanced but nothing matched, click buttons named advanced.
    if wants_advanced and not steps and not wants_disable:
        for el in elements:
            if _is_clickable(el) and _contains_any(_element_text(el), ADVANCED_KEYWORDS):
                add_step(el.uid, "click", "Fallback: click advanced related button.")
                break

    return Plan(intents=intents, steps=steps, warnings=warnings)
