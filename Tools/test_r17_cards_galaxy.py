"""Regression guards for the r17 horizontal mission cards and Galaxy API fix."""
from pathlib import Path
import ast
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
UI = (ROOT / 'slay_command_ui.py').read_text(encoding='utf-8')
GALAXY = (ROOT / 'APRogue.galaxy').read_text(encoding='utf-8')

class R17RegressionTests(unittest.TestCase):
    def test_unsupported_galaxy_attribute_function_is_gone(self):
        # Native SC2 Galaxy supports UnitTypeTestAttribute but NOT UnitHasAttribute.
        # This name was introduced twice in the potion-era changes and prevents
        # the entire APRogue library from compiling for all three races.
        self.assertNotIn('UnitHasAttribute(', GALAXY)
        self.assertIn('UnitTypeTestAttribute(UnitGetType(u), c_unitAttributeStructure)', GALAXY)
        self.assertGreaterEqual(GALAXY.count('UnitTypeTestAttribute(UnitGetType(u), c_unitAttributeStructure)'), 2)

    def test_native_cursor_and_potion_boon_reuse_are_retained(self):
        for token in (
            'UISetTargetingOrder(', 'TriggerAddEventUnitOrder(',
            'APRG_NormalizeLeviathanBoon(u, player);',
            'APRG_NormalizeHyperionBoon(u, player);',
        ):
            self.assertIn(token, GALAXY)
        self.assertIn('TriggerAddEventUnitOrder(g_aprgPotionOrderTrigger, null, AbilityCommand("move", 0))', GALAXY)

    def test_horizontal_mission_cards_are_race_tinted_and_compact(self):
        self.assertIn('nameplate=RoundedRectangle(', UI)
        self.assertIn('race_fills=', UI)
        self.assertIn('NODE_PLANET_CENTER_Y=58', UI)
        self.assertIn('ROUTE_FLOOR_SPACING=178', UI)
        self.assertIn('text_x=b.x+dp(110)', UI)
        self.assertIn('title.pos=(text_x,b.y+dp(8))', UI)
        self.assertIn('status_label.pos=(text_x,b.y+dp(81))', UI)
        self.assertIn('race_label.pos=(text_x,b.y+dp(56))', UI)
        self.assertIn('title.text_size=(text_width,None)' , UI)
        self.assertIn('b.x+dp(NODE_PLANET_X)', UI)

    def test_sale_background_instead_of_green_outline(self):
        self.assertIn("color=(.13,.23,.16,1) if shop and entry.get('sale')", UI)
        self.assertIn('sale_background=RoundedRectangle(', UI)
        self.assertIn("row_title+='  [color=7CFF9B][b]SALE[/b][/color]'", UI)
        self.assertNotIn('slay_sale_outline', UI)
        ast.parse(UI)

if __name__ == '__main__':
    unittest.main()
