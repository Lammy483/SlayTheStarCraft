"""Dev8 regressions: Stretchy Spines image, expansion purchase cap, and reward curve."""
from __future__ import annotations

import ast
import json
import math
import random
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'Payload'
GEN = (PAYLOAD / 'generate_slay_run.py').read_text(encoding='utf-8')
RUNTIME = (PAYLOAD / 'slay_the_starcraft.py').read_text(encoding='utf-8')


def isolate(source, name, env=None):
    fn = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = dict(math=math, random=random, Any=Any, Mapping=Mapping)
    scope.update(env or {})
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '<dev8-test>', 'exec'), scope)
    return scope[name]


class Dev8Regressions(unittest.TestCase):
    def test_spine_crawler_uses_existing_shop_icon_for_all_aliases(self):
        keys = (
            'boon_stretchy_spines', 'Stretchy Spines', 'BOON::stretchy_spines',
            'BOON::permanent_blessing::boon_stretchy_spines',
            'Permanent Blessing: Stretchy Spines', '伸长棘刺',
        )
        icon = 'btn-building-zerg-spinecrawler.png'
        self.assertTrue((PAYLOAD/'slay_assets/icons'/icon).is_file())
        for name in ('slay_ui_icons.json','slay_assets/item_btn_icons.json'):
            mapping = json.loads((PAYLOAD/name).read_text(encoding='utf-8'))
            for key in keys:
                self.assertEqual(mapping[key], icon, (name,key))
            self.assertEqual(mapping['Spine Crawler'], icon)
            self.assertEqual(mapping['Spine Rifling'], 'btn-unit-zerg-hydralisk.png')

    def test_shop_expansion_max_three_in_generation_purchase_and_restore(self):
        self.assertIn('SHOP_EXPANSION_MAX = 3', RUNTIME)
        eligible = RUNTIME.split('def _boon_candidates(',1)[1].split('def _roll_shop_stock(',1)[0]
        self.assertIn('int(state(ctx).get("shop_expansion", 0)) < SHOP_EXPANSION_MAX', eligible)
        direct = RUNTIME.split('def _purchase_boon(',1)[1].split('def grant_test_boon(',1)[0]
        self.assertIn('if int(s.get("shop_expansion", 0)) >= SHOP_EXPANSION_MAX:', direct)
        self.assertIn('return False, "Shop Expansion can only be purchased three times per run."',direct)
        self.assertIn('min(SHOP_EXPANSION_MAX, int(s.get("shop_expansion", 0)) + 1)',direct)
        sanitize = RUNTIME.split('def _sanitize_state(',1)[1].split('def ',1)[0]
        self.assertIn('state["shop_expansion"] = min(SHOP_EXPANSION_MAX, state["shop_expansion"])',sanitize)
        self.assertIn('state[mapping_key][expansion_id] = min(SHOP_EXPANSION_MAX',sanitize)
        self.assertIn('SHOP_STOCK_LOGIC_VERSION = 114',RUNTIME)
        # Test the actual can-buy path with a minimal state: stale stock at
        # 3+ is not sufficient to allow a fourth purchase, even after reroll.
        env = dict(
            POTION_CATALOG={},TERRAN_CONTRACTS='T',ZERG_CONTRACTS='Z',KERRIGAN_UNLOCK='K',SPEAR_UNLOCK='S',
            MERCENARY_CUSTOM_UPGRADE_ITEMS=set(),SPEAR_ENERGY_REGEN='s1',SPEAR_COOLDOWN_REDUCTION='s2',
            SPEAR_PRICE_DISCOUNT='s3',KERRIGAN_RECKLESS_POWER='k1',KERRIGAN_RECKLESS_SPEED='k2',
            KERRIGAN_PRICE_DISCOUNT='k3',SHOP_EXPANSION_MAX=3,
            enabled=lambda ctx: True,state_ready=lambda ctx: True,
            _is_progression_item=lambda n: False,_item_table=lambda: {},
            _parse_boon=lambda n: ('shop_expansion','') if n == 'BOON::shop_expansion' else ('',''),
            state=lambda ctx: ctx,
        )
        can_buy = isolate(RUNTIME,'can_buy_shop_item',env)
        self.assertTrue(can_buy({'shop_expansion':0},'BOON::shop_expansion'))
        self.assertTrue(can_buy({'shop_expansion':2},'BOON::shop_expansion'))
        self.assertFalse(can_buy({'shop_expansion':3},'BOON::shop_expansion'))
        self.assertFalse(can_buy({'shop_expansion':4},'BOON::shop_expansion'))

    def test_flat_victory_bonus_removed_without_changing_other_terms(self):
        reward = isolate(GEN,'credit_reward')
        fallback = isolate(RUNTIME,'_legacy_node_credit')
        for layer in range(12):
            pool = ((layer+3)//3)-1  # match expected mission tier
            extra = 50 if layer == 0 else 25 if layer == 1 else 0
            args=(pool,layer,0,0,False,random.Random(5))
            self.assertEqual(reward(*args),400+extra)
            self.assertEqual(reward(pool,layer,4,2,True,random.Random(5)),700+extra)
            self.assertEqual(fallback(dict(layer=layer,mission_pool=pool,mutation_value=4,blessing_value=2)),700+extra)
        self.assertEqual(reward(0,0,0,40,True,random.Random(5)),200) # floor 150 + opening 50
        self.assertEqual(reward(0,0,0,40,True,random.Random(5),mission_name='Lab Rat'),100)
        self.assertEqual(reward(0,0,2,0,False,random.Random(5),victory_credit_reward_multiplier=1.5),1050)
        self.assertIn('layer_reward = 0',GEN)
        self.assertIn('base + 125.0 * mf',GEN)
        self.assertIn('base - 50.0 + 125.0 * mf',RUNTIME)
        self.assertIn('credit_reward=round((base_reward + (100 if risk else 0)) * multiplier)',GEN) # risk stays

    def test_runtime_revision_matches_portable_launcher(self):
        revision = 'v1.2.0-release'
        manifest = json.loads((ROOT/'launcher_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['runtime_revision'],revision)
        self.assertIn('runtimeRevision = "'+revision+'"',(ROOT/'Tools/slay_launcher_windows.go').read_text(encoding='utf-8'))
        self.assertIn('$RuntimeRevision = "'+revision+'"',(ROOT/'Tools/bootstrap_slay_runtime.ps1').read_text(encoding='utf-8'))
        # The compiled Windows EXE belongs in the public ZIP, not Git history.
        self.assertTrue((ROOT/'Tools/slay_launcher_windows.go').is_file())


if __name__=='__main__':unittest.main()
