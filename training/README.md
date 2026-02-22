# Utbildningspaket: 2-veckors pilot för Universal Overlay Agent

Detta paket är framtaget för att snabbt validera att nya användare (utan appkunskap) kan använda agenten för att köra avancerade funktioner i befintliga appar.

## Innehåll

- `pilot_plan_2_veckor.md` – dag-för-dag-plan.
- `onboarding_guide.md` – körschema för introduktion.
- `prompt_mallar.md` – färdiga mallar att använda i träningen.
- `ovningar.md` – praktiska uppgifter med acceptanskriterier.
- `kpi_scorecard_template.csv` – mall för mätning av resultat.
- `pilot_checklist.md` – checklista före, under och efter pilot.
- `kommunikation_till_deltagare.md` – färdig text till deltagarna.
- `scripts/sammanstall_kpi.py` – skript som sammanfattar KPI-data.

## Mål för pilot

1. Minst 80 % av deltagarna ska kunna slutföra en "advanced mode"-uppgift i minst två appar.
2. Median tid till lyckad körning ska vara under 12 minuter efter onboarding.
3. Genomsnittligt behov av manuellt ingripande ska minska mellan vecka 1 och vecka 2.

## Snabbstart

1. Välj 10 deltagare och 2–3 mål-appar.
2. Följ dag-för-dag-planen i `pilot_plan_2_veckor.md`.
3. Registrera varje körning i `kpi_scorecard_template.csv`.
4. Kör sammanställning:

```bash
python3 training/scripts/sammanstall_kpi.py training/kpi_scorecard_template.csv
```

## Viktigt

Piloten mäter både teknik och pedagogik. Om tekniken fungerar men användarna ändå fastnar är det ett utbildningsproblem som ska lösas med tydligare mallar, feedback och guideflöden.
