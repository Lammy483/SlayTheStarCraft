











from __future__ import annotations



import argparse

import json

import os

import shutil

import subprocess

import sys

from pathlib import Path



PACKAGE_VERSION = "1.0.2.17"

PORTABLE_ROOT = Path(__file__).resolve().parents[1]

PAYLOAD_ROOT = PORTABLE_ROOT / "Payload"

TOOLS_ROOT = PORTABLE_ROOT / "Tools"

CONFIG_ROOT = PORTABLE_ROOT / "Config"





def _choose_directory(title: str, initial: Path | None = None) -> Path | None:

    try:

        import tkinter as tk

        from tkinter import filedialog

        app = tk.Tk()

        app.withdraw()

        chosen = filedialog.askdirectory(title=title, initialdir=str(initial) if initial and initial.exists() else None)

        app.destroy()

        return Path(chosen).resolve() if chosen else None

    except Exception:

        return None





def _find_archipelago() -> Path | None:

    candidates = [

        PORTABLE_ROOT / "Runtime" / "Archipelago",

        PORTABLE_ROOT / "Archipelago",

        PORTABLE_ROOT.parent / "Archipelago",

        Path.home() / "Desktop" / "SlayTheStarcraft" / "Archipelago",

        Path.home() / "Desktop" / "Archipelago",

    ]

    for candidate in candidates:

        if (candidate / "Generate.py").is_file() and (candidate / "worlds" / "sc2").is_dir():

            return candidate.resolve()

    return _choose_directory("Select your Archipelago source folder")





def _find_sc2() -> Path | None:

    candidates = [

        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "StarCraft II",

        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "StarCraft II",

    ]

    for candidate in candidates:

        if candidate.is_dir() and ((candidate / "Versions").exists() or (candidate / "Mods").exists()):

            return candidate.resolve()

    return _choose_directory("Select your StarCraft II folder")





def _find_python(ap_root: Path) -> Path:

    candidates = [

        PORTABLE_ROOT / "Runtime" / "Python" / "python.exe",

        ap_root / ".venv" / "Scripts" / "python.exe",

        Path(sys.executable),

    ]

    for candidate in candidates:

        if candidate.is_file():

            return candidate.resolve()

    raise RuntimeError("Could not find Slay's private Python runtime. Use Download Data in SlayTheStarCraft.exe first.")





def _run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:

    print("\n> " + " ".join(f'"{x}"' if " " in x else x for x in cmd))

    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)

    if result.returncode != 0:

        raise RuntimeError(f"Command exited with code {result.returncode}: {cmd[0]}")





def _validate_paths(ap_root: Path, sc2_root: Path, python_exe: Path) -> None:

    required_ap = [

        ap_root / "Generate.py",

        ap_root / "MultiServer.py",

        ap_root / "worlds" / "sc2" / "client.py",

        ap_root / "worlds" / "sc2" / "client_gui.py",

    ]

    missing = [str(path) for path in required_ap if not path.is_file()]

    if missing:

        raise RuntimeError("Archipelago runtime is incomplete: " + ", ".join(missing))

    if not python_exe.is_file():

        raise RuntimeError(f"Python executable does not exist: {python_exe}")

    if not sc2_root.is_dir():

        raise RuntimeError(f"StarCraft II directory does not exist: {sc2_root}")

    trigger = sc2_root / "Mods" / "ArchipelagoTriggers.SC2Mod" / "Base.SC2Data" / "LibABFE498B.galaxy"

    if not trigger.exists():

        raise RuntimeError(

            "Official Archipelago SC2 data is missing. The launcher data download should install it before this step."

        )





def _parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument("--archipelago", type=Path)

    parser.add_argument("--sc2", type=Path)

    parser.add_argument("--python", dest="python_exe", type=Path)

    parser.add_argument("--portable-runtime", action="store_true")

    parser.add_argument("--archipelago-ref", default="")

    parser.add_argument("--non-interactive", action="store_true")

    return parser.parse_args()





def main() -> int:

    args = _parse_args()

    if os.name != "nt":

        print("This setup helper is intended for Windows.")

        return 2

    try:

        ap_root = args.archipelago.resolve() if args.archipelago else _find_archipelago()

        if ap_root is None:

            raise RuntimeError("No valid Archipelago source folder was selected.")

        sc2_root = args.sc2.resolve() if args.sc2 else _find_sc2()

        if sc2_root is None:

            raise RuntimeError("No valid StarCraft II folder was selected.")

        python_exe = args.python_exe.resolve() if args.python_exe else _find_python(ap_root)

        _validate_paths(ap_root, sc2_root, python_exe)



        env = os.environ.copy()

        env["PYTHONNOUSERSITE"] = "1"

        env["SKIP_REQUIREMENTS_UPDATE"] = "1"

        env["SC2PATH"] = str(sc2_root)

        env["SLAY_PORTABLE_ROOT"] = str(PORTABLE_ROOT)

        env["KIVY_HOME"] = str(PORTABLE_ROOT / "Runtime" / "KivyHome")



        print(f"Slay the StarCraft v{PACKAGE_VERSION}")

        print(f"Archipelago: {ap_root}")

        print(f"StarCraft II: {sc2_root}")

        print(f"Python:       {python_exe}")

        print(f"Portable dir: {PORTABLE_ROOT}")

        if args.portable_runtime:

            print("Runtime mode:  private/self-contained")



        _run([

            str(python_exe), str(PAYLOAD_ROOT / "verify_release.py"),

            "--archipelago", str(ap_root), "--sc2", str(sc2_root),

        ], PAYLOAD_ROOT, env)

        _run([

            str(python_exe), str(PAYLOAD_ROOT / "install_slay.py"),

            "--archipelago", str(ap_root), "--sc2", str(sc2_root),

        ], PAYLOAD_ROOT, env)



        config = {

            "format_version": 2,

            "slay_version": PACKAGE_VERSION,

            "archipelago_root": str(ap_root),

            "sc2_root": str(sc2_root),

            "python_exe": str(python_exe),

            "runtime_mode": "portable" if args.portable_runtime else "external",

            "archipelago_ref": args.archipelago_ref or None,

        }

        CONFIG_ROOT.mkdir(exist_ok=True)

        (CONFIG_ROOT / "slay_install.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

        (PORTABLE_ROOT / "Runs").mkdir(exist_ok=True)

        (PORTABLE_ROOT / "Runtime" / "KivyHome").mkdir(parents=True, exist_ok=True)









        destination = PORTABLE_ROOT / "SlayTheStarCraft.exe"

        if not destination.is_file():

            raise RuntimeError("SlayTheStarCraft.exe is missing from the extracted Slay folder.")



        print("\nSlay data preparation complete.")

        print(f"Launcher: {destination}")

        return 0

    except Exception as exc:

        print(f"\nERROR: {exc}", file=sys.stderr)

        if not args.non_interactive:

            try:

                input("Press Enter to close...")

            except Exception:

                pass

        return 1





if __name__ == "__main__":

    raise SystemExit(main())

