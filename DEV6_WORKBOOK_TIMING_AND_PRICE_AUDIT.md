# v1.1.2 Dev6 — Balance workbook audit (2026-10-11)

Source of truth: `Slay The Starcraft (3).xlsx` uploaded 2026-10-11.
Compared with `Slay the Starcraft (2).xlsx` from 2026-10-07 and the Dev5 source.

**Timing convention**: All new relative times start when Slay establishes the player's macro base, except verbatim **"at the X minute mark"** references, which use mission time. Enemy patrol protection checks a player or allied building, ignores creep tumors, and samples route segments. On ground, Slay uses short connected waypoints because SC2 pathfinding is not guaranteed to follow a direct straight line.

## Updated hostile mutation timing

| Effect | Dev5 behavior / previous phase | Dev6 workbook implementation |
|---|---|---|
| Golden Armada | 24 range for 4m, 12 range until 9m | 24 until 6m, 12 until 12m, then free |
| True Golden Armada | 40 range for 10m, 20 until 15m | 40 for 10m, 30 until 15m, 20 until 20m, then free; Phoenix/Oracle orders follow same bound |
| Archons | Spawn away from base; old route checks | 20-range route buffer until 8m, 10 range until 12m, then free |
| Heroes of the Storm | Earlier patrol end and forced base orders | Start patrolling at 5m, 20 range until 15m, then unrestricted; defense-map base order at 15m |
| Active Enemies | 2m start | Start at 3m; 15 range route exclusion until 6m |
| Tosh and His Boys | First patrol 3m, Spectres 4m | Patrol 4m, Spectres 5m, 30-range route clearance persists |
| Marauder Kill Teams | 5m spawn, old route restrictions | 15-range route clearance until 12m |
| Too Many Wraiths | 1m initial, max rate at 12m | First at 2m, max rate at 13m |
| Viking Raids | Earlier first, 20–180s interval | First at 3m; +3s to minimum interval every 3m; unit count still grows over time |
| Dark Templar | 1–2.7m initial | First at 5m; +10s to interval per spawned wave |
| Drop Pods | 2m | First at 4m |
| Leviathan in Orbit | Drops shortly after base established | First drop at 4m, interval decreases 1s/min to 2s |
| Jetpacks | Waves at 2 and 4m | Waves at 4 and 6m; subsequent pacing unchanged |
| Hellion Run-by | First 45s, 1–2 first | First at 4m with 1 Hellion, then +1 unit and +4s between waves |
| Diamondbacks | First at 30s, 60% enemy territory | First at 1m, 90% enemy-territory move choice, declining 5 percentage points/min |
| Void Thrashers | 3m first | 4m first |
| ANOTHER GORGON | 2m first | 3m first |
| Torrasque | 3m first assault | First assault at 4m; always-visible revealer follows new respawns |
| Raynor's Raiders | 5m first flyby | 6m30s first flyby |
| Brakk's Pack | 10m assault | 11m assault |
| Odin | Spawn at establishment, attack 13m | First spawn and attack at 14m |
| Sniper Thor | Timed-defense attack at 15m | Timed-defense attack at 16m |
| Occasional Thor/Ultralisk/Colossus | Attack 5m after replacement | Attack 6m after replacement |
| Immortal Zergling | 1m first spawn | 3m first spawn |
| Mira's Mercenaries | 1m attack order | 3m first attack order |
| Dehaka's Pack | 3m first | 4m first, with updated escalation at 7/10/13m |
| Purifier mutation | Approach and escort shortly after establishment | Appears at establishment; begins moving and wave cooldowns 2m after establishment. Safe Haven native mothership unaffected |
| Drakken Laser Drill enemy mutation | Can activate immediately | Activates at 3m; visible from activation and chat notification |
| Leviathan Approaching | Begin moving 4m after establishment | Moves at 5m; mutalisk every 30s and brood lord every 55s initially, accelerate until **the mission's 20-minute mark** |
| Ultimate Harassment | Its own raids start earlier than standalone versions | Wraith/Viking/Hellion first waves and recurrences match individual mutation timing rules |
| Zagara's Banelings | 10m after establishment | First wave at **the 10-minute mission mark**, as explicitly stated in the workbook |

This is a timing/safety reconciliation, not a blanket rewrite of unrelated mechanics; pre-existing mission-specific island exceptions remain.

## Route safety

* Protection is against **any** structure belonging to the player or an ally, **not just the starting town hall**.
* Creep tumors are explicitly omitted in Slay's own/allied-building searches.
* Air patrol destinations are validated with straight-line sampling along the path, not only endpoints.
* Ground patrols use connected **3–8 range** hops, sample the direct segment every approximately 3 range, and reselect frequently; **actual SC2 navigation detours cannot be guaranteed to avoid buildings**, so live mission testing remains necessary.
* These restrictions govern scripted patrols, not a unit's spontaneous standard combat AI when it encounters enemies.

## Price reconciliation

All spreadsheet prices matched their existing catalog entries after these updates:

| Item | Old effective catalog | New catalog |
|---|---:|---:|
| Shop Expansion | 300 | 200 |
| Temporal Field (Spear of Adun) | 150 | 200 |
| Elite Mercenaries | 400 | 500 |
| Repeat Contractor | 200 | 300 |
| Spear of Adun Recharge (consumable rarity) | 2 = 250 credits | 1 = 125 credits |

Already correct before Dev6: Spear unlock 500, Spear half-price item 500, Kerrigan half-price item 500, Saving Grace 200, Invasion Fleet 1500. The entire set of literal prices in Boon, Spear, Merc, Kerrigan, Unit, and Consumable catalogs now matches the new workbook. Both purchase cost and the runtime consumable definition were updated for Spear recharge. **The unit-shop row `archipelago scout variants (including caladrius)` is named `archipelago scout variants` in the runtime catalog, but both specify 80 credits.**

### Workbook conflicts / interpretations

1. **Hyperion in a Bottle**: The new workbook's *description* column still contains `with its legendary resistance removed`, directly contradicting the user's later explicit statement that it is developer-only. Dev6 retains `Spawn the WoL hyperion` as the user-facing description; the resistance behavior is untouched.
2. **Invasion Fleet**: The new workbook specifies **two drop pods per second**, while older notes specify one. Dev6 follows the newer workbook, changing the fast-loop cooldown to 0.5 seconds; start remains the **5-minute mission mark** and active for two minutes.
3. **Archipelago Scout variants (including Caladrius)**: The source catalog stores the generic `archipelago scout variants` key, still priced at 80. This may already match variants through the category fallback; the workbook doesn't supply specific unit IDs, so no new explicit Caladrius alias was invented.

## Other user-requested fixes

- Saving Grace pre-rolls up to 5 blessing severity when purchased, presents each selected blessing in the existing shop reveal popup, and stores the chosen blessings for the next eligible mission instead of silently rerolling a new set.
- Starting Slay-effect notification is displayed again once, three seconds after the base is established, to avoid being buried by native campaign startup messages. This does not clear normal Archipelago chat history.
- Torrasque visibility uses the existing reveal-follow system, with dead revealer slots reusable on each respawn.
- New source, catalog, and test contracts are included in this development ZIP.

## Verification

- `python Payload/verify_release.py --source-only` — passes.
- 252 offline unittest cases pass (excluding `Tools/test_endless_mode.py`, a standalone integration harness requiring Archipelago and run JSON arguments).
- Windows launcher rebuilt and packaged for v1.1.2 Dev6.
- **Live StarCraft II testing not performed.** In particular, Saving Grace UI display and ground pathfinding should be confirmed in game.
