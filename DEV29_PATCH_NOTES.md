# Slay the StarCraft v1.1.2 Dev29 — Zagara fallback and bounded Baneling AI

Based on Dev28. No GitHub changes.

## Dependency behavior

- Verified that the Swarm dependency for Zagara remains conditional on the General blessing selecting commander index 18; it is not loaded globally.
- Preserved existing dependency-sensitive-mission restrictions and all unrelated Swarm, Void, Kerrigan, and Artanis requirements.
- On maps that naturally supply Swarm data, do not add a duplicate dependency.

## Zagara Commander

- Prefer the campaign-native `ZaGara` unit as in Dev28.
- If no such unit catalog entry is available, pick another catalog-valid hero from the existing Commander roster, excluding Zagara.
- If `ZaGara` has a catalog entry but the actual spawn fails, try the alternate Commander hero immediately.
- On later Zagara respawn failures, also try a different available Commander and retain that hero type for subsequent respawns.
- The player receives an in-game notice when a fallback hero was successfully deployed.
- Artanis retains strict native `ArtanisVoid` behavior.

## Zagara's Banelings mutation

- Limit target reacquisition to 25 Banelings each one-second mission tick, using a round-robin cursor.
- The first batch is issued at spawn, not all 100 commands together; the rest are issued over the following mission ticks.
- Preserve native attack-move ordering and search for reachable player buildings, units, then fallback destinations.
- Preserve all 100 units per wave (five spawn clusters of 20) and the mission-clock wave cadence.
- Reset retarget cursor when a mission starts, and retain progress across surviving waves.

## Validation

Offline source and regression verification only. Live SC2 tests still needed for Zagara and Baneling movement.
