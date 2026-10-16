# Slay the StarCraft v1.1.2 Dev8

Built on v1.1.2 Dev7. No GitHub branch or release was changed.

## Stretchy Spines portrait

- All display aliases for Stretchy Spines, including its permanent-blessing version and localized label, now use `btn-building-zerg-spinecrawler.png`.
- The portrait is the existing bundled Spine Crawler command-card image from `Payload/slay_assets/icons/`, the same source used by Slay's shop portraits. Both `Payload/slay_ui_icons.json` and `Payload/slay_assets/item_btn_icons.json` were updated. Spine Rifling still uses the Hydralisk image as intended.

## Shop Expansion cap

- Maximum three total Shop Expansions per run, including any extra starting shop slots configured at generation.
- The item is excluded from boon stock roll candidates once three expansions are active; any already displayed stock entry becomes unpurchasable. Direct purchase and boon purchase paths also reject a fourth expansion, including after a shop reroll.
- Existing state with more than three expansions is clamped on load (both the expansion count and purchase counter). Stock generation caps expansion size and the stock schema increments to 114 so an older saved shop rebuilds with the current limits.
- Shop Expansion's 200-credit base cost, +1 slot per category including consumable offers, and final-three-missions restriction are unchanged.

## Victory credits

- Removed the flat +100 credits added to **every** mission victory in r40. Normal baseline payout before tier, mutation, blessing, and first-layer bonuses is now 400 rather than 500.
- Kept +125 credits per mutation severity point, -100 per blessing severity, mission tier, 150-credit floor before Lab Rat's special -100, +50 for layer 1 and +25 for layer 2, the configurable victory reward multiplier, and the separately conditional high-risk/risky-investment bonuses.
- Generator and legacy-node fallback both use the new baseline. Opening credit-average estimates used for elite detection were lowered by 100 from their prior respective values; newly generated run rewards reflect the update, while already-generated node payouts remain stored and unchanged.

## Validation

- Source verifier and offline regression tests, including Dev8-specific tests for all portrait aliases, shop cap checks, reward calculations, and package revision. Requires in-game testing for the shop overlay/receipt.
- The Windows x64 GUI launcher is compiled with the Dev8 runtime revision `spine-expansion-credits-v112-dev8`.
