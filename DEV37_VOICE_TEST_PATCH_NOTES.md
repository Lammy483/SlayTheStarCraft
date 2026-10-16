# Dev37 — Sound catalog tester on confirmed working Dev36 Galaxy baseline

The player confirmed Dev28’s local `unitgroup wave;` identifier was the cause of the three-race Galaxy compile failure and that renaming it makes the mission launch. Dev37 is **Dev36 plus the isolated Dev33 sound-catalog tester**, NOT a reversion to Dev33 gameplay code.

- Preserves the `spawnedBanelings` fix and all Dev36 gameplay changes (Odin and Torrasque mineral-line exclusion, Jackson's Revenge Sniper Mercenaries fix, etc.).
- Restores the **21-line** Dev33 audio/portrait test. Begins automatically about 8 real seconds after APRogue initializes; type `?SlayVOTest` to replay when finished.
- Lines appear in order, with at least 7 real seconds between starts; longer recordings wait their complete duration. Preview shows `[VO x/21 PORTRAIT]`, `AUDIO ONLY` or `MISSING SOUND` in chat.
- Two shortened lines: Tychus at first player Drakken construction is capped to **7 real seconds**; Raynor for Air Support is capped to **2 real seconds**.
- Uses selected exact Sound IDs for 19 WoL lines, and performs a test-only exact asset filename lookup for the two HotS Archangel lines. No extra dependencies installed globally, no new event hooks yet.
- **Two existing gameplay voice hooks retained**: Marauder Kill Teams' first spawn and the Mira mercenary purchase. Other 11 voice events are not wired until recordings are verified.
- No rebundled heavy runtime. Portable launcher Go executable and manifest both retain `mira-camp-evacuation-v112-dev31` because that is the version compiled into the launcher; it does not identify Galaxy payload revision. Use Download Data when switching to this build to install this Galaxy source.
- Source tests and ZIP checks can verify consistency but do not compile Galaxy in the SC2 engine. Confirm mission launch/portraits/audio in-game.
