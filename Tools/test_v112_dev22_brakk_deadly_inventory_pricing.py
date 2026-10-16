"""Dev22 regression checks: Brakk stats, repeatable boon inventory, balance."""
import ast
import csv
from collections import Counter
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'Payload'
GALAXY = (PAYLOAD / 'APRogue.galaxy').read_text(encoding='utf-8')
RUNTIME = (PAYLOAD / 'slay_the_starcraft.py').read_text(encoding='utf-8')


def isolated_inventory_rows():
    node = next(n for n in ast.parse(RUNTIME).body if isinstance(n, ast.FunctionDef) and n.name == 'inventory_rows')
    scope = {
        'Any': object, 'Counter': Counter,
        '_item_table': lambda: {}, '_actual_item_counts': lambda ctx: Counter(),
        'state': lambda ctx: ctx, 'potion_inventory': lambda ctx: [],
        'BLESSING_SEVERITY': {}, 'EFFECT_BANK_BITS': {},
        'EFFECT_DISPLAY_NAMES': {'boon_deadly_weapons': 'Deadly Weapons', 'boon_auto_repair': 'Auto-repair', 'boon_defender': 'Defender'},
        'EFFECT_DESCRIPTIONS': {}, 'REPEATABLE_BOON_KINDS': {'deadly_weapons', 'auto_repair'},
        '_boon_id': lambda kind: 'BOON::' + kind,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<inventory test>', 'exec'), scope)
    return scope['inventory_rows']


class Dev22Changes(unittest.TestCase):
    def test_inventory_shows_all_purchased_stacks(self):
        inventory = isolated_inventory_rows()
        data = {
            'purchases': {},
            'permanent_boons': ['boon_deadly_weapons', 'boon_auto_repair', 'boon_defender', 'boon_deadly_weapons'],
            'permanent_blessings': [], 'permanent_mutations': [],
            'boon_purchases': {'BOON::deadly_weapons': 4, 'BOON::auto_repair': 3, 'BOON::defender': 1},
        }
        rows = inventory(data)
        by_id = {row['canonical_name']: row for row in rows}
        self.assertEqual(len(rows), 3)
        for boon, count in [('boon_deadly_weapons',4), ('boon_auto_repair',3), ('boon_defender',1)]:
            self.assertEqual(by_id[boon]['shop_count'], count, boon)
            self.assertEqual(by_id[boon]['total'], count, boon)
        # Old saved games with a single purchase still render x1.
        data['boon_purchases']['BOON::deadly_weapons'] = 1
        self.assertEqual({r['canonical_name']: r['total'] for r in inventory(data)}['boon_deadly_weapons'], 1)

    def test_deadly_weapons_25_percent_per_stack_in_catalog_and_game(self):
        self.assertIn('desiredBonus = baseValue * 0.25 * IntToFixed(g_aprgDeadlyWeaponsStacks);', GALAXY)
        self.assertNotIn('desiredBonus = baseValue * 0.3 * IntToFixed(g_aprgDeadlyWeaponsStacks);', GALAXY)
        with (PAYLOAD/'BOON_CATALOG.csv').open(newline='', encoding='utf-8-sig') as f:
            deadly = next(row for row in csv.DictReader(f) if row['Boon Title'] == 'Deadly Weapons')
        self.assertEqual(deadly['Description'], 'Your units all deal 25% more damage')
        self.assertIn('"deadly_weapons":"Your units all deal 25% more damage"', RUNTIME)

    def test_time_stop_price_is_1200(self):
        with (PAYLOAD/'SPEAR_OF_ADUN_SHOP_CATALOG.csv').open(newline='', encoding='utf-8-sig') as f:
            timestop = next(row for row in csv.DictReader(f) if row['Item Title'] == 'Time Stop (Spear of Adun)')
        self.assertEqual(int(timestop['Cost']), 1200)
        self.assertIn('SPEAR_SHOP_PRICE_OVERRIDES = _catalog_int_prices(_SPEAR_SHOP_CATALOG_ROWS)', RUNTIME)

    def test_only_brakk_gains_1000_life_and_3_armor(self):
        start = GALAXY.index('void APRG_TickBrakkArmy(int player, fixed now)')
        end = GALAXY.index('\nvoid ', start+1)
        body = GALAXY[start:end]
        self.assertIn('UnitGetPropertyFixed(brakk, c_unitPropLifeMax, c_unitPropCurrent) + 1000.0', body)
        self.assertIn('UnitGetPropertyFixed(brakk, c_unitPropLife, c_unitPropCurrent) + 1000.0', body)
        self.assertIn('UnitBehaviorAdd(brakk, "APRogueBrakkArmor", brakk, 1);', body)
        buff = ET.parse(PAYLOAD/'APRogueData.xml').find(".//CBehaviorBuff[@id='APRogueBrakkArmor']")
        self.assertIsNotNone(buff)
        self.assertEqual(buff.find('Modification').get('LifeArmorBonus'), '3')
        # The buff must not affect spawned pack minions by type.
        self.assertEqual(GALAXY.count('UnitBehaviorAdd(brakk, "APRogueBrakkArmor", brakk, 1);'),1)

if __name__ == '__main__': unittest.main()
