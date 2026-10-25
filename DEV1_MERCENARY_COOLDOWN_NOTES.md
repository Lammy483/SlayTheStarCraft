# v1.2.2.1 Dev1 — mercenary cooldown overflow repair

Development branch from the released v1.2.2 source. **No new public release.**

## Root cause and changes

The existing Repeat Contractor path already did `MaxF(1, value - 30*stacks)`
and the old three-second cooldown watchdog reset bad timers above 500 seconds,
but that watchdog only visited two cached contract buildings and discarded
abilities that the existing AP/mercenary unit classifier did not recognize.
Its existing timer lookup also omitted unit-wide and player-wide cooldown and
charge-regeneration scopes.

- Clamp mercenary cooldown and charge catalog fields before and after Repeat
  Contractor and Horde Mode reductions; positive recurring timers stay >=1.
- Preserve intentional `TimeStart=0`, including AP's Progressive Fast Delivery.
- Recover negative AP/campaign catalog durations to nonnegative values; recover
  values strictly >1000 to 10 seconds, without immediately subtracting
  Repeat Contractor again.
- Every three game seconds after base established, scan *all player-owned*
  Merc Compound and Predator Nest variants, including AP replacements,
  rather than only the two stored progression building pointers.
- Inspect attached abilities' direct, Cost[], InfoArray[], and nested Cost[]
  cooldown and charge fields even if their native unit IDs evade the
  mercenary command classifier.
- Check unit-ability, unit-scoped, and player-scoped timer links; if the
  **remaining time >1000 seconds**, set it to **10 seconds**. Do not alter
  legitimately long timers of 1000 seconds or less.

**AP distinction:** Rapid Reinforcement (Terran) reduces mercenary cooldowns
by 60 seconds; Progressive Fast Delivery (Terran) provides initial immediate
calldowns, so clamping its zero initial timers to one second is undesirable.

## Validation

- `python Payload/verify_release.py --source-only` passed.
- `python Tools/test_v1221_mercenary_cooldowns.py`: static and arithmetic
  regression coverage; the local expanded source equivalent passed all 6 tests.
- Installer's declaration-order, forward-call, and UnitCreate arity guards passed.
- Native SC2 Galaxy compilation/in-game cooldown behavior remains untested.

## Manual regression

In a newly launched Standard mission with Terran Merc Compound and/or Zerg
Predator Nest, purchase Repeat Contractor, Rapid Reinforcement, Progressive Fast
Delivery, and Evolutionary Leap in useful combinations. Call down mercs, watch
their ability cooldowns, and observe repeated casts. A bad timer above 1000
seconds should fall to 10 at the next three-second watchdog pass. Legitimate
cooldowns below that threshold are preserved.

The previous stable release v1.2.2 should remain unchanged until the fix has
been validated in live StarCraft II gameplay.
