from uoa_agent.models import UIElement
from uoa_agent.planner import plan_actions


def _demo_elements() -> list[UIElement]:
    return [
        UIElement(uid=0, tag="select", label="System mode", options=["Beginner", "Light", "Advanced", "Expert"]),
        UIElement(uid=1, tag="input", type="checkbox", label="Enable advanced mode", checked=False),
        UIElement(uid=2, tag="input", type="checkbox", label="Analytics", checked=False),
        UIElement(uid=3, tag="input", type="checkbox", label="Automation engine", checked=False),
    ]


def test_advanced_with_all_features_creates_toggle_and_select_steps() -> None:
    plan = plan_actions("Enable advanced mode with all features", _demo_elements())
    actions = {step.uid: step.action for step in plan.steps}

    assert plan.intents.wants_advanced is True
    assert plan.intents.wants_all_features is True
    assert actions[1] == "toggle_on"
    assert actions[2] == "toggle_on"
    assert actions[3] == "toggle_on"
    assert actions[0] == "select"


def test_disable_all_features_turns_known_toggles_off() -> None:
    elements = _demo_elements()
    elements[1].checked = True
    elements[2].checked = True

    plan = plan_actions("Disable all features", elements)
    actions = {step.uid: step.action for step in plan.steps}

    assert plan.intents.wants_disable is True
    assert actions[1] == "toggle_off"
    assert actions[2] == "toggle_off"


def test_safe_mode_skips_negative_toggles_when_enabling_all_features() -> None:
    elements = [
        UIElement(uid=0, tag="input", type="checkbox", label="Disable notifications", checked=False),
        UIElement(uid=1, tag="input", type="checkbox", label="Analytics", checked=False),
    ]

    plan = plan_actions("Enable all features", elements, safe_mode=True)
    actions = {step.uid: step.action for step in plan.steps}

    assert 0 not in actions
    assert actions[1] == "toggle_on"
    assert any("Safe mode skipped toggle" in warning for warning in plan.warnings)


def test_disable_advanced_prefers_basic_select_option() -> None:
    elements = [
        UIElement(
            uid=0,
            tag="select",
            label="Mode",
            options=["Beginner", "Light", "Advanced", "Expert"],
        ),
    ]

    plan = plan_actions("Disable advanced mode", elements)
    assert plan.steps[0].action == "select"
    assert plan.steps[0].value in {"Beginner", "Light"}
