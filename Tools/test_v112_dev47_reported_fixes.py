"""Dev47 regression guards for reported SC2 playtest defects.

Static source tests are not a substitute for compiling inside StarCraft II.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")


def body(name):
    m = re.search(r"^(?:void|bool|point|unit|int|fixed|string)\s+" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", G, re.M)
    assert m, f"Missing function {name}"
    start = G.index("{", m.start())
    depth = 1
    for i in range(start + 1, len(G)):
        if G[i] == "{":
            depth += 1
        elif G[i] == "}":
            depth -= 1
            if depth == 0:
                return G[start:i+1]
    raise AssertionError(f"Unclosed {name}")


class Dev47Fixes(unittest.TestCase):
    def test_three_race_fix_and_valid_forward_declaration(self):
        self.assertNotRegex(G, r"(?m)^\s*unitgroup\s+wave\s*;")
        self.assertNotIn("void APRG_TickNydusWorms(int player, fixed now);", G)
        self.assertLess(G.index("point APRG_ArchonImmortalPatrolDestination(unit mover, int player, fixed clearance);"), G.index("bool APRG_OrderPatrolMap("))
        self.assertIn("point APRG_ArchonImmortalPatrolDestination(unit mover, int player, fixed clearance) {", G)

    def test_archangel_test_not_registered(self):
        init = body("APRogue_Init")
        self.assertNotIn("g_aprgVOTestAutoTrigger = TriggerCreate", init)
        self.assertNotIn("g_aprgVOTestChatTrigger = TriggerCreate", init)
        self.assertIn("APRogueVO_Archangel_123", G)

    def test_pdd_deploys_once_ten_seconds_after_base_ready(self):
        f = body("APRG_TickPointDefenseDrones")
        self.assertIn('g_aprgPointDefenseSpawned = true;', f)
        self.assertIn('now < g_aprgMacroReadyTime + 10.0', f)
        self.assertNotIn('g_aprgNextPointDefenseScan = now + 5.0;', f)
        self.assertIn('UnitBehaviorHasFlag(behaviorName, c_unitBehaviorFlagTimedLife)', f)
        self.assertEqual(f.count('UnitCreate(1, "PointDefenseDrone"'), 1)

    def test_kerrigan_uses_workforce_reachable_ground(self):
        f = body("APRG_KerriganSafeHomePoint")
        self.assertIn("UnitPathableToPoint(worker, candidate, 2.0, 100000.0)", f)
        self.assertIn("APRG_PointNearMineralField(candidate, 4.0)", f)
        self.assertIn("RandomFixed(4.5, 10.0)", f)
        self.assertIn("APRG_KerriganSafeHomePoint(player)", body("APRG_CreateShopKerriganAtHome"))
        self.assertIn("APRG_KerriganSafeHomePoint(player)", body("APRG_PositionShopKerriganAtHome"))

    def test_tosh_retreats_immediately_but_does_not_interrupt_matrix(self):
        f = body("APRG_TickCovertAssistance")
        self.assertIn('matrixOrderIssued = APRG_TryUnitAbilityKeyword', f)
        self.assertIn("c_orderQueueAddToEnd", f)
        self.assertIn("c_orderQueueReplace", f)
        self.assertNotIn("now + 1.5", f)
        self.assertIn("g_aprgCovertToshNextOrder = now + 1.0", f)

    def test_archon_immortal_use_wider_patrol_destinations(self):
        f = body("APRG_OrderPatrolMap")
        self.assertIn('StringContains(UnitGetType(mover), "Immortal"', f)
        self.assertIn("APRG_ArchonImmortalPatrolDestination", f)
        d = body("APRG_ArchonImmortalPatrolDestination")
        self.assertIn("APRG_EnemyStructures(player)", d)
        self.assertIn("RegionRandomPoint(RegionPlayableMap())", d)
        self.assertIn("UnitPathableToPoint", d)
        self.assertIn("APRG_GoldenPatrolRouteSafe(origin, candidate, player, clearance)", d)

    def test_spawn_x_units_join_autonomous_ai(self):
        f = body("APRG_TickPotionSpawnQueues")
        gate = "if (kind == 17 || kind == 18 || (kind >= 1901 && kind <= 1918))"
        self.assertIn(gate, f)
        scoped = f.split(gate, 1)[1].split("\n            }\n        }", 1)[0]
        for phrase in ("APRG_MakeGroupUncommandable(created)", "UnitGroupAdd(g_aprgPotionAutoUnits, spawned)", "APRG_OrderAttackMove(spawned"):
            self.assertIn(phrase, scoped)

    def test_nydus_range_and_repeated_unload(self):
        f = body("APRG_TickNydusWorms")
        self.assertIn("maximumDistance = 25.0 + 5.0 * IntToFixed(g_aprgNydusSpawnCount)", f)
        self.assertIn('libNtve_gf_PlayAnimation(libNtve_gf_MainActorofUnit(worm), c_animNameDefault, "Spell", 0, c_animTimeDefault)', f)
        self.assertIn("g_aprgNydusNextUnitTime[slot] = now + 0.3333", f)
        find = body("APRG_FindNydusSpawnPoint")
        self.assertIn("RandomFixed(5.0, maximumDistance)", find)
        self.assertIn("if (distance < 5.0 || distance > maximumDistance)", find)


if __name__ == "__main__":
    unittest.main()
