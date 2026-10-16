"""v1.1.2 Dev19: Aberrations receive actual +10 HP per second from their boon."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / "Payload/APRogue.galaxy").read_text(encoding="utf-8")

def body(name):
    m = re.search(r"^(?:void|bool)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", G, re.M)
    if not m:
        raise AssertionError(f"missing {name}")
    start = G.index("{", m.start())
    count = 1
    for i in range(start+1,len(G)):
        if G[i] == "{": count += 1
        elif G[i] == "}":
            count -= 1
            if count == 0:
                return G[start+1:i]
    raise AssertionError(f"unclosed {name}")

class RegenerativeAberrationsDev19(unittest.TestCase):
    def test_matches_normal_and_legacy_spelling(self):
        f = body("APRG_IsRegenerativeAberrationType")
        self.assertIn('"Aberration"', f)
        self.assertIn('"Abberation"', f)
        self.assertIn('c_stringNoCase', f)

    def test_heals_explicitly_without_property_only_fix(self):
        f = body("APRG_TickRegenerativeAberrations")
        self.assertIn('APRG_EXT4_BOON_REGENERATIVE_ABERRATIONS', f)
        self.assertIn('APRG_PlayerMacroBaseReady(player)', f)
        self.assertIn('APRG_PlayerAllUnits(player)', f)
        self.assertIn('APRG_IsRegenerativeAberrationUnit(u)', f)
        self.assertIn('UnitSetPropertyFixed(u, c_unitPropLife, MinF(maximum, current + 10.0))', f)
        self.assertIn('maximum > current', f)
        self.assertIn('current > 0.0', f)
        self.assertNotIn('c_unitPropLifeRegen', f)

    def test_one_second_interval(self):
        f=body('APRG_TickRegenerativeAberrations')
        self.assertIn('now < g_aprgNextAberrationHealTime', f)
        self.assertGreaterEqual(f.count('g_aprgNextAberrationHealTime = now + 1.0'), 2)

    def test_active_gameplay_tick_and_per_mission_reset(self):
        self.assertIn('APRG_TickRegenerativeAberrations(player, now)',body('APRG_FastBoonTick_Func'))
        self.assertIn('g_aprgNextAberrationHealTime = 0.0',body('APRG_ActivateEffects'))

    def test_old_tagged_property_only_logic_is_removed(self):
        self.assertNotIn('APRG_RegenerativeAberration_', G)
        self.assertNotIn('c_unitPropLifeRegen, UnitGetPropertyFixed(u, c_unitPropLifeRegen, c_unitPropCurrent) + 10.0', G)

if __name__ == "__main__":
    unittest.main()
