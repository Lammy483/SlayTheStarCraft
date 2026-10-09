"""Regression checks for Slay v1.1.0 r22 source integration."""
from __future__ import annotations
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]/'Payload'
SHOP=(ROOT/'slay_command_ui.py').read_text(encoding='utf-8')
CORE=(ROOT/'slay_the_starcraft.py').read_text(encoding='utf-8')
GAL=(ROOT/'APRogue.galaxy').read_text(encoding='utf-8')

class R22Regression(unittest.TestCase):
    def test_shop_sale_price_and_highlight_use_same_live_state(self):
        ast.parse(SHOP)
        self.assertIn('slay.shop_stock(manager.ctx)', SHOP)
        self.assertIn('sales=set(slay.shop_sale_items(manager.ctx,preserve=True))', SHOP)
        self.assertIn('slay.price_for_item(name,manager.ctx) < slay._price_for_item_before_sale(name,manager.ctx)', SHOP)
        self.assertIn("'sale':discounted", SHOP)
        self.assertIn('sales=priced_sales', SHOP)
    def test_inventory_button_opens_after_modal_dismissal(self):
        self.assertIn("control('Inventory',lambda *_:self.navigate_to('inventory')", SHOP)
        self.assertIn('self.popup.slay_navigate_to = destination', SHOP)
        self.assertIn("control('Exit Shop',lambda *_:self.close()", SHOP)
        self.assertNotIn('self.popup.bind(on_dismiss=lambda _pop:', SHOP)
    def test_owned_consumables_have_descriptions_in_inventory(self):
        ast.parse(CORE)
        self.assertIn('for slot in potion_inventory(ctx):', CORE)
        self.assertIn('"section": "Consumables"', CORE)
        self.assertIn('"description": str(potion["description"])', CORE)
    def test_spawn_waves_are_capped_globally(self):
        self.assertIn('massBudget = 3;', GAL)
        self.assertIn('count = MinI(massBudget, expected - g_aprgPotionQueueDone[slot]);', GAL)
        self.assertIn('massBudget -= MaxI(0, count);', GAL)
        self.assertIn('(now - g_aprgPotionQueueStarted[slot]) * 30.0', GAL)
        self.assertIn('if (kind == 17 || kind == 18)', GAL)
    def test_cocoons_removed_after_both_kerrigan_respawn_routes(self):
        self.assertIn('void APRG_RemoveKerriganReviveCocoons(int player)', GAL)
        segment=GAL.split('void APRG_TickShopKerrigan(int player, fixed now)')[1].split('void APRG_TickContractStructures')[0]
        self.assertEqual(segment.count('APRG_RemoveKerriganReviveCocoons(player);'),2)
        self.assertIn('UnitRemove(u);', GAL.split('void APRG_RemoveKerriganReviveCocoons(int player)')[1].split('void APRG_PositionShopKerriganAtHome')[0])
    def test_consumable_overlay_shift(self):
        self.assertIn('DialogCreate(544, 60, c_anchorTopLeft, 320, 0, false)', GAL)

if __name__=='__main__': unittest.main()
