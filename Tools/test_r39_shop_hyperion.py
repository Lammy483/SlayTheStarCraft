"""r39 regressions: per-stock potions, track discounts, player-only Hyperion Yamato."""
import ast
import csv
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
CLIENT = (ROOT / 'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
GALAXY = (ROOT / 'Payload/APRogue.galaxy').read_text(encoding='utf-8')
CATALOG = ROOT / 'Payload/APRogueData.xml'


def body(name, source=CLIENT):
    tree = ast.parse(source)
    node = next((item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name), None)
    assert node is not None, name
    return ast.get_source_segment(source, node)


def galaxy_body(name):
    prefix = f'void {name}('
    start = GALAXY.index(prefix)
    start_brace = GALAXY.index('{', start)
    depth = 0
    for i in range(start_brace, len(GALAXY)):
        if GALAXY[i] == '{': depth += 1
        elif GALAXY[i] == '}':
            depth -= 1
            if depth == 0: return GALAXY[start:i + 1]
    raise AssertionError(name)


class ShopConsumableRules(unittest.TestCase):
    def test_shop_purchase_once_even_after_drinking(self):
        purchased = {'potion_inventory': [], 'potion_serial': 0, 'shop_potions_bought': [], 'spent': 0}
        potion = 'slay_potion::7'
        ctx = object()
        def slots(_): return purchased['potion_inventory'][:]
        env = dict(Any=Any, Sequence=Sequence, POTION_CATALOG={potion:{'name':'Test Potion','price':50}},
                   POTION_CAPACITY=2, enabled=lambda _:True, state_ready=lambda _:True,
                   state=lambda _:purchased, shop_stock=lambda _:[potion],
                   potion_inventory=slots, _potion_unlock_eligible=lambda _ctx, name: True,
                   credits=lambda _:999, price_for_item=lambda *_:50, _persist_state=lambda *_:None)
        for name in ('can_buy_shop_item','purchase'):
            exec(body(name),env)
        self.assertTrue(env['can_buy_shop_item'](ctx,potion))
        ok,msg=env['purchase'](ctx,potion)
        self.assertTrue(ok,msg)
        self.assertEqual(purchased['spent'],50)
        self.assertEqual(purchased['shop_potions_bought'],[potion])
        purchased['potion_inventory'].clear()  # The player actually uses the consumable.
        self.assertFalse(env['can_buy_shop_item'](ctx,potion))
        ok,msg=env['purchase'](ctx,potion)
        self.assertFalse(ok)
        self.assertIn('Reroll or win',msg)
        self.assertEqual(purchased['spent'],50)

    def test_shop_roll_and_reroll_clear_purchases_not_expansion(self):
        roll = body('shop_stock')
        boon = body('_purchase_boon')
        self.assertIn('s["shop_potions_bought"] = []',roll)
        reroll = boon.split('elif kind=="reroll_shop":',1)[1].split('elif kind==',1)[0]
        expand = boon.split('elif kind=="shop_expansion":',1)[1].split('elif kind=="reroll_shop":',1)[0]
        self.assertIn('s["shop_potions_bought"] = []',reroll)
        self.assertNotIn('s["shop_potions_bought"]',expand)
        purchase = body('purchase')
        self.assertIn('s["shop_potions_bought"] = list(dict.fromkeys(',purchase)
        self.assertIn('"shop_potions_bought": []',CLIENT)
        self.assertIn('raw_potion_purchases = value.get("shop_potions_bought", [])',CLIENT)

    def test_both_discount_prices_are_500(self):
        for filename, title in [('KERRIGAN_SHOP_CATALOG.csv','Reduced Kerrigan Shop Prices by 50%'),
                                ('SPEAR_OF_ADUN_SHOP_CATALOG.csv','Reduced Spear of Adun Shop Prices by 50%')]:
            with (ROOT/'Payload'/filename).open(encoding='utf-8-sig',newline='') as f:
                row=next(row for row in csv.reader(f) if row and row[0]==title)
            self.assertEqual(int(row[-1]),500)


class HyperionYamato(unittest.TestCase):
    def test_cost_exists_for_campaign_native_ability_before_runtime_patch(self):
        root=ET.parse(CATALOG).getroot()
        abil=root.find('./CAbilEffectTarget[@id="HyperionYamatoSpecial"]')
        self.assertIsNotNone(abil)
        cost=abil.find('Cost')
        self.assertEqual(cost.find('./Vital[@index="Energy"]').attrib['value'],'0')
        self.assertEqual(cost.find('Cooldown').attrib['TimeUse'],'0')

    def test_cost_and_cooldown_per_player_precede_both_spawn_paths(self):
        setup=galaxy_body('APRG_ConfigureHyperionYamato')
        for text in ('"HyperionYamatoSpecial"','"Cost.Vital[Energy]", player, "100"',
                     '"Cost.Cooldown.TimeUse", player, "15"',
                     '"Cost[0].Vital[Energy]", player, "100"'):
            self.assertIn(text,setup)
        self.assertEqual(GALAXY.count('APRG_ConfigureHyperionYamato(player);'),3)
        boon=GALAXY[GALAXY.index('void APRG_NormalizeHyperionBoon('):GALAXY.index('string APRG_LeviathanBoonType()')]
        self.assertIn('APRG_ConfigureHyperionYamato(player);',boon)
        replacement=GALAXY[GALAXY.index('APRG_TryGoliathsOnlineProducedUnit(trained, player);'):GALAXY.index('else if (!g_aprgLeviathanUsed')]
        self.assertLess(replacement.index('APRG_ConfigureHyperionYamato(player);'),replacement.index('libNtve_gf_ReplaceUnit('))
        bottle=GALAXY[GALAXY.index('else if (kind == 3 || kind == 4 || kind == 5) {'):GALAXY.index('else if (kind == 6)',GALAXY.index('else if (kind == 3 || kind == 4 || kind == 5) {'))]
        self.assertLess(bottle.index('APRG_ConfigureHyperionYamato(player);'),bottle.index('UnitCreate('))
        self.assertIn('APRG_NormalizeHyperionBoon(u, player)',bottle)


if __name__=='__main__': unittest.main()
