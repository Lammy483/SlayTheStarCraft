# Slay the StarCraft v1.2.3.1 — Events Dev7 progress

Working branch: develop/v1.2.3.1-odin-missions
Date: 2026-11-05
Status: Source regression and Galaxy declaration checks pass in GitHub Actions; **not SC2 gameplay-tested**.

## Event rules
- Standard Mode only; enabled by an opt-in checkbox defaulting off.
- Opening test selector plus subsequent event barriers at 3-mission intervals.
- No repeat of a currently eligible event until every eligible event was assigned. Include the opening selection in the used set. Once exhausted, repeats are permitted.
- Merchant Vessel raid grants one free random potion **without any credits**, and keeps the 5-minute mercenary retaliation next mission.

## Newly playable: Abathur's Evolution
- Eligible only when at least four distinct non-mercenary Zerg unit unlocks are owned.
- Agree: deterministic random half of unlocked Zerg units lost. Their shop unlock counts are removed and any pre-existing AP reward receipts for those units are forfeited locally. Mission network item stream filters these forfeited AP items. Later newly obtained copies can restore the unit.
- For each surviving Zerg unit, award up to three available unit-specific upgrade items. Rewards persist in event_awarded_items and are inserted as normal synthetic AP items in future missions.
- Refuse: Zerg upgrade prices permanently +50%.
- Results are displayed in a scrollable popup with units lost and upgrades gained.
- New persisted state keys event_forfeited_ap_counts and event_awarded_items are sanitized and restored.
- Corrected opening selector's "Choose a different test event" back action (previously looked up __test_select__ in EVENTS and crashed).

## Current scope
Merchant Vessel and Abathur's Evolution are the only ordinary randomly selected events.
The other eight remain inspectable via the opening test selector, with unimplemented choices disabled. Only existing refusal/avoid consequences may be playable.
The other events, full game integration tests, and an in-game test run remain pending.

## Validation
GitHub Actions: .github/workflows/events-dev6-smoke.yml
- Python compilation and source-only release verification
- Galaxy declaration/call validator
- Dev3–Dev6 regression tests, including new event state tests
