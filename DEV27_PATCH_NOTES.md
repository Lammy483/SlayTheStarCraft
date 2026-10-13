# Dev27 — Spider Mines are not structures

Based on Dev26. Slay version remains 1.1.2.

- Adds `APRG_IsSpiderMineType()` and shared `APRG_IsSlayStructureEffectEligibleType()` for campaign/AP Spider Mine IDs.
- Filters Spider Mines from the shared player, enemy, ground, and targetable structure collections so all boons using structure collections (notably Building Overcharge) ignore them.
- Filters allied building proximity checks; Spider Mines no longer count as a building for safe-spawn or patrol-clearance decisions.
- The Building Overcharge tracked-proxy cleanup path now handles preexisting Spider Mine sources too, rather than leaving orphan proxies.
- Keeps Widow Mine-specific guard and creeptumor exclusions.
- Also excludes Spider Mines from Nuclear Structures death effect, so a mine cannot count as an enemy structure for that mutation.
- Lab Rat already waits for a completed supply provider, 300 minerals collected, and seven extra seconds on Dev26 and the GitHub `develop/v1.1.0`/`release/v1.1.0` Galaxy code.

Offline verification only. Live StarCraft II testing recommended.
