# Prompt-mallar för piloten

Använd mallarna som utgångspunkt och byt ut [hakparentes]-fält.

## Mall 1: Aktivera avancerat läge

```
Open [APP_URL] and enable advanced mode.
Turn on all relevant features for advanced usage.
First show me the plan in dry run, then execute.
After execution, verify that advanced mode is active.
```

## Mall 2: Specifika funktioner

```
In [APP_URL], enable advanced mode and turn on:
- [FEATURE_1]
- [FEATURE_2]
- [FEATURE_3]
Do not change unrelated settings.
Show verification steps at the end.
```

## Mall 3: Säker körning med bekräftelse

```
In [APP_URL], prepare all steps required to activate advanced mode.
Run in dry mode and stop before applying changes.
I will confirm before final execution.
```

## Mall 4: Felsökning

```
In [APP_URL], I tried to enable advanced mode but it failed.
Inspect available controls again, identify why it failed,
and propose a corrected plan with minimal changes.
```

## Mall 5: Verifieringsfokus

```
Enable advanced mode in [APP_URL] with all needed features.
After execution, list exactly what changed and how to verify each change.
```

## Riktlinjer för bra prompts

- Var explicit med mål och begränsningar.
- Ange om körningen ska börja i dry run.
- Säg till om vissa settings inte får ändras.
- Be alltid om verifiering i slutet.
