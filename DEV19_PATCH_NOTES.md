# v1.1.2 Dev19 — Regenerative Aberrations

- Fixed Regenerative Abberations not producing reliable healing for player-owned Aberrations, including AP campaign variants.
- Replaced the one-time `LifeRegen` property edit (which could be ignored/reset and was never reapplied due to per-unit tag) with direct, capped +10 HP every game second after base establishment.
- Uses the existing normal/legacy Aberration unit ID detection, including unit variants whose IDs contain either spelling.
- Does not heal dead units, cannot exceed max HP, does not reset other natural regeneration, and does not double-apply the boon.
- Scoped to the owned Aberration family rather than applying to all Zerg units or structures.
- Adds five regression tests. Live SC2 runtime validation remains pending.
- Built from v1.1.2 Dev18, retaining the Artanis commander and all earlier fixes. GitHub unchanged.
