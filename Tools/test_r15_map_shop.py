"""r15 source-level regressions. Run without Archipelago or Kivy installed."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / 'Payload/slay_command_ui.py').read_text(encoding='utf-8')
THEME = (ROOT / 'Payload/slay_theme.py').read_text(encoding='utf-8')
ICON_MAP = json.loads((ROOT / 'Payload/slay_ui_icons.json').read_text(encoding='utf-8'))

class R15MapShopTests(unittest.TestCase):
    def test_contract_icons_use_real_internal_ids_and_existing_images(self):
        expected = {
            'PROGRESSION::terran_contracts': ('War Pigs', 'btn-unit-terran-marinemercenary.png'),
            'PROGRESSION::zerg_contracts': ('Hunter Killers', 'btn-unit-zerg-hydralisk-remastered.png'),
        }
        for internal, (mercenary, artwork) in expected.items():
            with self.subTest(internal=internal):
                self.assertEqual(ICON_MAP[internal], artwork)
                self.assertEqual(ICON_MAP[mercenary], artwork)
                self.assertTrue((ROOT / 'Payload/slay_assets/icons' / artwork).is_file())

    def test_acknowledgements_are_game_design(self):
        self.assertIn('Original author · Game Design, development, balance and bug fixes.', THEME)
        self.assertNotIn('Original author · Mod design,', THEME)

    def test_scroll_speed_is_halved(self):
        self.assertIn('scroll.scroll_wheel_distance=dp(45)', UI)
        self.assertNotIn('scroll.scroll_wheel_distance=dp(90)', UI)

    def test_map_key_overlays_instead_of_consuming_viewport_height(self):
        self.assertIn('overlay=FloatLayout(size_hint=(1,1))', UI)
        self.assertIn('campaign_root.remove_widget(shell)', UI)
        self.assertIn('overlay.add_widget(shell)', UI)
        self.assertIn('strip.pos_hint={\'top\':1}', UI)
        self.assertIn('overlay.add_widget(strip)', UI)
        self.assertIn('campaign_root.add_widget(overlay,index=shell_index)', UI)
        self.assertNotIn('manager.slay_mission_tab.content.add_widget(strip,index=1)', UI)
        self.assertIn('manager.slay_chart_overlay=overlay', UI)

    def test_mission_labels_in_horizontal_rounded_cards(self):
        self.assertIn('nameplate=RoundedRectangle(', UI)
        self.assertIn('text_x=b.x+dp(110)', UI)
        self.assertIn('title.pos=(text_x,b.y+dp(8))', UI)
        self.assertIn('race_label.pos=(text_x,b.y+dp(56))', UI)

    def test_sale_label_and_green_background_in_default_rows(self):
        self.assertIn("if shop and entry.get('sale'):", UI)
        self.assertIn("row_title+='  [color=7CFF9B][b]SALE[/b][/color]'", UI)
        self.assertIn("color=(.13,.23,.16,1) if shop and entry.get('sale')", UI)
        self.assertNotIn('self.slay_sale_outline=Line(', UI)
        self.assertIn('sale_background=RoundedRectangle(', UI)
        self.assertIn("'sale':discounted", UI)
        self.assertIn('sales=set(slay.shop_sale_items(manager.ctx,preserve=True))', UI)

    def test_spear_unlock_does_not_render_empty_icon_widgets(self):
        self.assertIn("if str(item).endswith('spear_unlock')", UI)
        self.assertIn('if icon.texture is not None:', UI)
        self.assertIn('if portrait is not None:', UI)
        self.assertIn('self.inspect_icon.height=dp(112) if has_icon else 0', UI)
        self.assertIn('self.inspect_icon.opacity=1 if has_icon else 0', UI)

    def test_python_parser_and_no_duplicate_map_legend(self):
        ast.parse(UI)
        self.assertEqual(UI.count('manager.slay_fixed_legend=legend'), 1)
        self.assertIn("legend=getattr(manager,'slay_fixed_legend',None)",UI)

if __name__ == '__main__':
    unittest.main()
