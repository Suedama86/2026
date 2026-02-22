from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from uoa_agent.models import (
    InspectRequest,
    InspectResponse,
    PlanRequest,
    PlanResponse,
    RunRequest,
    RunResponse,
)
from uoa_agent.planner import plan_actions
from uoa_agent.web_adapter import PlaywrightWebAdapter

app = FastAPI(
    title="Universal Overlay Agent",
    version="0.1.0",
    description="MVP API for inspecting and automating existing web applications.",
)

adapter = PlaywrightWebAdapter()
ui_dir = Path(__file__).resolve().parents[2] / "ui"
demo_dir = Path(__file__).resolve().parents[2] / "demo"
app.mount("/static", StaticFiles(directory=ui_dir), name="static")
app.mount("/demo", StaticFiles(directory=demo_dir), name="demo")

# Allow mobile/web clients to call the API in MVP mode.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(ui_dir / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/inspect", response_model=InspectResponse)
async def inspect(request: InspectRequest) -> InspectResponse:
    try:
        elements = await adapter.inspect(request.url, headless=request.headless)
    except Exception as exc:  # pragma: no cover - runtime/browser errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InspectResponse(elements=elements, count=len(elements))


@app.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest) -> PlanResponse:
    try:
        elements = await adapter.inspect(request.url, headless=request.headless)
    except Exception as exc:  # pragma: no cover - runtime/browser errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    planned = plan_actions(request.goal, elements, safe_mode=request.safe_mode)
    return PlanResponse(
        goal=request.goal,
        intents=planned.intents,
        inspected_count=len(elements),
        planned_steps=planned.steps,
        warnings=planned.warnings,
    )


@app.post("/run", response_model=RunResponse)
async def run_goal(request: RunRequest) -> RunResponse:
    try:
        elements, plan, logs = await adapter.run_goal(
            request.url,
            request.goal,
            headless=request.headless,
            dry_run=request.dry_run,
            safe_mode=request.safe_mode,
            auto_finalize=request.auto_finalize,
        )
    except Exception as exc:  # pragma: no cover - runtime/browser errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    applied_count = len([log for log in logs if log.status == "applied"])
    skipped_count = len([log for log in logs if log.status == "skipped"])
    failed_count = len([log for log in logs if log.status == "failed"])

    return RunResponse(
        goal=request.goal,
        intents=plan.intents,
        inspected_count=len(elements),
        planned_steps=plan.steps,
        warnings=plan.warnings,
        action_logs=logs,
        applied_count=applied_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
    )


def run() -> None:
    host, port = resolve_bind()
    uvicorn.run("uoa_agent.api:app", host=host, port=port, reload=False)


def resolve_bind() -> tuple[str, int]:
    host = os.getenv("UOA_HOST", "0.0.0.0")
    raw_port = os.getenv("PORT", os.getenv("UOA_PORT", "8000"))
    try:
        port = int(raw_port)
    except ValueError:
        port = 8000
    return host, port


if __name__ == "__main__":
    run()
