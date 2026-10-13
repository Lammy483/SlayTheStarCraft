# v1.1.2 Dev5 — Mutation threats to the player base and timing audit

## How to read this audit
All timings are **time after Slay identifies the macro base as established** unless they explicitly say **mission clock**. The readiness check normally requires a player worker and player structure for two update ticks. On Lab Rat it additionally requires a completed new non-town-hall supply provider, 300 mined minerals, and a seven-second delay after that provider is complete. Spawn attempts can be delayed if no legal pathable position or enemy owner exists. A delay means the first scripted event/order, **not immunity against ordinary SC2 combat AI** once a hostile is nearby. Mission-native enemy AI is not disabled by Slay's gate.

## Direct base-directed raids, drops, bombardment

| Mutation | First possible Slay hostile action | Later timing / notes |
|---|---|---|
| Too many Wraiths | Base + 1:00 | Repeat random 10–60 s initially, accelerating to 2–10 s by base + 12:00. Wraiths attack from different directions. |
| Viking Raids | Base + random 0:20–3:00 | Repeat random 20–180 s; land around mineral lines. |
| Dark Templar | Base + random 1:00–2:40 | Repeat every random 60–160 s, targeting player structures. |
| Drop Pods | Base + 2:00 | Repeat every random 40–80 s; hostile Terran infantry drops around map, and on non-island maps uses reachable ground. |
| Leviathan In Orbit | Base + ~0:20 | Drop pods increase frequency from one per 20 s to one per 2 s; can target near player units/base. |
| Jetpacks | Base + 2:00 | Second wave at +4:00; repeat about every 60 s afterward. Existing relevant enemy infantry can also fly. |
| Nuclear Annihilation | Base + 0:30 | A nuke sequence can start every 30 s; warning and detonation occur later. Location may be anywhere, including the base. |
| ANOTHER GORGON (enemy mutation) | Base + 2:00 | Enemy Gorgon spawns again every 60 s and flies toward the player. The identically named allied blessing is not a hostile threat. |
| Zagara's Banelings | Base + 10:00 | About 100 enemy banelings attack, repeating every 10 min. Distinct from the allied Zagara's Aid blessing. |
| Mineral Thieves | Base + random 0:01–0:30 | Enemy MULEs drop near mineral lines; repeat with a maximum random interval initially 30 s that shortens by 3 s per minute, to a 2 s minimum. They mainly steal resources, but constitute enemy entry into the base. |
| Hellion Run-by | Base + 0:45 | Repeat every 45 s; mineral-line infiltration. |
| Ultimate Harassment | Wraith +1:00, Viking +0:20, Hellion +0:45 | Independent ongoing raider timers: Wraith interval accelerates, Vikings every random 20–180 s, Hellions every 45 s. |
| Void Thrashers | Base + 3:00 | Repeat random 120–180 s, and attack player structures from range. |
| Drakken Laser Drill | As soon as base established and spawn succeeds | Enemy drill at least 30 range away from home base and 15 from any protected buildings; fires over long distance and pauses/retargets every ~9 seconds. |
| Purifier | Spawns after base establishment | Enemy mothership moves toward player base; escorted aircraft every 50 s, hostile ground waves every 120 s; no scripted initial grace period. Native Safe Haven purifier is separate. |
| Dehaka's Pack | Base + 3:00 | Primal army wave, interval scales with progression; attack retarget every 30 s. Dehaka hero first eligible +5:00, checked again every 3 min. |
| Torrasque | Base + 3:00 | First approach; after death, reappears after about 5 seconds, progresses in strength; retarget about every 10 s. |
| Marauder Kill Teams | Base + 5:00 | Two hostile teams spawn and patrol/attack; refresh their objectives every 30 s. |
| Raynor's Raiders | Spawn in enemy territory as soon as base established; **first flyby +5:00** | Hyperion and reinforcements fly toward your base, then return and repeat; next flyby normally 3 min after returning, with 90 s movement safety windows. |
| Mira's Mercenaries | Camp after base establishment | Every 60 s after spawn, two mercenaries attack random player structures until purchased. |
| Heroes of the Storm | Heroes spawn after base establishment | Random patrol routing begins +5:00; on timed-defense missions direct base orders begin +4:00 and repeat every 2 min. They can still fight naturally if approached earlier. |
| Tosh and his Boys | Tosh spawns in enemy territory after base establishment | Tosh begins patrol +3:00. Cloaked Spectres begin +4:00, then every minute while Tosh lives; Spectres try to nuke player buildings. |
| Brakk's Pack | Brakk and army spawn in hostile territory after base establishment | Direct attack on the player base at +10:00. |
| Odin (enemy) | Enemy Odin spawns in enemy base after establishment | Launches its scripted base assault at +13:00. Distinct from friendly Odin blessing. |
| Leviathan Approaching | Leviathan appears in enemy air territory when base established | Waits +4:00 before approaching the nearest player structure. Starts spawning Mutalisks/Brood Lords only after it stops near a player building. |
| Immortal Zergling | Base +1:00 | Spawns and attacks player structures; subsequent re-targeting; cannot be permanently killed by ordinary means. |
| 10 Minutes Until Destruction | **Mission clock 10:00**, provided base has been established | Every 20 seconds, sends enemy units to attack player structures. If base establishment is later than mission minute 10, starts at establishment. |
| Tal'darim Reinforcements | **Mission clock 20:00**, provided base has been established | Large Tal'darim assault waves every 60 s; existing wave targets retarget every ~30 s. |

## Patrols and roaming threats

| Mutation | Spawn/initial protection | Escalation and full access |
|---|---|---|
| Golden Armada | Spawn safely after base established; fleet patrols avoiding routes within **24 range** of player/allied non-tumor buildings until +4:00. | At **+4:00**, route clearance halves to **12 range**. At **+9:00**, unrestricted attack-move patrol destinations anywhere on playable map. |
| True Golden Armada | Spawn safely after base established; route clearance **40 range** until +10:00. | At **+10:00** clearance halves to **20 range**. At **+15:00** unrestricted attack-move anywhere; Phoenix orbit safety and Oracle Revelation restrictions follow this schedule. Mothership-death direct-base assault also delayed until +15:00. |
| Archons / Archons x5 | Begins spawning at base +2:00, outside a **15-range** protected structure clearance. | Adds up to 10/50 enemy Archons to roaming patrols; no explicit later base-access unlock, but normal aggro remains possible. |
| Siege Mode / Siege Mode x5 | Spawns after base established, tanks **at least 15 range** from player or allied non-tumor buildings. | 10/50 static siege tanks. They do not have an unlock timer; can fire if player approaches range. |
| Sniper Thor | Spawns after base established outside **20 range** of player or allied non-tumor buildings. | On timed-defense missions receives explicit base attack order at **+15:00**; otherwise enemy combat/aggro. |
| Diamondbacks | **Base +0:30** to spawn 50 wanderers | Wander repeatedly on their autonomous movement timer and may enter player areas; no staged safety cutoff. |
| Active enemies | **Base +2:00** | Continuously assigns attack-patrol routes to ordinary enemies, including paths through player territory; scans periodically; no later restrictions. |
| Burrowed Zerglings | 150 scattered after base established | No scripted assault timer. Can emerge/engage near player units. |
| Tower Defense | **Base +0:30** | Repeats hostile construction probes about every 30 s, pushing front structures toward the player. Excluded from Lab Rat generation. |
| Orlan's Planetary Fortress | Fortress, defenders, repairers spawn after base established, outside approximately **40 range** of player buildings. | Fortress weapon range increases by 1 every 30 s; eventual reach depends on location/survival. Stationary rather than patrol. |

## Event-triggered and indirect base threats

| Mutation | Trigger | Timing |
|---|---|---|
| Meat Grinder | Three visible hostile buildings periodically spawn zerglings, marines, or zealots; they attack player structures. | Sources selected only after base establishment; first wave after variable `APRG_CongaNextInterval` (initially about 24–36 s), then accelerates, depending on elapsed base time. |
| No Deaths Allowed | When a player unit dies, spawns an enemy Ultralisk near its death location. | No extra timer after base establishment; timed-life units excluded. |
| Zombie Apocalypse | Any eligible unit dies, creating hostile infested Terrans that target the player. | No extra timer after base establishment. |
| Zombies (hostile mutation) | Eligible death creates hostile infested Terran. | No extra timer after base establishment. The allied blessing with the same name does not threaten the player. |
| Victory is Temporary | Enemy has chance to respawn one minute after its death. | Death events only after base establishment, then **+1:00** delay per selected revival. |
| Nuclear Workers | A player's worker dies and detonates. | After establishment; can occur inside the base immediately on a worker death. |
| Nuclear Structures | An enemy building dies and detonates. | After establishment, at the building death event; near your army/base only when relevant. |
| Occasional Thor / Ultralisk / Colossus (enemy versions) | Selected hostile units transform into elites in place. | After establishment; some replacements receive a direct base attack order about **+5:00 after replacement**. The friendly blessing versions are not threats. |

## Scope and exceptions

- All listed **Slay mutations** are gated behind established-base readiness; enemy regeneration starts at established-base +1 s. Natural scripted mission enemies and normal campaign AI are **not** suppressed by this system.
- A distance restriction prevents scripted spawn/path selection but **does not make hostile units unable to attack** or stop every piece of native SC2 AI. Fleet escorts can aggro naturally before their full patrol unlock.
- `Enemy Spear of Adun` is disabled in this build; do not count it as a live attack. `Arguments` makes friendly units fight but doesn't spawn enemies. Pure economy/stat mutators (such as Enemy Regeneration, Adrenaline, Tactical Binoculars, Gargantuan Enemies) may increase the danger of ordinary enemies but do not initiate separate hostile routes or drops.
- Static sources that require pathing or a suitable enemy owner may fail to spawn on an individual map. Island maps have deliberate exceptions for airborne raids/drop locations.
