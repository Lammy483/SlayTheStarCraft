# Slay the StarCraft v1.1.2 Dev9

## Marauder Kill Teams
- No Marauder Kill Teams minimap pings on spawn or during subsequent retargeting.
- All members of both 15-Marauder/3-Medic teams are always visible to the player, using the existing moving-revealer system.
- Shared revealer capacity increased to 128 to avoid new teams exhausting the pool under common multi-mutation runs.
- Patrol behavior and 5-minute first spawn unchanged.

## Tosh and His Boys: Spectre nuclear strikes
- Existing native `Nuke` ability recognition could return a *valid order* despite campaign-specific missing ammunition requirements; the code then marked the mission complete and never performed the scripted fallback. The old fallback also required a cloaked Spectre to get within range 9 of its target, where it could die before beginning a strike.
- Every newly spawned Spectre now prepares for 4 seconds, selects a location within range 5 of the nearest eligible player building (creep tumors already excluded), displays a nuke-target indicator and a 12-second warning ping, then triggers the campaign `NukeDamage` effect directly.
- If the calling Spectre dies before detonation, the indicator is destroyed and the blast never happens. After a successful strike, the surviving Spectre resumes ordinary hostile combat AI.
- Tosh still spawns once; Spectres still first arrive 5 minutes **after base establishment** and recur every minute while Tosh is alive. Hostile staging positions must remain ground-pathable from the player's base.
- No enemy Ghost Academy or magazine is created. Other nuke effects and the player Ghost Reporting boon are unchanged.

## Testing
- Unit tests, source verification, and Windows launcher build are run offline. SC2 mission testing is still required, especially to ensure the NukeDamage effect is available in all campaign dependencies and revealers remain visible in fog.
