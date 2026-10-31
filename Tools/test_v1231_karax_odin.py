"""Regression tests for Karax Champion and enemy Odin changes."""
from pathlib import Path
import re
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"Payload"/"APRogue.galaxy").read_text(encoding="utf-8")

def body(name):
    match=re.search(r"(?m)^(?:void|point|string) "+re.escape(name)+r"\([^\n]*\) \{",SOURCE)
    if match is None: raise AssertionError("Missing: "+name)
    end=SOURCE.find("\n}\n",match.end())
    if end<0: raise AssertionError("Not closed: "+name)
    return SOURCE[match.start():end+2]

class KaraxOdin(unittest.TestCase):
    def test_karax_champion_id(self):
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, "KaraxChampion")',body("APRG_KaraxHeroType"))
        self.assertNotIn('return "Karax";',body("APRG_HeroCandidate"))
        self.assertIn('if (preferredIndex == 15 || preferredIndex == 16) { return APRG_KaraxHeroType(); }',body("APRG_FindValidHeroTypeFromIndex"))
        self.assertIn('return APRG_KaraxHeroType();',body("APRG_CommanderFallbackCandidate"))
    def test_no_wrong_commander_fallback_for_explicit_karax(self):
        s=body("APRG_GiveGeneralIfReady")
        self.assertIn("Karax could not spawn",s)
        self.assertIn("KaraxChampion was present in the catalog",s)
        self.assertIn('heroType == "KaraxChampion"',s)
        self.assertIn('g_aprgCommanderHeroType == "KaraxChampion"',s)
    def test_odin_stations_before_attack(self):
        s=body("APRG_TickDelayedOdin")
        self.assertLess(s.index("APRG_FindDelayedOdinStrongholdPoint(player)"),s.index("if (now < g_aprgMacroReadyTime + 840.0)"))
        self.assertIn("AISetUnitScriptControlled(g_aprgDelayedOdin, true)",s)
        self.assertIn("g_aprgNextDelayedOdinSpawnAttemptTime = now + 5.0",s)
    def test_odin_near_enemy_cluster_not_player(self):
        s=body("APRG_FindDelayedOdinStrongholdPoint")
        for needle in ("APRG_EnemyStructures(player)","APRG_EnemyMobileUnits(player)",
                       "UnitGroupAlliance(player, c_unitAllianceEnemy", "score = UnitGroupCount(nearby, c_unitCountAlive)",
                       "DistanceBetweenPoints(UnitGetPosition(home), candidate) < 32.0",
                       "APRG_DelayedOdinNearFriendlyBuilding(candidate, player, 24.0)",
                       "PointPathingIsConnected(candidate, UnitGetPosition(home))"):
            self.assertIn(needle,s)
        self.assertNotIn("APRG_RandomPathableHostileBaseAnchor",body("APRG_TickDelayedOdin"))
    def test_no_odin_respawn(self):
        s=body("APRG_TickDelayedOdin")
        self.assertEqual(s.count('UnitCreate(1, "Odin"'),1)
        self.assertIn("if (!g_aprgDelayedOdinSpawned)",s)
        self.assertIn("g_aprgDelayedOdinSpawned = true",s)

if __name__=="__main__":
    unittest.main()
