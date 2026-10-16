# Dev43 - 50 immortals (mutation)

- Title: 50 immortals.
- Description: There are 30 immortals patrolling around the map.
- Severity: 3.
- Same logic as the existing Archons mutation: starts 120 game seconds after base established; attempts one unit per normal tick; places each on a valid hostile patrol ground point away from player/allied buildings; uses the existing hostile patrol targeter.
- Exactly **30 Immortals**, not 50, per the supplied description.
- Separate spawn/retry counters from Archons and Archons x5; no shared unit-count state.
- Registered in both run-generation paths and the mission effect catalog, using free extension-E bit 536870912.
- No new global campaign dependencies.
- Live SC2 testing still required.
