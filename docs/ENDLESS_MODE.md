# Experimental Endless mode

Based on main 1.0.2.17. This draft is stacked on the optional command UI contribution; merge/rebase that presentation change first. Standard mode remains the default and existing saves without a mode keep their original behavior.

Choose **Endless Mode** in Game Mode before generating a new run. Only the current floor is playable. Each floor offers two to four choices, subject to the pool size, with at least one normal mission; one is high risk, with a 25% chance of two high-risk choices after floor six when there are enough choices. The current floor's offered maps and the previous four floors cannot repeat, including race variants. A minimum of 15 distinct maps is required. Generation uses the existing mission pools, legal mutation/blessing rolls and exclusions. Difficulty rises through the four existing tiers every four floors. Rewards use the native formula plus a floor increment and high-risk premium.

Selecting a mission locks the choice until victory. Completed floors remain visible with their floor number and no connecting edges. State includes a floor token so duplicate/late victory notifications cannot advance the next floor. Runtime and saves keep canonical mission/item identifiers. Game scripts and the native results/exit behavior are unchanged.

## Validation

- Source verifier passed.
- 120-floor simulation: legal candidates, all-offer five-floor exclusion, deterministic regeneration, native rewards once, duplicate victory protection, state persistence/reload and Standard-mode compatibility.
- Hidden UI: three completed floors plus the active choices, aligned planets, disabled history and no edges.
- No StarCraft II game was launched. Live server/game reconnection and long-run balance remain playtest requirements. This is a draft contribution, not a claim of a fully playtested release.

To rerun the state test after installing the extension, generate an isolated run with `SlayTheStarCraft.py`, then run `python Tools/test_endless_mode.py --archipelago <runtime-directory> --run-json <generated-run-json>`.

Blizzard artwork/audio and player saves are excluded. See UI_CONTRIBUTION_NOTES.md for installation and optional assets.
