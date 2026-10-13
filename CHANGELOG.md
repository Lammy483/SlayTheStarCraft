## v1.1.2 Dev24 — Recycled Armor Suits / Meat Grinder

- Reduced Recycled Armor Suits refunds on Marines to 10 minerals / 3 gas when Meat Grinder is owned, preserving 25/10 otherwise.

## v1.1.2 Dev23 — scripted Protoss warp animation

- Nexus Shields, Purifier hostile/escort, and For Aiur allied warp-in effects use the exact visibility-aware `ProtossGenericWarpInOut` attachment at `Ref_Origin` used by Blizzard's LotV Purifier campaign script (rather than the previous `Ref_Center` generic attachment).
- When the LotV model is missing from a WoL/HotS mission catalog, use the verified WoL Protoss `MothershipTeleportIn` model scaled down as a visible fallback before relying on the otherwise-insufficient `ProtossFastWarpinMarker`.
- Preserve five-second fade/stun and unit AI. Source-level only; the exact rendered VFX still needs in-game verification.

## v1.1.2 Dev22 — Brakk, inventory stacks, balance

- Brakk in Brakk's Pack receives +1000 max/current HP and +3 armor; the rest of his primal army does not.
- Deadly Weapons scales damage by +25% of base damage per stack instead of +30%.
- Inventory now uses the canonical boon purchase counter for both repeatable boons (Deadly Weapons and Auto-repair), while showing non-repeatable boons once.
- Time Stop costs 1200 credits instead of 900.

## v1.1.2 Dev20 — Regenerative Aberrations targeting and diagnostics

- Detect Aberration variants by internal link, unit-type name, and actual unit name. Search all owned units and double-schedule one capped heal through a shared timer.
- Add `?SlayAberrationDebug` to diagnose runtime detection without spamming ordinary gameplay messages.

## v1.1.2 Dev19 — Regenerative Aberrations

- Fixed player-owned Aberrations failing to heal from the +10 HP/second boon by replacing a fragile one-time native regeneration-property edit with a once-per-second capped health restore.
- Preserve natural healing, per-mission gating, all previous Dev18 changes.

# v1.1.2 Dev18 — Artanis commander uses the LotV ground hero

- Request the Void campaign catalog when the General blessing selects Artanis (commander index 9), the same as Alarak and Vorazun.
- Use the actual campaign unit `ArtanisVoid` (Twilight Blades) directly, bypassing the normal AP production replacement for this hero. Fall back to `AP_ArtanisVoid` only if the native unit is missing.
- Never replace an explicit Artanis commander with an unrelated random hero such as Urun if the catalog is unavailable. Display a clear in-game warning in that case.
- Keep the Haven dependency compatibility restriction intact; on sensitive Haven maps lacking Void data, display the warning rather than summoning Urun.
- Preserve respawns, commander bonuses, and every earlier Dev17 change. No release or GitHub branch updates.

# v1.1.2 Dev17 — Fix portable Warp Gate launch import

- Fix the Launch Slay `ModuleNotFoundError: No module named 'install_slay'` caused by isolated embedded Python missing `Payload` on its import path.
- Load the sibling hotkey installer by absolute path. Keep the existing runtime revision so players do not need to repeat Download Data; preserve customized `Config/slay_preferences.ini`. No gameplay changes.

## v1.1.2 Dev16 — Initial preferences / native objective protection

- Include default hotkey INI in ZIP.
- Add Devil's Playground original Zerg-structure-only victory fallback.
- Shield Purification NullCircuit objective actors from enemy-wide Slay modifiers.

## v1.1.2 Dev15 — Editable Warp Gate hotkey

- Added a persistent `Config/slay_preferences.ini` with `[Hotkeys] Warpgate=W` as the default; supported values are A-Z, 0-9, F1-F12.
- Download Data reads the player-owned INI and writes the requested Warp Gate key into the mod's GameHotkeys localization override and existing custom SC2 hotkey profiles.
- Repeated Download Data runs do not reset the INI to W; launch also synchronizes the preference before starting the private runtime.
- The packaged file is an `.ini.example` template to prevent future updates from replacing customized settings.
- Unsupported values are rejected with clear errors rather than silently reverting the user's selection.
- Offline regression tests cover both first install and repeated download/launch application. No gameplay changes.

## v1.1.2 Dev14 — Single mission effects message

- Show mutations and blessings once per mission in SC2 chat, three seconds after the player base is established; eliminate both early duplicate summary calls.

## v1.1.2 Dev13 – Odin (player only)
- Strip nuclear abilities and command-card buttons from player Odin variants; leave enemy Odin intact.
- Correct Odin blessing description to "You start with the odin".

# Slay the StarCraft 1.1.2 Dev12

- Leviathan in Orbit drops target random player/player-allied units or structures, excluding creep tumors and helper units.
- Every three seconds, sanitize overlong Merc Compound/Predator Nest cooldowns and charge timers: values above 500 seconds become 10 seconds, including ability catalog command fields.
- Preserve Dev11 Reconstruction Beam fix and prior changes; live gameplay testing remains outstanding.

# Slay the StarCraft 1.1.2 Dev11

- Fix the Spear of Adun autonomous-caster base gate: passive ability commands (including Reconstruction Beam) were disabled before base establishment and never re-enabled, even though the player had purchased them.
- Restore the autonomous Spear caster's ability-enabled state after the macro base is established, without resetting its passive cooldowns or the player-controlled Spear's existing cooldown handling.
- Keep the existing no-passives-before-base behavior and all Dev10 features.
- Static regression/source verification only; in-game SC2 behavior requires confirmation.

# Slay the StarCraft 1.1.2 Dev10

- Stretchy Spines uses the same bundled `btn-building-zerg-spinecrawler.png` as the Spine Crawler unlock (existing Dev9 icon mapping verified; no substitute web portrait).
- The Crucible now excludes mutations requiring enemy-owned structures or preferring enemy-structure spawn anchors, across generation, rerolls, and mission execution.
- Unlimited Power shop cost increased from 1,000 to 1,400 credits.
- All Dev9 features retained.

## v1.1.2 Dev9 — Marauder Kill Teams visibility and Tosh Spectre nukes
- Replaced all Marauder Kill Team minimap pings with moving, persistent revealers on every spawned Marauder and Medic. Increased the shared revealer registry from 64 to 128 slots so both full teams can be tracked alongside other always-visible mutations.
- Reworked Tosh's Boys Spectre strikes: after a four-second preparation, a living enemy Spectre designates a nuke within five range of the nearest player building, displays the Ghost nuke target indicator and warning ping, and detonates `NukeDamage` after a 12-second warning. Killing the Spectre cancels the strike. No Ghost Academy, ammunition magazine, or native Nuke order is required.
- Kept the original Tosh spawn/raid cadence and the existing pathable enemy staging-area restrictions.
- Source verification and offline regression coverage for both changes.

# v1.1.2 Dev8 (2026-10-11)

- Stretchy Spines now uses the existing Spine Crawler shop-icon artwork for all UI aliases.
- Shop Expansion is capped at three total acquisitions; stock generation, purchase checks, old saves, and shop capacities obey the cap.
- Remove the universal flat +100 victory credits per mission without changing mutation, blessing, high-risk, or other special reward components.
- See `DEV8_PATCH_NOTES.md` for full details.

# v1.1.2 Dev7 (2026-10-11)

- Bottled Leviathan and Hyperion are autonomous attackers instead of controllable units; their normal boons remain controllable.
- Leviathan native Mutalisk/Brood Lord AI uses independent 60s casts, and newborn units join the attack.
- Hyperion preserves internal resistance normalization and 100-energy, 15-second Yamato cooldown.
- Specialists now uses a Raven portrait.

## v1.1.2 Dev6 — October 11 workbook, base timing, patrol path clearance (unpublished)

- Compare the latest user workbook against the October 7 version and synchronize effect descriptions, severity, timing, and current literal shop prices.
- Make enemy Torrasque visible continuously, including after repeated respawns.
- Saving Grace reveals the exact pending blessing package on purchase, then applies the announced effects rather than rerolling.
- Reannounce Slay startup summary once shortly after base establishment to avoid native intro chatter hiding it.
- Validate protected patrol line segments, use shorter safe connected ground waypoints, and omit creep tumors from all protected building checks.
- Reschedule enemy attacks/raids, golden armadas, bosses, and native game-clock exceptions per workbook, including Invasion Fleet's new 2-per-second rate.
- Update Shop Expansion, Temporal Field, Elite Mercenaries, Repeat Contractor, and Spear Recharge costs; preserve the user-corrected Hyperion in a Bottle description despite stale workbook text.
- See `DEV6_WORKBOOK_TIMING_AND_PRICE_AUDIT.md` for an explicit before/after timing and price comparison.
- 252 offline tests plus source verification pass. Live SC2 verification remains necessary.

## v1.1.2 Dev5 — Zagara, Tosh Miners, patrol and base threat fixes (unpublished)

See `DEV5_PATCH_NOTES.md` and `DEV5_MUTATION_THREAT_AUDIT.md` for full details.

## v1.1.2 Dev4 (unpublished local development)

- Roll each mission's unscaled mutation and blessing severity budget before multiplying by the respective effect frequency. Zero frequency now guarantees no corresponding effects; early high-tier bonuses, final-quarter major mutations, opening-blessing injection, and red-path hardening cannot bypass zero. Reduced mutation frequency also disables forced red-path hardening.
- Reduce mean mutation severity by 2 per gameplay difficulty tier below Brutal: Hard -2, Medium -4, Easy -6. Applies across all missions, including the finale.
- Replace the second paragraph of the launcher difficulty description with the requested text recommending reduced gameplay difficulty first.
- Preserve all Dev3 Zagara/Purifier behavior, Dev2 timing/Lab Rat fixes, and Dev1 Baneling Stream behavior.

## v1.1.2 Dev3 (unpublished local development)

- Force hostile Zagara variants to die at 4 HP or less, including mission-native enemies not registered by Slay's generated-hero tracker. The existing kill/remove fallback is preserved to overcome story death-prevention effects.
- Restrict Purifier invulnerability-shield removal to Slay-created mutation or Purifier Alliance units and only when the corresponding effect is active. Native Safe Haven Purifier shield and Nexus-based unlock remain untouched when neither effect is selected (and the native unit is never targeted by the override).
- Preserve Dev2 base-establishment timing, Lab Rat Tower Defense exclusion, Lab Rat Horde Mode +25 minerals, and Dev1 Baneling Stream attack-move behavior.
- Offline source/unit regressions only; SC2 in-game verification remains required.

## v1.1.2 Dev2 (unpublished local development)

- Rebased periodic mutations and blessings to the completed player macro-base clock except explicitly mission-timed descriptions.
- Too Many Wraiths starts at base +60s and scales from base elapsed time; Golden Armada/True Golden Armada and Heroes of the Storm safety windows use the same clock.
- Excluded Tower Defense on Lab Rat; grants +25 starting minerals once when Lab Rat also has Horde Mode.
- Preserved Dev1 Baneling Stream building-target attack-move behavior.

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

---

# v1.1.0 hotfix HF8 — Starting credits and Smash and Grab workers

- Set the default starting credits back to **700** in the launcher and command-line run generator. Existing generated runs and saved balances are unchanged.
- **Smash and Grab** starts with 3 extra player-controlled workers. Slay detects the existing starting worker type (SCV, Drone or Probe, including Archipelago variants), spawns 3 near the established player base and grants them only once per mission.
- No changes to mission effects, economy rewards, catalog descriptions, or other mission starting armies.
- Retains all previous HF7 fixes and the public v1.1.0 version. The new runtime revision ensures Download Data reapplies the gameplay script.
- The unit-spawn behavior requires live testing in SC2; offline tests validate source and routing only.

# v1.1.0 hotfix HF7 — Engine of Destruction Loki protection recovery

- In Engine of Destruction only, detect when player-owned units reach the original Loki Aggro area or close to Loki, and allow the map's normal two-second undocking sequence to complete.
- If Loki remains invulnerable, remove its invulnerability state and known shield behavior, and release scripted AI. Recheck for stray reapplication while the mission is active.
- Preserve valid Loki maximum health; set a 2000-HP fallback only if the engine reports a missing/invalid maximum.
- Do not change other missions, standard Loki staging, descriptions or catalog balance. No packed map patches required.
- Keep the public version at 1.1.0 and advance the Windows launcher/runtime revision so the patch is actually applied by Download Data.
- Galaxy source verification and offline regression tests do not replace a live SC2 mission test.

# v1.1.0 hotfix HF6 — Crucible, icon parity, Fire Squad, Decay and Sniper Thor

- Exclude the Meat Grinder mutation from The Crucible in new-run generation and at mission launch (including existing generated runs and rerolls).
- Fix inventory item icons across categories by keeping canonical Archipelago item IDs. Use the same documented artwork resolution as the shop, including local images whose filenames do not start with `btn-`.
- Fire Squad now prefers the Archipelago Purification Colossus `AP_ColossusPurifier`, falling back only to the actual `ColossusPurifier` catalog entry, never the ordinary/Aiur Colossus.
- Decay skips workers, including SCVs, Drones, Probes, MULEs and identified worker variants.
- Sniper Thor spawns at least 20 range from player and player-allied structures. On timed-defense missions it receives an attack-move to the player base after 15 mission minutes.
- Restore Energized Queens' original user-authored catalog description without undoing the broadened unit matching. Hyperion in a Bottle retains its original catalog description, unchanged.
- Synchronize bootstrap, release manifest and launcher runtime revision markers, retaining v1.1.0.
- Gameplay/unit-ID changes still require live StarCraft II testing. No new text has been invented for in-game descriptions.

---

## v1.1.0 hotfix HF5 — Domination pickups without map editing

- Domination Baneling nests now accept any eligible **player-controlled ground unit**, even if Kerrigan is present or has respawned. This intentionally broadens the pickup rule at the user's request.
- The regular Archipelago map itself is not modified. Instead the Slay mission flag tells APRogue to select Archipelago's normal unrestricted pickup rule after the mission's Kerrigan/hero initialization. This is compatible with packed `.SC2Map` files and avoids another Download Data failure.
- All other missions keep their existing Kerrigan-presence behavior. Original Kerrigan spawning, hero registration, respawn, mission objectives and pickups are otherwise unchanged.
- Removed the HF3/HF4 optional Domination map rewriting logic; retained legacy HF3 map-script backup cleanup on uninstall. Package version remains 1.1.0; no GitHub changes.
- Offline verification cannot prove that the original API4 map's periodic pickup event behaves correctly in a live SC2 launch. Test collecting a nest using an ordinary ground unit with Kerrigan alive and after Kerrigan respawns.

## v1.1.0 hotfix HF4 — safe optional map patches, nonblocking version checks

- A reported HF3 first-time installation stopped with `Domination API4 map script not found`. The SC2 API4 data had been verified and did not contain an editable `Maps/ArchipelagoCampaign/HotS/ap_domination.SC2Map/MapScript.galaxy` at that path. Requiring a plain-text source inside a potentially packed `.SC2Map` was incorrect.
- Treat the Domination-specific Kerrigan patch as optional. If the map is packaged, unavailable or has incompatible script contents, log a visible warning, don't modify it, and continue installing mandatory Slay patches. For unpacked editable Domination maps, apply the validated change after successful mandatory patch installation with independent backup and failure recovery. Do not create an invented map source or silently assume the fix applied.
- Package-version-only `PACKAGE_VERSION = ...` discrepancies in pre-install and post-install checks are warnings; missing gameplay or structural markers remain fatal. Match the same policy in bundled-source preflight verification.
- Added regression tests for absent/packed/editable/incompatible maps and version-only drift. The user-reported Domination issue remains unfixed on packed map installations pending a safe packed-map-compatible solution.
- Keep display version 1.1.0 and rebuild a distinct HF4 package; no GitHub publishing.

## v1.1.0 hotfix HF3 — Domination Baneling nest pickup after Kerrigan respawn

- Fix the *Domination* Baneling-nest bonus pickups becoming inaccessible after Kerrigan is replaced by the Slay/HotS respawn system. Archipelago's mission script checks only `gv_militaryUnits`, which it rebuilds every 0.25 seconds using the map's original `gv_kerrigan` reference. If the unit object changes, the new Kerrigan is missing from the eligible pickup group.
- Patch *only* `Maps/ArchipelagoCampaign/HotS/ap_domination.SC2Map/MapScript.galaxy` during Slay installation. When the original Kerrigan is no longer alive, the mission rebinds its `gv_kerrigan` pointer to a living player-owned Kerrigan (excluding eggs, cocoons and birth placeholders); the native pickup handler then processes nest objectives and rewards unchanged.
- Preserve Archipelago's no-Kerrigan branch, where regular ground units may collect nests. No change to other mission maps, Kerrigan abilities or global hero respawn timing.
- Back up the original Domination map script before patching, reapply safely on repeat installs, reject unknown map versions rather than editing them blindly, roll back if setup fails, and restore the original on Slay uninstallation. Updates SC2's locally installed Archipelago map data, not just the portable runtime.
- Rebuild the native Windows launcher with a new runtime revision so existing installations run Download Data to apply the fix. The public package still reports **v1.1.0**. Source checks and offline regression tests are not a native SC2 Galaxy compiler or a live pickup test.

## v1.1.0 hotfix HF2 — Energized Queens matches all Queen units

- Energized Queens now applies to any player-owned mobile unit whose internal catalog unit ID **or localized displayed name** contains "Queen" (case-insensitive), including Archipelago's `AP_Queen` Swarm Queen. The previous filter accepted only `SwarmQueen` or `BroodQueen` unit IDs and missed the standard AP variant.
- Cached display-name checks by unit type to avoid repeated localized-name lookups during combat. Kept the existing energy regeneration behavior and 400-credit cost.
- Expanded the boon shop eligibility to any owned unit unlock containing "Queen" in its name, and updated the displayed boon description.
- All other gameplay and package version markers remain at v1.1.0. Test the actual energy gain in StarCraft II; source checks cannot prove Galaxy behavior in-game.

## v1.1.0 Endless Mode hotfix — installer verification repair

- Fixed the portable Download Data installation stopping at "Applying Slay patches" because different package-version markers were expected by the installer. All release components now consistently use 1.1.0.
- Pre-install package version checks now use the version from bundled `VERSION.txt`, rather than hard-coded past release numbers. The installer success message uses the same version.
- Strengthened source verification to check *all bundled-source pre-install markers* for launcher, generator, Slay runtime, and Galaxy before packaging. No gameplay changes.

## v1.1.0 Endless Mode hotfix — retire mode and correct orphaned mission tooltips

- Remove the Game Mode selector from run setup. New runs are always Standard Mode. Attempts to generate new Endless Mode runs through the Python launcher API are rejected with a clear error; old run files are not deleted or silently converted.
- Correct the legacy Endless mission UI's half-second forced rebuild. Stable floors now reuse their mission cards and tooltips, and chart/floor changes explicitly remove old tooltips before buttons are replaced. Previously created Endless saves may still be opened but are no longer an actively supported game mode.
- Keep the release's existing Standard Mode mission map, gameplay scripts, mutation/boon pools, and economy unchanged.
- Package as a distinct v1.1.0 hotfix ZIP with matching Windows launcher, manifests and private runtime revision. Existing v1.1.0 installations may need one **Download Data** update to apply the new runtime revision.
- These fixes are covered by offline regression and source checks; live Kivy/StarCraft II testing remains necessary.

## v1.1.0 public release — UI polish and promotion

- Wangfeng acknowledgement now reads **"Chinese localization and improved UI"**.
- Campaign Length's longer cautionary note wraps to its available column width and expands its label, field and settings grid to show the entire text at narrower widths/DPI scales.
- Source snapshot promoted from the r40 integration baseline; no additional gameplay balance changes in the release polish.
- The stable release manifest and player-facing release notes now identify v1.1.0 as the public release. Endless Mode remains labelled ALPHA.

## v1.1.0 development r40 — flat victory bonus, Hyperion movement, Invasion Fleet pacing

- Replace +50 victory credits times mission number with a flat **+100 victory credits on every mission**. Base reward is now 500 (formerly 400 + 50 × mission number). Tier adjustment, 125 credits/mutation severity, -100 credits/blessing severity, Lab Rat -100, minimum reward and user multiplier are unchanged. Apply this to generator, legacy runtime fallback, and opening credit estimates; remove the additional +50 per floor in Endless Mode so its reward also receives the flat baseline rather than another increasing mission bonus. Risky mission extra 100 remains.
- **Raynor's Raiders (enemy Hyperion mutation):** remove the scripted stuck-movement detection and position nudge (`UnitSetPosition`) so Time Stop cannot cause teleporting. Keep native flying move orders, refreshed every 3 seconds, plus the existing flyby, damage retreat, repair and drop-pod logic.
- **Invasion Fleet boon:** at mission minute five, deploy one allied Zerg drop pod per second through minute seven (120 seconds total), rather than twice per second for one minute. Updated item description; expected total remains roughly 120 pods when eligible drop points exist.
- New r40 regression tests and adjusted r38 baseline assertions. Static tests cannot verify Galaxy compilation or Time Stop behavior in live SC2.

## v1.1.0 development r39 — consumable stock, track discounts, Hyperion Yamato

- Each shop consumable offer can be purchased only once until a real reroll or mission victory. The purchased offer remains displayed but disabled after use; inventory capacity remains two, and Shop Expansion does not reset sold offers. Purchased-offer state persists across launcher restarts.
- "Reduced Spear of Adun Shop Prices by 50%" and "Reduced Kerrigan Shop Prices by 50%" cost 500 credits, previously 400.
- Hyperion in a Bottle and the Hyperion boon now preconfigure the native HyperionYamatoSpecial ability's player-specific cost before creation / replacement: 100 energy, 15-second use cooldown. Native campaign's missing cost fields are seeded at zero in APRogueData.xml so enemy Hyperions retain original values. Live SC2 verification is still required.
- No victory-credit reward change from r38. The standard formula and its potential late-game inflation are documented in the delivery summary.

## v1.1.0 development r38 — mutation victory-credit reward adjustment

- New mission victories now grant **125 credits per mutation severity point**, reduced from 150. Updated the run-generator reward, the client-side fallback reward, opening-credit estimates, and installer source assertions together so displayed and awarded credits stay consistent.
- Blessing credit reductions (-100 per severity), mission-tier/layer calculations, fixed bonuses, shop costs, and mutation selection/danger scoring are unchanged.
- Added focused regression tests for the generator and fallback. This is a development build for testing before promoting to main.

## v1.1.0 development r37 — Purifier Vortex targets visible units only

- The shared autonomous ability scanner could cast Purifier Vortex at an enemy building or at its point, because generic enemy target groups include structures. Slay-spawned Purifiers now have a dedicated `VortexPurifier` target picker that considers only **visible, alive, enemy non-structure units** within the native 10-range, checks native order validity, and preserves the previous movement/attack order.
- Applied to both the enemy **Purifier mutation** and the friendly **Purifier Alliance boon**. The normal generic Vortex building/point fallback is bypassed for these Slay Purifiers only. The mutation's scripted Planet Cracker takes priority and is not interrupted once started. Original map-scripted Purifier encounters and other autonomous casters are unchanged.
- Added r37 source regressions covering the eligible-target filter, vision, range, both AI paths, no fallback, and command resumption. Live SC2 verification remains necessary for successful Vortex casts and the visual effect.

## v1.1.0 development r36 — collapsible consumables, zombie origins, Purifier reinforcement AI

- Added an in-mission consumable minimizer: a small `-` button at the right of the two top-row consumables reduces the whole HUD panel to a single `+` restore button. The minimized panel no longer covers the mission objectives; consumed/empty slots still hide normally. The same native targeting and consumption rules are retained.
- Allow natural/campaign Infested Terran and Infested Civilians to trigger Zombies blessing/mutation and Zombie Apocalypse on death (subject to the shared worker/timed-life rules). Slay-created zombie units receive origin tags and are excluded from *both* zombie mechanisms so simultaneous mutations/blessings cannot recursively produce zombies.
- Purifier Alliance and For Aiur warped allies now join the recurring friendly support AI after their five-second warp stun; Purifier Alliance reinforcements also receive periodic target refreshes. Hostile Purifier mutation escorts now join the normal hostile raid AI after warp-in; ground waves already used that group. All scripted warp visuals and five-second stun remain intact.
- Kept r35's mutation Purifier-only `InvulnerabilityShield` stripping at creation and every tick on **all missions**, without changing Safe Haven's map boss or the friendly Purifier Alliance boon. Corrected `APRG_IsScriptedPurifier` so the Slay mutation enemy is an eligible combat target rather than being misclassified as a map-scripted objective.
- Added r36 regression coverage and updated four previous UI tests to reflect the wider expandable potion bar. Live StarCraft II testing is still necessary for the minimize control, attack AI and Purifier vulnerability.

## v1.1.0 development r35 — Purifier mutation shield fix

- The Wings of Liberty `Purifier` unit has `InvulnerabilityShield` in its base unit catalog. Safe Haven removes/reapplies it for its scripted boss, but Slay-created Purifiers do not participate in that mission event. The inherited shield was therefore unintended on Haven's Fall and potentially any other mission.
- Immediately remove `InvulnerabilityShield` and clear the invulnerable state on the **mutation-spawned enemy Purifier**. Reassert its vulnerability in the mutation tick if campaign triggers restore the shield. Do not alter Safe Haven's normal scripted boss or the separate allied Purifier Alliance boon. The mutation stays enabled on both Haven missions.
- Added targeted offline regression tests; live SC2 verification remains necessary to check that the shield vanishes and the mutation's planet cracker/escorts continue normally.

## v1.1.0 development r34 — Leviathan army selection and quiet consumables

- Both native Leviathan unit variants (`Leviathan`, `LeviathanHOTS`) now have `ArmySelect` enabled in the base and player-specific catalogs. The override runs at mission activation and whenever the Leviathan boon or Leviathan in a Bottle normalizes its unit, matching the working Karass F2 approach.
- Removed the consumable-use `[Slay]` notice dialog, its timed-hide tick, and all consumable-click `[Slay]` informational messages (target prompts, failure notices, use acknowledgments, and test consumable use). Native target cursor, button `[TARGETING]` state, spending safeguards, and consumable behavior are unchanged.
- Added regression tests. Real F2 behavior must still be verified in an actual StarCraft II mission.

## v1.1.0 development r33 — settings clarity and requirements write resilience

- Replaced the Campaign Length difficulty claim with "changing run length may alter difficulty in unexpected ways" without modifying run generation.
- Game-mode selector now labels Endless Mode as "Endless Mode (ALPHA)" while preserving its internal `endless` value and Standard Mode as the default.
- Private runtime bootstrap no longer rewrites unmodified Archipelago requirements files; if a Gitless replacement is necessary, it clears the read-only attribute before writing. This reduces a known potential cause of Access Denied failures in `Runtime/Archipelago/worlds/_sc2common/requirements.txt`. Other permission/AV failures still require log investigation.

## v1.1.0 development r32 — Niadra birth cooldowns, Mira clearance, hostile laser drill break

- Niadra's native Swarm Queen birth/train commands (including the available Zergling, Roach and Hydralisk variants) now have 60-second cooldowns applied at hero creation, using the same player-specific catalog normalization style as the Leviathan's native spawn abilities.
- Mira's Mercenaries now require their camp center to be at least 40 range from all player-owned or allied structures (giving the requested 20-range buffer even after squad spread). On ordinary maps, the camp must have ground pathing to the player's home. Removed the fallback patrol-point path that bypassed those safety checks. An unsafe attempt now waits and retries rather than spawning near friendly buildings.
- The mutation-spawned enemy Drakken Laser Drill interrupts its sustained beam every nine seconds via Stop, pauses for two seconds, then resumes native attacks. This caps uninterrupted fire intervals below ten seconds as a mitigation for Guardian Shell/invulnerability bugs. The allied drill blessing is unaffected.
- Added three focused safety regression tests. Source-only checks do not validate live Galaxy compilation or prove the Guardian Shell bug is eliminated; test the mechanic in-game.

## v1.1.0 development r31 — elite openings, inventory navigation, Tosh shield, icons

- On the first mission layer, 900+ victory-credit missions are marked elite/high-risk even when the usual dynamic opening-average comparison does not mark them; layer-one elites do not gain the extra 100 victory credits.
- Inventory now places Show Cards/List, Shop, and Exit Inventory in that order at the top-right; the redundant bottom Close Inventory control is removed.
- Shop/Inventory switches use one-shot navigation handled by the normal dismissal lifecycle. Exit Shop and Exit Inventory only close; reroll rebuilds Shop once and cannot trigger inventory navigation.
- Glass Cannons blessing severity increased from 1 to 2 in both generator/runtime tables and the effect catalog.
- Tosh attempts his actual campaign Psi Shield (`VoodooShield`) immediately after taking health damage, preserving his attack-move order.
- Terran Upgrade Pack now uses the bundled Terran Armory image rather than the Zerg Evolution Chamber image.
- Automated regression tests added/updated. Source-level verification does not replace live SC2 Galaxy compilation or playtesting.

## v1.1.0 development r30 — Single-Use Tools and Tosh and his Boys

- **Single-Use Tools** (400 credits): owning this boon awards one randomly rolled shop-eligible consumable after a completed mission if there is an empty consumable slot. It never exceeds two inventory slots, does not reward pre-purchase victories, and records completed missions to avoid repeat awards on reconnect or reopening the shop.
- **Tosh and his Boys** (mutation severity 3): Tosh starts in ground-connected enemy territory and starts attack/patrol AI three minutes after the base is established. Four minutes after establishment, a cloaked Spectre raid begins, recurring once per minute while Tosh lives. Spectres attack-move toward the nearest pathable player building and try to nuke within five range of it. They attempt their native ability first, with an interruptible warning-and-detonation fallback for campaign variants lacking nuke support. The mutation is prohibited on island missions.
- New regression coverage for both systems. Full SC2 Galaxy mission verification is still required; source-level checks are not a native SC2 compiler.

## v1.1.0 development r29 — documented icons, consumable shop, mercenary squads, HUD, VO

- Prefer the exact Archipelago SC2 item documentation artwork for upgrades with a documented image, including 35 source-map corrections. Shipped images are used locally; older UI-themed icons remain as fallback for unavailable source files.
- Give all 19 consumables and the 18 random-unit consumables appropriate local SC2 artwork. In particular, Mass Spellcasters uses the High Templar, Mass Stimpack uses Stimpack, Hyperion uses the Battlecruiser, and Leviathan uses the Spawn Leviathan icon.
- Shop Expansion adds one rolled consumable offer per stack (+1 per purchase) without increasing the two-consumable inventory capacity. Includes a stock-version bump so cached old rolls refresh.
- Mercenary Favor generates suitable squad sizes (four War Pigs, two Hammer Securities, single Jotun/Jackson's Revenge and other heavy mercenaries) from living Merc Compound/Predator Nest sites rather than the main base. Uses the standard player unit factory and avoids consuming the potion when no eligible mercenary can spawn.
- Warfield's Drop Pod Wave VO triggers once on potion activation, not with each landed pod, and no longer increments recurring Warfield drop VO counters.
- Native potion HUD controls shrink from 260×56 to 235×44 and move flush with the top anchor, staying about 15% in from the left to clear objective text.
- Confirm the allied For Aiur/Nexus Shields and Purifier hostile/escort scripted warp-in queues share the campaign model animation, five-second stun and fade.
- Offline regression coverage added; gameplay, artwork scale, and placement still need live in-game validation.

## v1.1.0 development r28 — storm targeting, Spear energy, mission safety, warp-in effects

- Autonomous High Templar (including Mass Spellcasters and Specialists) prioritize Psionic Storm ahead of generic abilities, ignore misleading native autocast flags, and choose dense enemy groups (up to 24 potential targets) within casting range. They resume their previous attack-move order after a cast. Player-controlled High Templar are unaffected.
- Spear of Adun Recharge consumable now fills only the Spear energy pool, without trying to reset cooldowns. It is eligible for the shop only after the Spear has been unlocked and at least **two distinct active abilities** have been unlocked; passive upgrades and repeated levels of the same ability do not count. The free initial Deploy Pylon counts as one ability.
- Nexus Shields cannot roll on **Smash and Grab**, whether during run generation or later mutation acquisition/rerolls.
- Scripted ally/Purifier warp-ins now attach the campaign-standard `ProtossGenericWarpInOut` animated model to the unit as the primary effect, rather than treating the `ProtossFastWarpinMarker` point actor as a successful warp animation. Five-second pause and fade-in are unchanged.
- Offline validation and regression coverage added. Visuals and ability usage require live StarCraft II testing; GitHub unchanged.

## v1.1.0 development r27 — one-time contract structures and HUD placement

- Fixed the Merc Compound regenerating after destruction. Previously, `APRG_TickContractStructures` interpreted a dead tracked compound as a reason to create another. Both Merc Compound and Predator Nest now use a one-time-per-mission resolution flag: failed initial placement can retry, but destruction never triggers a replacement.
- Repositioned the two consumable buttons from the upper-right overlay to the top-left region, panel left edge 320 SC2 UI units (~15% on a 16:9 screen), 4 units from the top. The external Archipelago announcement frame and consumable mechanics are unchanged.
- Source regression tests cover both once-only structure flags and the new HUD location. In-game verification is still required. Not pushed to GitHub.

## v1.1.0 development r26 — consumable gameplay and warp-in feedback

- Move the consumable buttons down another 12 game UI units, and show successful use notices for four seconds. The separate Archipelago notification frame could not be moved safely from Slay's Galaxy script and remains unchanged.
- Extend the scripted Nexus Shields, Purifier, and For Aiur warp-in stun/fade from three to five seconds; attempt a world-space Fast Warp In marker with the existing attached-model fallback. Actual animation visibility needs in-game verification.
- Hyperion in a Bottle: configure Yamato energy cost and cooldown alongside the Hyperion boon, with full initial energy.
- Mass Spellcasters: create actual native campaign Infestors rather than accidentally substituting Infested Terrans; keep Specialists-compatible spellcasters plus requested extra units and initialize them at full energy.
- Spear of Adun Recharge: reset caster and player cooldown links found in the Spear abilities rather than only their first link; recharge both caster forms.
- Mercenary Favor: resolve actual mercenary unit IDs and their squad sizes, without consuming charges or cooldowns. The actual live mercenary train commands are not invoked.
- Controllable named-unit consumables: no automatic attack orders or autonomous AI enrollment. The uncontrollable Mass Marines and Mass Spellcasters waves retain their standard attack AI. Resolve healthy unlocked AP variants once per use, prefer known default War Council choices, and fall back to a normal unit if an AP variant is an invalid placeholder.
- Keep existing 30/s mass-spawn limit and all compatibility wire IDs. GitHub not updated.

## v1.1.0 development r25 — installer verification hotfix and Armada buffers

- Fix `Download Data` failure during *Applying Slay patches*: installer still required deleted `APRG_GoldenArmadaEarlySafety` from the older emergency-retreat implementation. Check the current `APRG_GoldenPatrolRouteSafe`, `APRG_FindGoldenSafeAirPoint` and `APRG_GoldenSafePatrolDestination` helpers instead.
- Validate the installer's complete APRogue Galaxy required-symbol list during source verification, **before** releasing the archive; add a regression that deliberately introduces the r24 bug and confirms validation rejects it.
- Non-True Golden Armada: change central spawn safety radius to 40 (from 55), patrol clearance to 24 for the fleet's central route (20 minimum + approximately 4 formation margin). The path sampling and checks against player/allied structures remain active until four minutes.
- **True Golden Armada unchanged:** spawn clearance 55, early patrol clearance 40, special timing remains in place.
- GitHub not updated (by request).

## v1.1.0 r24 — Golden Armada safety, consumables, and HUD corrections

- Spear of Adun unlock price is 500 credits.
- Golden Armada uses allied-building-safe enemy-side spawn points and segment-validated enemy-territory patrols before its four-minute engagement window. Removed the earlier reactive retreat behavior and, critically, the air-reachability relocation that moved the fleet toward the player's base after a valid spawn.
- True Golden Armada retains its existing ten-minute protected patrol interval. It no longer uses that relocation, checks its fleet and Phoenix routes against player/allied buildings, avoids premature mothership-loss assaults before four minutes, and delays Oracle Revelation orders until its protected patrol phase ends.
- Added 0.25 average mutation severity per mission number in the generator and expected-danger/credit model (mission ten +2.5 severity on average), on top of the existing +1 global baseline.
- Shop and inventory refresh consumed consumable serials on open and show the actual number of free slots; shop header updates after purchase.
- Removed “native SC2” from the consumable targeting instructions.
- The private consumable-targeting Marine is hidden, unselectable, invulnerable, untargetable, non-highlightable, and excluded from Slay player-unit collections. It remains present internally to preserve the targeting cursor.
- Preserved r23 gameplay and launcher behavior; no GitHub update.

## v1.1.0 r23 — Baneling AI, mercenary Battlecruiser, live consumables and Kill Teams

- Baneling Stream uses shared validated attack-move point orders and reselects destinations every 8 seconds; ground target fallback avoids idle suicide units.
- Orlan's Planetary Fortress uses the campaign's `DukesRevenge` unit ID (the actual mercenary Battlecruiser per SC2 Campaign RequirementsAI); generic Battlecruiser fallback is preferred over incomplete Jackson-name placeholder entries. Mercenary Favor uses the same resolver.
- Standard enemy/player attack-target selection excludes invulnerable structures and units, without removing them from the general mission structure pools.
- Running SC2 bot polls the current run's consumable slots for changes and sends an isolated `?SlayConsumables` chat handshake. The Galaxy receiver validates run token and serials, refreshes hidden/visible HUD buttons, and resets the used flag only on a newly assigned serial. Startup `?APRogue` configuration remains unchanged.
- Marauder Kill Teams receive +3 armor and +3 bonus ranged damage on spawned Marauders, and +3 armor on Medics. Existing special model and fallback damage buff behavior remains.
- Source-only validation is not an SC2 Galaxy compiler or live mission verification. No GitHub changes.

## v1.1.0 r22 — Shop sale consistency, inventory consumables, spawn throttling and Kerrigan cleanup

- Initialize current stock before sale selection, then reconcile highlighted sale rows with the live discounted price after any prewarm/cache rebuild. Do not highlight a row simply because it appears in an outdated sale ID set.
- Add an Inventory button between Show Cards and Exit Shop in the shop header. Dismiss the shop before opening the inventory modal.
- Show purchased, unused consumables in Inventory with the exact catalog description; keep consumables hidden after their consumption serial is recorded in the mission bank.
- Throttle Mass Marines and Mass Spellcasters to a shared maximum of three units per 0.1-second fast tick (30 units per second total), even if both consumable waves run simultaneously. Other unit-spawn consumables retain their original timing.
- Move the top-right consumable button panel down by 12 game UI units.
- On either successful Kerrigan respawn path, remove living player-owned Kerrigan revive cocoons.
- Archipelago's in-mission announcement overlay is owned by the external Archipelago SC2 mod. It is not reliably addressable from APRogue's consumable Dialog; announcement repositioning remains pending rather than risking unrelated SC2 frame modification.
- Retain all r21 systems and stable consumable wire IDs. Do not push this local patch to GitHub.

## v1.1.0 r21 — Consumables, mission risk, shop and Heroes of the Storm safety

- Reclassify Sonic Disrupter and Psi Screen (Psi Disrupter upgrades) under Defensive Structures & Detectors, alongside the Psi Disrupter itself.
- Rename visible Potions labels, shop headings, slot messages, and in-game UI notifications to Consumables. Preserve stable internal IDs and the SC2Bank keys for compatibility with existing saves.
- Display the uploaded Effect Description column verbatim for all 19 consumable types, excluding Development notes. The randomized unit offer substitutes the rolled quantity and plural unit name into the original description template.
- Move Exit Shop into the popup header's top-right corner, with Show Cards immediately to its left; eliminate the shop footer.
- Draw a full red High Risk circle around each high-risk planet and make the High Risk text red.
- Heroes of the Storm hostile heroes must spawn >=20 range from player/allied structures. Until 4 minutes of mission time, patrol targets and sampled straight-line routes maintain the same clearance. The original 4-minute timed-defense attack behavior remains unchanged.

## v1.1.0 r20 — Planet routes and Spear Pylon progression

- Draw race-tinted mission-card backgrounds in the chart background canvas, route curves above those cards, and child planet images above the curves. Connectors now terminate ~12dp inside each planet for a visually angled emerge/enter effect.
- Use independently measured, two-line-capable mission titles so long names are not truncated at the beginning or by fixed texture heights.
- Spear of Adun purchase and start-with-Spear now include one real first-tier Progressive Proxy Pylon item, including migration of existing saved Spear owners; the next paid tier grants the reinforcement squad. Refresh the live AP item stream after the Spear unlock.
- Update Spear unlock/pylon descriptions and the three combined progressive race weapon/armor shop descriptions.
- No changes to the APRogue Galaxy gameplay file.

## v1.1.0 r19 — Launcher settings hotfix and 50% translucent planet cards

- Fix r18 themed-launcher regression that hid the game options: the launcher now inserts Available Races above the form, but the theme still unpacked the seven root widgets in their old order, treating the race row as the form. Detect the four-column GridLayout by widget type so changes to widget order cannot silently remove the full settings controls.
- Keep Available Races immediately above the generator options, with right-aligned explanation and functioning race selection. Retain Generate/Load/Reset actions, the folder selector and difficulty description panel.
- Set all three race-tinted mission rectangle fills and the fallback rectangle fill to 50% alpha. Soften the surrounding race-tinted outline to match.
- Add executable mock-Kivy layout regression tests for both orderings and the no-race fallback, plus 50% opacity checks. SC2 gameplay and all potion effects unchanged.

## v1.1.0 r18 — generator, mission map, potion HUD and boon icon polish

- Moved race selection above the main generator options; right-aligned both its title and difficulty note immediately beside the checkboxes.
- Reduced each planet card height from 128dp to 116dp and tightened internal text spacing; opened horizontal branch separation from 25dp to 40dp.
- Mission connections now render over card backgrounds without misleading triangular arrowhead glyphs.
- Potion HUD moved to the top-right corner; empty or spent slot controls are hidden, and the entire dialog is hidden when neither slot contains an unused potion. Native targeting remains unchanged.
- Audited boon portraits with direct unit associations, correcting unit mismatches and their permanent-blessing variants using only bundled icons.
- Updated source assertions and added dedicated regression tests. No changes to the general combat/effect logic or mission generation.

# Changelog

## 1.1.0 r17 - Galactic native validation and horizontal planet cards

- Fix two **new compile-breaking Galaxy calls** introduced with the potion updates: `UnitHasAttribute(unit, c_unitAttributeStructure)` is not a Galaxy native. Replace both with `UnitTypeTestAttribute(UnitGetType(unit), c_unitAttributeStructure)`. One occurs in the campaign-building scan and the other in the Odin defensive-structure filter. This may explain the persistent all-races critical failure after the r16 event registration fix. **Requires a live SC2 campaign launch to confirm.**
- Audit the newly introduced potion function names against the documented native API. Preserve potion targeting, spawn, and boon normalization logic.
- Replace centered vertically stacked planet nodes with horizontally oriented rounded mission cards: planet on left, status/race/name on right. Give Terran a very subtle blue tint, Zerg a violet tint, and Protoss a gold tint. Size each card from measured text width, not a clipped fixed label.
- Reduce route vertical floor spacing from 205dp to 178dp, adjust planet-centered curve attachment points and preserve the scroll/zoom overlay.
- Replace green sale outlines with lightly green-tinted backgrounds in both compact shop rows and expanded cards. Keep the SALE text and purchase logic unchanged.
- Add regression checks for invalid Galaxy function calls, label geometry, card colors and sale treatment; update pre-r17 presentation-only assertions.

## 1.1.0 r16 - Galaxy three-race fix and reduced repeat effects

- Fix invalid `TriggerAddEventUnitOrder` registration in the potion targeting code: the Galaxy native takes a `unitref`, but r9-r15 supplied a `unit`. A null unitref with strict `EventUnit()` filtering fixes the script-wide compile error while preserving native potion cursor behavior.
- After the full route and red-path adjustments, process all mission effects chronologically from layer 1 through the finale. Each previously encountered mutation or blessing independently has a 50% chance to switch to another legal effect at equal severity. Prefer effects not previously seen; repetition remains possible. Same-severity substitution leaves credit rewards, route difficulty, and the final-layer severity guarantees intact.
- No special Meat Grinder (`conga_line`) weighting was found; its normal severity-3 selection and independent draws allowed repeats.
- Add regression protection for the Galaxy argument type and effect-repeat logic.

## 1.1.0 r15 - Route viewport, shop sale visuals, and icon polish

- Use War Pigs' existing command-button art for Terran Contracts, and Hunter Killers' Hydralisk variant art for Zerg Contracts. Set both internal progression IDs and player-facing aliases, not just their captions.
- Change the author acknowledgement from "Mod design" to "Game Design".
- Halve mission-map wheel scrolling from 90dp to 45dp.
- Overlay the vertical route legend and zoom controls on the planet viewport instead of reserving a 104dp strip above it. The viewport now reaches the credits/inventory/shop row, and the differently shaded background band disappears.
- Remove opaque mission-title/race/status nameplates while retaining all labels and widened title spacing.
- Completely omit the Spear of Adun unlock portrait widget if no icon exists, including the inspector's reserved image height.
- Restore visible green SALE labels and inset green borders for discounted items in the default four-column shop list; preserve green styling on card view.
- No Galaxy gameplay, potion logic, mission-generation, or economy changes from r14.

## 1.1.0 r14 - Settings, compact UI, and mission balance

- New-run default Starting Credits: **600** (previously 700), in both the launcher and standalone generator. Previously generated runs retain their configured starting credits.
- New mission victory credit minimum: **150** (previously 250), before the Lab Rat -100 exception and the user-configurable victory multiplier. Existing generated runs preserve their already-rolled rewards.
- Increase the base mean mutation severity budget by **+1** on every floor and all campaign lengths, before applying Mutation Frequency. Update expected danger and opening-credit benchmarks so red-border difficulty classification remains calibrated.
- In generator settings add notes that removing races and increasing campaign length make the run easier; remove the Adventure Configuration heading, and rename Difficulty Description to Difficulty.
- Planet-map connections now extend farther into planet sprites, exposing more of each bezier curve and leaving the arrowhead at the visible sprite edge.
- Only the left route legend retains a dark background, arranged vertically (Available, Completed, High Risk), without the Sector Route heading. Zoom controls retain full functionality without a spanning header band.
- Compact shop heading, shift Shop label right, remove extra top/bottom popup margins, keep the borderless background and the existing purchase behavior.
- Halve UI sound volume again: `0.08 -> 0.04` in both themed and command UI audio paths.
- Correct the Additional Starting Minerals icon from MULE to mineral crystals, and the Additional Starting Vespene icon from refinery to the gas resource icon.
- Replace Terran Contract's SCV and Zerg Contract's egg icons with the closest **available building illustrations** (Terran Factory/Zerg Hive). Exact Mercenary Compound and Predator Nest icons are not bundled yet.
- Remove the misleading Immortal image from Unlock Spear of Adun, and add the description: "The Spear of Adun is available on all missions but starts with no abilities."
- Added nine focused regression tests. No changes to the Galaxy script or potion behavior.

## 1.1.0 r13 - Shop controls, popup frame, and potion purchase eligibility

- Rename the shop footer to `Exit Shop` and the shop heading to `Shop`; remove the redundant `All Categories` heading in the four-column shop overview.
- Remove the extra `Technology` action from all list entries, including combat units, defensive structures, and detectors. Related-technology information remains available in the existing card inspector.
- Remove the Kivy modal's bright nine-slice frame/title separator, use a flat dark background, and reduce the content gutters to reclaim space.
- Fix Slay-only potion purchase eligibility: the generic Archipelago item-table renderer erroneously marked every potion unavailable. It now delegates potion eligibility to the same two-slot and unlock requirements enforced by the actual purchase operation.
- Source-only regression tests cover empty/full potion slots, gated offers, randomized variants, and shop UI source. No Galaxy changes.

## 1.1.0 r11 - Tab navigation and mission race labels

- Preserve the real Archipelago tab identifiers (`Archipelago`, `Starcraft 2 Launcher`, `Slay Setup`) while displaying `Console Log`, `Missions`, `Settings` in the themed buttons. Fixes failures in `switch_screens()` and after run generation/loading.
- Mission nodes now show simply `Terran`, `Zerg`, or `Protoss` beneath the title; the playable race remains accurate for swapped mission variants.
- No gameplay/Galaxy/catalog changes from r10.

## 1.1.0 - Development

- Potion development r9: prices are now 125 × severity; Leviathan and Hyperion bottles use their existing boon normalization routines with player control. A private off-map caster now starts native SC2 Move command targeting and resolves actual issued ground/unit targets. Requires in-game SC2 testing.
- The previous r8 release added 16 potions, two consumable slots, two shop offers, and a bank-backed consumption handshake.

- Lab Rat now waits for a newly completed non-town-hall supply provider, then waits 7 additional seconds before the macro-base gate unlocks spawn placement.

- Fixed an Immortal Zergling Galaxy compile error caused by a five-argument `UnitCreate` call; release validation now checks all `UnitCreate` calls for the required six arguments.
- Fixed the unavailable-mission X marker by drawing two separate diagonals and doubled its size.

- Integrated Wangfeng's English StarCraft-style command UI.
- Added selectable Terran/Zerg/Protoss run setup.
- Added optional Endless Mode while Standard Mode remains the default.
- Fixed private embedded-Python loading of the Endless client patch helper during Download Data.
- Ported Wangfeng's full English SC2 theme lifecycle onto the v1.1.0 launcher and fixed the Endless mission-table wrapper that could leave the route blank.
- Refined the themed UI: list view is the shop/inventory default, original four-column category layout/colors are restored, map zoom/scroll behavior is revised, mission labels/outlines are larger, navigation/settings copy is cleaned up, and UI sound volume is reduced.

This file records public/development milestones. The more detailed rolling development notes remain in `README.txt`.

## 1.0.2.17 - Development

- True Golden Armada patrols unrestricted random playable-map destinations after 10 minutes, allowing routes to cross and attack through the player base.
- Removed temporary 10x development selection bonuses from newly introduced mutations so they use normal mutation selection probabilities.

## 1.0.2.16 - Development

- Fire in the Sky excludes both Another Gorgon effects in generation and runtime/random acquisition.
- Kerrigan announces successful respawns in chat.
- Commander heroes announce successful respawns using canonical player-facing hero names.
- Prepared the source tree for GitHub collaboration with source validation, build helpers, contribution templates, and repository hygiene files.

## 1.0.2.x - Development lineage

The `1.0.2.x` line contains bug fixes and active development based on the stable `1.0.2` release. It includes mission pacing work, shop corrections, standardized autonomous combat AI, death-spawn safety, portable installer fixes, new/experimental mutations, Golden Armada work, and the Test Potion prototype. See `README.txt` for the detailed cumulative notes carried by the current development build.

## 1.0.2 - Stable release

Public stable release baseline used for the current bug-fix development branch.

### v1.1.0 potion development r10 (unreleased)

- Applied the updated 19-potion catalog with 125 × rarity pricing; reduced the Odin/Leviathan/Hyperion severities to 2/3/4.
- Added Mass Marines and Mass Spellcasters as short-duration, nonblocking spawn queues with resource spending and autonomous Slay AI.
- Added a shop-rolled, dynamically named unit-spawn potion with a fixed quantity computed from combined base mineral/gas costs; offers and purchases preserve the rolled variant.
- Preserved r9 native targeting and boon-based Leviathan/Hyperion behavior. See POTIONS_TEST_NOTES.md for implementation caveats.

## v1.1.0 r12 — Planet mission chart hotfix

- Fix `slay_endless_ui.py`'s `resolve_route_positions` wrapper to accept and forward the optional measured node-width mapping. The wrapper still accepted only three arguments after the wide-title layout began passing four; it caused `TypeError` on ordinary Adventure missions and triggered the legacy rectangular-map fallback.
- Preserve widened mission titles, abbreviated race labels, working themed tabs and all r10 potion effects. No Galaxy gameplay modifications.
- Add a dedicated regression suite for the chart adapter in Adventure and Endless modes.

### v1.1.2 Dev21 (development)
- Clamp Slay and AP-adjusted mercenary recruitment cooldown/charge durations to at least 1 second, retaining the three-second >500s overflow recovery to 10 seconds.
- Make Meat Grinder boon Marines reacquire attack targets every 10 seconds without requiring Cloning Technology.
- Prevent Slay's scripted damage and scripted AoE near Null Circuits from destroying The Purification mission objectives outside native mission death handling.

## v1.1.2 Dev25 — Unit unlocks and recycled armor refunds

- Reaver/HERC/Infested Liberator unlocks set to 100 credits. Recycled Armor Suits refunds 8 minerals and 2 gas for uncommandable Slay infantry and 25/10 for controllable infantry.

### Dev26 — Kerrigan respawns and performance
- Confirm playable Kerrigan respawns after one second before messaging; retry failed spawns at the player base without another 60-second wait.
- Meat Grinder spreads five Marine spawns over fast ticks (two per tick).
- Autonomous Marine/Clone retarget work uses shared enemy groups and 40-unit tick budget, retaining nearest reachable target selection.

### Dev27 — Spider Mine structure exclusions
- Exclude Spider Mines from building-targeted Slay effects, especially Building Overcharge, through shared structure queries.
