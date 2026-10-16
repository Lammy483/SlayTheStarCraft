"""v1.2.0 Tosh native nuke release-source hotfix regression checks."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
G = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
TOSH = G[G.index("void APRG_TickToshAndHisBoys("):G.index("bool APRG_IsOdinDefensiveStructure(")]
SHIELD = G[G.index("bool APRG_TryToshDefensiveShield("):G.index("point APRG_ToshSpectreChooseNukePoint(")]
SPAWN = G[G.index("point APRG_ToshPathableHostileSpawnPoint("):G.index("bool APRG_TryToshDefensiveShield(")]
AI = G[G.index("bool APRG_TryCategorizedAutonomousAbility("):G.index("bool APRG_TryFriendlyAutonomousAbility(")]

class ToshSpectreReleaseHotfix(unittest.TestCase):
    def test_hostile_tosh_not_blocked_by_two_hundred_energy(self):
        self.assertIn("if (!shieldCast) { APRG_TryGeneratedHeroAbility(g_aprgTosh, player); }", TOSH)
        self.assertNotIn("UnitGetPropertyFixed(g_aprgTosh, c_unitPropEnergy, c_unitPropCurrent) >= 200.0", TOSH)
        self.assertNotIn("caster == g_aprgTosh", AI)
        self.assertIn("caster == g_aprgCovertTosh", AI)
        self.assertIn("APRG_TryToshDefensiveShield(g_aprgTosh)", TOSH)
    def test_ground_path_uses_ground_not_building_centers(self):
        self.assertIn("UnitGroupClosestToPoint(workers, UnitGetPosition(home))", SPAWN)
        self.assertIn("PointPathingIsConnected(candidate, homeGround)", SPAWN)
        self.assertIn("PointPathingIsConnected(UnitGetPosition(spectre), candidate)", SPAWN)
        self.assertIn("anchor = UnitGroupRandomUnit(APRG_EnemyStructures(player)", TOSH)
    def test_locked_target_and_unsticking_without_combat_ai(self):
        self.assertIn("targetPoint = APRG_ToshSpectreChooseNukePoint(spec, player);", TOSH)
        self.assertIn("g_aprgToshSpectreNukePoint[slot] = targetPoint;", TOSH)
        self.assertIn("approachPoint = APRG_ToshSpectreApproachPoint(spec, targetPoint);", TOSH)
        self.assertIn("g_aprgToshSpectreLastProgressTime[i] + 20.0", TOSH)
        self.assertIn("PointWithOffsetPolar(targetPoint, RandomFixed(6.0, 8.0)", SPAWN)
        self.assertIn("if (distance > 9.0)", TOSH)
        self.assertIn('OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)', TOSH)
    def test_preserve_native_nuke_and_timing(self):
        self.assertIn("APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 300.0", G)
        self.assertIn("g_aprgNextToshSpectreTime = now + 60.0;", TOSH)
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);', TOSH)
        self.assertIn("UnitGetPropertyFixed(spec, c_unitPropEnergyMax, c_unitPropCurrent)", TOSH)
        self.assertNotIn("APRG_CreateObjectiveSafeSlayEffect", TOSH)
        self.assertNotIn("libNtve_gf_CreateModelAtPoint", TOSH)
    def test_raw_galaxy_never_uses_unsupported_ternary_operator(self):
        import re
        # The very small subset of Galaxy we ship does not accept ?:.
        # Strip comments and string contents before testing the source.
        code = re.sub(r'(?s)/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"', '', G)
        self.assertNotIn('?', code)
        self.assertIn('if (targetPoint == null) {', TOSH)
        self.assertIn('g_aprgToshSpectreLastDistance[slot] = 999999.0;', TOSH)

    def test_no_known_three_race_declaration_regression(self):
        self.assertNotIn("void APRG_TickNydusWorms(int player, fixed now);", G)
        self.assertNotRegex(G, r"\bunitgroup\s+wave\s*;")

if __name__ == "__main__":
    unittest.main()
