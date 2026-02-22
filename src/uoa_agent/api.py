from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from uoa_agent.models import InspectRequest, InspectResponse, RunRequest, RunResponse
from uoa_agent.web_adapter import PlaywrightWebAdapter

app = FastAPI(
    title="Universal Overlay Agent",
    version="0.1.0",
    description="MVP API for inspecting and automating existing web applications.",
)

adapter = PlaywrightWebAdapter()
ui_dir = Path(__file__).resolve().parents[2] / "ui"
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

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


@app.post("/run", response_model=RunResponse)
async def run_goal(request: RunRequest) -> RunResponse:
    try:
        elements, plan, logs = await adapter.run_goal(
            request.url,
            request.goal,
            headless=request.headless,
            dry_run=request.dry_run,
        )
    except Exception as exc:  # pragma: no cover - runtime/browser errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RunResponse(
        goal=request.goal,
        intents=plan.intents,
        inspected_count=len(elements),
        planned_steps=plan.steps,
        action_logs=logs,
    )


def run() -> None:
    host = os.getenv("UOA_HOST", "0.0.0.0")
    port = int(os.getenv("UOA_PORT", "8000"))
    uvicorn.run("uoa_agent.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
