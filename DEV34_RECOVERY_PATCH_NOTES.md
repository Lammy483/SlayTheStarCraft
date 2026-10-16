# Dev34 recovery build (v1.1.2) — three-race startup isolation, Odin/Torrasque, Jackson

This build is based on **Dev32** gameplay/voice source, not Dev33's new automatic VO test script. Dev33 introduced several extra test triggers/functions/timers. They are temporarily removed as the most recent potential source of the global Galaxy failure; the exact compiler error is not yet known. Dev32's two gameplay VO event hooks (Marauder Kill Teams and Mira purchase) remain intact.

- Enemy Odin mutation: up to 12 bounded retries to choose a location at least 5 range from all mineral fields; no forced spawn into a bad point, does not change 14-minute post-base timing.
- Enemy Torrasque mutation: spawn point validator rejects all points within range 5 of minerals (including fallback to hostile anchor). This is applied on every respawn.
- Jackson's Revenge (`DukesRevenge` / `AP_DukesRevenge`): targeted range behavior applies +50% of initial weapon range per Sniper Mercenaries stack, using an existing 0.05-per-stack range buff, avoiding duplicated stacking. Applies to units spawned before or after purchasing the upgrade. Other mercenaries' weapon catalog paths are unchanged.
- Launcher manifest aligned to actual compiled Dev31 portable runtime binary (Dev32 manifest was out of sync).
- No change to SC2 dependency load order, no changes to other player or enemy spawns, no global gameplay version upgrade.
- Dev33 approved voice catalog preserved in `Tools/voice_line_manifest.csv`; experimental Galaxy changes preserved as `Tools/SUSPENDED_Dev33_VO_Test.diff`, not installed or executed. The 21-line automatic voice test is disabled while resolving the reported all-race failure.

**Testing needed:** StarCraft II itself is not available in the build environment, so successful real Galaxy compilation has NOT been verified. First try generating/loading a Terran, Zerg, and Protoss mission. If all races still fail, capture the *first* Galaxy compile error from SC2's log/editor (not just the Slay critical message), and test a pre-voice Dev31 build. Then test Odin/Torrasque spawn placement and Jackson's visible weapon ranges.
