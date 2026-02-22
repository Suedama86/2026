# Android-klient (APK)

Detta är en enkel Android-app (WebView) för Universal Overlay Agent.

## Syfte

APK:n gör det enkelt att använda verktyget på telefon:
- Ange URL till en körande UOA-backend
- Kör agenten via backendens webb-UI i appen

## Bygg

1. Öppna `android/` i Android Studio.
2. Vänta på Gradle sync.
3. Välj **Build > Build APK(s)**.

## Exempel på backend-URL

- Emulator: `http://10.0.2.2:8000/`
- Fysisk telefon på samma nät: `http://<din-lan-ip>:8000/`

## Viktigt

Denna mobilapp kör inte Playwright lokalt i telefonen.
Playwright körs på backend-servern (din dator eller server).
