# Slay the StarCraft — Events Dev14 hotfix (2026-11-05)

This is an experimental Standard Mode Events (BETA) build. No native SC2
gameplay has been confirmed in this automated environment.

## Three-race Galaxy startup failure
The Dev13 Rory Swann field-test implementation declared a local Galaxy
variable named `native` in two functions. `native` is a Galaxy keyword,
so even races/events that never execute those functions could fail to
compile the shared APRogue library on mission startup.

Both declarations and all uses are renamed to `mechUnitType`. A new
regression test checks every local variable declaration in APRogue.galaxy
for reserved Galaxy keywords, in addition to existing arity/forward
declaration validation and the no-ternary guard.

## Missing banner, shop icons, changed button colors
The lightweight Dev13 package contained `slay_assets/item_btn_icons.json`
but no original PNG artwork files. The JSON maps icon names but cannot draw
the images. Missing button textures also changed Kivy fallback colors.

On first launch Dev14 searches sibling Slay installation directories for
the original UI artwork and copies it into both the portable Payload and
installed Archipelago theme folder. If no adjacent installation contains it,
open **Settings > Restore UI Artwork** and select the folder of an older
Slay installation that still displays the original banner. Restart Slay
after importing. Without those original artwork files, Dev14 shows a dark
banner fallback rather than a pale-blue rectangle; the full SC2 portraits
are not synthesized by this patch.

## Test plan
1. Install or extract Dev14 into a fresh directory; the art-recovery
   functionality does not need a reinstall of SC2 maps or mods.
2. Select Standard Mode with Events (BETA) checked. Generate a test run
   and enter one Terran, one Zerg and one Protoss mission. Confirm there
   is no three-race Galaxy critical error. Repeat with Events disabled
   to check the shared-script regression.
3. Force the Rory Swann field-test event; verify chosen unit spawns and
   its 50-kill trial can complete. Test success and failure follow-ups.
4. Check the Settings banner, shop portraits, and button styling. If
   artwork is absent, select your previous Slay install through the new
   Restore UI Artwork button and restart.
5. Verify a normal Standard run, Crew and Campaign remain functional.

The Windows workflow validates Python, Galaxy lexical/syntax guards and
regressions, then builds a portable launcher. It does not invoke SC2
itself, so the three-race fix remains pending user game testing.
