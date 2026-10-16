# Slay the StarCraft v1.1.2 Dev7

Built on v1.1.2 Dev6; all Dev6 timing, patrol, catalog, and notification changes are retained.

## Bottled heroes

- **Leviathan in a Bottle** (rarity 3): Displays **"Spawn the WoL leviathan, but you cannot control it"**. Spawns at the selected location, cannot be selected or ordered, and attack-moves toward enemy structures. Its native Mutalisk and Brood Lord abilities are requested by an autonomous scheduler, with independent 60-second cooldowns. Summoned native Mutalisks and Brood Lords also join Slay's attack AI; no artificial fallback wave is added. Native ability availability is campaign-dependent.
- **Hyperion in a Bottle** (rarity 4): Displays **"Spawn the WoL hyperion, but you cannot control it"**. Spawns at the selected location, cannot be selected or ordered, and uses the existing friendly autonomous combat AI to attack the enemy base and cast Yamato. Yamato retains the 100-energy cost and 15-second cooldown. The existing internal resistance-removal normalization is preserved but never appears in user-facing potion text.
- These commandability changes apply **only to the bottled consumables**, not the permanent boons (which remain controllable). Odin is unchanged.

## Specialists image

- All item/boon/permanent-blessing `specialists` icon aliases now use `btn-unit-terran-raven.png` rather than the Lurker icon, in both icon maps.

## Validation

- Offline test suite and source verification are included in the package. Live SC2 testing is still required for the two native hero ability sets and native child-unit creation events.
- Runtime revision updated to `bottled-autonomous-heroes-v112-dev7`; Windows x64 GUI launcher rebuilt from Go source.
