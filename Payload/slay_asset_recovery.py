"""Recover locally extracted SC2 UI artwork from a previous Slay installation.

The public lightweight bundle intentionally does not contain copyrighted SC2
textures. The icon-map JSON alone is not an icon pack; without PNGs the
settings banner, shop portraits and themed buttons fall back to flat colors.
"""
from __future__ import annotations

from pathlib import Path
import shutil

THEME_BANNER = "ui_screen_mainmenurebrandlow.png"
THEME_BUTTON = "sc2_ui_glues_bluebuttons_taskbarbuttonup.png"


def locate_art(folder: Path) -> Path | None:
    """Accept a previous installation root, its Payload, or its art folder."""
    root = Path(folder).expanduser()
    candidates = (
        root,
        root / "slay_assets",
        root / "Payload" / "slay_assets",
        root / "Runtime" / "Archipelago" / "worlds" / "sc2" / "slay_assets",
        root / "worlds" / "sc2" / "slay_assets",
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / THEME_BANNER).is_file() and (candidate / THEME_BUTTON).is_file():
            return candidate
    return None


def import_art(folder: Path, destinations: tuple[Path, ...]) -> int:
    """Copy actual art to the portable payload and the installed AP UI module."""
    source = locate_art(folder)
    if source is None:
        raise ValueError(
            "No SC2 UI artwork found. Select the folder of your older Slay "
            "installation that still displays the original banner and shop icons."
        )
    count = sum(p.is_file() for p in source.rglob("*.png"))
    if count < 2:
        raise ValueError("Selected installation does not contain its UI artwork.")
    for destination in destinations:
        if source.resolve() != destination.resolve():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, destination, dirs_exist_ok=True)
    return count


def recover_from_siblings(portable_root: Path, destinations: tuple[Path, ...]) -> bool:
    """Reuse artwork from adjacent older installations without a network fetch."""
    portable_root = Path(portable_root)
    if not portable_root.is_dir():
        return False
    parent = portable_root.parent
    try:
        siblings = list(parent.iterdir())[:100]
    except OSError:
        return False
    for folder in siblings:
        if not folder.is_dir() or folder.resolve() == portable_root.resolve():
            continue
        if not any(word in folder.name.casefold() for word in ("slay", "starcraft")):
            continue
        if locate_art(folder) is None:
            continue
        try:
            import_art(folder, destinations)
            return True
        except OSError:
            continue
    return False
