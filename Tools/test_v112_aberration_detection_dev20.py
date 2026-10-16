"""Dev20: native and AP Aberration variants, and diagnostics for runtime reports."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')

class AberrationDetectionDev20(unittest.TestCase):
    def test_internal_unit_id_and_display_name(self):
        self.assertIn('StringContains(unitType, "Aberration"',G)
        self.assertIn('StringContains(unitType, "Abberation"',G)
        self.assertIn('TextToString(UnitTypeGetName(unitType))',G)
        self.assertIn('TextToString(UnitGetName(u))',G)
        self.assertIn('APRG_RegenerativeAberrationType_',G)
    def test_scan_and_heal(self):
        self.assertIn('units = APRG_PlayerAllUnits(player);\n    for (i = UnitGroupCount(units, c_unitCountAlive)',G)
        self.assertIn('!APRG_IsRegenerativeAberrationUnit(u)) { continue; }',G)
        self.assertIn('MinF(maximum, current + 10.0)',G)
    def test_single_scheduler_window_and_main_tick(self):
        self.assertIn('APRG_TickRegenerativeAberrations(player, now);',G)
        self.assertEqual(G.count('void APRG_TickRegenerativeAberrations(int player, fixed now)'),1)
        self.assertIn('g_aprgNextAberrationHealTime = now + 1.0;',G)
    def test_opt_in_debug_only(self):
        self.assertIn('TriggerAddEventChatMessage(g_aprgAberrationDebugTrigger, c_playerAny, "?SlayAberrationDebug", false)',G)
        self.assertIn('UnitGroupSelected(player)',G)
        self.assertIn('active=" + flag',G)
        self.assertIn('owner=" + IntToString(UnitGetOwner(u))',G)

if __name__ == '__main__': unittest.main()
