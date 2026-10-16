import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"
GAL = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
RUN = (PAYLOAD / "slay_the_starcraft.py").read_text(encoding="utf-8")
GEN = (PAYLOAD / "generate_slay_run.py").read_text(encoding="utf-8")

class Dev41Effects(unittest.TestCase):
    def test_catalog_exact_titles_descriptions_and_severities(self):
        rows = list(csv.DictReader((PAYLOAD / "EFFECT_CATALOG.csv").open(encoding="utf-8")))
        titles = {
            "Point Defense Drones": ("Mutation", "1", "Enemy structures each have a point defense drone deployed near them to stop your projectiles"),
            "Heavily-Defended Drakken Laser Drill": ("Mutation", "6", "The enemy has a Heavily-Defended Drakken Laser Drill"),
            "Multiple Air Bogies": ("Mutation", "1", "Zerg air units occasionally attack your base"),
            "Covert Assistance": ("Blessing", "1", "Tosh works independently to assist you. He does not respawn."),
        }
        for title, expected in titles.items():
            found = [r for r in rows if r["Title"] == title]
            self.assertEqual(1, len(found), title)
            self.assertEqual(expected, (found[0]["Mutation or Blessing"], found[0]["Severity"], found[0]["Description"]))

    def test_unique_bank_e_bits(self):
        expected = {
            "APRG_EXT3_MUT_POINT_DEFENSE_DRONES": "16777216",
            "APRG_EXT3_MUT_HEAVILY_DEFENDED_DRAKKEN": "33554432",
            "APRG_EXT3_MUT_MULTIPLE_AIR_BOGIES": "67108864",
            "APRG_EXT3_BLESS_COVERT_ASSISTANCE": "134217728",
        }
        for name, bit in expected.items():
            self.assertIn("const int " + name + " = " + bit + ";", GAL)
            self.assertIn("APRG_HasExtension3(" + name + ")", GAL)

    def test_drill_reuses_existing_behavior(self):
        self.assertIn("APRG_HasMutation(APRG_MUT_DRAKKEN_DRILL) ||", GAL)
        self.assertIn("APRG_SpawnHeavyDrakkenGuards(player, owner, p);", GAL)
        self.assertIn('unitType = "SiegeBreaker";', GAL)
        self.assertIn('unitType = "MissileTurret";', GAL)

    def test_drone_persistence(self):
        self.assertIn('UnitCreate(1, "PointDefenseDrone"', GAL)
        self.assertIn('UnitBehaviorRemove(drone, behaviorName, c_unitBehaviorCountAll)', GAL)
        self.assertIn("g_aprgPointDefenseSpawned = true;", GAL)
        self.assertIn("now < g_aprgMacroReadyTime + 10.0", GAL)

    def test_bogies_waves_and_proximity(self):
        self.assertIn("g_aprgMacroReadyTime + 300.0", GAL)
        self.assertIn("now + 120.0 + 10.0 * IntToFixed(g_aprgAirBogieWaveNumber)", GAL)
        self.assertIn("APRG_PointNearPlayerOrAlliedBuilding(p, player, 10.0)", GAL)
        self.assertIn("RandomInt(1, 4) == 1", GAL)

    def test_covert_tosh(self):
        self.assertIn("!UnitIsAlive(g_aprgCovertTosh)) { return; } // never respawn", GAL)
        self.assertIn("hp < maxHp * 0.5", GAL)
        self.assertIn("regenRate = 0.5;", GAL)
        self.assertIn("regenRate += 1.0;", GAL)
        self.assertIn("hp + regenRate * MinF(elapsed, 2.0)", GAL)
        self.assertIn("APRG_AddAlliedSupport(created, spawnPoint, player, true);", GAL)
        self.assertIn('APRG_TryUnitAbilityKeyword(g_aprgCovertTosh, "DefensiveMatrix"', GAL)
        self.assertIn("APRG_TryCategorizedAutonomousAbility(g_aprgCovertTosh, player, true)", GAL)
        self.assertNotIn("if (spawnedThisScan >= 16) { break; }", GAL)

    def test_both_generator_paths(self):
        for source in (RUN, GEN):
            self.assertIn('"point_defense_drones"', source)
            self.assertIn('"heavily_defended_drakken_laser_drill"', source)
            self.assertIn('"multiple_air_bogies"', source)
            self.assertIn('"covert_assistance"', source)
        self.assertIn('effect == "covert_assistance" and mission_name.casefold() in ISLAND_MISSION_NAMES', RUN)
        self.assertIn('forbidden_blessings.add("covert_assistance")', GEN)
        self.assertIn('effect == "point_defense_drones" and bool(data.get("timed_defense", False))', RUN)
        self.assertIn('forbidden_mutators.add("point_defense_drones")', GEN)

    def test_no_reserved_galaxy_variable(self):
        self.assertNotRegex(GAL, r"\bunitgroup\s+wave\s*;")

if __name__ == "__main__":
    unittest.main()
