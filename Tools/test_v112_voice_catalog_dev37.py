"""Dev39 preservation: selected VO catalog and now game-event playback."""
import re
import unittest
from pathlib import Path
G=(Path(__file__).resolve().parents[1]/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

class CampaignVoiceTest(unittest.TestCase):
    def test_all_new_requests_registered(self):
        ids=['TTychus02Tychus00008','TTychus02Raynor00020','TTychus05Horner00013',
        'THanson03AHorner00001','TTychus05Horner00032','TValerian01Raynor00043',
        'THorner02Orlan00012','THorner02Orlan00019','TValerian02BAdjutant00035',
        'TValerian02BAdjutant00017','THanson02BriefingHanson00001']
        for sound in ids:
            self.assertIn('soundId == "'+sound+'"',G)
            self.assertIn(sound,G)
    def test_real_time_archangel_only(self):
        self.assertIn('for (i = 0; i < 2; i += 1)',G)
        self.assertIn('Wait(7.0, c_timeReal)',G)
        self.assertIn('Wait(duration + 0.5, c_timeReal)',G)
        self.assertIn('"TValerian01Raynor00043", 2.5',G)
    def test_no_mission_dependency_changes(self):
        self.assertNotIn('Mods\\StarCoop',G)
        self.assertNotIn('TriggerAddEventTimePeriodic(g_aprgVOTestAutoTrigger, 1.0, c_timeGame)',G)
        self.assertNotIn('TriggerAddEventTimePeriodic(g_aprgVOTestAutoTrigger, 1.0, c_timeReal)',G)
    def test_portrait_and_missing_diagnostics(self):
        for key in ('PORTRAIT','AUDIO REGISTERED','MISSING SOUND','SoundPortraitModel(line)',
          'TransmissionLastSent()','SoundLastPlayed()'):
            self.assertIn(key,G)
    def test_exact_hots_assets(self):
        for name in ('zmission_lab02_lab02mech_123.ogg','zmission_lab02_lab02mech_124.ogg'):
            self.assertIn(name,G)
        self.assertIn('APRG_VOTestFindHotSByExactAsset(id)',G)
    def test_other_voice_lines_during_test_defer(self):
        self.assertIn('if (g_aprgVOTestRunning) { return; }',G)
        self.assertIn('TimerGetRemaining(g_aprgVONextRealTimer)',G)
        self.assertIn('TimerStart(g_aprgVONextRealTimer, duration + 0.35, false, c_timeReal)',G)

if __name__=='__main__':unittest.main()
