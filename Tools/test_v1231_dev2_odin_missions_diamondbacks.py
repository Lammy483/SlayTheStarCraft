"""Regression checks for Dev2 Odin placement, finite Diamondbacks and mission choices."""
from __future__ import annotations
from pathlib import Path
import unittest
import ast
import re
ROOT=Path(__file__).resolve().parents[1]
GALAXY=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
GEN=(ROOT/'Payload/generate_slay_run.py').read_text(encoding='utf-8')
GUI=(ROOT/'Payload/slay_launcher.py').read_text(encoding='utf-8')
def body(name):
    m=re.search(r'(?m)^(?:point|void|bool) '+re.escape(name)+r'\([^\n]*\) \{',GALAXY)
    if not m:raise AssertionError(name)
    return GALAXY[m.start():GALAXY.index('\n}\n',m.end())]
class Dev2Features(unittest.TestCase):
    def test_odin_tiered_retries_keep_ally_clearance(self):
        f=body('APRG_FindDelayedOdinStrongholdPoint')
        for phrase in ('g_aprgDelayedOdinPlacementAttempts / 6','tier >= 1','tier >= 3',
                       'tier < 2 && APRG_GroundSpawnsNeedPlayerPathing()',
                       'APRG_DelayedOdinNearFriendlyBuilding(candidate, player, 24.0)',
                       'DistanceBetweenPoints(UnitGetPosition(home), candidate) < 32.0'):
            self.assertIn(phrase,f)
        helper=body('APRG_DelayedOdinNearFriendlyBuilding')
        self.assertIn('c_unitAllianceAlly',helper)
        self.assertIn('c_targetFilterStructure',helper)
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding',helper)
    def test_diamondbacks_finite(self):
        s=body('APRG_SpawnDiamondbackWanderers')
        self.assertIn('UnitCreate(50, "Diamondback"',s)
        self.assertIn('if (g_aprgDiamondbackWanderersSpawned ||',s)
        self.assertIn('g_aprgDiamondbackWanderersSpawned = true',s)
        self.assertEqual(GALAXY.count('UnitCreate(50, "Diamondback"'),1)
        self.assertNotIn('UnitCreate(',body('APRG_TickDiamondbackWanderers'))
    def test_possible_missions_both_layers(self):
        self.assertIn('def possible_mission_names(',GEN)
        self.assertIn('MissionFlag.NoBuild not in m.flags',GEN)
        self.assertIn('def filter_possible_missions(',GEN)
        self.assertIn('candidates = filter_possible_missions(candidates, excluded_missions)',GEN)
        self.assertIn("default='[\"Lab Rat\"]'",GEN)
        self.assertIn('Popup(title="Possible Missions"',GUI)
        self.assertIn('checkbox.active = name.casefold() != "lab rat"',GUI)
        self.assertIn('excluded_missions=tuple(name for name, checkbox in mission_checks.items() if not checkbox.active)',GUI)
        tree=ast.parse(GEN)
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='filter_possible_missions')
        ns={}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'<filter>','exec'),ns)
        sample=[{'short_name':'Lab Rat','race':'Terran'},{'short_name':'Lab Rat','race':'Zerg'},
                {'short_name':'Outbreak','race':'Zerg'}]
        self.assertEqual(ns['filter_possible_missions'](sample,['lAb RaT']),[sample[2]])
if __name__=='__main__':unittest.main()
