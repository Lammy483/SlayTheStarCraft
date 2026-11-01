"""Dev4 static regression tests. Run with Python -m unittest discover -s Tools -p test_v1231_dev4*.py."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GEN = (ROOT / "Payload/generate_slay_run.py").read_text(encoding="utf-8")
CLIENT = (ROOT / "Payload/slay_the_starcraft.py").read_text(encoding="utf-8")
LAUNCHER = (ROOT / "Payload/slay_launcher.py").read_text(encoding="utf-8")
GALAXY = (ROOT / "Payload/APRogue.galaxy").read_text(encoding="utf-8")

def galaxy_fn(name, ret):
    m = re.search(r"(?m)^" + ret + r" " + name + r"\([^\n]*\) \{", GALAXY)
    if not m:
        raise AssertionError("missing "+name)
    e = GALAXY.find("\n}\n", m.end())
    if e < 0:
        raise AssertionError("unclosed "+name)
    return GALAXY[m.start():e+2]

class Dev4(unittest.TestCase):
    def test_python_compiles(self):
        for name, s in (("generator", GEN), ("client", CLIENT), ("launcher", LAUNCHER)):
            ast.parse(s, filename=name)
    def test_possible_missions_columns_without_instructions(self):
        self.assertIn("def possible_mission_groups", GEN)
        self.assertIn('for title, names in mission_groups.items()', LAUNCHER)
        self.assertIn('mission_groups = _mission_module.possible_mission_groups', LAUNCHER)
        self.assertNotIn("Uncheck a mission to exclude", LAUNCHER)
    def test_destruction_on_zero_hour_only(self):
        self.assertIn('DESTRUCTION_TIMED_DEFENSE_ALLOWLIST = {"Zero Hour"}', GEN)
        self.assertIn('mission_name.casefold() != "zero hour"', CLIENT)
    def test_severity_red_from_three(self):
        self.assertIn("if severity < 3:", CLIENT)
        self.assertIn('3: "FFB0B0"', CLIENT)
    def test_three_workbook_mutations(self):
        for name in ("armored_enemies", "swarms_of_unit", "explosive_armor_mutation"):
            self.assertIn(name, CLIENT)
        for name in ("swarms_of_unit", "explosive_armor_mutation"):
            self.assertIn(name, GEN)
    def test_swarm_contract(self):
        p = galaxy_fn("APRG_SpawnSwarmWave", "bool")
        self.assertIn("3000 + 1000 * g_aprgSwarmWaveCount", p)
        self.assertIn("i < 4", p)
        self.assertIn("APRG_AddHostileRaiders", p)
        self.assertIn("if (g_aprgSwarmSpawnPoints[i] == null) { return false; }", p)
        self.assertIn("g_aprgNextSwarmTime = now + 240.0", galaxy_fn("APRG_TickSwarmsOfUnit","void"))
        self.assertIn("g_aprgNextSwarmTime = g_aprgMacroReadyTime + 300.0", galaxy_fn("APRG_TickSwarmsOfUnit","void"))
    def test_swarm_mission_flag_and_island_air(self):
        self.assertIn('SWARM_UNITS = (', CLIENT)
        self.assertIn('range(11, len(SWARM_UNITS)) if base_name in ISLAND_MISSION_NAMES', CLIENT)
        self.assertIn("flags |= swarm_unit_index(ctx, int(mission_id)) << 24", CLIENT)
        self.assertIn("MISSION_FLAG_SWARMS_OF_UNIT = 4194304", CLIENT)
        self.assertIn("APRG_TickSwarmsOfUnit(player, now)", GALAXY)
    def test_explosive_mutation_uses_half_damage_against_hostile_owner(self):
        d=galaxy_fn("APRG_Death_Func","bool")
        self.assertIn("APRG_MISSION_FLAG_EXPLOSIVE_ARMOR_MUTATION", d)
        self.assertIn("APRG_DealExplosiveArmorDamage(p, owner,", d)
        self.assertIn("10.0 * UnitTypeGetProperty", d)
    def test_sniper_range_non_melee_plus_one(self):
        m=galaxy_fn("APRG_ApplyMercenaryUnitUpgrades","void")
        self.assertIn("wc = 20 * sniperStacks", m)
        self.assertIn("if (value > 1.5)", m)
        self.assertIn('FixedToString(IntToFixed(sniperStacks)', m)
        self.assertNotIn("value * 0.5 * IntToFixed(sniperStacks)", m)
    def test_prior_dev3_still_present(self):
        self.assertIn('"AdeptPhaseShift"', galaxy_fn("APRG_DeathSpawnExcluded","bool"))
        self.assertIn("g_aprgNextVoidThrasherTime = now + 8.0", GALAXY)

if __name__ == "__main__":
    unittest.main()
