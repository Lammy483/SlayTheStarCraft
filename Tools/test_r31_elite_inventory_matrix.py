"""r31 focused regression checks for elite classification and modal transitions."""
from __future__ import annotations

import ast
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
CLIENT = (ROOT / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GENERATOR = (ROOT / 'generate_slay_run.py').read_text(encoding='utf-8')
GALAXY = (ROOT / 'APRogue.galaxy').read_text(encoding='utf-8')
UI = (ROOT / 'slay_command_ui.py').read_text(encoding='utf-8')
PATCHER = (ROOT / 'install_slay.py').read_text(encoding='utf-8')
ICONS = (ROOT / 'slay_ui_icons.json').read_text(encoding='utf-8')


class R31Regression(unittest.TestCase):
    def test_opening_mission_nine_hundred_is_elite_without_credit_bonus(self):
        scope = {'Mapping': dict, '_expected_opening_credit_average': lambda config: 500.0}
        tree = ast.parse(CLIENT)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == '_mission_is_difficulty_outlier_in_nodes')
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<risk>', 'exec'), scope)
        is_elite = scope['_mission_is_difficulty_outlier_in_nodes']
        cfg = {'choice_layers': 12}
        self.assertTrue(is_elite({1: {'layer': 0, 'credit_reward': 900, 'expected_opening_credit_average': 500}}, 1, cfg))
        self.assertFalse(is_elite({1: {'layer': 0, 'credit_reward': 899, 'expected_opening_credit_average': 500}}, 1, cfg))
        self.assertIn('bonus = 0 if int(data.get("layer", -1)) == 0 else DANGER_CREDIT_BONUS', CLIENT)

    def test_glass_cannons_severity_two_everywhere(self):
        self.assertIn("'glass_cannons': 2", CLIENT)
        self.assertIn("'glass_cannons': 2", GENERATOR)
        with (ROOT / 'EFFECT_CATALOG.csv').open(encoding='utf-8-sig', newline='') as stream:
            row = next(x for x in csv.DictReader(stream) if x['Title'] == 'Glass Cannons')
        self.assertEqual(row['Severity'], '2')

    def test_inventory_header_button_order_and_explicit_transition(self):
        header = UI[UI.index('class CardConsole:'):UI.index('        root.add_widget(top)', UI.index('class CardConsole:'))]
        positions = [header.index('top.add_widget(self.view_button)'), header.index("control('Shop',"),
                     header.index("control('Exit Inventory',")]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('Close Inventory', UI)
        self.assertNotIn('self.popup.bind(on_dismiss=lambda _pop:', UI)
        self.assertIn('self.popup.slay_navigate_to = destination', UI)
        self.assertIn('self.manager.slay_shop_reopen_pending = False', UI)
        self.assertIn('destination = getattr(popup, "slay_navigate_to", None)', PATCHER)
        self.assertIn('elif reopen:', PATCHER)

    def test_tosh_casts_actual_campaign_shield_on_first_damage(self):
        source = GALAXY[GALAXY.index('bool APRG_TryToshDefensiveShield('):
                        GALAXY.index('void APRG_TickToshAndHisBoys(')]
        self.assertIn('health >= healthMax - 0.5', source)
        self.assertIn('"VoodooShield"', source)
        self.assertIn('UnitOrderIsValid(tosh, shieldOrder)', source)
        self.assertIn('APRG_RecordAICast(tosh, abilityType)', source)
        self.assertIn('APRG_TryToshDefensiveShield(g_aprgTosh);', GALAXY)

    def test_terran_pack_uses_bundled_armory_icon(self):
        self.assertIn('"BOON::upgrade_pack::terran": "btn-building-terran-armory.png"', ICONS)
        self.assertTrue((ROOT / 'slay_assets/icons/btn-building-terran-armory.png').is_file())


if __name__ == '__main__':
    unittest.main()