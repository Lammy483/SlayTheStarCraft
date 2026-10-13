"""v1.1.2 Dev3: enemy Zagara finish-at-6-HP and safe-native-Purifier regression."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAL = (ROOT / "Payload/APRogue.galaxy").read_text(encoding="utf-8")


def function(name):
    match = re.search(r"^(?:void|bool)\s+" + re.escape(name) + r"\([^)]*\)\s*\{", GAL, re.M)
    if not match:
        raise AssertionError(f"Missing Galaxy function: {name}")
    start = GAL.index("{", match.start())
    depth = 0
    for pos in range(start, len(GAL)):
        if GAL[pos] == "{":
            depth += 1
        elif GAL[pos] == "}":
            depth -= 1
            if depth == 0:
                return GAL[start:pos+1]
    raise AssertionError(f"Unbalanced Galaxy function: {name}")


class ZagaraAndPurifier(unittest.TestCase):
    def test_generated_enemy_zagara_finishes_at_four_hp(self):
        tick = function("APRG_TickGeneratedHeroNoRevive")
        self.assertIn('"Zagara", c_stringAnywhere, c_stringNoCase', tick)
        self.assertIn("<= 6.0", tick)
        self.assertIn("UnitKill(u);", tick)
        self.assertIn("if (UnitIsAlive(u)) { UnitRemove(u); }", tick)
        self.assertNotIn("<= 3.1", tick)

    def test_untracked_mission_enemy_zagara_included(self):
        tick = function("APRG_TickEnemyZagaraFatalHp")
        self.assertIn("candidates = APRG_EnemyAllUnits(player)", tick)
        self.assertIn('StringContains(UnitGetType(zagara), "Zagara",', tick)
        self.assertIn(" > 6.0", tick)
        self.assertIn("APRG_DisableGeneratedHeroRevive(zagara)", tick)
        self.assertIn("UnitKill(zagara)", tick)
        self.assertIn("UnitRemove(zagara)", tick)
        main = function("APRG_Tick_Func")
        self.assertIn("APRG_TickEnemyZagaraFatalHp(player, now)", main)

    def test_purifier_override_is_scoped_to_selected_effect_and_own_unit(self):
        helper = function("APRG_RemoveSlayPurifierInvulnerability")
        self.assertIn("purifier == g_aprgPurifier", helper)
        self.assertIn("APRG_HasExtension3(APRG_EXT3_MUT_PURIFIER)", helper)
        self.assertIn("purifier == g_aprgPurifierAlliance", helper)
        self.assertIn("APRG_HasExtension4(APRG_EXT4_BOON_PURIFIER_ALLIANCE)", helper)
        self.assertIn("else { return; }", helper)
        self.assertIn('UnitBehaviorRemove(purifier, "InvulnerabilityShield", c_unitBehaviorCountAll)', helper)
        self.assertIn('UnitSetState(purifier, c_unitStateInvulnerable, false)', helper)
        self.assertEqual(2, function("APRG_TickPurifier").count("APRG_RemoveSlayPurifierInvulnerability(g_aprgPurifier)"))
        self.assertEqual(2, function("APRG_TickPurifierAlliance").count("APRG_RemoveSlayPurifierInvulnerability(g_aprgPurifierAlliance)"))
        # In particular, never pass an arbitrary Purifier / mission-owned unit.
        self.assertEqual(4, GAL.count("APRG_RemoveSlayPurifierInvulnerability(g_aprg"))

    def test_no_global_purifier_catalog_change(self):
        assert 'CatalogFieldValueSet(c_gameCatalogUnit, "Purifier", "BehaviorArray"' not in GAL
        assert 'CatalogFieldValueModify(c_gameCatalogUnit, "Purifier", "BehaviorArray"' not in GAL

if __name__ == "__main__":
    unittest.main()
