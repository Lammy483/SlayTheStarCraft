"""Regression checks for production native Spectre nuke targeting."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
TOSH = GALAXY[GALAXY.index("void APRG_TickToshAndHisBoys("):GALAXY.index("bool APRG_IsOdinDefensiveStructure(")]
PICK = GALAXY[GALAXY.index("point APRG_ToshSpectreChooseNukePoint("):GALAXY.index("void APRG_TickToshAndHisBoys(")]

class NativeSpectreTargetTest(unittest.TestCase):
    def test_timing_is_production_cadence(self):
        self.assertIn('APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 300.0', GALAXY)
        self.assertIn('g_aprgMacroReadyTime + APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY', TOSH)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;', TOSH)
        self.assertNotIn('APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 60.0', GALAXY)

    def test_chooses_target_at_birth(self):
        self.assertIn('targetPoint = APRG_ToshSpectreChooseNukePoint(spec, player);', TOSH)
        self.assertIn('g_aprgToshSpectreNukePoint[slot] = targetPoint;', TOSH)
        self.assertIn('if (!UnitIssueOrder(spec, OrderTargetingPoint(AbilityCommand("move", 0),', TOSH)
        self.assertIn('g_aprgToshSpectreLastProgressTime[slot] = now;', TOSH)
        self.assertIn('g_aprgToshSpectreNukePoint[i];', TOSH)

    def test_25_percent_mobile_preference_plus_allied_units(self):
        self.assertIn('preferMobile = RandomInt(1, 4) == 1;', PICK)
        self.assertIn('APRG_PlayerMobileUnits(player)', PICK)
        self.assertIn('c_unitAllianceAlly', PICK)
        self.assertIn('c_targetFilterStructure', PICK)

    def test_structure_aim_within_five(self):
        self.assertIn('APRG_PlayerStructures(player)', PICK)
        self.assertIn('RandomFixed(0.0, 4.5)', PICK)
        self.assertIn('APRG_IsSlayStructureEffectEligibleType', PICK)
        self.assertIn('RegionContainsPoint(RegionPlayableMap(), p)', PICK)

    def test_cast_keeps_original_point_and_no_attack_approach(self):
        self.assertIn('OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)', TOSH)
        self.assertIn('if (distance > 9.0)', TOSH)
        self.assertIn('g_aprgToshSpectreNextOrderTime[i] = now + 5.0;', TOSH)
        self.assertNotIn('targetPoint = PointWithOffsetPolar(UnitGetPosition(target),', TOSH)
        start = TOSH.index('if (g_aprgToshSpectrePhase[i] != 1')
        end = TOSH.index('castOrder = OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0)', start)
        approach = TOSH[start:end]
        self.assertNotIn('APRG_OrderAttackMove(spec', approach)
        self.assertIn('APRG_NearestPathablePlayerStructure(spec, player)', approach)

    def test_native_nuke_and_silo_not_removed(self):
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);', TOSH)
        self.assertIn('UnitOrderHasAbil(spec, "TacNukeStrike")', TOSH)
        self.assertIn('g_aprgToshSpectreNukeTime[i] = now + 23.0;', TOSH)

    def test_no_old_compile_regression(self):
        self.assertNotIn('void APRG_TickNydusWorms(int player, fixed now);', GALAXY)
        self.assertNotRegex(GALAXY, r'\bunitgroup\s+wave\s*;')

if __name__ == '__main__': unittest.main()
