# Dev26 — Kerrigan respawns and lag mitigation

Based on Dev25. Version remains 1.1.2. GitHub untouched.

## Kerrigan

- The native mission revive or manual spawn is **not** announced immediately: the new unit must be alive and inside the playable map at least one full game second later.
- Creation favors a safe location by a living player home structure, rather than placing Kerrigan in combat at the position where she died. The cocoon/death point is a fallback only if home placement fails.
- A failed hero creation or immediate death retries after two seconds without restarting the original respawn timer or announcing a phantom hero.
- The early native HotS revive grace remains (2 seconds before Slay's timer); premature native replacement remains suppressed for Reckless upgrade timers.
- `APRG_FindShopKerrigan` requires an alive, correctly owned, selectable unit inside playable bounds; cocoon clean-up and upgrades run after the verified respawn.

## Meat Grinder

- Marine completions queue five identical Marine-family units; the 0.1-second fast-tick dispatcher creates at most two per tick and preserves owner, position, facing, supply-free state, uncommandability, handled tag, AI/retarget group, and count.
- Queue holds 1024 simultaneous production jobs; very unlikely saturation falls back to an immediate five-unit spawn **rather than dropping Marines**.

## Performance audit

- Automated Marine/Clone retargeting now handles up to 40 living units per one-second mission tick instead of causing a single large 10-second synchronized spike.
- Reuses filtered enemy building and mobile-unit target groups **within** each retarget batch, still evaluating distance and pathability individually per unit. This cuts redundant unit-group scans without changing target preference.
- Meat Grinder spawn burden is separated from the production-complete event. It uses the existing fast tick rather than registering a new trigger per Marine.
- Existing systems reviewed and left untouched to preserve gameplay: Zombie Apocalypse spawns already use a bounded job queue; mass consumables already use a global budget; the other high-count mission-specific scripted waves are not retimed because doing so could change combat difficulty.
- Additional large scaling risks not changed: pathability checks for very large armies are inherently expensive, and extremely large repeated on-death effects still cost engine work proportional to unit deaths. Proper SC2 client profiling remains necessary to prioritize further engine-side optimization.

Tests are offline source/regression checks; real SC2 runtime verification is still needed.
