# v1.1.2 Dev14 — Mission effect announcement de-duplication

- Resolved repeated mutation and blessing announcements in the in-game SC2 chat. Previously, the fast-tick startup handler, regular startup handler, and the post-base reminder could each display the same lists (the first two shared a guard, resulting in two actual displays per mission).
- Now exactly one Galaxy `APRG_DisplayActiveEffects` call occurs per mission, three seconds after the player's macro base is established. This keeps the Dev6 visibility fix without repeating effects.
- The single-shot guard resets on mission load, not during reconnects or periodic ticks.
- The standalone Archipelago client's mission launch log/summary is retained; only the duplicated in-game Galaxy chat output is removed.
- All previous Dev13 gameplay changes are preserved. Requires a live SC2 check for actual mission UI timing.
