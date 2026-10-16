# Dev51 — production native Spectre nuke targeting

Source base: Dev50. No catalog, global dependency, or voice playback changes.

- Tosh and His Boys: first Spectre spawn restored to 300 seconds (5 minutes) after the macro base is established. Subsequent successful spawns are one per 60 seconds while Tosh lives; failed spawns still retry at five-second intervals.
- A new `APRG_ToshSpectreChooseNukePoint` picks the actual **nuke point as soon as the Spectre spawns**. 25% of the time it uses the position of the nearest player/player-allied non-structure unit; otherwise it uses a point 0–4.5 away from the nearest eligible player/player-allied building. If no mobile target is available, it falls back to a building.
- Spectres move directly toward that locked point while script-controlled. The nuke is cast as soon as the Spectre is within 9 range; no attack-move or target reselection phase precedes the strike. A point is chosen later only if no eligible targets existed at spawn.
- Native `TacNukeStrike`, temporary hidden Ghost Academy ammunition, cleanup, and test diagnostics remain unchanged.
- The Multiple Air Bogies Tychus sound was confirmed audible by live test. Its implementation was **not changed** in this build.
- The three-race Galaxy repairs from Dev36 and Dev46 remain intact. Actual SC2 compilation and gameplay need an in-game test; source-level verification alone is not a compiler.
