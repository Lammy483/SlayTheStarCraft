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

## Notes

This release keeps the confirmed Galaxy initialization regression fixes. Offline tests cover the source, but not every mutation/mission combination has been live-tested. In particular, the final Dev51 Spectre retargeting update needs additional playtesting.
