# Dev38 — selected campaign sound catalog registration

**Cause of Dev37 all-MISSING results:** the sound files exist in SC2 campaign archives, but most mission-specific CSound IDs (such as `TTychus02Tychus00008`) are not loaded by Archipelago campaign maps. Unlike Warfield, the tester did not resolve a loaded catalog entry, and there was no local Sound definition. These are valid original IDs in native Blizzard campaign mission scripts.

**Fix:** Install 21 isolated `CSound` entries (19 WoL + 2 HotS) in `APRogueData.xml`, with explicit localized asset filenames. WoL entries inherit Blizzard `Campaign2D` defaults; HotS entries inherit `VO`. Runtime prefers original CSound entries (and metadata) when available and otherwise falls back to `APRogueVO_...` entries. All mission game dependencies remain unchanged. This tests whether the campaign audio files can actually be resolved across missions; mere catalog registration does not prove audible playback.

Automatic 21-clip sound tester from Dev37 remains. Chat labels `REGISTERED` instead of claiming the asset was definitely audible. All gameplay Galaxy modifications from Dev37, especially the fixed baneling variable, remain. Two production triggers (Mira purchase and Marauder kill teams) now resolve local sound entries as fallback; other event hooks remain pending.

**On testing:** Use Download Data before launching, to write both updated `Payload/APRogueData.xml` and `Payload/APRogue.galaxy`. Test in WoL and HotS; if a line is REGISTERED but silent, the unresolved problem is asset mounting or path access, not the missing Sound catalog entry. Validate audible playback and portrait individually.

**Safety:** This build adds only 21 isolated catalog records to the existing Slay data mod, and does not add global Liberty, Swarm, or Void dependencies. It is an in-game audio diagnostic, not an engine-compiled guarantee of playback.
