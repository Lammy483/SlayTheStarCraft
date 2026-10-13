# Slay the StarCraft v1.1.2 Dev5 (unpublished)

- Zagara is forcibly killed at current life <=6, for both hostile Zagaras (including native mission variants) and player-controlled commander Zagara. Only enemy targets have Slay-generated hero no-revive behavior stripped; the friendly hero retains the ordinary commander respawn pipeline.
- Tosh's Miners' five SCVs now honor the current player's Archipelago allowed-unit tech tree, blocking disallowed building production commands and hiding locked building buttons. No automatic tech unlocking.
- Hyperion in a Bottle user-facing description is now `Spawn the WoL hyperion`; the resistance normalization remains only an implementation detail.
- Exclude creep tumors from all player/allied building-clearance patrol checks.
- All mutation tick processing and enemy regeneration wait for macro-base readiness; death-triggered hostile mutations and resource catalog mutations are deferred until readiness. Lab Rat's full custom base-establishment gate is preserved.
- Golden Armada: maintain 24-unit protected route clearance until base+4m; halve to 12 through base+9m; then attack-patrol unrestricted across entire map.
- True Golden Armada: maintain 40-unit clearance until base+10m; halve to 20 through base+15m, then attack-patrol anywhere. Apply the same stages to Phoenix orbit safety, Oracle pursuit, and mothership-death retaliation.
- Cone-line mutation spawning ramp and enemy mineral-thief timing now use base-relative elapsed time.
- Detailed base threat timing is in `DEV5_MUTATION_THREAT_AUDIT.md`.
- Offline regression tests and source verification run; native SC2 mission execution not available in this environment.
- Based on Dev4, keeping Dev1–Dev4 fixes; not pushed to GitHub.
