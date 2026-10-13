# Dev12 — Leviathan in Orbit target selection and mercenary cooldown watchdog

## Leviathan in Orbit
Hostile Leviathan drop pods now choose random player-owned or player-allied units or buildings as targets, excluding creep tumors and non-gameplay helper units. If the target is above unwalkable terrain, retry other targets. On normal missions, preserve the connected-to-base pathing rule; island missions permit drops on other islands. Only fallback is next to a player home building, not an unrelated random point.

## Mercenary cooldown watchdog
Every 3 seconds after base establishment, scan available Terran Merc Compound and Zerg Predator Nest mercenary abilities. Runtime cooldowns and charge regeneration, plus ability catalog cooldowns for the affected command and nested cost fields, are reset to 10 seconds only if they exceed 500 seconds. Normal cooldowns remain unchanged. Applies with no mercenary upgrade purchases as well.

Dev11 sanitized runtime links but reset to 0 and did not directly examine command-level catalog cooldown fields; the 4,843-second tooltip can reflect either kind.

Offline regression/source checks do not substitute for live SC2 validation.
