"""Dev5 Kerrigan respawn safety regression checks.

Run from the release root: python -m unittest Tools/test_v1231_dev5_kerrigan_vortex.py
"""
from pathlib import Path
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")

def func(name, result_type):
    pat = r"(?m)^" + re.escape(result_type) + r" " + re.escape(name) + r"\([^\n]*\) \{"
    match = re.search(pat, SOURCE)
    if not match:
        raise AssertionError("Missing " + name)
    end = SOURCE.find("\n}\n", match.end())
    if end < 0:
        raise AssertionError("Unclosed " + name)
    return SOURCE[match.start():end+2]

class KerriganSafety(unittest.TestCase):
    def test_spawn_can_never_tag_broodling(self):
        verify = func("APRG_CreateVerifiedShopKerriganUnit", "unit")
        self.assertIn("APRG_IsShopKerriganType(UnitGetType(result))", verify)
        self.assertIn("APRG_ShopKerrigan_", verify)
        self.assertIn("candidateType != nativeType", verify)
        self.assertIn("if (created != null && UnitGroupCount(created, c_unitCountAlive) > 0)", verify)
        self.assertIn('"Broodling"', func("APRG_IsShopKerriganType", "bool"))
    def test_both_creation_routes_are_verified(self):
        for name in ("APRG_CreateShopKerriganAtHome", "APRG_CreateShopKerriganAtPoint"):
            self.assertIn("APRG_CreateVerifiedShopKerriganUnit", func(name,"unit"))
    def test_vortex_is_not_a_death(self):
        tick = func("APRG_TickShopKerrigan","void")
        self.assertIn("if (g_aprgShopKerrigan != null && UnitIsAlive(g_aprgShopKerrigan)", tick)
        self.assertIn("UnitGetOwner(g_aprgShopKerrigan) == player", tick)
        self.assertIn("APRG_IsShopKerriganType(UnitGetType(g_aprgShopKerrigan))", tick)
        self.assertLess(
            tick.index("if (g_aprgShopKerrigan != null && UnitIsAlive(g_aprgShopKerrigan)"),
            tick.index("g_aprgShopKerriganDeathTime = now;"),
        )
    def test_vortex_return_is_not_removed_or_respawned(self):
        tick = func("APRG_TickShopKerrigan","void")
        self.assertNotIn("UnitRemove(fresh)", tick)
        self.assertIn("if (fresh == g_aprgShopKerrigan && UnitIsAlive(fresh))", tick)
        self.assertIn("g_aprgShopKerriganDeathTime = -1.0;", tick)
        self.assertIn("if (respawnElapsed >= respawnDelay - 2.0)", tick)
    def test_normal_death_delay_kept(self):
        tick = func("APRG_TickShopKerrigan","void")
        self.assertIn("respawnDelay = APRG_KerriganRespawnDelay()", tick)
        self.assertIn("g_aprgShopKerriganVerifyAt = now + 1.0", tick)
        self.assertIn("g_aprgShopKerriganNextRetryAt = now + 2.0", tick)
        self.assertIn("APRG_FindKerriganCocoonPoint(player)", tick)

if __name__ == "__main__":
    unittest.main()
