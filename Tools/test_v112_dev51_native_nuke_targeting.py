"""Regression checks for v1.2.0 native Spectre targeting and standoff approach."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
G = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
TOSH = G[G.index("void APRG_TickToshAndHisBoys("):G.index("bool APRG_IsOdinDefensiveStructure(")]
PICK = G[G.index("unit APRG_ToshSpectreChooseTarget("):G.index("void APRG_TickToshAndHisBoys(")]

class NativeSpectreTargetTest(unittest.TestCase):
    def test_production_timing(self):
        self.assertIn('APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 300.0', G)
        self.assertIn('g_aprgMacroReadyTime + APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY', TOSH)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;', TOSH)
    def test_choose_target_and_point_on_spawn(self):
        self.assertIn('target = APRG_ToshSpectreChooseTarget(spec, player, false);', TOSH)
        self.assertIn('targetPoint = APRG_ToshSpectreRandomNukePoint(target);', TOSH)
        self.assertIn('g_aprgToshSpectreNukePoint[slot] = targetPoint;', TOSH)
        self.assertIn('g_aprgToshSpectreApproachPoint[slot] =', TOSH)
    def test_mobile_chance_and_eligible_structures(self):
        self.assertIn('RandomInt(1, 4) == 1', PICK)
        self.assertIn('APRG_PlayerMobileUnits(player)', PICK)
        self.assertIn('c_unitAllianceAlly', PICK)
        self.assertIn('APRG_IsSlayStructureEffectEligibleType(typeName)', PICK)
        self.assertIn('APRG_IsTownHallType(typeName)', PICK)
    def test_valid_fixed_distances_and_random_nuke_point(self):
        for key in ('nearestNonTownHallDistance','nearestTownHallDistance','mobileDistance'):
            self.assertIn('fixed '+key+' = 100000.0;', PICK)
        self.assertIn('RandomFixed(0.0, 5.0)', PICK)
        self.assertIn('RegionContainsPoint(RegionPlayableMap(), candidate)', PICK)
    def test_standoff_near_native_range_not_base_center(self):
        self.assertIn('APRG_ToshSpectreStandoffPoint(spec, targetPoint)', TOSH)
        self.assertIn('DistanceBetweenPoints(UnitGetPosition(spec), targetPoint) > 11.75', TOSH)
        self.assertIn('g_aprgToshSpectreNextOrderTime[i] = now + 2.0;', TOSH)
        self.assertNotIn('targetPoint = UnitGetPosition(APRG_FindPlayerHomeStructure', TOSH)
    def test_native_nuke_and_silo(self):
        self.assertIn('OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)', TOSH)
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);', TOSH)
        self.assertIn('UnitOrderHasAbil(spec, "TacNukeStrike")', TOSH)
        self.assertIn('g_aprgToshSpectreNukeTime[i] = now + 23.0;', TOSH)
        self.assertNotIn('APRG_CreateObjectiveSafeSlayEffect', TOSH)
    def test_known_raw_galaxy_regressions(self):
        self.assertNotIn('void APRG_TickNydusWorms(int player, fixed now);', G)
        self.assertNotRegex(G, r'\bunitgroup\s+wave\s*;')

if __name__ == '__main__': unittest.main()
