"""v1.1.2 regression checks for Baneling Stream structure engagement.

Static checks alone cannot substitute for a live SC2 ability/order test.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAL = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')

def segment(first: str, last: str) -> str:
    return GAL.split(first, 1)[1].split(last, 1)[0]

class BanelingStreamV112(unittest.TestCase):
    def test_baneling_uses_attack_move_without_plain_move_fallback(self):
        f = segment('bool APRG_OrderBanelingStreamAttackMove(', 'void APRG_TickBanelingStream(')
        self.assertIn('OrderTargetingPoint(AbilityCommand("attack", 0), destination)', f)
        self.assertIn('UnitOrderIsValid(u, attackOrder)', f)
        self.assertNotIn('APRG_OrderStandardMove', f)
        self.assertNotIn('AbilityCommand("move",', f)

    def test_eligible_buildings_precede_mobile_or_random_patrol(self):
        f = segment('void APRG_OrderBanelingStreamUnit(', 'void APRG_TickBanelingStream(')
        self.assertLess(f.index('APRG_BanelingStreamBuildingTarget('), f.index('APRG_NearestEnemyGroundMobile('))
        self.assertLess(f.index('APRG_NearestEnemyGroundMobile('), f.index('APRG_RandomFixedPatrolPointForUnit('))
        self.assertNotIn('RandomInt(0, 1)', f)
        self.assertIn('APRG_OrderBanelingStreamAttackMove(u, destination)', f)

    def test_only_targetable_reachable_enemy_structures(self):
        f = segment('unit APRG_BanelingStreamBuildingTarget(', 'void APRG_OrderBanelingStreamUnit(')
        self.assertIn('APRG_EnemyTargetableStructures(player)', f)
        self.assertIn('UnitTestState(candidate, c_unitStateInvulnerable)', f)
        self.assertIn('UnitPathableToPoint(u, UnitGetPosition(candidate), 6.0, 100000.0)', f)

    def test_cadence_and_spawn_type_preserved(self):
        f = segment('void APRG_TickBanelingStream(', 'unit APRG_CreateTychusAtHome(')
        self.assertIn('now + RandomFixed(5.0, 15.0)', f)
        self.assertIn('g_aprgNextBanelingStreamRetargetTime = now + 8.0;', f)
        self.assertIn('APRG_CreatePlayerBaneling(player, p)', f)

if __name__ == '__main__':
    unittest.main()
