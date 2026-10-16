# Dev30 — Blessing / mutation description audit

- Correct six `EFFECT_CATALOG.csv` rows that had copied descriptions from same-named effects of the opposite kind. Corrected: Occasional Ultralisk (blessing), Occasional Thor (blessing), Occasional Colossus (blessing), Zombies (blessing), ANOTHER GORGON (blessing), and Drakken Laser Drill (mutation).
- Restored wording verbatim from the October 11 MutationsBlessings workbook. Every other effect description is unchanged; all seven same-named mutation/blessing pairs are independently verified by regression tests.
- The existing kind-specific `(title, mutation|blessing)` lookup in `slay_the_starcraft.py` is retained; no gameplay rules, severities, or effect IDs changed.
- Tests are source-level; live in-game tooltip/chat confirmation remains outstanding.
