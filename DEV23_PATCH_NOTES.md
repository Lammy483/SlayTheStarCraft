# Dev23: scripted Protoss warp-in visual repair

Blizzard's `ppurifier03` campaign script attaches `ProtossGenericWarpInOut` using `libNtve_gf_AttachModelToUnitInheritVisibility(unit, model, "Ref_Origin")`. Slay previously used the non-visibility-inheriting attachment at `Ref_Center`, which could leave the spawned units merely fading in. Use the native attachment path for both `APRG_ProcessPurifierHostileWarpQueue` (Nexus Shields/Purifier) and `APRG_ProcessAllyWarpQueue` (For Aiur/Purifier Alliance).

On campaigns where the generic model is not available, try `MothershipTeleportIn` (already used by Blizzard's WoL Safe Haven map) as a reduced-size Protoss entry flash. The last-resort marker is not assumed to be a complete animation. The five-second pause/fade and order/AI handling remain the same. Model/catalog availability and visual correctness require live SC2 testing.

This build is based on Dev22. No GitHub changes.
