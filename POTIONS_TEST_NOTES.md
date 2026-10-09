## r37 Purifier Vortex live checks

- Purifier Alliance boon: put an enemy structure within 10 range but no visible enemy units; the allied Purifier must **not** cast Vortex on the structure. Then move visible enemy units within 10 range and confirm it can cast at them and resumes moving afterwards.
- Purifier mutation: repeat with player structures only, then player army units nearby. The enemy Purifier should use Vortex on visible player units, **not** on buildings. Its scripted Planet Cracker behavior should be unaffected.
- Confirm neither version casts at hidden/fogged units and that the map's original scripted boss (if present) remains unchanged.

## r36 live checks — minimize, Zombies and Purifier AI

1. In a mission with two consumables, click the small `-` button. Confirm the entire panel collapses to a small `+` restore button and stops covering mission objectives. Expand and activate a targeted and nontargeted consumable; ensure inventory persistence, native targeting, and right-click cancellation still work. Repeat after using a consumable and with zero available slots.
2. With the Zombies blessing/mutation or Zombie Apocalypse, kill naturally existing Infested Terran (and campaign Infested Civilians). They should trigger death-spawns unless they have timed life. Zombie units spawned by Zombies or Zombie Apocalypse should never trigger additional zombie spawns even with both effects active.
3. Trigger Purifier Alliance and follow friendly Zealots, Stalkers, Void Rays, and air escorts through the five-second warp. They must proactively attack nearby enemies and retarget after their targets die, including when their original order stalls. Repeat with For Aiur and with mutation Purifier escorts/ground waves attacking the player.
4. On Haven's Fall, Safe Haven, and a non-Haven mission, the mutation-spawned enemy Purifier must take immediate damage, with no `InvulnerabilityShield` buff. The normal Safe Haven scripted boss encounter must retain its campaign shield behavior. Player AI should target the mutation Purifier normally.
5. Check the three playable races for Galaxy compilation, targeting, and non-overlapping HUD controls.

### r35 Purifier mutation regression

- On Haven's Fall (without Kerrigan), activate the Purifier mutation and attack its newly spawned mothership. Confirm damage goes through immediately and no InvulnerabilityShield buff remains.
- On Safe Haven, verify the separate vanilla/Archipelago scripted Purifier encounter still uses its own shield progression; the Slay mutation's additional Purifier must be vulnerable from the start.
- Confirm the mutation still moves, spawns escorts/ground waves and fires Planet Cracker; check a non-Haven mission for the same behavior.
- Purifier Alliance (friendly boon) is deliberately unchanged.

## r34 live regression checks

1. Acquire the Leviathan boon, produce a Corruptor to replace with the native Leviathan, and press F2 (select all army). Confirm the Leviathan is selected with other army units and remains commandable.
2. Use Leviathan in a Bottle, press F2, and confirm the spawned Leviathan joins the selection. Test both standard WoL and HotS campaign mission dependencies if possible.
3. Use a non-targeted consumable and a targeted consumable. Neither should show a `[Slay]` informational message or temporary notice panel. Targeting should still show `[TARGETING]` on the consumable button and the native target cursor; invalid clicks must not spend it.
4. Confirm ordinary gameplay `[Slay]` warnings/alerts are unaffected.

## r32 live tests — Niadra, Mira, enemy Drakken

1. Obtain Niadra as a Commander and through Heroes of the Storm. Use Birth Zergling, Birth Roach and Birth Hydralisk, including available upgraded strain variants; each used birth ability should have a 60-second cooldown. Verify ability cards and cooldown visualization, and that unrelated abilities are unchanged. Check WoL, HotS and LotV mission contexts.
2. Trigger Mira's Mercenaries beside a dense player/allied base. Their camp must be >=20 range from every friendly building. Repeat on a non-island map with isolated enemy pockets; Mira's ground force must be able to reach the player's base. If no safe point exists, there must be no unsafe fallback placement. Check spawn performance with the full squad.
3. Spawn an enemy Drakken Laser Drill and watch one durable player unit being continuously targeted. The beam should break by nine seconds, remain interrupted about two seconds and resume attacking. Repeat with a unit saved by Spear of Adun Guardian Shell: it must not become permanently invulnerable. Check that the friendly Drakken boon does not pulse/pause.
4. Smoke test launch and Galaxy compilation with each of the three player race settings (avoid the prior three-race critical regression).

## r30 live tests — Single-Use Tools / Tosh and his Boys

1. Purchase Single-Use Tools (400). On each subsequent mission victory, return to shop/inventory: one random, eligible shop consumable is awarded when an inventory slot is free. With two occupied slots, no reward is given or queued for later. Reconnect/reopen should not grant a duplicate. Earlier victories never give retroactive rewards.
2. Trigger Tosh and his Boys on a non-island mission, verify Tosh spawns on a pathable hostile part of the map. He patrols from three minutes after base established. At four minutes first hostile cloaked Spectre approaches and calls a nuke close to a player building; repeat each minute only while Tosh lives. Killing a casting Spectre should prevent any fallback detonation. Kill Tosh and confirm later Spectres stop spawning, without resurrecting Tosh.
3. Check the enemy Tosh/Spectre variants and native SpectreNuke capability on WoL, HotS, LotV. Check no three-race critical error, and verify mission-island exclusions in generation and later rerolls.

## r29 live tests — icons, Shop Expansion, squads, warp visuals

1. Open Consumables in the shop and inventory. Confirm icons differ by effect: Mass Spellcasters = High Templar; Mass Stimpack = Stimpack; Hyperion = Battlecruiser; Leviathan = Leviathan; random spawn choices match their actual unit. Confirm no missing-texture/empty images.
2. Compare upgrade icons against the Archipelago SC2 content-docs site for source images (Nano Projectors, Mercenary Munitions, Superior Warp Gates, etc.); documentation artwork must win over UI guessed icons.
3. Buy Shop Expansion repeatedly and verify Consumables displays one extra eligible offer per purchase, starting from two, without allowing more than two carried consumables. Test newly expanded shop immediately and after reroll.
4. With both Merc Compound and Predator Nest alive and unlocked merc types, activate Mercenary Favor. Confirm War Pigs=4, Hammer Securities=2, heavy Jotun/Jackson's Revenge=1; Terran mercs arrive near Merc Compound and Zerg mercs near Predator Nest. Also test no potion loss when neither contract structure remains alive.
5. Drop Pod Wave: Warfield says Deploy Drop Pods exactly once, not once per impact. Check ten pods still land with the expected units.
6. Check the narrower buttons near the top and at 15% from left; objective labels must not be obscured, at standard and wide aspect ratios.
7. Check visible warp-in effect, five-second pause/fade, and later combat for Nexus Shields, For Aiur, Purifier hostile reinforcements and Purifier escorts.

## r28 live tests — High Templar, Spear Recharge, warp-in animation

1. Use **Mass Spellcasters** with a native High Templar and have it approach groups of enemies. Check that it casts Psi Storm on clustered units whenever it has sufficient energy, then continues its attack-move. Also verify the Specialists blessing's autonomous High Templar. Player-commanded Templar must remain entirely manually controllable.
2. Unlock Spear of Adun: the **Spear of Adun Recharge** consumable should be hidden while only Deploy Pylon is available, then eligible after buying one *additional distinct active* Spear ability, such as Orbital Strike. Buying Guardian Shell, Overwatch, Reconstruction Beam, or only another Pylon tier should not satisfy the condition. Use the potion after reducing Spear energy and activating an ability; energy should refill, but existing ability cooldowns must continue normally.
3. Generate a run with Smash and Grab and reroll/add mutations to that mission. **Nexus Shields** must never appear there, but remains allowed on appropriate other missions.
4. Compare scripted **For Aiur, Nexus Shields, and Purifier** warp-ins in WoL, HotS, and LotV. Look for the campaign's shimmering `ProtossGenericWarpInOut` animation at each unit, *as well as* the existing five-second fade/stun. This is source verified but cannot be confirmed visually without StarCraft II.

## r27 contract building permanence and consumable placement

In a mission with Terran Mercenaries enabled, let the Merc Compound spawn, destroy it, and continue for at least one minute. It must never reappear. Repeat with the Predator Nest when Zerg Mercenaries are enabled. If no valid building spawn position exists yet, initial placement must still retry when a suitable anchor becomes available. Both buildings can appear again in a *new* mission.

Consumables should now sit at the absolute top of the mission HUD, beginning around 15% from the left on 16:9 displays, rather than competing with the Archipelago messages in the upper-right. Verify that objectives remain legible and that both controls remain clickable. Other aspect ratios use the same 320-unit offset, so the percentage will vary slightly; spot-check at 16:10 or 4:3 if relevant.

## r26 live tests (unverified in StarCraft II)

Use a random-unit consumable containing a Stalker, Zealot, Immortal, or Siege Tank after unlocking an AP variant. Verify the spawn is a healthy unlocked variant, can be commanded immediately, and receives no automatic attack order. Verify the default War Council variants are selected when available. If no safe AP variant is unlocked, the normal native unit should appear. Mass Marines and Mass Spellcasters must remain uncommandable and autonomous.

Verify warp visuals over the full five-second stun window in Nexus Shields, Purifier, and For Aiur cases, especially on WoL and HotS missions. Verify all intended visuals appear in addition to the five-second unit fade. Check Hyperion Yamato uses energy and a cooldown, Spear recharge restores ability cooldowns after using them, Mercenary Favor grants every unlocked squad, and Mass Spellcasters spawn real Infestors/other spellcasters at full energy. The external Archipelago messages cannot yet be repositioned safely by Slay; only the consumable notices last four seconds.

## r24 targeting-caster safety and live test

The private `APRoguePotionTargetCaster` remains a player-owned native Move-order actor, but now uses XML `NoDraw`, `Unselectable`, `Unclickable`, `Uncursorable`, `Untargetable`, and `Invulnerable` flags, plus runtime selectable/targetable/tooltip state suppression. It must never show up in all-army selection or be attacked. Confirm the native SC2 point and unit targeting cursor still works in WoL/HotS/LotV after these flags are set. Do not mark it `Uncommandable` because that could prevent the scripted Move order event used for targeting.

Verify Golden Armada on The Outlaws in particular: the rebel base should be outside the 55-range spawn buffer and 40-range route buffer; the early fleet should use safe Move orders until four minutes. True Golden Armada keeps its ten-minute early patrol mode and waits at least four minutes before a mothership-death assault. Live SC2 testing is required; offline checks cannot prove native AI behavior or map-specific placement.

## r23 mid-mission consumable test

Start a mission with no consumables. Open the Slay shop while the mission is running, buy one consumable, and verify its button appears at the top right within roughly a game second; buy a second and verify the additional button. Use a consumable and buy a replacement without restarting the mission; check that the replacement is not marked used by the old serial. Watch the SC2/chat logs for `?SlayConsumables`. Relaunch to ensure startup handshake still works. This path is source-tested but not SC2-tested. Also test Baneling Stream attack-move and Orlan's `DukesRevenge` ship on different campaigns.

## r22 mass-wave testing

Mass Marines and Mass Spellcasters create no more than three units total per 0.1s game tick, shared across both queues. A 500-unit wave takes at least ~16.7 game seconds. Check that the units appear across many updates without freezing the mission, remain autonomous, and that bought but unused consumables appear in Inventory with their verbatim descriptions. Top-right consumable controls have moved downward 12 UI units. The external Archipelago message overlay has not been repositioned; it requires a verified frame hook.

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
