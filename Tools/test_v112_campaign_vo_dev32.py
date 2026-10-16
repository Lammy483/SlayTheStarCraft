"""Dev32 scripted WoL voice assignments and bounded playback tests."""
import re
import unittest
from pathlib import Path
G = (Path(__file__).resolve().parents[1]/"Payload/APRogue.galaxy").read_text(encoding="utf-8")

def body(name):
    m = re.search(r"^(?:void|bool|string|unitgroup)\s+"+re.escape(name)+r"\s*\([^)]*\)\s*\{",G,re.M)
    if not m: raise AssertionError("Missing function: "+name)
    start=G.index("{",m.start()); level=1
    for i in range(start+1,len(G)):
        if G[i]=="{": level+=1
        elif G[i]=="}":
            level-=1
            if level==0:return G[start+1:i]
    raise AssertionError("Unclosed function: "+name)

class SelectedVOTests(unittest.TestCase):
    def test_exact_sound_ids_and_no_generic_scan(self):
        f=body('APRG_QueueCampaignVO')
        self.assertIn('"THorner01Horner00019"', body('APRG_IsApprovedCampaignVOSoundId'))
        self.assertIn('"THorner02Han00022"', body('APRG_IsApprovedCampaignVOSoundId'))
        self.assertNotIn('CatalogEntryCount', f)
        f=body('APRG_PlayWarfieldVOImmediate')
        self.assertIn('soundId = APRG_ResolveSelectedCampaignVOSound(suffix)',f)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogSound, nativeId)',body('APRG_ResolveSelectedCampaignVOSound'))
        self.assertIn('SoundLink(soundId, 0)',f)
        self.assertIn('SoundLink(soundId, c_soundIndexAny)',f)

    def test_mira_purchase_only(self):
        f=body('APRG_TickMiraMercenaries')
        self.assertLess(f.index('minerals < 6000'),f.index('APRG_QueueCampaignVO("THorner02Han00022", 0.0)'))
        self.assertLess(f.index('g_aprgMiraMercenariesPurchased = true'),f.index('APRG_QueueCampaignVO("THorner02Han00022", 0.0)'))

    def test_kill_team_single_initial_spawn(self):
        f=body('APRG_TickMarauderKillTeams')
        self.assertIn('APRG_QueueCampaignVO("THorner01Horner00019", 0.0)',f)
        self.assertLess(f.index('g_aprgMarauderKillTeamsSpawned = true'),f.index('APRG_QueueCampaignVO'))
        self.assertLess(f.index('APRG_QueueCampaignVO'),f.index('if (now < g_aprgNextMarauderKillTeamRetargetTime)'))
        self.assertIn('UnitGroupCount(g_aprgMarauderKillTeamUnits, c_unitCountAlive) > 0',f)

    def test_bounded_playback_doesnt_clear_others(self):
        f=body('APRG_TickWarfieldVOQueue')
        self.assertIn('TransmissionClear(g_aprgVOStopTransmission)', body('APRG_VORealStop_Func'))
        self.assertIn('SoundStop(g_aprgVOStopSound, false)', body('APRG_VORealStop_Func'))
        self.assertNotIn('TransmissionClearAll', f)
        f=body('APRG_PlayWarfieldVOImmediate')
        self.assertIn('maxSeconds > 0.0 && maxSeconds < duration', f)
        self.assertIn('TransmissionLastSent()', f)
        self.assertIn('SoundLastPlayed()', f)
        self.assertIn('TimerStart(g_aprgVOStopRealTimer, maxSeconds, false, c_timeReal)', f)
        self.assertIn('g_aprgVOStopAt = maxSeconds', f)

    def test_no_new_dependencies(self):
        self.assertNotIn('mods/starcoop',G.lower())
        f=body('APRG_QueueCampaignVO')
        self.assertNotIn('Dependency',f)

if __name__=='__main__':unittest.main()
