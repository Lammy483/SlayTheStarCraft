## v1.1.2 Dev25 — Unit unlock pricing and Recycled Armor Suits

- Reaver 100 credits; HERC 100 credits; Infested Liberator 100 credits.
- Recycled Armor Suits: 8 minerals / 2 gas on eligible player-owned, Slay-marked uncommandable Terran infantry (including Warfield Drop Pods, Cloning Technology and Meat Grinder). Normal controllable infantry still 25/10 even if Meat Grinder is owned.
- Requires Download Data after installing new Galaxy script; preserve customized `Config/slay_preferences.ini`.
- Built from Dev24; offline tests/source verification only, awaiting SC2 validation.

## v1.1.2 Dev24 — Recycled Armor Suits / Meat Grinder

- Marine-family deaths refund 10 minerals and 3 gas when both boons are owned; other infantry and solo Recycled Armor suits stay 25/10.

# v1.1.2 Dev23 — Nexus Shields scripted warp effects

- Use the native LotV Purifier visibility-aware warp-in model at `Ref_Origin` for Nexus Shields and other scripted Protoss reinforcement waves.
- Cross-campaign fallback uses a reduced WoL Protoss entry model when the LotV generic is missing.
- Five-second stun/fade and AI unchanged. Live SC2 visual verification needed.
- Previous Dev22 gameplay changes retained.

# v1.1.2 Dev22 — Brakk, repeatable inventory, balance

- Brakk: +3 armor and +1000 HP (maximum and current) on spawn.
- Deadly Weapons: +25% of base weapon damage per purchased stack (was +30%).
- Repeatable boon inventory displays each stack count correctly, for Deadly Weapons and Auto-repair.
- Time Stop Spear ability: 1200 credits.
- Preserves Dev21 and older fixes. Live SC2 verification pending.

# v1.1.2 Dev20 — Aberration regeneration follow-up

- Broader Archipelago Aberration recognition and once-per-second healing fallback; debug selected Aberration with `?SlayAberrationDebug`.
- Complete Dev19 and older features preserved.

# v1.1.2 Dev18 — Artanis commander uses the LotV ground hero

- Request the Void campaign catalog when the General blessing selects Artanis (commander index 9), the same as Alarak and Vorazun.
- Use the actual campaign unit `ArtanisVoid` (Twilight Blades) directly, bypassing the normal AP production replacement for this hero. Fall back to `AP_ArtanisVoid` only if the native unit is missing.
- Never replace an explicit Artanis commander with an unrelated random hero such as Urun if the catalog is unavailable. Display a clear in-game warning in that case.
- Keep the Haven dependency compatibility restriction intact; on sensitive Haven maps lacking Void data, display the warning rather than summoning Urun.
- Preserve respawns, commander bonuses, and every earlier Dev17 change. No release or GitHub branch updates.

# v1.1.2 Dev17 — Fix portable Warp Gate launch import

- Fix the Launch Slay `ModuleNotFoundError: No module named 'install_slay'` caused by isolated embedded Python missing `Payload` on its import path.
- Load the sibling hotkey installer by absolute path. Keep the existing runtime revision so players do not need to repeat Download Data; preserve customized `Config/slay_preferences.ini`. No gameplay changes.

## v1.1.2 Dev16 — Initial preferences and campaign objectives

- Includes editable `Config/slay_preferences.ini` in the initial ZIP. You can customize the Warp Gate key before the first Download Data, and repeated downloads preserve the key.
- Devil's Playground: early-victory fallback checks only original destroyable Zerg buildings. New hidden/non-Zerg/generated buildings do not block this condition.
- The Purification: stops generic Slay enemy-wide modifications from touching the native Null Circuits, while keeping their original mission scripting intact. Root cause of reported objective disappearance remains under investigation.

## v1.1.2 Dev15 — Custom Warp Gate hotkey

Edit `Config/slay_preferences.ini` after downloading data to set `Warpgate=E` (or your preferred key). Download Data preserves the file and always reapplies its current value, even on a second or later download. Launching Slay also syncs the preference. The packaged `.ini.example` is a safe template that does not overwrite user preferences in future updates. Supports letters, digits, F1-F12; defaults to W. Close SC2 before changing it.

## v1.1.2 Dev14 — Mission announcements

- Fixed repeated mutation and blessing chat announcements at mission start. The one summary is now shown three seconds after base establishment.

## v1.1.2 Dev12

Leviathan in Orbit pods target random player/allied units or buildings. Merc Compound and Predator Nest cooldowns are checked every three seconds, resetting any timers above 500 seconds to 10. See `DEV12_PATCH_NOTES.md`. Built on Dev11; live testing pending.

## v1.1.2 Dev10

Crucible enemy-structure mutation exclusions, Unlimited Power 1400 credits, verified shared Spine Crawler icon.

### Dev9 — Marauder Kill Teams map visibility and Tosh Spectre nukes

- Removed all periodic/spawn Marauder Kill Team pings. Both entire teams stay revealed with moving player-vision regions.
- Tosh Spectres perform a scripted, warning-marked 12-second nuke without needing Ghost Academy ammo. A living Spectre must survive the channel for the detonation to happen; otherwise the nuke is cancelled.
- Preserves earlier Dev8 gameplay/economy changes. See `DEV9_PATCH_NOTES.md` for implementation details.

**Dev8:** Stretchy Spines Spine Crawler portrait, Shop Expansion max 3, and removal of the universal +100 mission victory bonus. See `DEV8_PATCH_NOTES.md`.

**Dev7:** Bottled Leviathan/Hyperion autonomous unit AI, updated consumable descriptions, Specialists Raven icon. See DEV7_PATCH_NOTES.md.

# Slay the StarCraft v1.1.2 Dev6 — workbook timing/safety update

Development build based on Dev5. Changes: Torrasque always revealed, Saving Grace purchase popup with preselected blessings, startup effect summary reannouncement, updated patrol path clearance, enemy timing and price reconciliation. See `DEV6_WORKBOOK_TIMING_AND_PRICE_AUDIT.md` for the full list, clock exceptions, and workbook discrepancies.

Live SC2 gameplay has not been tested. GitHub unchanged.

---

# Slay the StarCraft v1.1.2 development build 2 — Base-established timing and Lab Rat

Unpublished local development build based on v1.1.2 Dev1 (Baneling Stream). No GitHub branch was modified.

- **Too Many Wraiths:** first raid occurs 60 seconds after the macro base is established, and its accelerating cadence is calculated from elapsed time since that point rather than mission time.
- Rebased the initial schedules for timed raid mutations and periodic blessings on the macro-base-ready event: Viking Raids, Dark Templar, occasional enemy replacements, Heroes of the Storm, Tower Defense, Jetpack attacks, Zagara's Banelings/Aid, air support, Lost Vikings, Warfield's Reinforcements, resource ticks and other scheduled effects. Existing mission-flag mutations with base-relative gates remain unchanged.
- Golden Armada, True Golden Armada, Heroes of the Storm, and Sniper Thor safety / attack escalation windows now use elapsed time since base establishment.
- Preserved literal mission-clock mechanics: **10 Minutes Until Destruction**, **Tal'darim Reinforcements (after 20-minute mark)**, **Invasion Fleet (5-minute mark)**, **Purifier Alliance (5-minute mark)**.
- **Lab Rat:** Tower Defense is forbidden in mission mutation selection. In a Lab Rat mission with Horde Mode, add exactly **25 minerals** once after effect configuration, before base establishment; no bonus in other missions or without Horde Mode.
- All v1.1.2 Dev1 Baneling Stream attack-move/building-targeting modifications retained.

**Validation:** offline Python regression tests and package source validator. Live SC2 timing, ability catalog, and launch verification remain untested.

---

# Slay the StarCraft v1.1.2 development build 1 — Baneling Stream

This is the first local development build toward v1.1.2, not a published stable release.

- Baneling Stream Banelings now issue an explicit **attack-move** order, never a plain-move fallback when attack is unavailable.
- Prefer pathable enemy structures (including buildings) as the destination. Only look for a ground unit or patrol point when a reachable building is unavailable.
- Keep the vanilla Baneling unit ID, normal automatic enemy engagement, existing 5–15 second source cadence, and eight-second retarget cadence.
- Preserve all v1.1.1 fixes and the user-authored Baneling Stream in-game description verbatim.

**Test status:** Offline/source validation only. Verify SC2 combat against enemy buildings before publishing v1.1.2.

---

## v1.1.1 hotfix HF1 — Leviathan Approaching

- Spawn the hostile Leviathan as soon as the player's macro base is established, as before.
- Hold position for **240 seconds after the base-ready timestamp**, not from mission start. Only then order it to approach the nearest player building.
- Stop once within 30 range of a player building. Regular, native, and damage-triggered Mutalisk/Brood Lord spawning remain disabled until the approach completes and the stop order is issued.
- Leave all other mutations, the player Leviathan boon, and catalog descriptions unchanged.
- Requires live SC2 testing to confirm movement and native spawn-ability behavior with the selected campaign dependencies.

# Slay the StarCraft v1.1.1 — Release Notes

## Changes

- **Occasional Colossus:** Its blessing now prefers the **Purification Colossus** (`AP_ColossusPurifier`, then `ColossusPurifier`). Slay's player-spawned Colossus default now prioritizes that Purifier variant, with the normal Colossus as a dependency-safe fallback. Enemy Colossus mutations retain their existing behavior.
- **Invasion Fleet:** Shop cost reduced to **1,500 credits**. In-game description restored **exactly** to: "At the 5 minute mark of each mission, many zerg drop pods attack the enemy for 2 minutes". Gameplay duration and pod cadence are unchanged.
- **Credit replacement items:** New runs default to **60 credits** per credit-item replacement (previously 50).
- **Early mission rewards:** All first-layer missions earn an additional **50 credits**, and all second-layer missions earn an additional **25 credits**, subject to the existing victory multiplier. Later layers unchanged.
- **Starting credits:** Remains **700** by default.
- Includes all fixes from v1.1.0 HF1–HF8, including Loki, Domination, inventory, installer resilience, and Smash and Grab workers.

The credit defaults and generated mission payouts apply to new runs; existing run files retain their saved values. No other in-game catalog descriptions were edited.

## Validation

Static release verification and offline unit tests are performed before packaging. Live StarCraft II execution still needs confirmation, especially the Purification Colossus in the Occasional Colossus blessing.

### v1.1.2 Dev21
See `DEV21_PATCH_NOTES.md` for mercenary cooldown clamping, Meat Grinder boon retargeting, and Null Circuit scripted-damage protection.

### Dev26 (development)
- Kerrigan respawns are validated before chat confirmation and retry without restarting their timer.
- Meat Grinder and autonomous unit retargeting distribute expensive work across ticks. See `DEV26_PATCH_NOTES.md`.

### Dev27 (development)
- Spider Mines no longer count as structures for Slay structure-based effects. See `DEV27_PATCH_NOTES.md`.
