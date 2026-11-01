"""Regression guards for v1.2.3.1 Dev3 Galaxy mutation fixes."""
from pathlib import Path
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")

def body(ret, name):
    match = re.search(r"(?m)^" + re.escape(ret) + r" " + re.escape(name) + r"\([^\n]*\) \{", SOURCE)
    if match is None:
        raise AssertionError("Missing Galaxy handler " + name)
    end = SOURCE.find("\n}\n", match.end())
    if end < 0:
        raise AssertionError("Unclosed Galaxy handler " + name)
    return SOURCE[match.start():end + 2]

class Dev3Regressions(unittest.TestCase):
    def test_thrasher_fallbacks(self):
        s = body("point", "APRG_FindVoidThrasherPoint")
        for token in ("APRG_EnemyStructures(player)", "APRG_EnemyMobileUnits(player)",
                      "RegionRandomPoint(RegionPlayableMap())", "APRG_LabRatEnemySpawnAllowed",
                      "APRG_VoidThrasherPointNearFriendlyUnits(candidate, player, 7.0)"):
            self.assertIn(token, s)
    def test_thrasher_failures_retry(self):
        self.assertIn("bool APRG_SpawnVoidThrasher(int player)", SOURCE)
        self.assertIn("if (APRG_SpawnVoidThrasher(player))", SOURCE)
        self.assertIn("g_aprgNextVoidThrasherTime = now + 8.0", SOURCE)
    def test_no_death_spawns_for_scarabs_or_adept_shades(self):
        s = body("bool", "APRG_DeathSpawnExcluded")
        for token in ("Scarab", "AdeptPhaseShift", "AdeptShade"):
            self.assertIn('"' + token + '"', s)
        for name in ("APRG_BasicZombieDeathExcluded", "APRG_ZombieApocalypseDeathExcluded"):
            self.assertIn("APRG_DeathSpawnExcluded", body("bool", name))
        self.assertIn("!deathSpawnExcluded", body("bool", "APRG_Death_Func"))
    def test_nuclear_workers_ignores_morph_eggs(self):
        for token in ("Egg", "Cocoon", "Larva", "Chrysalis", "Dummy", "Placeholder"):
            self.assertIn('"' + token + '"', body("bool", "APRG_IsWorkerTypeForDeath"))
        d = body("bool", "APRG_Death_Func")
        self.assertIn("!APRG_UnitHasTimedLife(dead)", d)
        self.assertIn("!UnitTypeTestAttribute(unitType, c_unitAttributeStructure)", d)
    def test_instigator_uses_own_blink(self):
        s = body("void", "APRG_EnsureBlinkOnUnit")
        self.assertIn('StringContains(unitType, "Instigator"', s)
        self.assertLess(s.index('"Instigator"'), s.index('UnitAbilityRemove(u, "Blink")'))

if __name__ == "__main__":
    unittest.main()
