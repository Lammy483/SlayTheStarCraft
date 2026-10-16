import pathlib, unittest, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
G=(ROOT/'Payload'/'APRogue.galaxy').read_text(encoding='utf8')
DATA=(ROOT/'Payload'/'APRogueData.xml').read_text(encoding='utf8')

def body(name):
    m=re.search(r"^(?:void|bool|point|unit|int|fixed|string)\s+"+name+r"\s*\([^;]*?\)\s*\{",G,re.M)
    assert m,name
    start=G.index('{',m.start()); d=1
    for i in range(start+1,len(G)):
        if G[i]=='{':d+=1
        elif G[i]=='}':
            d-=1
            if d==0:return G[start:i+1]
    raise AssertionError(name)

class Dev50Fixes(unittest.TestCase):
    def test_pdd_is_single_deployment_per_mission(self):
        f=body('APRG_TickPointDefenseDrones')
        self.assertIn('g_aprgPointDefenseSpawned = true;',f)
        self.assertIn('now < g_aprgMacroReadyTime + 10.0',f)
        self.assertNotIn('g_aprgNextPointDefenseScan',G)
        self.assertNotIn('g_aprgPointDefenseProtected',G)
        self.assertEqual(f.count('UnitCreate(1, "PointDefenseDrone"'),1)
        self.assertIn('g_aprgPointDefenseSpawned = false;',G)
    def test_kerrigan_fallback_remains_close_to_base(self):
        f=body('APRG_KerriganSafeHomePoint')
        self.assertIn('pass < 2',f)
        self.assertIn('if (pass == 0 && worker != null &&',f)
        self.assertIn('APRG_PlayerSafeSpawnPoint(player,',f)
        self.assertIn('PointWithOffsetPolar(homePoint, 5.0',f)
        self.assertIn('APRG_PointNearMineralField(candidate, 4.0)',f)
    def test_tosh_regen_includes_extra_one_at_home(self):
        f=body('APRG_TickCovertAssistance')
        self.assertIn('regenRate = 0.5;',f)
        self.assertIn('regenRate += 1.0;',f)
        self.assertIn('<= 8.0',f)
        self.assertIn('hp + regenRate * MinF(elapsed, 2.0)',f)
    def test_air_bogie_voice_uses_local_catalog_any_index_and_audio(self):
        self.assertIn('APRG_QueueCampaignVO("TRaynor03Tychus00013", 0.0);',body('APRG_TickMultipleAirBogies'))
        self.assertIn('nativeId == "TRaynor03Tychus00013"',body('APRG_ResolveSelectedCampaignVOSound'))
        f=body('APRG_PlayWarfieldVOImmediate')
        self.assertIn('suffix == "TRaynor03Tychus00013"',f)
        self.assertIn('SoundLink(soundId, c_soundIndexAny)',f)
        self.assertIn('suffix != "TRaynor03Tychus00013" && portraitModel',f)
        self.assertIn('SoundPlay(line, PlayerGroupAll(), 100.0, 0.0);',f)
        self.assertIn('traynor03tychus00013.ogg',DATA.lower())
    def test_previous_three_race_repair_preserved(self):
        self.assertNotIn('void APRG_TickNydusWorms(int player, fixed now);',G)
        self.assertNotRegex(G,r'\bunitgroup\s+wave\s*;')
    def test_native_spectre_nukes_preserved(self):
        self.assertIn('AbilityCommand("TacNukeStrike", 0)',G)
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);',G)
if __name__=='__main__':unittest.main()
