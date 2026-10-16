# Dev47 — Live-test follow-up fixes

Based on the Dev46 Galaxy declaration-repair candidate; keeps the verified Dev40 Nydus fix and all Dev41–44 effects.

- **Archangel VO:** The two Archangel recordings were confirmed audible; the automatic two-clip preview and `?SlayVOTest` handler are no longer installed. Sound catalogs and normal campaign VO queue remain present.
- **Point Defense Drones:** Track the protected enemy structure by its permanent unit-tag DataTable key, only after a successful drone creation. A replacement drone is never spawned for the same building, even if a previous drone dies. Remove any `TimedLife`-flagged behavior on the drone, not only behaviors whose ID contains `TimedLife`.
- **Kerrigan:** All initial home spawns, first-placement moves, and home respawns select nearby pathable ground free of mineral congestion and reachable by workers when locally available. No fallback placement on the middle of an impassable town hall.
- **Covert Assistance:** When Tosh falls below half health, immediately queue his homebound move after the native Defensive Matrix cast (or issue it directly after the shield fallback). No 1.5-second wait for first retreat order.
- **Archons / Immortals:** Change only units belonging to the Slay hostile patrol group of these types. Draw patrol destinations from randomly selected enemy structure neighborhoods or open map territory, with a bounded search, walkable-route checks, and protection from passing through player/allied structures during the original restricted phase (20 range before 8 minutes after base, 10 range before 12 minutes, then unrestrained).
- **Spawn [amount] [unit] consumable:** Add kinds 1901–1918 to the same noncommandable group and bounded automatic attack-retargeting AI as Mass Marines.
- **Nydus Worms:** First worm spawns 5–25 range from player/allied structures; upper bound gains 5 range per new worm. Repeat the native `Spell` unload animation for each spawned unit during a wave.

## Validation

- `python Payload/verify_release.py --source-only` passed.
- 444 offline unit tests passed, including eight new focused regression checks.
- ZIP integrity checked on package creation.
- No in-game SC2 Galaxy compile or gameplay validation has been performed for Dev47.
