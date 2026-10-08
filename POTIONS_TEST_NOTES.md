# Consumables — compatibility and testing notes (r21)

The user-facing feature is now called **Consumables**. Existing `POTION_*` Python symbols, `APRG_Potion*` Galaxy functions, serial keys, and `SlayTheStarCraftPotions.SC2Bank` are *internal compatibility identifiers*, deliberately unchanged to avoid invalidating saved runs and client/Galaxy handshakes. `Payload/POTION_CATALOG.csv` retains its file name for the same reason. User-visible item descriptions are taken exclusively from its `Effect Description` column, never from the development notes.

# Previous targeting and catalog test notes — r9

- Fixed consumable prices: 125 × severity (formerly 100 × rarity). The updated user-supplied catalog contains 19 consumables with severities 1–4.
- Leviathan in a Bottle now uses exactly the Leviathan boon's unit resolver and ability 60-second cooldown normalization. It no longer scripts duplicate Mutalisk / Brood Lord spawns. It remains player-owned and controllable.
- Hyperion in a Bottle now uses exactly the Hyperion boon's normalization (3,000 HP, armor 3, no innate regen, behavior resistance cleanup, Yamato energy/cooldown). Remains player-owned and controllable.
- Native point/unit targeting is initiated with the StarCraft II UISetTargetingOrder native cursor on a private off-map caster with a Move order. Unit targeting uses OrderGetTargetUnit rather than the former nearest-unit approximation. Invalid selections should not consume consumables. Right-click cancels.
- Tosh's Miners unchanged: workers spawn beside the flying Command Center.
- **Live validation required**: this build was not run inside SC2; the native cursor, dummy caster and correct order event behavior must be tested on campaign maps.

## r10 — user-supplied catalog update (2026-10-08)

- The exact uploaded 19-row balance table is retained as `Payload/POTION_CATALOG.csv`.
- Existing 16 consumable wire IDs remain unchanged to preserve save compatibility. New consumables use IDs 17 (Mass Marines), 18 (Mass Spellcasters), and 19 (random spawn roll). The random offer has 18 curated combat-unit variants with wire IDs 1901–1918.
- Updated prices (125 × rarity): Odin 250, Leviathan 375, Hyperion 500. Other existing prices retain their severity multiplier; the three new consumable types each cost 125.
- Mass Marines immediately consumes up to 5,000 available minerals and queues one Marine for each 10 minerals consumed, up to 500. Mass Spellcasters similarly consumes up to 5,000 gas and queues one spellcaster per 20 gas, up to 250. Consumables are not spent for less than 10 minerals/20 gas or when the player base is missing.
- Both queues distribute creation over approximately two in-game seconds via the existing 0.1s fast-tick (maximum 25 spawns per tick, two concurrent queues). Units are player-allied but nonselectable/uncommandable, receive no supply consumption, attack-move toward standard Slay enemy targets, and idle units are periodically retargeted. Spellcasters use Slay's existing autonomous-ability AI. Spellcaster candidates follow the Specialists blessing plus Brood Queen, Medic, and High Templar variants. Missing variant IDs fall back to standard High Templar.
- The randomized spawn consumable rolls its unit **when the shop stock is generated**, displays the exact amount/name in the shop, persists that variant in inventory, and sends the matching stable variant wire ID in the existing mission handshake. Quantity is `floor(2000 / (mineral + gas cost))` from a curated list of conventional base-unit costs. Units spawn over two seconds at the player-selected location and auto-attack enemies; unlike Mass Marines/Spellcasters, these units remain commandable.
- The two-consumable-slot limit, two offers per shop cycle, native targeting, consumable consumption bank, and r9 Leviathan/Hyperion boon reuse remain unchanged.
- SHOP_STOCK_LOGIC_VERSION incremented to 112 so saved shop stock refreshes with the expanded catalog.
- **Not live-tested in StarCraft II.** The Galaxy runtime and unit-variant availability require tests in WoL, HotS, and LotV; static validation cannot guarantee API or catalog behavior. Native targeting and bank synchronization still need verification in SC2.
