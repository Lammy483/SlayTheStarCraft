# Dev19 — Marauder Kill Team ground placement and group movement

- Spawn only on walkable ground connected to the player's base, near hostile buildings, avoiding cliffs and building-center fallbacks. Missing teams retry without respawning dead teams.
- Each team remains 15 Marauders and 3 Medics, created in three compact five-Marauder subgroups within 1.8 map units of its shared center.
- Each team gets ONE reachable attack-move waypoint. Every surviving squad member must arrive within 9 range before the whole team receives its next waypoint.
- A 90-second watchdog may reissue the existing waypoint but never assigns scattered individual destinations.
- Existing 12-minute safe-patrol phase, one-time audio, squad composition, and buffs retained.
- Fog-of-war visual rendering remains unchanged pending a separate Dimmed-fog experiment.
- Full portable Windows ZIP and auto-launch update scripts remain bundled.

Offline source tests included. Live gameplay and pathing still need verification.
