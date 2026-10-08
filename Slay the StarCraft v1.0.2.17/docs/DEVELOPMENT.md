# Development Guide

## Major components

### `Payload/generate_slay_run.py`
Creates the campaign map, chooses missions/effects, computes mission rewards and danger, and writes per-run state.

### `Payload/slay_the_starcraft.py`
Persistent Slay runtime logic used by the patched Archipelago SC2 client: shop state, inventory/progression, effect eligibility, rerolls, mission launch metadata, and UI state.

### `Payload/APRogue.galaxy`
Mission-side gameplay implementation. This contains mutation/blessing behavior, unit spawning and autonomous AI, hero handling, combat modifiers, and the `?APRogue` launch handshake.

### `Payload/install_slay.py`
Patches the pinned Archipelago SC2 client/runtime and installs Slay's Galaxy/data files. It contains strict pre/post-install checks intentionally designed to catch drift in the pinned upstream snapshot.

### `Tools/bootstrap_slay_runtime.ps1`
Builds the private portable runtime: embedded Python, pinned Archipelago source, Python dependencies, SC2 API data checks, and Slay patch application.

### `Tools/slay_launcher_windows.go`
Small native Windows bootstrap launcher used before the Python runtime exists.

## Validation

Source-only validation:

```powershell
python .\Payload\verify_release.py --source-only
```

Full install verification is performed by the portable setup flow against a real Archipelago runtime and StarCraft II installation.

## Generated files

Do not commit:

- `Runtime/`
- `Runs/`
- `Config/`
- downloaded Archipelago source/runtime files
- logs
- `__pycache__/`
- `SlayTheStarCraft.exe`
- release ZIPs

The repository should be sufficient to rebuild the small launcher and reproduce the bootstrap/install process without storing the large downloaded runtime.

## Galaxy conventions

- Keep loops bounded.
- Prefer catalog validity checks when campaign-dependent unit/ability IDs are involved.
- Use standardized attack-move/patrol/plain-move helpers instead of ad hoc movement when possible.
- Temporary/timed-life/fake units should not recursively trigger death-spawn effects.
- Preserve developer/debug commands used for beta recovery and regression testing.
- When changing mission compatibility, enforce exclusions both in initial generation and in runtime/dynamic effect acquisition paths.
