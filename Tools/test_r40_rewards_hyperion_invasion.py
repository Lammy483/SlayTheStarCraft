"""r40/Dev8 regressions: reward formula, native Raynor movement, Invasion Fleet duration."""
from __future__ import annotations
import ast
import csv
import math
import random
import unittest
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
GEN = (ROOT/'Payload/generate_slay_run.py').read_text(encoding='utf-8')
CLIENT = (ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
GALAXY = (ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')


def isolated_function(source, name):
    fn = next((n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name==name),None)
    assert fn is not None,name
    env={'math':math,'random':random,'Any':Any,'Mapping':Mapping}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<reward-test>','exec'),env)
    return env[name]


class CreditRewardR40(unittest.TestCase):
    def test_removed_flat_bonus_and_mutation_rate(self):
        reward=isolated_function(GEN,'credit_reward')
        fallback=isolated_function(CLIENT,'_legacy_node_credit')
        # Use matching tier/expected tier at each layer so only the mutation
        # and blessing severity should alter credit values.
        for layer in range(12):
            tier=(layer+3)//3-1
            self.assertEqual(reward(tier,layer,0,0,False,random.Random(1)),400 + (50 if layer == 0 else 25 if layer == 1 else 0))
            self.assertEqual(reward(tier,layer,4,2,True,random.Random(1)),700 + (50 if layer == 0 else 25 if layer == 1 else 0))
            self.assertEqual(fallback(dict(layer=layer,mission_pool=tier,mutation_value=4,blessing_value=2)),700 + (50 if layer == 0 else 25 if layer == 1 else 0))
            self.assertEqual(reward(tier,layer,0,0,False,random.Random(1),mission_name='Lab Rat'),300 + (50 if layer == 0 else 25 if layer == 1 else 0))
        self.assertEqual(reward(0,0,0,40,True,random.Random(1)),200)
        self.assertEqual(reward(0,0,0,40,True,random.Random(1),mission_name='Lab Rat'),100)
        self.assertEqual(reward(0,0,4,0,False,random.Random(1),victory_credit_reward_multiplier=1.5),1425)
        self.assertIn('layer_reward = 0',GEN)
        self.assertNotIn('layer_reward = 50 * layer_number',GEN)
        self.assertIn('base + 125.0 * mf',GEN)
        self.assertIn('credit_reward=round((base_reward + (100 if risk else 0)) * multiplier)',GEN)
        self.assertNotIn('base_reward + 50 * floor',GEN)

    def test_raynor_hyperion_uses_normal_movement_not_teleport(self):
        body=GALAXY.split('void APRG_RaynorMoveToward(',1)[1].split('void APRG_TickRaynorsRaiders(',1)[0]
        self.assertIn('UnitIssueOrder(g_aprgRaynorHyperion, OrderTargetingPoint(AbilityCommand("move", 0), destination)',body)
        self.assertIn('g_aprgRaynorNextMoveRefreshTime = now + 3.0;',body)
        self.assertNotIn('UnitSetPosition(',body)
        self.assertNotIn('PointWithOffsetPolar(',body)
        self.assertNotIn('g_aprgRaynorFallbackMovement',GALAXY)
        self.assertNotIn('g_aprgRaynorLastMoveProgressTime',GALAXY)
        self.assertNotIn('UnitSetPosition(g_aprgRaynorHyperion',GALAXY)
        self.assertIn('APRG_RaynorBeginMove(g_aprgRaynorTargetPoint, now)',GALAXY)
        self.assertIn('APRG_RaynorMoveToward(g_aprgRaynorSafePoint, now)',GALAXY)
        # Damage-triggered retreat and Flyby SCVs are not changed.
        self.assertIn('raynorLife <= g_aprgRaynorFlybyStartLife * 0.5',GALAXY)
        self.assertIn('APRG_TickRaynorRepairSCVs(g_aprgRaynorHyperion);',GALAXY)

    def test_invasion_pods_twice_per_second_for_two_minutes(self):
        tick=GALAXY.split('void APRG_TickInvasionFleet(',1)[1].split('void APRG_TickBaseLeviathanBurst(',1)[0]
        self.assertIn('now < 300.0 || now >= 420.0',tick)
        self.assertIn('g_aprgNextInvasionFleetDropTime = now + 0.5;',tick)
        self.assertIn('APRG_QueueRealDropPod(APRG_DROP_KIND_INVASION_FLEET, player, p, null)',tick)
        self.assertIn('APRG_ResolvePlayerZergDrop(player, p, true)',tick)
        with (ROOT/'Payload/BOON_CATALOG.csv').open(encoding='utf-8',newline='') as f:
            entries=list(csv.DictReader(f))
        row=next(r for r in entries if r['Boon Title']=='Invasion Fleet')
        self.assertEqual(row['Description'],'At the 5 minute mark of each mission, many zerg drop pods attack the enemy for 2 minutes')
        self.assertEqual(int(row['Cost']),1500)


if __name__=='__main__':
    unittest.main()
