Slay the StarCraft v1.0.2.7

Slay the StarCraft is a single-player StarCraft II roguelike built on the
Archipelago StarCraft II framework.

V1.0.2.7 DEVELOPMENT
Built on the v1.0.2.6 development branch from the stable v1.0.2 release.
- Diamondbacks now choose connected patrol destinations across the whole map: 60% toward enemy-base areas and 40% anywhere pathable.
- The mutation/blessing chat summary is delayed until the mission UI is active so it reliably appears at mission start.
- Spreadsheet balance updates applied: Torrasque now waits 5 seconds to respawn; Dehaka's Pack uses the new 3/6/9/12-minute cadence; Ultimate Harassment is severity 5 with its updated description.
- Added True Golden Armada (severity 6), including the massive fleet, circling Phoenixes, Revelation Oracles, early-base safety, and the Mothership-death attack transition.
- Recent development mutations, including True Golden Armada, retain 10x selection weighting for testing.
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
- AP mission-pool targets now rise linearly from 1 near the opening to 4 at the
  final mission, while the opening retains its special selection rules.
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
1. Extract the entire "Slay the StarCraft v1.0.2.7" folder somewhere writable.
2. Double-click SlayTheStarCraft.exe.
3. If required game data is missing or needs an update, click Download Data and
   leave the launcher open while downloading data. This may take several minutes.
4. StarCraft II is detected automatically in normal installations. If needed,
   use Select SC2 Folder and choose the StarCraft II folder containing Versions.
5. Once data is ready, Slay opens the run setup screen. Later launches go directly
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
