"""r38: each mutation severity point adds 125 victory credits, not 150."""
from __future__ import annotations

import ast
import math
import random
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = (ROOT / 'Payload/generate_slay_run.py').read_text(encoding='utf-8')
CLIENT = (ROOT / 'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
INSTALLER = (ROOT / 'Payload/install_slay.py').read_text(encoding='utf-8')


def isolated_function(source: str, name: str):
    fn = next((n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if fn is None:
        raise AssertionError(f'Missing reward function {name}')
    env = {'math': math, 'random': random, 'Mapping': Mapping, 'Any': Any}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '<reward-test>', 'exec'), env)
    return env[name]


class MutationCreditRewardR38(unittest.TestCase):
    def test_generator_pays_125_each_with_other_terms_unchanged(self):
        reward = isolated_function(GENERATOR, 'credit_reward')
        def got(mutations=0, blessings=0, pool=0, layer=0, multiplier=1.0, mission=''):
            return reward(pool, layer, mutations, blessings, bool(blessings), random.Random(123),
                          mission_name=mission, victory_credit_reward_multiplier=multiplier)
        self.assertEqual(got(), 500)
        for severity in (1, 2, 4, 8):
            self.assertEqual(got(mutations=severity) - got(), 125 * severity)
        self.assertEqual(got(mutations=3, blessings=2), 500 + 3*125 - 2*100)
        self.assertEqual(got(mutations=2, pool=2), 500 + 2*125 + 600)
        self.assertEqual(got(mutations=4, multiplier=1.5), 1500)
        self.assertEqual(got(mutations=4, mission='Lab Rat'), 900)

    def test_runtime_legacy_fallback_matches_generator(self):
        fallback = isolated_function(CLIENT, '_legacy_node_credit')
        generate = isolated_function(GENERATOR, 'credit_reward')
        for pool in (0, 2, 4):
            for layer in (0, 3, 8):
                for severity in (0, 1, 4, 7):
                    data = dict(layer=layer, mission_pool=pool, mutation_value=severity,
                                blessing_value=2, mission_name='Smash and Grab')
                    self.assertEqual(fallback(data),
                                     generate(pool, layer, severity, 2, True, random.Random(2),
                                              mission_name='Smash and Grab'))

    def test_credit_expectations_and_installer_marker_updated(self):
        self.assertIn('base + 50.0 + 125.0 * mf', GENERATOR)
        self.assertIn('base + 125.0 * mf', CLIENT)
        self.assertIn('125.0 * mutation_mean', GENERATOR)
        self.assertIn('effect_reward = (125 * int(mutation_value))', GENERATOR)
        self.assertIn('effect_reward = (125 * int(mutation_value))', INSTALLER)
        self.assertNotIn('effect_reward = (150 * int(mutation_value))', GENERATOR)
        # Danger weighting isn't a credit award; don't unintentionally reweight it.
        self.assertIn('trial[2] * 150 - trial[3] * 100', GENERATOR)


if __name__ == '__main__':
    unittest.main()
