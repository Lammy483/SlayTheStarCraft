# Dev15 — User-editable Warp Gate hotkey

- Add `Config/slay_preferences.ini` generated on first Download Data. Default `Warpgate=W`; change to a letter, digit or function key (F1-F12).
- Both initial and subsequent Download Data runs honor the current value, not a hardcoded W. Mod GameHotkeys and relevant SC2 custom profiles are kept in sync.
- Native Windows launcher now applies the preference at launch, including automatic and button-based launch paths. If a changed preference needs elevated SC2 folder access, the launcher warns the player to run Download Data, which already handles elevation.
- The ZIP includes only `slay_preferences.ini.example`, so extracting an updated ZIP does not overwrite a player's customized live file.
- No Galaxy, mission generation, shop, or balance logic changed.
- Tests cover repeat download, post-download editing, launch reapplication, invalid values, and custom profile updates. Windows SC2 runtime test pending.
