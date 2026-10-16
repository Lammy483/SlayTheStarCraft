# v1.1.2 Dev22 — Brakk health and armor; repeatable inventory; balance

- Brakk spawned by Brakk's Pack receives 1000 extra max and current HP, plus a Brakk-only +3 armor buff. His pack and unrelated units of the same type receive no bonus.
- Deadly Weapons now adds 25% of baseline damage per stack; the existing data-table reconciliation and additive stacking are otherwise unchanged. Updated the runtime shop tooltip and BOON_CATALOG.csv.
- Inventory rows determine repeatable boons from the canonical `boon_<kind>` effect ID, not a partial explicit reverse mapping. Both Deadly Weapons and Auto-repair now use their actual `BOON::<kind>` purchase counts; nonrepeatable boons remain x1. This fixes display only: purchases and gameplay stack counts were already correct.
- Time Stop (Spear of Adun) costs 1200 credits in the authoritative catalog.
- Galaxy source verification and applicable Python offline regressions passed; live SC2 test remains necessary.
- No GitHub changes.
