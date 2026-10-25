"""Regression: Jetpacks mutation cannot be generated or added later on Smash and Grab."""
from __future__ import annotations
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]

def extract(path, name, glob):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    func=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==name)
    code=compile(ast.fix_missing_locations(ast.Module(body=[func],type_ignores=[])),str(path),'exec')
    ns=dict(glob)
    exec(code,ns)
    return ns[name]

G=ROOT/'Payload/generate_slay_run.py'
S=ROOT/'Payload/slay_the_starcraft.py'

def gen_exclusions():
    return extract(G,'_effect_exclusions_for_mission',dict(
        LIMITED_BANK_MISSION_EXCLUSIONS=set(), GORGON_MISSION_EXCLUSIONS={'fire in the sky'},
        crucible_mutation_exclusions=lambda _:set(),ISLAND_MISSION_NAMES=set(),
        DESTRUCTION_MISSION_EXCLUSIONS=set(),DESTRUCTION_TIMED_DEFENSE_ALLOWLIST=set(),
        dependency_sensitive_effect_exclusions=lambda _: (set(),set()),
        RICH_MINERALS_MISSION_EXCLUSIONS=set()))

def runtime_allowed():
    def fake_node(ctx,mission_id):return ctx.missions[int(mission_id)]
    return extract(S,'_mutation_allowed_for_mission',dict(
        DISABLED_MUTATIONS=set(), node=fake_node, _mission_base_name=lambda n:n.split(' (')[0],
        GORGON_MISSION_EXCLUSIONS=set(),CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS=set(),
        ISLAND_MISSION_NAMES=set(),DEPENDENCY_SENSITIVE_MISSIONS=set(),
        SWARM_DEPENDENCY_MUTATIONS=set(),VOID_DEPENDENCY_MUTATIONS=set()))

class SmashGrabRegression(unittest.TestCase):
    def test_generator_blocks_jetpacks_but_not_other_missions(self):
        excluded=gen_exclusions()
        for name in ('Smash and Grab','Smash and Grab (Terran)','Smash and Grab (Zerg)',
                     'SMASH AND GRAB (Protoss)'):
            with self.subTest(name=name):
                bad,good=excluded({'name':name,'short_name':name,'race':'terran'})
                self.assertIn('jetpacks',bad)
                self.assertIn('nexus_shield',bad)
        not_bad,_=excluded({'name':'The Great Train Robbery','race':'terran'})
        self.assertNotIn('jetpacks',not_bad)
    def test_runtime_blocks_jetpacks_for_smash_and_grab(self):
        allowed=runtime_allowed()
        ctx=SimpleNamespace(missions={1:{'mission_name':'Smash and Grab'},
                                     2:{'mission_name':'Smash and Grab (Zerg)'},
                                     3:{'mission_name':'The Great Train Robbery'}})
        for mid in (1,2):
            self.assertFalse(allowed(ctx,mid,'jetpacks'))
            self.assertFalse(allowed(ctx,mid,'nexus_shield'))
        self.assertTrue(allowed(ctx,3,'jetpacks'))

if __name__=='__main__':unittest.main()
