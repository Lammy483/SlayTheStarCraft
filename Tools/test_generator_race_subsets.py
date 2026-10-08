"""Offline race-selection/mission-pool regression; run with Python, no AP or SC2 needed.

Pool counts match build missions per playable race in the pinned AP c311685
mission catalog. This test exercises the full Slay assignment and effect rolls,
not just the launcher command-line arguments.
"""
import importlib.util
import itertools
from pathlib import Path
import random
import unittest

payload=Path(__file__).resolve().parents[1]/'Payload'
spec=importlib.util.spec_from_file_location('generate_slay_run',payload/'generate_slay_run.py')
generator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

POOL_COUNTS={
    'Terran':(5,8,24,21,6),
    'Zerg':(3,10,18,21,5),
    'Protoss':(4,13,22,13,5),
}


def candidate_pool(races):
    candidates=[]
    for race in races:
        for pool,count in enumerate(POOL_COUNTS[race]):
            for slot in range(count):
                ident=len(candidates)+10000
                candidates.append(dict(
                    id=ident,name=f'{race} test {ident}',short_name=f'{race} test {ident}',
                    race=race,pool=pool,campaign='Wings of Liberty',
                    race_swap=False,kerrigan=False,lotv=False,timed_defense=False,
                ))
    return candidates


class RaceSubsetGenerationTests(unittest.TestCase):
    def test_all_race_selections_reserve_a_playable_final_mission(self):
        for count in (1,2,3):
            for selected in itertools.combinations(POOL_COUNTS,count):
                candidates=candidate_pool(selected)
                for seed in range(30):
                    with self.subTest(races=selected,seed=seed):
                        rng=random.Random(seed)
                        edges=generator.generate_edges(11,rng)
                        generator.validate_graph(11,edges)
                        nodes=generator.assign_missions(11,'brutal',candidates,edges,rng)
                        self.assertEqual(len(nodes),len(edges))
                        self.assertEqual(len({n['id'] for n in nodes.values()}),len(nodes))
                        self.assertEqual(nodes[(11,generator.FINAL_LANE)]['pool'],4)
                        self.assertTrue(all(n['race'] in selected for n in nodes.values()))
                        self.assertTrue(any(
                            n['layer']==0 and n['credit_reward']<=350 for n in nodes.values()
                        ))


if __name__=='__main__':
    unittest.main()
