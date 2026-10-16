# v1.1.2 Dev16 — Initial Preferences and Mission Objectives

- Bundles `Config/slay_preferences.ini` directly in the initial lightweight ZIP. Download Data and launch use the existing player-owned value; repeated data downloads never reset it.
- Devil's Playground: adds a separate early-victory fallback when all original, vulnerable Zerg structures are destroyed, ignoring later spawned structures and non-Zerg invisible/invulnerable helper actors. A non-empty baseline must have been captured after map initialization. Other mission victory conditions are untouched.
- Purification: excludes native `NullCircuit`/`NullCircuitActivated` objective units from Slay's generic enemy-unit scans (regeneration and other global modifiers). Leaves damage, death handling, and mission scripts untouched. This is a precautionary compatibility fix; the specific disappearing-but-uncounted failure is not yet conclusively reproduced.

**Important:** Updating by extracting a newer ZIP over an existing folder can overwrite a customized INI if the extraction utility replaces existing files. Back up or choose 'skip existing' for `Config/slay_preferences.ini`; clicking Download Data does not overwrite it.

**Validation:** Python generator/runtime tests and source verification. Live SC2 behavior still needs testing on both missions.
