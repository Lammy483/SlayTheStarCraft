Slay the StarCraft v1.1.0

Slay the StarCraft is a single-player StarCraft II roguelike built on the
Archipelago StarCraft II framework.

V1.1.0 DEVELOPMENT

- True Golden Armada now chooses unrestricted random playable-map patrol destinations after 10 mission minutes. Its fleet attack-moves to those points, so routes can naturally cross and engage the player base.
- Removed the temporary 10x development selection boost from recently added mutations; new mutations now use the same normal selection weighting as established mutations.
- Fire in the Sky now excludes both Another Gorgon blessing and mutation in initial generation and runtime/random-effect acquisition.
- Kerrigan and Commander heroes now announce successful respawns in game chat using player-facing hero names.
- This development source tree is prepared for GitHub collaboration; generated runtime/cache/binary artifacts are intentionally excluded from source control.
- Terran/Zerg/Protoss Upgrade Pack boons require at least 3 actually owned unit/morph unlocks of that race. Buildings, mercenaries, Nova equipment, Royal Guard, and merely shop-available units do not count.
- Enemy Spear of Adun mutation is disabled in generation, runtime activation, and Golden Goose/Risky Investment purchase paths until a reliable implementation exists.
- Death-spawn exclusions now cache SC2 timed-life status when units are created in addition to checking it at death, preventing temporary units from producing Zombies, Zombie Apocalypse units, or No Deaths Allowed Ultralisks even if their timed-life behavior is removed during death handling.
- Windows bootstrap no longer depends on building the legacy mpyq 0.2.5 source distribution. It downloads/validates the pure-Python module directly, fixing the release-1.0.2 failure seen on some clean machines.
- Standardized death-trigger exclusions so temporary/fake units do not recursively create death-spawn units. Locust/LocustFlying, Broodlings, Interceptors, Changelings, hallucinations/decoys, workers, timed-life units, and Slay-marked uncommandable/free units are excluded from zombie death spawns and No Deaths Allowed ultralisks.
- Lab Rat does not count the tiny gated opening as an established base. Slay waits for 300 newly collected minerals and newly made supply before enabling base-established hostile effects.
- Brakk's Pack and Odin now announce their timed attacks in game chat.
- Enemy Spear of Adun now prefers AP's autonomous Spear caster, creates a regular caster as fallback, uses broader ability-name matching, and retries failed casts quickly instead of silently waiting for the next long interval.
- Leviathan Approaching sets the Leviathan's Bio/Plasmid/Stasis special-ability cooldown paths to 120 seconds for the hostile owner.
- Corrected the runtime/map-side red-border threshold to 250 as well as the generator, so displayed elite borders use the stricter v1.0.2.11 rule consistently.
- Hotfix: corrected the installer pre-install verifier to expect shop stock logic version 109.
Built on the v1.0.2.10 development branch from the stable v1.0.2 release.
- AP mission difficulty now uses a smooth campaign-length-independent tier distribution. It starts at 48% Starter / 38% Easy / 12% Medium / 1.9% Hard / 0.1% Very Hard, then exponentially tilts toward harder tiers by fractional run progress with steepness 1.8. The AP tier is rolled before the mission, so tiers with more candidate missions do not receive extra probability.
- The guaranteed Starter opening option remains, and the final mission is always Very Hard.
- Mission-tier progression is slightly faster than v1.0.2.10 while remaining campaign-length independent.
- Mutation severity now compensates for AP mission tier: the mutation mean shifts by +2 severity for each tier below the layer's expected AP tier and -2 for each tier above it, with fractional tier differences interpolated.
- Red/elite borders now require 250 danger points above the layer expectation instead of 200, making marginally-above-average missions less likely to be marked red.
- Normal and True Golden Armada non-Phoenix ships now use 1.9 movement speed for tighter fleet cohesion. For the first 10 mission minutes, Armada patrol destinations and sampled route segments avoid player-controlled and player-allied buildings by at least 25 range, with conservative extra formation clearance.
- True Golden Armada Mothership now has 1000 life and 1000 shields.
- Orlan's Planetary Fortress now prioritizes the JacksonsRevenge unit link and dynamically scans loaded unit catalog entries for Jackson variants before falling back to generic mercenary battlecruiser aliases.
- Leviathan Approaching now stops permanently once it reaches 30 range of a player building; its spawned Mutalisks and Brood Lords receive attack orders toward the player instead.
- Leviathan Approaching retaliates to its first damage with one extra Mutalisk cast and unleashes 20 Mutalisk casts over 4 seconds when it first falls to half life.
- Odin now spawns only once, attack-moves toward the player, uses Odin Barrage on unit clumps or defensive structures, and never respawns after death.
- Odin and Torrasque detect 30 seconds of blocked movement and can destroy allied structures physically trapping them.
- Orlan's Planetary Fortress now prefers the BattlecruiserMerc catalog entry for Jackson's Revenge and replenishes its repair crew back toward 20 SCVs.
- Autonomous combat movement is standardized around three behaviors: attack-move toward a strategic target, attack-move while patrolling the map, and plain move for effects that intentionally should not engage along the route.
- Allied Zombies, Cloning Technology units, Meat Grinder Marines, allied support units, hostile scripted raiders, Dark Templar raids, Tal'Darim Reinforcements, Dehaka's Pack, and occasional replacement attackers use attack-move routing so they engage enemies encountered while traveling.
- Autonomous allied and hostile combat groups now receive generic ability-use checks while moving; casts queue the prior travel/combat order again afterward so ability use does not strand the unit. Support/reactive abilities can also fire between engagements, while offensive abilities still require a valid target in their actual range.
- Marauder Kill Teams are restored to two independent map-patrol squads. Each squad shares a patrol destination, attack-moves through enemies, keeps its Medic support with it, and is included in hostile autonomous ability handling.
- Race Upgrade shop categories may roll unit-specific upgrades only when the corresponding unit is already owned or is one of the actual unit cards currently displayed in that race's Unit shop.
- Diamondbacks now choose connected patrol destinations across the whole map: 60% toward enemy-base areas and 40% anywhere pathable.
- The mutation/blessing chat summary is delayed until the mission UI is active so it reliably appears at mission start.
- Spreadsheet balance updates applied: Torrasque now waits 5 seconds to respawn; Dehaka's Pack uses the new 3/6/9/12-minute cadence; Ultimate Harassment is severity 5 with its updated description.
- Added True Golden Armada (severity 6), including the massive fleet, circling Phoenixes, Revelation Oracles, early-base safety, and the Mothership-death attack transition.
- Random Blessing purchases now open a result popup showing the blessing and
  its description.
- Unit Upgrade Pack purchases now open a result popup listing every granted
  upgrade with descriptions and available item images.
- Reroll Mutations and Blessings now also rerolls the currently selected
  unfinished mission. A mission already running keeps its current launch state,
  but the rerolled effects are used the next time that mission boots.
- Rory Swann in Heroes of the Storm now has dedicated Flaming Betty handling,
  including a native-order attempt and a guarded campaign-unit fallback.
- Vorazun Commander and Heroes of the Storm now use the actual campaign hero
  catalog entry instead of the unreliable bare Vorazun id.
- Tychus remains available to Heroes of the Storm as the campaign Tychus hero
  and remains excluded from normal Commander rolls.
- SCV Jump Jets no longer occupies a command-card slot, preventing it from
  overlapping the Archon Merge command while leaving the passive upgrade active.
- Campaign Length is now configurable from 2 to 31 missions, defaulting to 12.
- Mutation and Blessing Frequency are numeric multipliers; 0.40 means 40% of the
  normal per-mission severity mean.
- Non-12-mission campaigns dynamically scale mutation/blessing pressure across
  their actual length. The final quarter guarantees a severity-4+ mutation and
  the stronger late mutation picker starts after the halfway point.
- AP mission difficulty scales smoothly by fractional campaign progress, so the
  same curve works for every supported campaign length rather than changing at fixed layers.
- Extra Shop Slots (0-3), Start with Spear of Adun, and Start with Kerrigan are
  now launcher options. Each extra slot counts as a starting Shop Expansion.
- Launcher setup fields are balanced evenly across four columns (3 settings each).
- Eight new mutations are included for testing in this development build. Their
  generation selection weights are temporarily multiplied by 10 so they are
  much easier to encounter.
- The new mutations include Hellion mineral-line run-bys, Diamondback wanderers,
  a base-stalking Leviathan, delayed Odin assault, combined Terran raids, Brakk
  with a primal army, Colonel Orlan's fortified Planetary Fortress, and an
  experimental enemy Spear of Adun.
- Those eight test mutations now use their intended short names and the player-facing
  descriptions contain only the concise descriptions, not implementation notes.
- Nexus Shield and Purifier ground reinforcements now use a deterministic 3-second
  Protoss warp-in presentation: the real unit is paused, fades in under the attached
  warp effect, then unpauses and attacks.

GETTING STARTED
1. Extract the entire "Slay the StarCraft v1.1.0" folder somewhere writable.
2. Release packages include SlayTheStarCraft.exe. GitHub source checkouts omit generated binaries; contributors should build it first with Tools\build_launcher.ps1.
3. Double-click SlayTheStarCraft.exe.
4. If required game data is missing or needs an update, click Download Data and
   leave the launcher open while downloading data. This may take several minutes.
5. StarCraft II is detected automatically in normal installations. If needed,
   use Select SC2 Folder and choose the StarCraft II folder containing Versions.
6. Once data is ready, Slay opens the run setup screen. Later launches go directly
   to Slay when the runtime and StarCraft II location are valid.

OPEN BETA
This release is intended for public testing. If you encounter a startup or data
preparation problem, keep the files under Runtime\Logs\; they contain diagnostic
information useful for bug reports.

Developer/debug commands remain available in the client for testing and recovery
from beta issues.

DATA AND INSTALLATION
- Python and Archipelago are stored privately under Runtime\ in this folder.
- Existing compatible Runtime data can be reused and updated in place.
- Nothing is added to the system Python installation or PATH.
- No Windows service, background updater, or Apps & Features entry is created.
- Official Archipelago SC2 API4 Maps/Mods are copied into the existing StarCraft II
  Maps/Mods tree as needed.
- Run files are stored under Runs\ and launcher state under Config\.
- The launcher is unsigned, so Windows may show an Unknown Publisher or
  SmartScreen warning.
