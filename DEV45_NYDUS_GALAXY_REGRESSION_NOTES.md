# Dev45 - Nydus Galaxy compilation regression fix

Live isolation with the same Dev44 runtime and data: Dev39 `APRogue.galaxy` initializes normally; Dev40 and later scripts cause the three-race critical error.

**Root cause candidate identified in the Dev39->Dev40 source diff:** Dev40 used unsupported native `UnitGroupUnit(buildings, j)` in `APRG_FindNydusSpawnPoint` to select a structure anchor. Dev39 did not contain that native. The valid 1-based indexed native is `UnitGroupUnitFromEnd` and is already used throughout the working source.

**One-line runtime change:**

```galaxy
anchor = UnitGroupUnitFromEnd(buildings, j);
```

The mutation selection, allied structure filtering, Nydus animations and waves, live vision and VO, Hybrid Research, Covert Assistance, Immortals and subsequent features are otherwise unchanged. A new release verifier guard and focused tests reject `UnitGroupUnit(` in future builds.

This fix has been source-verified and regression-tested offline. It has **not yet been validated by launching StarCraft II**.
