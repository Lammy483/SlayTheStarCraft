"""r18 UI, Galaxy visibility, and unit-boon icon regression guards."""
import ast
import json
import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'Payload'
LAUNCHER = (ROOT/'slay_launcher.py').read_text()
UI = (ROOT/'slay_command_ui.py').read_text()
GALAXY = (ROOT/'APRogue.galaxy').read_text()
ICONS = json.loads((ROOT/'slay_ui_icons.json').read_text())

class R18Tests(unittest.TestCase):
    def test_races_above_options_instead_of_action_buttons(self):
        self.assertIn('root.remove_widget(form)\n    root.add_widget(race_row)\n    root.add_widget(form)', LAUNCHER)
        self.assertIn('halign="right"', LAUNCHER)
        self.assertIn('(Removing races makes the game easier)', LAUNCHER)
        self.assertIn('"Available Races"', LAUNCHER)
        self.assertLess(LAUNCHER.index('root.add_widget(race_row)'), LAUNCHER.index('root.add_widget(button_row)'))
        ast.parse(LAUNCHER)

    def test_compact_spaced_cards_and_foreground_connections_without_arrows(self):
        self.assertIn('NODE_CARD_HEIGHT=116',UI)
        self.assertIn('dp(40)',UI)
        self.assertIn('dp(44)*max(0,len(row)-1)',UI)
        self.assertIn('chart.canvas.before.add(group)',UI)
        self.assertIn('chart.canvas.before.remove(old)',UI)
        self.assertNotIn('tip_y=b.y-dp(6)',UI)
        self.assertNotIn('arrowhead=Line',UI)
        ast.parse(UI)

    def test_empty_potion_slots_hidden_and_hud_near_top_left(self):
        self.assertIn('DialogCreate(490, 60, c_anchorTopLeft, 320, 0, false)',GALAXY)
        self.assertIn('DialogControlSetVisible(g_aprgPotionButton[i], players, false)',GALAXY)
        self.assertIn('DialogControlSetVisible(g_aprgPotionButton[i], players, true)',GALAXY)
        self.assertIn('DialogSetVisible(g_aprgPotionDialog, players,',GALAXY)
        self.assertIn('!g_aprgPotionUsed[0] && g_aprgPotionType[0] > 0',GALAXY)
        self.assertIn('!g_aprgPotionUsed[1] && g_aprgPotionType[1] > 0',GALAXY)
        self.assertNotIn('"  |  EMPTY"',GALAXY)
        self.assertIn('UISetTargetingOrder(',GALAXY)

    def test_unit_related_boon_icons_match_units_and_exist(self):
        for key, fragment in {
            'BOON::corrosive_claws':'zerg-zergling',
            'BOON::concussed_shells':'terran-marauder',
            'BOON::cell_division':'zerg-ultralisk',
            'BOON::invasion_fleet':'zerg-mutalisk',
            'BOON::kill_streak':'terran-ghost',
            'BOON::dead_man_switch':'terran-spectre',
            'BOON::defender':'protoss-photoncannon',
            'BOON::unexpected_evolution':'protoss-stalker',
        }.items():
            with self.subTest(key=key):
                value=ICONS[key]
                self.assertIn(fragment,value)
                self.assertTrue((ROOT/'slay_assets/icons'/value).is_file(),value)

if __name__=='__main__': unittest.main()
