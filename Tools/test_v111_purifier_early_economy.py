"""v1.1.1 regression coverage for the exact requested release changes."""
from __future__ import annotations
import importlib.util
import csv
import json
import random
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=ROOT/'Payload'
G=(PAYLOAD/'APRogue.galaxy').read_text(encoding='utf-8')
S=(PAYLOAD/'slay_the_starcraft.py').read_text(encoding='utf-8')
L=(PAYLOAD/'slay_launcher.py').read_text(encoding='utf-8')
R=(PAYLOAD/'generate_slay_run.py').read_text(encoding='utf-8')

class V111Tests(unittest.TestCase):
    def test_purifier_is_player_spawn_default_and_occasional_uses_it(self):
        resolver=G.split('string APRG_PlayerSpawnCatalogTypeForPlayer(',1)[1].split('string APRG_PlayerSpawnCatalogType(',1)[0]
        for word in ('unitType == "Colossus"','"AP_ColossusPurifier"','"ColossusPurifier"', 'return unitType;'):
            self.assertIn(word,resolver)
        occ=G.split('bool APRG_OccasionalBlessing_Func(',1)[1].split('bool APRG_IsOccasionalReplacementSource(',1)[0]
        self.assertIn('replacementType = "Colossus";',occ)
        self.assertIn('replacementType = APRG_PlayerSpawnCatalogTypeForPlayer(replacementType, player);',occ)
        self.assertIn('libNtve_gf_ReplaceUnit(trained, replacementType',occ)
        self.assertIn('APRG_PlayerSpawnCandidateHealthy(player, "AP_ColossusPurifier", false)',resolver)

    def test_canonical_boon_price_and_verbatim_description(self):
        with (PAYLOAD/'BOON_CATALOG.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
        row=next(r for r in rows if r['Boon Title']=='Invasion Fleet')
        self.assertEqual(row['Description'],'At the 5 minute mark of each mission, many zerg drop pods attack the enemy for 2 minutes')
        self.assertEqual(int(row['Cost']),1500)
        self.assertIn('"invasion_fleet":1500',S)
        self.assertNotIn('"invasion_fleet":1700',S)

    def test_defaults_and_legacy_nodes(self):
        self.assertIn('DEFAULT_STARTING_CREDITS = 700',L)
        self.assertIn('starting_credits: int = 700,',R)
        self.assertIn('DEFAULT_ITEM_CREDIT_REWARD = 60',L)
        self.assertIn('item_credit_reward: int = 60,',R)
        self.assertIn('if not opening_easy_guarantee or base_reward <= 400:',R)
        self.assertIn('get("item_credit_reward", 60)',S)
        self.assertIn('default=60, help="Credits granted by each credit-item replacement (default 60)"',R)
        spec=importlib.util.spec_from_file_location('release_v111_gen',PAYLOAD/'generate_slay_run.py')
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for layer, bonus in ((0,50),(1,25),(2,0),(9,0)):
            tier=(layer+3)//3-1
            v=mod.credit_reward(tier,layer,2,1,True,random.Random(1))
            self.assertEqual(v,400+250-100+bonus)
        spec=importlib.util.spec_from_file_location('release_v111_core',PAYLOAD/'slay_the_starcraft.py')
        # Use a source-level assertion for the fallback because Archipelago is not
        # available to import as a module in the offline tests.
        self.assertIn('if layer == 0:\n        reward += 50',S)
        self.assertIn('elif layer == 1:\n        reward += 25',S)

    def test_release_identifiers(self):
        self.assertEqual((ROOT/'VERSION.txt').read_text().strip(),'1.1.2')
        manifest=json.loads((ROOT/'launcher_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['slay_version'],'1.1.2')
        rev=manifest['runtime_revision']
        self.assertEqual(rev,'spider-mine-structure-exclusions-v112-dev27')
        self.assertIn(rev,(ROOT/'Tools/bootstrap_slay_runtime.ps1').read_text())
        self.assertIn(rev,(ROOT/'Tools/slay_launcher_windows.go').read_text())

if __name__=='__main__': unittest.main()
