import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload'/'APRogue.galaxy').read_text()

class Dev37VoiceAndGalaxyTests(unittest.TestCase):
    def test_fixed_reserved_keyword(self):
        self.assertIn('unitgroup spawnedBanelings;', G)
        self.assertNotRegex(G,r'(?m)^\s*unitgroup\s+wave\s*;')
    def test_preview_entrypoints(self):
        for s in ['APRG_VOTestSequence','?SlayVOTest','APRG_VOTestChat_Func',
            'APRG_VOTestAuto_Func',
            'TriggerAddEventTimePeriodic(g_aprgVOStopRealTrigger, 0.125, c_timeReal)']:
            self.assertIn(s,G)
    def test_gameplay_fixes_retained(self):
        for s in ['APRRG_NotExistingDoNotUse','APRogueSupportCrewRange005','APRG_PointNearMineralField(p, 5.0)']:
            if s=='APRRG_NotExistingDoNotUse': self.assertNotIn(s,G)
            else: self.assertIn(s,G)
    def test_real_time_sequence_and_caps(self):
        for value in ['for (i = 0; i < 2; i += 1)', 'Wait(duration + 0.5, c_timeReal)',
                      '"TTychus02Tychus00008", 7.0', '"TValerian01Raynor00043", 2.5']:
            self.assertIn(value,G)
    def test_no_global_dependency(self):
        self.assertNotIn('mods/starcoop',G.lower())
        self.assertNotIn('unitgroup wave;',G)

if __name__=='__main__':unittest.main()
