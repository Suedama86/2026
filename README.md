# Universal Overlay Agent (MVP)

Detta projekt är en första fungerande version av en app som lägger en AI-agent ovanpå en befintlig webbaserad applikation.

## Vad MVP:n kan göra

- Inspektera en valfri webbsida och lista interaktiva kontroller (knappar, inputs, selects, switches).
- Tolka ett mål i naturligt språk, t.ex.:
  - "Enable advanced mode with all features"
  - "Turn on expert settings"
- Planera åtgärder och utföra dem automatiskt i sidan via Playwright.
- Köra i `dry_run` för att visa plan utan att klicka/skriver något.

> Viktigt: Detta är en MVP för webbappar. För desktopappar krävs integration med OS-tillgänglighet/API eller vision-baserad automation.

## Snabbstart

### 1) Installera beroenden

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
```

### 2) Starta API + UI

```bash
uoa-agent
```

Servern kör på:
- API docs: `http://127.0.0.1:8000/docs`
- Enkel UI: `http://127.0.0.1:8000/`

## Demo

En enkel demosida finns i `demo/demo_app.html`.

Starta en lokal filserver:

```bash
python -m http.server 9000
```

Öppna sedan i agentens UI:

`http://127.0.0.1:9000/demo/demo_app.html`

Ange mål:

`Enable advanced mode with all features`

## API

### `POST /inspect`
Begäran:

```json
{
  "url": "http://127.0.0.1:9000/demo/demo_app.html",
  "headless": true
}
```

### `POST /run`
Begäran:

```json
{
  "url": "http://127.0.0.1:9000/demo/demo_app.html",
  "goal": "Enable advanced mode with all features",
  "headless": true,
  "dry_run": false
}
```

## Arkitektur

- `uoa_agent/planner.py`: Tolkning av mål + planering av steg.
- `uoa_agent/web_adapter.py`: Webbinspektion och exekvering via Playwright.
- `uoa_agent/api.py`: FastAPI-endpoints och enkel frontend.

## Nästa steg för produktion

- LLM-baserad planering med kontext från UI-träd + historik.
- Human-in-the-loop med riskklassning och godkännande vid känsliga steg.
- Fler adapters (desktop accessibility, native app APIs, RPA-fallback).
- Persistenta app-profiler och lärande per applikation/version.
