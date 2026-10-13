# v1.1.2 Dev17 — Portable Warp Gate hotkey launch fix

**Fixed `ModuleNotFoundError: No module named 'install_slay'` on Launch Slay** after Download Data.

The Windows launcher uses Python's embeddable distribution with an isolated `python313._pth`; `Payload` is not guaranteed to be in `sys.path` when a script is executed by absolute path. `slay_hotkeys.py` imported `install_slay` by module name even though the file was bundled beside it. This caused launch to fail before opening Archipelago.

The hotkey sync script now loads `Payload/install_slay.py` using its **absolute sibling path**, as the installer already does for its other isolated-runtime helper. This works in isolated Python and does not modify the global environment. Missing helper files produce a clear error without an uncaught import traceback.

**No Download Data rerun, runtime reset, or SC2 reinstall is required for this fix.** The existing `Runtime` remains compatible. Change `Config/slay_preferences.ini` normally; Launch Slay applies it on the next launch. Download Data still uses the same saved value.

For an existing Dev16 installation, replace only `Payload/slay_hotkeys.py`, or extract the Dev17 hotfix ZIP over the existing installation. The complete Dev17 distribution also includes the file. When using the full ZIP, avoid overwriting an edited `Config/slay_preferences.ini` during extraction.

Offline regression covers the actual CLI with `python -I` (reproduces the Dev16 traceback), repeated launch synchronization, intact INI, and readable missing-helper failure. No Galaxy/gameplay changes and no GitHub push.
