"""Dev31: Evacuation effect exclusion and early reliable Mira camp placement."""
import importlib.util
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'Payload' / 'generate_slay_run.py'
RT = ROOT / 'Payload' / 'slay_the_starcraft.py'
GAL = ROOT / 'Payload' / 'APRogue.galaxy'


def galaxy_function(name):
    s = GAL.read_text(encoding='utf-8')
    start = s.index(name + '(')
    start = s.rfind('\n', 0, start)
    open_brace = s.index('{', start)
    level = 1
    i = open_brace + 1
    while level:
        if s[i] == '{': level += 1
        if s[i] == '}': level -= 1
        i += 1
    return s[start:i]


class EvacuationMiraDev31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('slay31_gen', GEN)
        cls.gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gen)

    def test_evacuation_banned_for_every_race_variant(self):
        for name in ('Evacuation', 'The Evacuation', 'Evacuation (Zerg)', 'Evacuation (Terran)', 'Evacuation (Protoss)'):
            with self.subTest(name=name):
                forbidden, _ = self.gen._effect_exclusions_for_mission({'name':name,'short_name':name,'race':'terran'})
                self.assertIn('nuclear_annihilation', forbidden)
                for seed in range(12):
                    effects = self.gen.roll_effects(6,12,'brutal',random.Random(seed),
                        forbidden_mutators=forbidden,mutation_frequency=2.5)
                    self.assertNotIn('nuclear_annihilation',effects[0])

    def test_exclusion_only_evacuation_and_rerolls(self):
        for name in ('Rendezvous','The Outlaws','The Dig'):
            forbidden,_=self.gen._effect_exclusions_for_mission({'name':name,'short_name':name,'race':'terran'})
            self.assertNotIn('nuclear_annihilation',forbidden)
        runtime = RT.read_text(encoding='utf-8')
        self.assertIn('if mission_name.strip().casefold() in {"evacuation", "the evacuation"}', runtime)
        self.assertIn('forbidden_mut.add("nuclear_annihilation")',runtime)

    def test_mira_search_does_not_wait_for_enemy_casualties(self):
        src=galaxy_function('APRG_FindMiraCampPoint')
        self.assertNotIn('APRG_EnemyAllUnits', src)
        self.assertNotIn('nearestEnemy', src)
        self.assertNotIn('UnitGroupClosestToPoint', src)
        self.assertIn('APRG_MAX_POINT_ATTEMPTS * 2',src)
        self.assertIn('clearance = 40.0',src)
        self.assertIn('clearance = 26.0',src)
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(candidate, player, clearance)',src)
        self.assertIn('APRG_GroundSpawnsNeedPlayerPathing()',src)
        self.assertRegex(src,r'return null;\s*}$')

    def test_no_false_spawn_success_when_all_types_unavailable(self):
        src=galaxy_function('APRG_SpawnMiraMercenaries')
        self.assertIn('if (campPoint == null) { return; }',src)
        self.assertIn('if (owner < 0) { return; }',src)
        self.assertIn('UnitGroupCount(g_aprgMiraMercenaries, c_unitCountAlive) <= 0',src)
        self.assertLess(src.index('UnitGroupCount(g_aprgMiraMercenaries'),src.index('g_aprgMiraMercenariesSpawned = true;'))

if __name__=='__main__': unittest.main()
