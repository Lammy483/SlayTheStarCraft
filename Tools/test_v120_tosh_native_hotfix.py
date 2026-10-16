"""v1.2.0 release checks for user-verified native Tosh/Spectre nukes."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
G = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
TOSH = G[G.index("void APRG_TickToshAndHisBoys("):G.index("bool APRG_IsOdinDefensiveStructure(")]
SELECTOR = G[G.index("unit APRG_ToshSpectreChooseTarget("):G.index("point APRG_ToshSpectreStandoffPoint(")]
SPAWN = G[G.index("point APRG_ToshPathableHostileSpawnPoint("):G.index("bool APRG_TryToshDefensiveShield(")]
AI = G[G.index("bool APRG_TryCategorizedAutonomousAbility("):G.index("bool APRG_TryFriendlyAutonomousAbility(")]

class ToshSpectreReleaseHotfix(unittest.TestCase):
    def test_hostile_tosh_and_covert_tosh_ability_rules(self):
        self.assertIn('APRG_TryToshDefensiveShield(g_aprgTosh);', TOSH)
        self.assertIn('UnitGetPropertyFixed(g_aprgTosh, c_unitPropEnergy, c_unitPropCurrent) >= 200.0', TOSH)
        self.assertIn('caster == g_aprgCovertTosh || caster == g_aprgTosh', AI)
    def test_spawn_and_native_standoff_path(self):
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))', SPAWN)
        self.assertIn('APRG_ToshSpectreStandoffPoint(spec, targetPoint)', TOSH)
        self.assertIn('PointPathingPassable(candidate)', G)
        self.assertIn('g_aprgToshSpectreApproachPoint[slot]', TOSH)
    def test_fixed_distance_range_for_nearest_building(self):
        for key in ('nearestNonTownHallDistance','nearestTownHallDistance','mobileDistance'):
            self.assertIn('fixed '+key+' = 100000.0;', SELECTOR)
        self.assertNotIn('999999.0', SELECTOR)
    def test_native_ammo_and_no_scripted_damage(self):
        self.assertIn('OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)', TOSH)
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);', TOSH)
        self.assertIn('g_aprgToshSpectreNukeTime[i] = now + 23.0;', TOSH)
        self.assertNotIn('APRG_CreateObjectiveSafeSlayEffect', TOSH)
        self.assertNotIn('libNtve_gf_CreateModelAtPoint', TOSH)
    def test_release_schedule_and_no_staged_diagnostic_first_spawn(self):
        self.assertIn('APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 300.0', G)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;', TOSH)
        self.assertNotIn('TEST ONLY: First Spectre', G)
    def test_raw_galaxy_never_uses_unsupported_ternary_operator(self):
        code = re.sub(r'(?s)/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', '', G)
        self.assertNotIn('?', code)
    def test_known_three_race_regressions(self):
        self.assertNotIn('void APRG_TickNydusWorms(int player, fixed now);', G)
        self.assertNotRegex(G, r'\bunitgroup\s+wave\s*;')

if __name__ == "__main__": unittest.main()
