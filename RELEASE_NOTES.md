# Slay the StarCraft v1.2.3

Complete Windows release based on the v1.2.2 release and v1.2.2.1 Dev4 development changes.

## Changes since v1.2.2

### Mercenary cooldown correction
- Prevent the Archipelago **Rapid Reinforcement (Terran)** upgrade from applying its native unchecked 60-second reductions to mercenary starting and repeat cooldowns. Slay applies the equivalent reduction with a safe minimum, including when combined with **Repeat Contractor** stacks.
- Preserve **Progressive Fast Delivery** and its immediate initial calldowns.
- Normalize invalid negative cooldown durations and clamp invalid catalog cooldowns over 1,000 seconds to 10 seconds.
- Expand the live mercenary timer failsafes to player-wide, unit-wide, and ability-level cooldown/charge links; check player-owned Merc Compounds and Predator Nests every three game seconds.
- Correct Galaxy syntax introduced in the first cooldown-development attempt that prevented missions from loading (the reported three-race error).

### Shop fixes
- Correct **Enhanced Allies** from an erroneous 999,999-credit placeholder to **600 credits**.
- Repair the prices and descriptions for all 11 boons introduced in the v1.2.2 release: Eternal Perdition, Speedy Buildings, Enhanced Allies, Explosive Predators, Harvesting Equipment, Refective Diamondbacks, Psionic Guardians, Improved morphs, Psionic Lords, Unlimited Scarabs, and Armor Disintegration.

### Mission compatibility
- **Jetpacks** mutation can no longer appear on **Smash and Grab**, including race variants. Both initial generation and live mutation eligibility checks enforce this.

## Installation
1. Extract the ZIP into a writable folder (do not run it within the ZIP).
2. Run `SlayTheStarCraft.exe`.
3. Select **Download Data** when prompted; the launcher installs its private Python/Archipelago runtime and StarCraft II data without a system-wide Python installation.
4. Launch Slay.

If upgrading, retain any personal `Config/slay_preferences.ini` preferences and run saves. Campaign and Crew Challenge remain **BETA**.

## Validation status
The source verifier, focused boon-price and mission-exclusion tests, and Galaxy syntax checks pass. ZIP extraction and integrity were checked. Native Windows launch and live StarCraft II cooldown behavior were **not tested in this environment**; please verify them before wide distribution.
