# Dev46 Galaxy declaration repair (UNCONFIRMED IN-GAME)

This release starts from Dev45 and removes one redundant Galaxy function prototype:
`void APRG_TickNydusWorms(int player, fixed now);`
It appeared at a later line than that function's actual definition, unlike the working Dev39 baseline.
No other gameplay source changes were made in the full build.

IMPORTANT: Offline validation cannot guarantee the game's Galaxy compiler accepts this
source. The removed declaration is a concrete structural anomaly to isolate, not a
confirmed root cause. Test `Dev40_NoLatePrototype` first from the separate
Galaxy-only diagnostic package. If that still fails, try its
`Dev40_NoLatePrototype_NoActorSound`, then `Dev40_StubNydus` variants.

The previous Dev45 assertion that UnitGroupUnit is an invalid native was WRONG:
UnitGroupUnit(unitgroup, int) is a valid native in SC2. Dev45's replacement
with UnitGroupUnitFromEnd is equivalent for the randomly selected index,
but this was not the root cause.

Other additions audited:
- Dev41 unit behavior APIs UnitBehaviorCountAll/UnitBehaviorGet/UnitBehaviorRemove
  match published native signatures. The Heavily Defended Drill forward declaration
  precedes its first use and definition.
- Dev42 hybrid choose/spawn functions are defined before the death handler.
- Dev43 Immortals spawn helper is defined before the tick call.
- Dev44 voice queue function already had a prior prototype in the working baseline.

No global campaign dependency change. The user should use the same Dev44/Dev45
launcher and mission for source-isolation tests and NOT run Download Data again.
