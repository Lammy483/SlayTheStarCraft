# v1.1.2 Dev21 — Mercenary cooldown floor, Meat Grinder AI, Null Circuit protection

## Mercenary cooldown integrity

- Repeat Contractor now clamps every positive mercenary recruitment cooldown/charge timer to a minimum of **1 second** rather than letting a reduction produce zero.
- Horde Mode's ability timer halving also respects the 1-second floor for mercenary recruitment.
- Both Merc Compound and Predator Nest retain the **3-second watchdog**, which checks per-command, per-cost-entry, and shared mercenary cooldown/charge catalog fields after Archipelago tech upgrades. It corrects positive sub-second durations, and restores 1 second when a player-specific duration reaches zero/negative despite a positive baseline duration in the unmodified catalog. Naturally zero-valued/unused timers remain zero.
- Existing overflow repair is **unchanged**: cooldown catalog values or active cooldown/charge timers over **500 seconds** reset to **10 seconds**. Ready abilities (zero time remaining) are not forcibly put on cooldown.

## Meat Grinder boon Marines

- Marines spawned by the boon already enter the autonomous clone/assault group but were only periodically retargeted when Cloning Technology was active.
- They now reacquire nearby reachable enemy structures or enemy units **every 10 seconds**, even when Meat Grinder is the only boon enabled. Initial attack-move behavior and uncommandable status are preserved. No changes to the hostile Meat Grinder mutation.

## The Purification — Null Circuits

- `NullCircuit` and `NullCircuitActivated` are excluded from Slay's direct scripted damage helper and Explosive Armor's direct-damage/death loop.
- Slay-created nuclear strike and Psi Storm effect requests now test their area against Null Circuit positions; if the area would overlap an objective, the scripted AoE is suppressed instead of risking an objective disappearing without its native death trigger.
- **Native mission damage, regular attacks, and objective/death scripts remain untouched.** This protection is deliberately limited to Slay-issued damage, not to invulnerability against every game effect.

## Checks

- 319 applicable offline regression tests passed; legacy `test_endless_mode.py` requires a live game and was not run.
- Source verification passed. Live StarCraft II verification is still needed, particularly mercenary cooldowns with multiple AP cooldown upgrades and Null Circuit destruction under overlapping explosions.
