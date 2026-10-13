"""Dev4: roll severity before scaling; zero multiplier is absolute; difficulty -2/tier."""
from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('severity_frequency_dev4', ROOT/'Payload'/'generate_slay_run.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


class FixedGaussRng(random.Random):
    def __init__(self, value):
        super().__init__(123)
        self.value = value
        self.means = []
    def gauss(self, mean, stdev):
        self.means.append((mean, stdev))
        return self.value


class SeverityFrequencyDev4(unittest.TestCase):
    def test_scaled_roll_not_scaled_gaussian_mean(self):
        # With a roll of 6 each, at 0.5 the target is 3, not a rerolled
        # Gaussian with the same variance. FixedGaussRng makes it deterministic.
        for factor in (0, 0.25, 0.5, 1, 1.5, 2):
            rng = FixedGaussRng(6)
            targets = []
            old_picker = gen._pick_effects_for_budget
            try:
                def record(catalog, target, rng, **kwargs):
                    targets.append(target)
                    return []
                gen._pick_effects_for_budget = record
                gen.roll_effects(5, 11, 'brutal', rng, mutation_frequency=factor,
                                 blessing_frequency=factor)
            finally:
                gen._pick_effects_for_budget = old_picker
            self.assertEqual(targets, [min(20,round(6*factor)), min(12,round(6*factor))])

    def test_early_tier_blessing_bonus_is_scaled_too(self):
        rng = FixedGaussRng(6)
        targets = []
        old = gen._pick_effects_for_budget
        try:
            def record(catalog, target, rng, **kwargs):
                targets.append(target)
                return []
            gen._pick_effects_for_budget = record
            gen.roll_effects(0, 11, 'brutal', rng, mission_pool=4,
                             mutation_frequency=0, blessing_frequency=0)
        finally:
            gen._pick_effects_for_budget = old
        self.assertEqual(targets, [0, 0])

    def test_zero_frequency_never_creates_effects_in_any_layer(self):
        for layer in range(12):
            for difficulty in gen.GAME_DIFFICULTY:
                for seed in range(18):
                    result = gen.roll_effects(layer, 11, difficulty, random.Random(seed),
                        final=(layer == 11), mission_pool=(4 if layer == 11 else min(4,layer//3)),
                        mutation_frequency=0, blessing_frequency=0)
                    self.assertEqual(result, ([], [], 0, 0), (layer,difficulty,seed))

    def test_each_difficulty_tier_reduces_mean_by_exactly_two(self):
        for layer in (0, 4, 8, 11):
            for diff, offset in [('brutal',0), ('hard',-2), ('medium',-4), ('easy',-6)]:
                rng = FixedGaussRng(0)
                gen.roll_effects(layer, 11, diff, rng, final=layer==11, mission_pool=2,
                                 mutation_frequency=0, blessing_frequency=0)
                base = gen._base_effect_means(layer,11,layer==11)[0]
                tier = (gen.target_pool(layer,11,diff,layer==11) - 2) * gen.MISSION_TIER_MUTATION_SEVERITY_PER_TIER
                self.assertAlmostEqual(rng.means[0][0], max(0,base + tier + offset))
                score = gen.expected_danger_score(layer, 11, diff, 1, 0, layer == 11)
                self.assertIsInstance(score,int)

    def test_zero_multipliers_respected_by_full_run_generation(self):
        from test_generator_race_subsets import candidate_pool
        candidates = candidate_pool(('Terran','Zerg','Protoss'))
        for mf,bf in [(0,0),(0,1),(1,0),(0.5,0.0)]:
            rng = random.Random(20261011)
            edges = gen.generate_edges(11,rng)
            assigned = gen.assign_missions(11,'medium',candidates,edges,rng,
                          mutation_frequency=mf, blessing_frequency=bf)
            self.assertTrue(assigned)
            if not mf:
                self.assertTrue(all(not x['mutators'] for x in assigned.values()), (mf,bf))
            if not bf:
                self.assertTrue(all(not x['blessings'] for x in assigned.values()), (mf,bf))

    def test_difficulty_description_is_exact(self):
        launcher = (ROOT/'Payload'/'slay_launcher.py').read_text()
        self.assertIn('described above, then it is recommended to try on a reduced gameplay difficulty before tweaking other settings.',launcher)
        self.assertNotIn('recommended to reduce the Mutation Frequency Multiplier',launcher)


if __name__ == '__main__':
    unittest.main()
