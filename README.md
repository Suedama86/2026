# Universal Overlay Agent (MVP)

Detta projekt är en första fungerande version av en app som lägger en AI-agent ovanpå en befintlig webbaserad applikation.

## Vad MVP:n kan göra

- Inspektera en valfri webbsida och lista interaktiva kontroller (knappar, inputs, selects, switches).
- Tolka ett mål i naturligt språk, t.ex.:
  - "Enable advanced mode with all features"
  - "Turn on expert settings"
- Planera åtgärder och utföra dem automatiskt i sidan via Playwright.
- Köra i `dry_run` för att visa plan utan att klicka/skriver något.
- Safe mode: undvik riskabla toggles (t.ex. kontroller med "disable/off").
- Auto-finalize: försök klicka "Save/Apply" efter lyckad körning.

> Viktigt: Detta är en MVP för webbappar. För desktopappar krävs integration med OS-tillgänglighet/API eller vision-baserad automation.

## Snabbstart

### 1) Installera beroenden

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m playwright install chromium
```

### 2) Starta API + UI

```bash
uoa-agent
```

Servern kör på:
- API docs: `http://127.0.0.1:8000/docs`
- Enkel UI: `http://127.0.0.1:8000/`

> Servern lyssnar nu på `0.0.0.0` som standard för att kunna nås från mobil på samma nät.
> Ändra vid behov med `UOA_HOST` och `UOA_PORT`.

## Snabbast utan dator: kör i molnet (Render)

Målet här är att du ska kunna använda verktyget direkt från Pixel via en publik URL.

### 1) Publicera repo på GitHub

Om koden redan ligger på GitHub kan du hoppa över detta steg.

### 2) Deploya med Render Blueprint

Det finns en färdig `render.yaml` i projektet.

I Render:
1. Logga in på [render.com](https://render.com).
2. Välj **New +** > **Blueprint**.
3. Välj ditt GitHub-repo.
4. Deploya tjänsten (Docker byggs automatiskt).

### 3) Öppna från mobilen

När deploy är klar får du en URL som:

`https://<din-app>.onrender.com/`

Öppna den i Pixel (Chrome eller Android-appen) och kör:
- Demoapp-URL: `/demo/demo_app.html`
- Goal: `Enable advanced mode with all features`
- Klicka **Preview Plan** och sedan **Execute Plan**

## Android APK (WebView-klient)

För att köra verktyget enklare på Android finns ett native Android-projekt i `android/`.
APK:n innehåller en WebView som öppnar din UOA-backend.

### Förutsättningar

- Android Studio (senaste stabila)
- En körande UOA-backend (lokalt eller i moln)

### Bygg APK i Android Studio

1. Öppna projektmappen `android/` i Android Studio.
2. Vänta tills Gradle sync är klar.
3. Välj **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
4. Installera `app-debug.apk` på telefonen.

### Backend-URL i mobilen

När appen startar kan du ange backend-URL i fältet högst upp, till exempel:

- Emulator: `http://10.0.2.2:8000/`
- Fysisk mobil på samma Wi-Fi: `http://<din-dators-lan-ip>:8000/`
- Publik server: `https://din-domän/`

Om du kör lokalt behöver du starta backend med:

```bash
UOA_HOST=0.0.0.0 UOA_PORT=8000 uoa-agent
```

## Demo

En enkel demosida finns i `demo/demo_app.html` och serveras automatiskt via backend på:

`/demo/demo_app.html`

Ange mål:

`Enable advanced mode with all features`

## API

### `POST /inspect`
Begäran:

```json
{
  "url": "http://127.0.0.1:8000/demo/demo_app.html",
  "headless": true
}
```

### `POST /run`
Begäran:

```json
{
  "url": "http://127.0.0.1:8000/demo/demo_app.html",
  "goal": "Enable advanced mode with all features",
  "headless": true,
  "dry_run": false,
  "safe_mode": true,
  "auto_finalize": true
}
```

### `POST /plan`
Begäran:

```json
{
  "url": "http://127.0.0.1:8000/demo/demo_app.html",
  "goal": "Enable advanced mode with all features",
  "headless": true,
  "safe_mode": true
}
```

## Arkitektur

- `uoa_agent/planner.py`: Tolkning av mål + planering av steg.
- `uoa_agent/web_adapter.py`: Webbinspektion och exekvering via Playwright.
- `uoa_agent/api.py`: FastAPI-endpoints och enkel frontend.
- `android/`: Native Android WebView-klient som kan byggas till APK.
- `Dockerfile` + `render.yaml`: cloud deploy för mobilanvändning utan dator.

## Utbildning och pilot

För ett färdigt utbildningsupplägg (2-veckors pilot, onboarding, övningar, KPI) se:

- `training/README.md`

## Nästa steg för produktion

- LLM-baserad planering med kontext från UI-träd + historik.
- Human-in-the-loop med riskklassning och godkännande vid känsliga steg.
- Fler adapters (desktop accessibility, native app APIs, RPA-fallback).
- Persistenta app-profiler och lärande per applikation/version.
