# Dev33 — User-selected campaign dialogue playback test

Based on Dev32. This is a **test build** rather than the final event-triggered implementation.

- **Automatic** test begins ~8 real seconds after APRogue loads in a mission.
- Can replay by entering `?SlayVOTest` in chat (only when not already playing).
- **21 lines**: 11 new event requests, two earlier scripted lines, six Horner drop-pod candidates, and two HotS Archangel candidates.
- Chat shows sequence number, exact resolved Sound ID, speaker/event and status: `PORTRAIT`, `AUDIO ONLY`, `MISSING SOUND`.
- Adjacent clips begin at least 7 **real** seconds apart; longer sounds delay the next to prevent overlap.
- First Tychus drill sound capped at 7 **real** seconds. Air-support Raynor line capped at 2 **real** seconds.
- WoL uses exact supplied filenames transformed to Sound IDs. A missing catalog entry is reported, never substituted with a random line.
- Two HotS entries have unknown IDs: this *test only* searches exact asset filename in Sound catalog and reports any resolved ID. No production runtime wildcard searches.
- Facial animation: uses SoundPortraitModel metadata from each clip's Sound entry and normal SC2 transmission portrait (the corresponding .fxa model facial controller is loaded by SC2). In the absence of that metadata, plays AUDIO ONLY with a diagnostic chat line. No forced fabricated portrait paths.
- Existing game events (Mira mercenary purchase and Kill Teams) are unchanged. **The newly requested gameplay event hooks have deliberately not been wired yet** pending the test results.
- No global dependencies, no audio imports, no GitHub push.
- `launcher_manifest.json` keeps the existing `mira-camp-evacuation-v112-dev31` runtime revision because the precompiled Windows Go launcher in this source ZIP is still that exact binary. Do **not** change this revision without rebuilding the launcher, or an existing runtime may be treated as stale. The voice patch itself is labeled Dev33 in the ZIP and patch notes.

## Important
The tool cannot run the SC2 engine here. Check in-game loading/portrait animations, especially on non-WoL maps. If many WoL lines report MISSING SOUND, Sound catalog entries/dependencies are not loaded in that mission and need a targeted approach.
