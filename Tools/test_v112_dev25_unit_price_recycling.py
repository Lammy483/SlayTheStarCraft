"""Dev25 pricing and per-unit controllability refunds, not boon-combination discounts."""
import csv
import unittest
from pathlib import Path
from test_v112_recycled_meat_grinder_dev24 import func

ROOT = Path(__file__).resolve().parents[1]

class UnitPricesAndRecycledArmor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'Payload/UNIT_SHOP_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
            rows = list(csv.DictReader(f))
        cls.prices = {r['Unit']:int(r['Price']) for r in rows}
        cls.names = [r['Unit'] for r in rows]

    def test_reaver_and_herc_prices(self):
        self.assertEqual(self.prices['Reaver'],100)
        self.assertEqual(self.prices['HERC'],100)
        self.assertEqual(self.names.count('Reaver'),1)
        self.assertEqual(self.names.count('HERC'),1)

    def test_infested_liberator_price(self):
        self.assertEqual(self.prices['Infested Liberator'],100)
        self.assertEqual(self.names.count('Infested Liberator'),1)

    def test_other_unit_prices_unchanged(self):
        self.assertEqual(self.prices['Scout'],100)
        self.assertEqual(self.prices['Predator'],50)
        self.assertEqual(self.prices['Hercules'],100)

    def test_all_spawn_examples_use_shared_uncommandable_marker(self):
        self.assertIn('DataTableSetBool(true, "APRG_Uncommandable_"',func('APRG_MakeGroupUncommandable'))
        self.assertIn('APRG_MakeGroupUncommandable(created);',func('APRG_TryCloneProducedUnit'))
        self.assertIn('APRG_MakeGroupUncommandable(created);',func('APRG_SpawnMeatGrinderExtra'))
        self.assertIn('APRG_AddAlliedSupport(created, p, player, true);',func('APRG_ResolveWarfieldDrop'))

    def test_shop_uses_catalog_overrides_for_unlock_items(self):
        shop=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
        self.assertIn('UNIT_SHOP_PRICE_OVERRIDES = _load_unit_shop_price_overrides()',shop)
        self.assertIn('UNIT_SHOP_PRICE_OVERRIDES.get(item_name, 150)',shop)

if __name__ == '__main__':
    unittest.main()
