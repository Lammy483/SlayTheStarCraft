"""r30: mission-completion consumable rewards and Tosh patrol/nuke guarantees."""
import ast
import csv
import hashlib
import random
import re
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
CLIENT = (ROOT / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GENERATOR = (ROOT / 'generate_slay_run.py').read_text(encoding='utf-8')
GALAXY = (ROOT / 'APRogue.galaxy').read_text(encoding='utf-8')


def function_source(text, name):
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(text, node)


class R30Tests(unittest.TestCase):
    def test_catalog_pricing_severity_and_shop(self):
        with (ROOT / 'BOON_CATALOG.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = {row['Boon Title']: row for row in csv.DictReader(stream)}
        self.assertEqual(rows['Single-Use Tools']['Cost'], '400')
        self.assertIn('random consumable', rows['Single-Use Tools']['Description'])
        with (ROOT / 'EFFECT_CATALOG.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = {row['Title']: row for row in csv.DictReader(stream)}
        self.assertEqual(rows['Tosh and his Boys']['Mutation or Blessing'], 'Mutation')
        self.assertEqual(rows['Tosh and his Boys']['Severity'], '3')
        self.assertIn('"single_use_tools","boon_single_use_tools",True', CLIENT)
        self.assertIn('"single_use_tools":400', CLIENT)
        self.assertIn("'tosh_and_his_boys': 3", GENERATOR)
        self.assertIn('"tosh_and_his_boys": MISSION_FLAG_TOSH_AND_HIS_BOYS', CLIENT)

    def test_single_use_boon_no_backfill_after_purchase(self):
        self.assertIn('s["single_use_tools_last_victory"] = victory_count(ctx)', CLIENT)
        self.assertIn('"single_use_tools_last_victory"', CLIENT)
        self.assertIn('if len(slots) >= POTION_CAPACITY:', function_source(CLIENT, '_single_use_tools_grant'))

    def test_awards_once_per_mission_with_shop_eligibility(self):
        scope = {'Any': Any, 'hashlib': hashlib, 'random': random, 'POTION_CAPACITY': 2,
                 'POTION_PREFIX': 'p::', 'POTION_VARIANT_PREFIX': 'p::19::',
                 'POTION_RANDOM_UNITS': tuple(range(18)),
                 'POTION_CATALOG': {'p::1': {'index': 1}, 'p::12': {'index': 12}, 'p::19': {'index': 19},
                                    'p::19::1': {'index': 1901}},
                 '_potion_unlock_eligible': lambda ctx, name: name != 'p::12',
                 'victory_count': lambda ctx: ctx.wins, 'state': lambda ctx: ctx.state,
                 '_persist_state': lambda ctx: None}
        exec(compile(ast.parse(function_source(CLIENT, '_single_use_tools_grant')), '<single-use>', 'exec'), scope)
        fn = scope['_single_use_tools_grant']
        from types import SimpleNamespace
        ctx = SimpleNamespace(slay_config={'run_seed': 342}, wins=2, state={
               'permanent_boons': ['boon_single_use_tools'], 'single_use_tools_last_victory': 2,
                         'potion_inventory': [], 'potion_serial': 0})
        self.assertEqual(fn(ctx, []), [])
        ctx.wins = 3
        first = fn(ctx, [])
        self.assertEqual(len(first), 1)
        self.assertNotEqual(first[0]['id'], 'p::12')
        self.assertEqual(fn(ctx, first), first)
        ctx.wins = 4
        second = fn(ctx, first)
        self.assertEqual(len(second), 2)
        ctx.wins = 5
        self.assertEqual(fn(ctx, second), second)
        self.assertEqual(ctx.state['single_use_tools_last_victory'], 5)
        # Even if the player consumes one after an already-full completion, it
        # cannot retroactively collect the skipped reward.
        self.assertEqual(len(fn(ctx, second[:1])), 1)
        ctx.wins = 6
        self.assertEqual(len(fn(ctx, second[:1])), 2)

    def test_tosh_timings_pathing_and_one_life(self):
        self.assertIn('const int APRG_MISSION_FLAG_TOSH_AND_HIS_BOYS = 32768;', GALAXY)
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))', GALAXY)
        self.assertGreaterEqual(GALAXY.count('APRG_ToshPathableHostileSpawnPoint(anchor, player)'), 2)
        body = GALAXY[GALAXY.index('void APRG_TickToshAndHisBoys('):GALAXY.index('bool APRG_IsOdinDefensiveStructure(')]
        for expected in ('APRG_RandomPathableHostileBaseAnchor(player)',
                         'g_aprgMacroReadyTime + 180.0', 'g_aprgMacroReadyTime + 240.0',
                         'now + 60.0', 'g_aprgToshSpawned = true',
                         'if (g_aprgTosh != null && UnitIsAlive(g_aprgTosh))',
                         'APRG_TryGeneratedHeroAbility(g_aprgTosh, player)',
                         'APRG_RegisterMutationEnemyGroup(created)',
                         'UnitBehaviorAdd(spec, "APRogueCloakedNightmare", spec, 1)',
                         'RandomFixed(0.0, 5.0)', 'APRG_TryUnitAbilityKeyword(spec, "Nuke"',
                         'g_aprgToshSpectreNextOrderTime[i] = now + 4.0',
                         'if (!UnitIsAlive(spec))', 'now + 12.0'):
            self.assertIn(expected, body)
        self.assertIn('"tosh_and_his_boys"', function_source(CLIENT, '_mutation_allowed_for_mission'))
        self.assertIn('"tosh_and_his_boys"', function_source(GENERATOR, '_effect_exclusions_for_mission'))


if __name__ == '__main__':
    unittest.main()
