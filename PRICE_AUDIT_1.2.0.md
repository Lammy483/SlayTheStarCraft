# v1.2.0 Workbook Pricing Audit

Pricing source: `Slay The Starcraft (4).xlsx`, uploaded October 2026. Compared all price-bearing rows across Boons, Spear of Adun, Mercs, Kerrigan, Units and Upgrades, and Consumables with the shipped catalogs.

| Sheet | Item | Dev51 price | v1.2.0 price |
|---|---|---:|---:|
| Boons | Meat Grinder | 400 credits | **500 credits** |
| Units and Upgrades | Infested Liberator | 100 credits | **50 credits** |

Every other directly corresponding price and price formula matched. The workbook's `archipelago scout variants (including caladrius)` maps to the existing `archipelago scout variants` price family and remains **80 credits**. Kerrigan Levels remain `15 × number of levels`, and consumables remain `125 × rarity`.

The Meat Grinder fallback cost was changed in `Payload/slay_the_starcraft.py` as well as `BOON_CATALOG.csv`. No mutation severities or descriptions were overwritten. Event descriptions mention separate event outcome prices, not shop catalog entries; event logic was not modified as part of the price audit.

The full source verifier and 468 applicable regression tests passed after price and release metadata changes.
