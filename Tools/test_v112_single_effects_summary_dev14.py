"""One player-facing Galaxy effects summary after base establishment.

Protect against the Dev6 delayed replay and the fast/slow startup ticks
producing multiple copies of mutations and blessings in the game chat.
"""
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

class MissionSummaryDev14(unittest.TestCase):
    def test_one_display_callsite_in_galaxy(self):
        self.assertEqual(G.count('APRG_DisplayActiveEffects(player);'),1)
        self.assertEqual(G.count('g_aprgEffectsSummaryAfterBaseDisplayed = true;'),1)
        self.assertNotIn('g_aprgEffectsSummaryDisplayed',G)

    def test_only_after_base_established_and_three_second_delay(self):
        tick=G.split('bool APRG_Tick_Func(',1)[1].split('void APRogue_Init(',1)[0]
        self.assertIn('APRG_UpdateMacroBaseReady(player);',tick)
        self.assertRegex(tick,r'if \(!g_aprgEffectsSummaryAfterBaseDisplayed && APRG_PlayerMacroBaseReady\(player\) &&\s*now >= g_aprgMacroReadyTime \+ 3\.0\)')
        self.assertIn('APRG_DisplayActiveEffects(player);',tick)
        self.assertLess(tick.index('APRG_UpdateMacroBaseReady(player);'),tick.index('APRG_DisplayActiveEffects(player);'))

    def test_flag_resets_on_new_mission_only(self):
        load=G.split('bool APRG_Load_Func(',1)[1].split('bool APRG_',1)[0]
        self.assertIn('g_aprgEffectsSummaryAfterBaseDisplayed = false;',load)
        self.assertNotIn('g_aprgEffectsSummaryAfterBaseDisplayed = false;', G.split('bool APRG_FastBoonTick_Func(',1)[1].split('bool APRG_',1)[0])

    def test_two_lines_in_each_single_summary(self):
        block=G.split('void APRG_DisplayActiveEffects(',1)[1].split('int APRG_GetPrimaryPlayer(',1)[0]
        self.assertIn('"[Slay] Mutations: "',block)
        self.assertIn('"[Slay] Blessings: "',block)
        self.assertEqual(block.count('UIDisplayMessage('),2)

if __name__ == '__main__':
    unittest.main()
