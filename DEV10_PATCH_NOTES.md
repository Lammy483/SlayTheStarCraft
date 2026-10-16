# Slay the StarCraft v1.1.2 Dev10

## Portrait
- Stretchy Spines shares precisely the same bundled Spine Crawler unlock icon: `btn-building-zerg-spinecrawler.png`. It was already correct in Dev9 package mappings; no unrelated portrait has been imported or substituted.

## The Crucible
- 27 enemy-structure-dependent/anchored mutations are prohibited on all Crucible variants, even if an effect has a random-location fallback.
- Includes native hostile building target effects (Meat Grinder, Nexus Shield, Nuclear Structures), spawn-anchor-dependent armies and raids (Golden Armada variants, Purifier, Tosh, Brakk, Odin, Dark Templar, Drop Pods, etc.).
- Preserves effects not tied to pre-existing enemy buildings, e.g. Orlan’s newly created fortress, Sniper Thor, native-unit combat modifiers.
- Exclusions apply in run generation, same-severity anti-repeat rerolls, shop effect rerolls, and runtime mutation activation, including previously generated saves.

## Economy
- Unlimited Power: 1,400 credits in `BOON_CATALOG.csv` and the pricing fallback.

No GitHub changes. Live SC2 gameplay remains untested.
