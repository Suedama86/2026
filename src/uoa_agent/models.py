from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InspectRequest(BaseModel):
    url: str
    headless: bool = True


class RunRequest(InspectRequest):
    goal: str
    dry_run: bool = False


class UIElement(BaseModel):
    uid: int
    tag: str
    role: str = ""
    type: str = ""
    label: str = ""
    text: str = ""
    placeholder: str = ""
    checked: bool | None = None
    value: str | None = None
    options: list[str] = Field(default_factory=list)


ActionType = Literal["click", "toggle_on", "toggle_off", "fill", "select"]


class ActionStep(BaseModel):
    uid: int
    action: ActionType
    value: str | None = None
    reason: str


class IntentSummary(BaseModel):
    wants_advanced: bool = False
    wants_all_features: bool = False
    wants_disable: bool = False
    raw_goal: str


class Plan(BaseModel):
    intents: IntentSummary
    steps: list[ActionStep] = Field(default_factory=list)


class ActionLog(BaseModel):
    uid: int
    action: ActionType
    status: Literal["planned", "applied", "skipped", "failed"]
    detail: str


class InspectResponse(BaseModel):
    elements: list[UIElement]
    count: int


class RunResponse(BaseModel):
    goal: str
    intents: IntentSummary
    inspected_count: int
    planned_steps: list[ActionStep]
    action_logs: list[ActionLog]
