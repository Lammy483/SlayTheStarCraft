# Slay the StarCraft v1.2.0

Release based on v1.1.2 Dev51. This is a feature update to v1.1.0.

## Highlights

- New mutations: Nydus Worms, Point Defense Drones, Heavily-Defended Drakken Laser Drill, Multiple Air Bogies, Hybrid Research, and Immortals.
- New Covert Assistance blessing: Tosh fights autonomously and retreats to recover.
- More consistent enemy patrol placement, autonomous consumable allies, scripted reinforcement behavior and mutation timing relative to base establishment.
- Tosh and His Boys Spectres use the native Tactical Nuclear Strike and choose strike targets when spawned.
- Campaign voice announcements for new and existing mutation events; improved WoL sound catalog registration.
- Improved Kerrigan and commander spawning, mission-specific behavior, and unit AI/performance.
- Additional generator, shop, map, consumable, launcher and Galaxy reliability fixes.

## Balance updates in this release

- Meat Grinder boon: **500 credits**.
- Infested Liberator unit unlock: **50 credits**.
- The uploaded October 2026 balancing workbook was audited across the Boons, Spear of Adun, Mercenaries, Kerrigan, Units and Upgrades, Consumables, and Events sheets. All other direct catalog prices were consistent.
- Archipelago Scout variants remain 80 credits.

## v1.2.0 Tosh/Spectre release-source hotfix

- Enemy Tosh casts his own defensive shield first without a hard 200-energy threshold blocking his remaining native abilities.
- Tosh and Spectres use reachable ground positions near hostile structures rather than rejecting paths to building footprint centers.
- Spectres retain their spawn-selected target, approach a reachable position inside native nuke cast range, retry stalled movement, and restore nuke-casting energy after a long cloaked approach.
- Native Tactical Nuclear Strike, temporary Ghost Academy ammunition, 5-minute first spawn and 60-second follow-ups remain unchanged.
- Static/source checks were updated; live mission verification remains necessary.

## v1.2.0 Tosh hotfix Galaxy syntax correction

- Replace a C/Galaxy++ `?:` conditional inadvertently introduced in the Tosh/Spectre hotfix with valid raw Galaxy `if/else` syntax. This addresses the script compilation failure observed as the three-race critical error.
- Add a static regression check that rejects unsupported conditional expressions in raw Galaxy source.

## v1.2.0 Tosh native-nuke approach correction (Dev52)

- Restore Dev49's actual working movement behavior: Spectres issue their first move immediately and reissue a direct move every 5 seconds, even when a stale order remains queued.
- Remove the 6–8-range random approach-point search that could return no valid point and leave the Spectre motionless after spawning.
- After 20 seconds without progress, recover toward the nearest pathable player structure and report the fallback in the existing nuclear diagnostics.
- Keep a strike target chosen at spawn (including the 25% mobile-target option); preserve the native Tactical Nuke Strike, Ghost Academy ammunition, and five-minute/one-minute timing.

## Notes

This release keeps the confirmed Galaxy initialization regression fixes. Offline tests cover the source, but not every mutation/mission combination has been live-tested. In particular, the final Dev51 Spectre retargeting update needs additional playtesting.
