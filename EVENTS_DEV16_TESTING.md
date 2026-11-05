# Events Dev16 — event handshake hotfix (experimental)

## Shared native-event activation fix
The AP mission client transmits `?APRogue`, `?SlayEvent` and
`?SlayMech` in succession. The Galaxy `APRG_Load_Func` callback
previously reset *only* the two new event packets (mask, parameters,
mechanical mode and event bank) to zero, while leaving preexisting
APRogue mutation masks alone. If the packets arrived before the
load-finished callback, all new native events silently failed together.

Dev16 keeps packet-driven event settings from mission-global initialization
through load completion and only resets the per-mission spawned actors.
The event handler now reports one chat acknowledgment on accepting a
nonzero mask, and Swann's handler reports its trial mode. These are
experimental diagnostics in the SC2 chat, **not event popup descriptions**.

## Simple full update from Downloads
Download the full Windows ZIP and the helper
`Install-Slay-From-Downloads.ps1` into your Downloads folder. From
**any PowerShell working directory**, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\Install-Slay-From-Downloads.ps1"
```

The helper finds the most recently downloaded Slay Dev ZIP and detects
existing installations beneath Downloads. Select the correct installed
folder if several are found. It runs the *newly downloaded* ZIP's updater,
which replaces the entire `Payload` and `Tools` directories plus all
packaged root files, reinstalls SC2/AP changes using your current runtime,
and preserves downloaded `Runtime`, saved runs, preferences and local
artwork. No `Download Data` required if runtime revision matches.

You can override discovery explicitly with `-ZipPath` and
`-ExistingInstall` using real paths.

## What to check in SC2
1. Select Nova's Mission and accept. After mission base establishment,
   look for `[Slay] Event effects activated (mask 3)` in chat,
   then `Nova has joined your forces`. The mask may contain additional
   flags in later runs.
2. Organism Field Test acceptance should show an event-mask acknowledgment
   for the selected challenge, then a spawn notice after base
   establishment. The Brutalisk should be visible in enemy territory.
3. Swann field test should show `[Slay] Swann trial activated (mode 1)`,
   and the first actor spawn notice after base establishment.
4. If the packet acknowledgment appears but a spawn notice doesn't,
   focus on placement, unit IDs and base detection. If no acknowledgment
   appears, focus on client packet delivery and event-state calculation.
5. Check one mission per race to rule out the three-race Galaxy error.
   Verify other missions, the shop and user artwork are unchanged.

Automated source validation and PowerShell parsing are not a live SC2
mission compiler; actual in-game outcomes remain to be tested.
