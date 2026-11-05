# Slay the StarCraft — Events Dev12 test build

Branch: `develop/v1.2.3.1-odin-missions`. Date: 2026-11-05.
This is an **untested SC2 gameplay build**, not a public release.

## Changes since Events Dev11

1. **Rory Swann — failed field test:** Enemy mechanical patrols now attack-move
   toward the player's home structure rather than toward an enemy base anchor.
   A source-level Galaxy regression test checks the target selection.
2. **Abathur — AP upgrade copies:** Previously awarded Archipelago upgrades
   already contribute to logical owned-item counts. Do not add those copies
   a second time when deciding whether an upgrade has remaining quantity.
   This allows a surviving unit to receive an additional valid upgrade copy.
3. **Unstable Vortex — shop continuity:** Preserve `shop_cycle_purchases`
   so items sold earlier in the current shop cycle remain sold, even after
   owned upgrades are forfeited and credits are refunded.

## How to test

1. Download the **slay-the-starcraft-events-dev12-test-windows** artifact
   from the Events Dev12 portable test build GitHub Actions workflow and
   extract the entire folder before launching `SlayTheStarCraft.exe`.
2. Select Standard Mode, enable **Events (BETA)** (off by default), and
   generate a run. Select any event using the opening test selector.
3. Test Rory Swann: choose a field-test unit, complete its trial mission
   without reaching 50 kills, then verify next-mission enemy mechanical
   units attack toward your own base instead of standing around enemy bases.
4. Test Abathur with at least four unlocked Zerg units, including
   unit-specific upgrades that support multiple copies, and verify
   the survivors receive available real AP item upgrades.
5. Test Vortex at a normal event checkpoint with an item already purchased
   from the current shop: enter the vortex, verify the refunded credits,
   the unchanged shop offers and discounts, and the fact that already-sold
   item offers do not become purchasable again. Event resolutions must not
   count as victories or cause stock rerolls.
6. Retest all ten events and all three races in real SC2 for native event
   spawn logic, Galaxy syntax, bank persistence, and client restarts.

Source-only CI checks Python compilation, release verification, Galaxy
declaration checks, and the Dev3–Dev11 event regression suites. This does
**not** substitute for a live StarCraft II playtest.
