"""Potion native type safety and repeat avoidance, independent of SC2 installation."""
import importlib.util
import random
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_gen_r16", ROOT / "Payload" / "generate_slay_run.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

class R16RegressionTests(unittest.TestCase):
    def test_galaxy_unitref_event_registration(self):
        galaxy=(ROOT/"Payload"/"APRogue.galaxy").read_text(encoding="utf-8")
        self.assertIn('TriggerAddEventUnitOrder(g_aprgPotionOrderTrigger, null, AbilityCommand("move", 0))', galaxy)
        self.assertNotIn('TriggerAddEventUnitOrder(g_aprgPotionOrderTrigger, g_aprgPotionTargetCaster,', galaxy)
        self.assertIn('EventUnit() != g_aprgPotionTargetCaster', galaxy)

    def test_same_severity_and_legality(self):
        def node(layer, mutation, blessing):
            return dict(layer=layer, race="Terran", name="Zero Hour (Terran)",short_name="Zero Hour",
                        mutators=[mutation], blessings=[blessing],
                        mutation_value=gen.MUTATORS[mutation],
                        blessing_value=gen._blessing_severity_for_layer(blessing,layer),
                        credit_reward=450)
        start = {(0,0):node(0,'conga_line','general'),
                 (0,1):node(0,'conga_line','general'),
                 (1,0):node(1,'conga_line','general'),
                 (2,0):node(2,'conga_line','general'),
                 (3,0):node(3,'conga_line','general')}
        run={k:dict(v, mutators=v['mutators'][:],blessings=v['blessings'][:]) for k,v in start.items()}
        gen._reduce_repeats_across_run(run, random.Random(2026))
        self.assertEqual(run[(0,0)]['mutators'],['conga_line'])
        self.assertEqual(run[(0,0)]['blessings'],['general'])
        for pos, data in run.items():
            self.assertEqual(len(data['mutators']),1)
            self.assertEqual(len(data['blessings']),1)
            self.assertEqual(gen.MUTATORS[data['mutators'][0]],start[pos]['mutation_value'])
            self.assertEqual(gen._blessing_severity_for_layer(data['blessings'][0],pos[0]),start[pos]['blessing_value'])
            self.assertEqual(data['credit_reward'],450)
            self.assertEqual(data['mutation_value'],start[pos]['mutation_value'])
            self.assertEqual(data['blessing_value'],start[pos]['blessing_value'])
        self.assertNotEqual([data['mutators'] for _,data in sorted(run.items())],
                            [data['mutators'] for _,data in sorted(start.items())])

    def test_50_percent_reroll_probability(self):
        # Independent two-node runs: the second copy is rerolled in ~50% of
        # draws, not forbidden. Ignore cases with no alternative (there are
        # many legal severity-3 mutations).
        sample=1000
        count=0
        for seed in range(sample):
            assigned={(0,0):dict(layer=0,race='Terran',name='Zero Hour (Terran)',short_name='Zero Hour',
                                mutators=['conga_line'],blessings=[]),
                      (1,0):dict(layer=1,race='Terran',name='Zero Hour (Terran)',short_name='Zero Hour',
                                mutators=['conga_line'],blessings=[])}
            gen._reduce_repeats_across_run(assigned,random.Random(seed))
            count+=assigned[(1,0)]['mutators'][0]!='conga_line'
        self.assertTrue(430 <= count <= 570,count)
        self.assertTrue(count < sample)

    def test_race_and_mission_exclusions(self):
        # A repeated blessing cannot reroll to a restricted race blessing,
        # or a dependency-sensitive blessing prohibited on the target map.
        assigned={
            (0,0):dict(layer=0,race='Terran',name='Zero Hour (Terran)',short_name='Zero Hour',mutators=[],blessings=['general']),
            (1,0):dict(layer=1,race='Protoss',name="Haven's Fall (Protoss)",short_name="Haven's Fall",mutators=[],blessings=['general'])
        }
        for seed in range(100):
            states={k:dict(v,blessings=list(v['blessings'])) for k,v in assigned.items()}
            gen._reduce_repeats_across_run(states,random.Random(seed))
            b=states[(1,0)]['blessings'][0]
            forbidden=gen._effect_exclusions_for_mission(states[(1,0)])[1]
            self.assertNotIn(b,forbidden)
            self.assertEqual(gen._blessing_severity_for_layer(b,1),gen._blessing_severity_for_layer('general',1))

if __name__ == '__main__': unittest.main()
