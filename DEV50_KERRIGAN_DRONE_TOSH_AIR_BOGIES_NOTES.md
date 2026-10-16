# Dev50: Kerrigan placement, one-time PDD, Tosh, Air Bogies voice

- Fix Kerrigan safe-position search to fall back to walkable base-adjacent points if worker path reachability rejects everything; final fallback remains near player home. Existing selection, hero type, and respawn logic unchanged.
- Point Defense Drones now deploy ONCE at 10 seconds after macro base established. No five-second scanner, new-building follow-up or drone replacement; native timed-life behaviors still removed.
- Covert Assistance Tosh still gains 0.5 HP/s normally and receives an additional 1 HP/s while within range 8 of the player's base.
- Multiple Air Bogies: native Blizzard TRaynor03Tychus00013 uses SoundLink(...,-1), so prefer local registered Sound when present, use c_soundIndexAny and audio-only SoundPlay to avoid actor/portrait transmission silencing. The line queues once per successful wave.
- Native Spectre nuke test from Dev49 preserved, including fast first spawn and diagnostics.
- Offline tests cannot confirm SC2 runtime voice playback or mission-specific unit placement.
