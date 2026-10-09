# Slay the StarCraft v1.1.0

A feature release of the single-player StarCraft II Archipelago roguelike.

## Highlights

- Overhauled English StarCraft-style interface for mission selection, shops, inventory, setup and in-mission consumables; Chinese localization contributions and improved UI by Wangfeng.
- Configurable Standard Mode campaign lengths, new run options, and experimental **Endless Mode (ALPHA)**.
- New and updated mutations, blessings, boons, consumable potions, AI behaviors and scripted reinforcements across all three campaigns.
- Victory reward balance: flat 100-credit baseline bonus per mission, 125 credits per mutation severity point, and a 100-credit deduction per blessing severity point, plus tier and special adjustments.
- First-run launcher downloads its private Python, Archipelago and SC2-specific data as needed. The ZIP does not require a system Python installation.

## Installation

1. Extract the ZIP to a normal writable folder (for example `C:\Games\SlayTheStarCraft`), not directly into the Windows Program Files folder.
2. Launch `SlayTheStarCraft.exe`.
3. Choose **Download Data** on first launch and keep the launcher open while it finishes. StarCraft II and its campaign content must already be installed.
4. Generate a run or load an existing one.

Endless Mode is **ALPHA**; use Standard Mode for the intended v1.1.0 experience. The release has passed automated source checks, but not every mission/unit combination can be verified by automated tests.
