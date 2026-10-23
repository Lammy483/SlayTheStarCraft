# Slay the StarCraft v1.2.2

Portable Windows release based on the cumulative Dev90 gameplay source.

## Highlights

- **Standard**, **Campaign (BETA)**, and **Crew (BETA)** modes, including Crew reserves, free deployment, and persistent unit rosters.
- Outbreak is now a Tier 0 mission; the Standard shop places Boons in its third column.
- Deadly Vultures uses a native weapon-effect catalog modifier instead of scripted damage.
- Shared mission and item fixes: Great Train Robbery, Devil’s Playground, Niadra commander, Golden Armada, credits, and more.
- The original 12-mission high-risk generation balance is preserved; other campaign lengths are normalized.
- Warp Gate is **not** rebound by default in public builds. Set a `[Hotkeys] Warpgate=E` preference in `Config/slay_preferences.ini` only if desired.

## Installation

Extract this ZIP into a new writable folder, launch `SlayTheStarCraft.exe`, choose Download Data for the initial runtime, then Launch Slay. Requires StarCraft II; no system-wide Python installation required.

## Important release notes

- Campaign and Crew are labeled BETA.
- Source-level and installer tests passed, but the complete v1.2.2 package has not been tested on a fresh Windows installation. Verify native SC2 interactions (especially Deadly Vultures, Niadra, and Crew) before a wide public announcement.
