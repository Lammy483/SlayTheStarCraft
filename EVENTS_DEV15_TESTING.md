# Slay the StarCraft — Events Dev15 (experimental test build)

## Installation

This is a **complete lightweight Windows build**: all Payload, Tools, Config
examples, the launcher EXE, and release notes. The large downloaded Python,
Archipelago, and SC2 data are intentionally not included.

**Preferred update:** Extract this ZIP to a *separate* directory, close Slay
and StarCraft II, then run the included `Tools/Update-ExistingSlay.ps1`:

```powershell
powershell.exe -ExecutionPolicy Bypass -File ".\Tools\Update-ExistingSlay.ps1" -ExistingInstall "C:\path\to\your\Dev14" -NewBuild "."
```

Or run the previous updater inside your Dev14 installation with `-NewZip`
pointing at this ZIP. The new updater **replaces the complete Payload and Tools
folders, plus every shipped top-level file**, and then reinstalls the complete
Slay patch into your existing private Archipelago runtime and StarCraft II
mod. It preserves `Runtime`, `Runs`, installed paths, preferences, and imported
SC2 PNG/audio artwork. Previous Payload/Tools are backed up to
`Runtime/UpdateBackups/<timestamp>`.

If Windows says you cannot write to the StarCraft II mods folder, run the
PowerShell console as Administrator. A changed runtime revision will still
require Download Data; none was introduced in Dev15.

## What changed

- **Psionic Lords**: description and native damage trigger now use **3% per
  qualifying damage event**, independently for repeated attacks on the same
  enemy. The actual Psionic unit attribute is checked. Converted units remain
  AI-controlled. Psionic Guardians remains at 1%.
- **Nova and Brakk allies**: spawn real native hero actors after base
  establishment each eligible mission. No AP production variant substitution.
  Hero loss across missions is saved only on a real `UnitDied` event, not on a
  temporarily absent/hidden hero during Mothership Vortex.
- **Tosh, Nova and Zagara enemies**: actor creation is validated and retries
  if its unit/path is not viable; enemy heroes roam connected points within
  enemy territory. Enemy actor deaths use the same real-death receipts.
- **Abathur's Organism Field Test**: test Brutalisk now spawns on enemy-side
  walkable ground, tries valid Brutalisk catalog variants, is revealed, and
  patrols between enemy-side locations. Its death triggers quest completion;
  subsequent allied/enemy Brutalisks use validated spawns. Event acceptance
  popup no longer includes implementation/location notes.
- **Rory Swann's mechanical field test**: temporary trial units use direct
  native unit creation and safe base-adjacent ground instead of the AP
  production-variant resolver. Enemy failure units roam enemy territory.
  Event description and options pluralize the selected mechanical unit name.
- **Ground access:** enemy event spawns validate path connectivity to
  *walkable ground near the player's base*, not the unwalkable centers of
  town halls; a mobile enemy unit can act as an anchor if a mission currently
  has no enemy structures.

## Suggested in-game checks

1. Choose Nova at the initial test event, then enter any Standard mission.
   Check that Nova visibly appears after your base is established, in each
   following mission, and survives a Mothership Vortex without being recorded
   as killed. Verify actual death permanently stops later appearances.
2. Accept Abathur's Organism Field Test and enter the next mission. Check for
   `Abathur's Brutalisk field test has begun` in chat, a visible Brutalisk in
   connected enemy territory, enemy-side patrols, and the kill receipt.
3. Accept Swann's Field Test, inspect the displayed plural unit count, and
   check actual allied mechanical units spawn after base establishment. Make
   50 kills to claim the AP unlock. If failed, verify later enemy patrols.
4. Equip Psionic Lords with 30 Ghosts and attack high-health non-structure
   targets. Each qualifying damage event has a fresh 3% roll, including
   repeated shots at the same target. Converted targets should be AI-led.
5. Try each race to check Galaxy compilation, plus Events disabled to ensure
   the shared native script still works for ordinary missions.

## Validation

Local Python compilation, `verify_release.py --source-only`, and 49 regression
checks passed. No real in-game StarCraft II Galaxy compilation or actor spawn
was performed by this build process, so native behavior remains experimental.
