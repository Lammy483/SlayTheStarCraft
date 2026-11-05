# Slay the StarCraft — Events Dev11 test build

Branch: `develop/v1.2.3.1-odin-missions`. Date: 2026-11-05.
**This is an experimental source-integrated build, not a released version.**
GitHub smoke checks exercise Python logic and static Galaxy validation; no real
StarCraft II mission was run as part of the CI validation.

## Testing the events
1. Install/extract the complete portable Windows build; run `SlayTheStarCraft.exe`.
2. Use **Download Data** if needed, then launch the generator.
3. Choose **Standard Mode** and enable the **Events (BETA)** checkbox (off by default).
4. Generate a run. The start-of-run test selector lets you choose any of the ten
   events before mission one, without completing three missions first.
5. Check ordinary progression: events block the route after every third mission.
6. Verify resolving an event does **not** reroll the current shop, restock
   consumed potion offers, rotate discounts, or advance the shop cycle.
   Changing prices and newly unlocked items should refresh their availability.

## All ten event choices have source implementations
- **Merchant Vessel**: three one-use potion offers, raid for a potion without
  credits, hostile five-pod reprisal next mission, or leave.
- **Abathur's Evolution**: lose half the unlocked nonmercenary Zerg unit types
  and gain up to three real AP unit-specific upgrade items for each survivor,
  with no boons; or accept Zerg upgrade price penalty.
- **Nova's Mission**: AP Ghost/Spectre unlock; ally Nova or enemy Nova/Tosh,
  with bank-backed death persistence.
- **Zagara**: Brakk's Pack trial for permanent allied 100-Baneling waves, or
  join Brakk while Zagara sends hostile waves until slain.
- **Organism Field Test**: hostile Brutalisk trial and permanent ally/enemy
  Brutalisk thereafter; or Zerg price penalty.
- **Mechanical Ground Terran Unit Field Test**: choose an unowned factory
  unit, spawn roughly 1000 resources' worth in next mission, count 50 kills
  via native unit-death trigger, grant its real AP unlock once on success and
  +20% life/speed/weapon damage on future instances, or spawn buffed enemy
  patrols after failure; or Terran unit price penalty.
- **Dr Hansen's Colonists**: player-owned untargetable (not invulnerable) hut,
  periodic hostile infested waves, 150 credits per surviving mission, hut loss
  persisted in the SC2 bank; or refuse.
- **The Primal Crystalis**: grant 70 AP Kerrigan levels and force Brakk's/Dehaka's
  Pack mutation in future missions without increasing rewards; or Kerrigan
  price penalty.
- **Solarite Conversion**: next-mission 5000 mineral/gas trial; buffs or debuffs
  to Spear regeneration/cooldowns based on success; or Spear price penalty.
- **Unstable Vortex**: locally forfeit owned AP items, shop purchases, potions,
  and boons, then refund the total spent credits without rerolling shop stock;
  or avoid.

## Expected limitations / testing priorities
- Galaxy declaration/call checks do not prove an SC2 map will compile with
  all its native dependencies. Check for the historical three-race critical
  error by launching a mission in each race.
- Verify Nova/Tosh/Brakk/Zagara actors, hut placement, unit type fallback,
  the 50-kill counter and player-specific catalog +20% weapon effects in SC2.
- Verify the bank-backed quest rewards and persistent deaths after restarting
  the client as well as between missions.
- Test normal Standard with Events off, and both Crew and Campaign modes, for
  unintended event behavior.
- No branch has been promoted to a public release; do not mark Dev11 stable.

## Continuation
Check `Payload/slay_events.py`, `Payload/slay_the_starcraft.py`,
`Payload/APRogue.galaxy`, `Payload/install_slay.py`, and
`Tools/test_v1231_dev11_mechanical_events.py`.
