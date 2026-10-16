Slay the StarCraft v1.1.2 Dev17 — Launch Slay hotkey import fix

Existing Dev16 installation:
1. Close Slay / StarCraft II.
2. Extract this hotfix ZIP into your existing SlayTheStarCraft folder.
3. When prompted, replace Payload\slay_hotkeys.py.
4. Click Launch Slay. You do NOT need to click Download Data again.

This ZIP contains only the corrected Python script and these instructions.
It does not overwrite Config\slay_preferences.ini, Runtime, Runs, or any SC2 files.

Root cause: the portable Python runtime uses an isolated ._pth import path,
so 'from install_slay import ...' failed even though Payload\install_slay.py
was present. The helper now loads install_slay.py from its absolute sibling path.

For a fresh installation, use the full Dev17 ZIP instead.
