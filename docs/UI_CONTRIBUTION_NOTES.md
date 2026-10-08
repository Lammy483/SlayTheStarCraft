# UI and gameplay contribution notes

Original mod and ongoing development: **Lammy**. Chinese localization and UI/custom-mode contributions: **Wangfeng (王枫 / Wangfeng114514)**. StarCraft II artwork, icons, and audio remain the property of their respective rights holders. SC2 Archipelago provides the base mission and item systems; Redfrog's roguelike mods inspired the original mod.

## Version and scope

The migration is based on Lammy483/SlayTheStarCraft `main`, commit `73d1328`, version **1.0.2.17**. It retains the author's current gameplay fixes and adds the contributed UI and optional run settings. Endless mode is a separate, optional gameplay extension and should be reviewed separately from presentation changes. A pull request does not replace or merge the author's main branch automatically.

## Source checkout versus a playable package

This is a source repository. `Runtime`, downloaded Archipelago source, generated executables, player saves, and extracted Blizzard assets are deliberately excluded from Git contributions. A source ZIP is therefore not equivalent to a complete player release.

For a normal installation, use the author's release package, extract it to a writable folder, point the launcher at the actual StarCraft II installation, click **Download Data**, and then **Launch Slay**. The Wings of Liberty, Heart of the Swarm, and Legacy of the Void campaigns are required; Nova Covert Ops is not required. Follow the repository's `docs/DEVELOPMENT.md` and `docs/RELEASING.md` for a source build. Keep existing `Runs` and `Config` directories when upgrading.

## Missing maps, Mods, or runtime dependencies

Check that the selected StarCraft II directory contains `Versions`. Use Download Data to install the pinned dependencies and required Archipelago data. Do not substitute arbitrary newer Archipelago versions: the installer validates known source revisions. A runtime-revision mismatch should be investigated rather than bypassed. Keep the failure log and report the affected filename and version.

## Optional UI artwork and audio

Planet textures, command-button icons, panel artwork, and interface sounds must come from the user's own StarCraft II installation or an explicitly permitted asset package. They must not be committed to this repository. Fonts and native extraction libraries also need their own licenses and compatible builds.

The current localized package stores converted local assets in `Payload/slay_assets/` and copies them to `Runtime/Archipelago/slay_assets/`. Its item-to-button map is `item_btn_icons.json`; command icons go in `slay_assets/icons/`, planet images in `slay_assets/planets/`, and optional UI sounds in `slay_assets/sounds/`. Use the corresponding **btn-** command texture for each item, not unrelated portraits or model images. This is the localized-package layout, not a claim that upstream already implements this asset pipeline.

If an optional image is missing, do not edit gameplay IDs or download an untrusted asset bundle to hide the problem. Re-extract the matching asset from the selected local installation or restore it from the same compatible localized package. Restart the launcher after replacing cached images. Missing optional sound must not block a button action.

The upstream UI contribution works without an asset pack: it draws original planet/starfield fallbacks and interface borders. Optional artwork is read from `slay_assets` beside `slay_command_ui.py`, or the directory set by `SLAY_UI_ASSETS`. Item button filenames are mapped in `slay_ui_icons.json`. Set `SLAY_UI_STYLE=classic` before launching to use the original interface. Asset-free UI simulations passed at 1920×1080, 1400×950 and 1024×720; native purchase callbacks, category coverage, discount duplicates, inventory, route selection and 12 dense layout cases were exercised. Local texture caching is bounded; no remote image request is made during navigation.

## Compatibility and testing

Keep canonical English mission/item/effect identifiers in saved data and network messages. Translate display strings through explicit locale keys; do not replace identifiers to obtain translated UI text. Existing saves must retain their stored options and progression.

Required source check: `python Payload/verify_release.py --source-only`. UI simulations, generation tests, and save/reload tests do not substitute for an in-game playtest. Release notes and pull requests must distinguish these checks from actual StarCraft II results.
