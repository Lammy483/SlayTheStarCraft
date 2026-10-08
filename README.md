# Slay the StarCraft

Slay the StarCraft is a single-player StarCraft II roguelike built on the Archipelago StarCraft II framework. A run generates a branching sequence of campaign missions with randomized mutations, blessings, shops, persistent progression, credits, and cross-campaign systems.

This repository tracks the source for the Windows launcher, Slay runtime/client integration, run generator, Galaxy gameplay layer, data catalogs, installer tooling, and validation scripts.

## Current development version

`1.0.2.17`

The stable public release lineage is `1.0.2`; `1.0.2.x` builds are development work toward the next bug-fix release.

### 1.0.2.17 changes

- True Golden Armada uses unrestricted random playable-map patrol destinations after 10 minutes, so attack-move routes can cross and engage the player base.
- Removed the temporary 10x development selection boost from recently added mutations; they now use normal selection weighting.

### 1.0.2.16 changes

- Fire in the Sky cannot roll or dynamically acquire the Another Gorgon blessing or mutation.
- Kerrigan displays `Kerrigan has respawned` when her Slay-managed respawn completes.
- Commander heroes display `<Hero Name> has respawned` after their one-minute respawn.
- The repository is cleaned for collaborative source control and includes validation/build helpers.

See [README.txt](README.txt) for the current player-facing development changelog and installation behavior.

## Repository layout

- `Payload/` - Slay Python runtime, generator, installer patches, Galaxy script, XML/game strings, and shop/effect catalogs.
- `Tools/` - portable runtime bootstrap, SC2 data installer, launcher setup utility, and native Windows launcher source.
- `docs/` - contributor-facing architecture, development, and known-issues documentation.
- `.github/` - CI and contribution templates.

Generated Python/Archipelago runtime data, run state, logs, ZIP releases, and compiled executables are deliberately not committed.

## Development setup

Requirements for source development:

- Windows 10/11
- StarCraft II with the campaign content used by Archipelago SC2
- Python 3.13 for local validation/tooling
- Go for rebuilding `SlayTheStarCraft.exe`

Validate the repository without requiring a populated Archipelago runtime:

```powershell
python .\Payload\verify_release.py --source-only
```

Build the native Windows launcher:

```powershell
.\Tools\build_launcher.ps1
```

For a normal portable install/test, the launcher/bootstrap downloads its private Python and pinned Archipelago runtime into `Runtime\`; nothing is installed into the system Python environment or PATH.

## Contributing

Fork the repository or create a feature branch, make one focused change, run source validation, and open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

For gameplay changes, avoid replacing working Galaxy behavior just to refactor it. Mission-specific SC2 variants and campaign dependencies matter; test across Wings of Liberty, Heart of the Swarm, and Legacy of the Void when the affected mechanic is cross-campaign.

## Releases

Source control should contain source and small data files. End-user ZIPs and compiled launcher binaries should be attached to GitHub Releases rather than committed to Git history.

## Third-party software and game data

Slay the StarCraft integrates with Archipelago and StarCraft II. The bootstrap downloads a pinned Archipelago source snapshot and uses the user's existing StarCraft II installation. Blizzard game assets and the large Archipelago runtime are not stored in this repository.

## License

No standalone license for Slay the StarCraft has been selected in this repository yet. Contributors should not assume rights beyond those granted by applicable upstream licenses and copyright law until a project license is added.
