"""Apply user-editable Slay hotkeys without downloading or reinstalling data.

Called on every launcher start; Download Data independently applies the same INI
through install_slay.install(). No system Python or global package required.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import importlib.util


def load_hotkey_helpers():
    """Load the sibling installer without relying on Python's module search path.

    The portable Python runtime uses an isolated ._pth file that omits Payload.
    Normal ``from install_slay import ...`` therefore fails on Launch Slay even
    though the file exists right beside this script.
    """
    installer = Path(__file__).resolve().with_name("install_slay.py")
    if not installer.is_file():
        raise FileNotFoundError(f"Required Slay hotkey helper is missing: {installer}")
    spec = importlib.util.spec_from_file_location("_slay_hotkey_installer", installer)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load Slay hotkey helper at {installer}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return (
        module.patch_mod_game_hotkeys,
        module.patch_warpgate_hotkey,
        module.read_warpgate_preference,
    )


def apply_hotkeys(portable_root: Path, sc2_root: Path) -> tuple[str | None, bool, int]:
    patch_mod_game_hotkeys, patch_warpgate_hotkey, read_warpgate_preference = load_hotkey_helpers()
    key = read_warpgate_preference(portable_root)
    game_hotkeys = (
        sc2_root / "Mods" / "ArchipelagoTriggers.SC2Mod"
        / "enUS.SC2Data" / "LocalizedData" / "GameHotkeys.txt"
    )
    if not game_hotkeys.is_file():
        raise FileNotFoundError(
            f"The Slay mod hotkeys are not installed at {game_hotkeys}. "
            "Click Download Data to install them."
        )
    current = game_hotkeys.read_text(encoding="utf-8-sig")
    updated = patch_mod_game_hotkeys(current, key)
    changed = updated != current
    if changed:
        try:
            game_hotkeys.write_text(updated, encoding="utf-8")
        except PermissionError as exc:
            raise PermissionError(
                f"Could not update Warp Gate key inside {game_hotkeys}. "
                "Close StarCraft II and click Download Data to apply the "
                "preference with the required permissions."
            ) from exc
    changed_profiles = patch_warpgate_hotkey(key) if key is not None else []
    return key, changed, len(changed_profiles)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable-root", required=True, type=Path)
    parser.add_argument("--sc2-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        key, mod_changed, profiles_changed = apply_hotkeys(args.portable_root, args.sc2_root)
        print(f"Warp Gate hotkey={key}; mod updated={mod_changed}; custom profiles updated={profiles_changed}")
    except (OSError, ValueError) as exc:
        print(f"Warp Gate preference error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
