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
