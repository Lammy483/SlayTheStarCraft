# Dev31 — Evacuation and Mira’s Mercenaries

## Nuclear Annihilation
- Ban `nuclear_annihilation` for Evacuation (including `The Evacuation` and all three race variants) in the generator's mission-specific exclusions.
- Also ban it from in-run shop mutation rerolls; do not change its behavior or availability on other missions.

## Mira’s Mercenaries
- Found a reproducible cause of delayed camp creation: `APRG_FindMiraCampPoint` required a location at least 18 away from *all enemy units* in addition to a 40-range player/allied-building buffer and ground connectivity. If none existed it silently waited, so destroying enemy units could make the camp spawn unexpectedly late.
- Remove the unnecessary enemy-unit check; Mira is an enemy-owned camp and can share enemy territory.
- Prefer 40-range building separation, then try 26-range center separation on crowded maps such as Rendezvous. Preserve ground accessibility and an absolute rejection of unsafe positions near player/allied buildings. Never force an unsafe fallback.
- Do not report the camp as successfully spawned if no mercenary unit was created (e.g. invalid catalog data); retry later.
- Do not alter the 6000-mineral purchase, composition, or attack timing.

## Validation
- Source verifier and offline tests; no in-game testing.
- No GitHub push requested.
