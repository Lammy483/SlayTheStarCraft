# Slay the StarCraft v1.1.2 Dev28 — Lab Rat hostile spawns and Zagara fixes

Based on the **Dev27** lightweight Windows distribution. This is an offline development build; no GitHub branch was updated.

## Lab Rat (hostile spawn exclusion)

- Keep the completed-supply + seven-second base-established gate.
- On Lab Rat, candidate **enemy** spawn points must be at least **15 map units** from the player's home/base structure.
- New hostile ground-point finder retries safe, passable, player-reachable positions, extending the range when nearby points are inside the protected area.
- Delayed enemy Odin uses the safe finder. If it cannot find a valid position, retry later; **never** fall back to the enemy building's unsafe position.
- Shared enemy raid-air/ground and hero-patrol origin selectors also enforce the final-position Lab Rat limit. No change to other missions' clearance.
- Zagara's Banelings use the same safe ground-point finder for their attack-wave origins.

## Zagara's Banelings enemy mutation

- Attack-move (not the general AI helper that can fall back to plain move) toward the nearest *reachable* player structure.
- If no reachable building exists, target a reachable player mobile unit; then try the home structure, then an accessible patrol point.
- Reacquire targets at four-second intervals, and release native AI script control.
- Preserve **100 Banelings** per wave and the ten-minute mission-clock cadence. Spread them across up to five safe spawn points (20 each) to reduce the single-point body-blocking problem; if fewer than five positions are valid, use the first safe point rather than dropping units.

## Zagara Commander

- The selected commander index is **18**. The previous index-18 mapping returned `Zagara`, even though campaign mission scripts create `ZaGara`.
- Resolve index 18 to `ZaGara` via a native catalog check, without choosing an unrelated fallback hero if it is absent.
- Non-HotS missions request Swarm dependencies when the Commander blessing selects Zagara; HotS uses native assets. Respect existing sensitive-mission dependency restrictions.
- Spawn/respawn the native `ZaGara` directly; report an unavailable catalog to the player rather than silently spawning another hero.

## Verification

- Offline Galaxy/source validation and regression tests only. In-game SC2 appearance and AI/pathing remain to be confirmed.
