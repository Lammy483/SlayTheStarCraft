# Dev40 — Archangel and Nydus Worms

- Archangel: search original loaded Sound catalog by audio filename before local registration fallback (Warfield pattern); diagnostic shows Sound path, length availability. No dependency additions. Portrait not required.
- Nydus Worms mutation: severity 3; E bit 1; not available on Templar's Charge; first worm 240 seconds after macro base established, next worms every 60–70 seconds; valid ground-path-only locations within 2–15 of allied/player structures for the first worm, increasing maximum distance by 5 per worm; 3-second retry without consuming cooldown when no location.
- Each worm plays native WoL Birth 02 with birth sound, maintains map visibility while alive and repeats waves every 60 seconds starting 10 seconds after birth; streaming units one per 0.333 game seconds to player buildings with standard attack-move. Cap 32 simultaneously tracked worms, reusing dead slots.
- Blizzard mission reference: THanson01/T-Raynor03 scripts use NydusCanal, Birth 02, NydusWorm_Birth, Spell, NydusWorm_Unload.
- Static verification only; actual SC2 integration testing needed, especially Nydus collision/actor and HotS audio assets.
