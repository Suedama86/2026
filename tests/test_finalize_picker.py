from uoa_agent.models import UIElement
from uoa_agent.web_adapter import _pick_finalize_uid


def test_pick_finalize_uid_prefers_save_apply_labels() -> None:
    elements = [
        UIElement(uid=0, tag="button", text="Cancel"),
        UIElement(uid=1, tag="button", text="Apply changes"),
        UIElement(uid=2, tag="button", text="Save"),
    ]

    # "Apply changes" gets a stronger weighted score than just "Save".
    assert _pick_finalize_uid(elements) == 1


def test_pick_finalize_uid_ignores_dangerous_controls() -> None:
    elements = [
        UIElement(uid=0, tag="button", text="Delete all"),
        UIElement(uid=1, tag="button", text="Reset settings"),
    ]

    assert _pick_finalize_uid(elements) is None
