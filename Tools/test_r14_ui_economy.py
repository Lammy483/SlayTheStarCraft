"""r14 regression tests for requested shop, launcher, route and economy changes."""
import ast
import csv
import importlib.util
import json
from pathlib import Path
import random
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'Payload'

def load_generator():
    spec = importlib.util.spec_from_file_location('slay_r14_generator', P/'generate_slay_run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class R14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=load_generator()
        cls.launcher=(P/'slay_launcher.py').read_text(encoding='utf-8')
        cls.theme=(P/'slay_theme.py').read_text(encoding='utf-8')
        cls.chart=(P/'slay_command_ui.py').read_text(encoding='utf-8')
        cls.support=(P/'slay_ui_support.py').read_text(encoding='utf-8')
        cls.runtime=(P/'slay_the_starcraft.py').read_text(encoding='utf-8')

    def test_credit_defaults(self):
        self.assertIn('DEFAULT_STARTING_CREDITS = 600',self.launcher)
        self.assertIn('default=600, help="Starting shop credits (default 600)"',(P/'generate_slay_run.py').read_text())
        self.assertIn('height=dp(90) if "\\n" in label_text else dp(70)',self.launcher)

    def test_reward_floor_and_special_lab_rat(self):
        g=self.g
        self.assertEqual(g.credit_reward(0,0,0,40,True,random.Random(0)),150)
        self.assertEqual(g.credit_reward(0,0,0,40,True,random.Random(0),'Lab Rat'),50)
        self.assertIn('reward = max(150, old_reward - (100 * layer_number))',self.runtime)

    def test_mutation_mean_plus_one_for_every_campaign_length(self):
        g=self.g
        self.assertAlmostEqual(g._base_effect_means(0,11)[0],2.95)
        self.assertAlmostEqual(g._base_effect_means(0,2)[0],4.0)
        self.assertAlmostEqual(g._base_effect_means(10,11)[0],12.15)
        self.assertAlmostEqual(g._base_effect_means(11,11,True)[0],15.87)
        self.assertIn('_curve_value(_EXPECTED_MUTATION_SEVERITY_PROFILE, frac) + 1.0',self.runtime)

    def test_captions_and_form_notes(self):
        for term in ('(Removing races makes the game easier)',
                     '(Longer campaign lengths makes the game easier)'):
            self.assertIn(term,self.launcher)
        self.assertIn('text="[b]DIFFICULTY[/b]"',self.theme)
        self.assertNotIn('ADVENTURE CONFIGURATION',self.theme)
        self.assertNotIn('DIFFICULTY DESCRIPTION',self.theme)

    def test_shop_compact_top_and_bottom(self):
        self.assertIn('size_hint=(.998,.998)',self.chart)
        self.assertIn('height=dp(34)',self.chart)
        self.assertIn('width=dp(17)',self.chart)
        self.assertIn('border=(0,0,0,0)',self.chart)
        self.assertIn('separator_height=0, title_size=0',self.chart)

    def test_map_legend_vertical_and_arrows_buried(self):
        self.assertNotIn('Sector Route',self.chart)
        self.assertIn('◉ Available[/color]\\n',self.chart)
        self.assertIn('key_panel=BoxLayout(',self.chart)
        self.assertIn('strip.add_widget(key_panel)',self.chart)
        self.assertIn('NODE_PLANET_X',self.chart)
        self.assertIn('NODE_CARD_HEIGHT-12',self.chart)
        self.assertIn('ROUTE_FLOOR_SPACING=178',self.chart)
        self.assertNotIn('panel(strip,color=',self.chart)

    def test_quieter_both_ui_audio_backends(self):
        self.assertIn('sound.volume = 0.04',self.theme)
        self.assertIn('sound.volume=.04',self.support)
        self.assertNotIn('sound.volume = 0.08',self.theme)
        self.assertNotIn('sound.volume=.08',self.support)

    def test_correct_resources_and_non_worker_contract_icons(self):
        icons=json.loads((P/'slay_ui_icons.json').read_text(encoding='utf-8'))
        self.assertEqual(icons['Additional Starting Minerals'],'icon-mineral-nobg.png')
        self.assertEqual(icons['Additional Starting Vespene'],'icon-gas-terran-nobg.png')
        for name in ('Additional Starting Minerals','Additional Starting Vespene','PROGRESSION::terran_contracts','PROGRESSION::zerg_contracts'):
            self.assertTrue((P/'slay_assets/icons'/icons[name]).is_file(),name)
        # r15 replaces r14's temporary Factory/Hive building portraits with
        # the requested War Pigs and Hunter Killers unit artwork.
        self.assertEqual(icons['PROGRESSION::terran_contracts'], icons['War Pigs'])
        self.assertEqual(icons['PROGRESSION::zerg_contracts'], icons['Hunter Killers'])

    def test_spear_unlock_has_description_and_no_misleading_image(self):
        with (P/'SPEAR_OF_ADUN_SHOP_CATALOG.csv').open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        row=next(row for row in rows if row['Item Title']=='Unlock Spear of Adun')
        self.assertEqual(row['Description'],'The Spear of Adun is available on all missions but starts with no abilities.')
        self.assertIn("return PROGRESSION_DESCRIPTIONS.get(item_name, \"\")",self.runtime)
        self.assertIn('def shop_icon_texture(item, source=',self.chart)

if __name__=='__main__':unittest.main()
