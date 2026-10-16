# Dev41 — Four new mutations/blessing

Based on the Dev40 Nydus/Archangel Windows build.

## New effects
- Point Defense Drones (mutation, severity 1): one persistent Raven Point Defense Drone beside each enemy structure, including new structures. Excluded from timed-defense maps. Uses a capped rolling scan to prevent large unit-creation spikes. Removes existing TimedLife behaviors from spawned units.
- Heavily-Defended Drakken Laser Drill (mutation, severity 6): shares existing hostile drill 3-minute post-base timer and targeting/visibility/safety logic, with five SiegeBreakers and five MissileTurrets spawned in its vicinity when the drill appears.
- Multiple Air Bogies (mutation, severity 1): three Mutalisks at 5 minutes after base establishment, then another wave with one additional Mutalisk, wave intervals starting at 2m and growing by 10s per wave. After global mission time 10m, a 25% roll each elapsed minute permanently increments the Brood Lord count included in later waves. Origin is a map edge >=10 from player/allied structures.
- Covert Assistance (blessing, severity 1): player-owned but uncommandable Tosh becomes active at mission time 1:00 once a player home structure exists. Allied-targeting hero AI, defensive matrix if available, Tosh's native Psi Shield as fallback; retreats below half health and re-enters battle only at full health. Regenerates 0.5 HP/sec and never respawns. Excluded from island missions.

## Compatibility and validation
- Preserved three-race Galaxy keyword fix, Dev40 Nydus logic and Archangel audio testing, gameplay VO, and existing fixes.
- No additional global SC2 dependencies.
- Uses previously unused bank-E effect-mask bits, no transport protocol changes.
- Galaxy source verification passed. Thirty focused and historical offline regression tests passed.
- Not verified by SC2 runtime compilation or actual in-game play. Test a mission before assuming all new effects work.
- Dev35 hash gate is not included; install the new shared Galaxy/data with Download Data when switching builds.
