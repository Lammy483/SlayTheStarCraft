"""Dev34 isolation and targeted spawn/mercenary regression checks."""
from pathlib import Path
import unittest, re, json

ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload'/'APRogue.galaxy').read_text()


def body(name):
    m=re.search(r'^(?:void|bool|point|fixed|int|string)\s+'+re.escape(name)+r'\([^)]*\)\s*\{',G,re.M)
    if not m:raise AssertionError('function missing '+name)
    pos=G.index('{',m.start()); level=1
    for i in range(pos+1,len(G)):
        if G[i]=='{':level+=1
        if G[i]=='}':
            level-=1
            if level==0:return G[pos+1:i]
    raise AssertionError('unbalanced '+name)

class Dev34Recovery(unittest.TestCase):
    def test_no_experimental_startup_or_global_dependencies(self):
        self.assertIn('APRG_VOTestSequence', G)
        self.assertIn('g_aprgVOTestAutoTrigger', G)
        self.assertIn('APRG_QueueCampaignVO("THorner02Han00022", 0.0)',G)
        self.assertIn('APRG_QueueCampaignVO("THorner01Horner00019", 0.0)',G)
        self.assertNotIn('UnitHasAttribute(',G)
        self.assertNotIn('mods/starcoop',G.lower())
    def test_valid_voice_local_declaration_block(self):
        f=body('APRG_PlayWarfieldVOImmediate')
        self.assertLess(f.index('bool campaignLine;'), f.index('sound playedSound'))
        self.assertIn('campaignLine = APRG_IsApprovedCampaignVOSoundId(suffix)', f)
    def test_torrasque_validates_each_respawn(self):
        self.assertIn('APRG_PointNearMineralField(p, 5.0)',body('APRG_TorrasqueSpawnPointClear'))
        self.assertIn('APRG_TorrasqueSpawnPointClear(p, player)',body('APRG_FindTorrasqueSpawnPoint'))
        self.assertIn('APRG_FindTorrasqueSpawnPoint(player)',body('APRG_SpawnTorrasque'))
    def test_odin_safe_retry_and_no_second_spawn(self):
        f=body('APRG_TickDelayedOdin')
        self.assertIn('APRG_PointNearMineralField(p, 5.0)',f)
        self.assertIn('spawnAttempt < 12',f)
        self.assertIn('g_aprgDelayedOdinSpawned',f)
        self.assertIn('g_aprgMacroReadyTime + 840.0',f)
        self.assertLess(f.index('!APRG_PointNearMineralField(p, 5.0)'),f.index('UnitCreate(1, "Odin"'))
    def test_jackson_range_is_targeted_and_persistent(self):
        f=body('APRG_ApplyMercenaryUnitUpgrades')
        self.assertIn('unitType == "DukesRevenge" || unitType == "AP_DukesRevenge"',f)
        self.assertIn('"APRG_JacksonSniper_" + IntToString(UnitGetTag(u))',f)
        self.assertIn('DataTableGetInt(true, key + "_AppliedStacks")',f)
        self.assertIn('UnitBehaviorAdd(u, "APRogueSupportCrewRange005", u, wc - wi)',f)
        self.assertIn('if (sniperStacks > 0)',f)
        self.assertIn('CatalogFieldValueModify(c_gameCatalogWeapon, weaponType, "Range"',f)
        data=(ROOT/'Payload'/'APRogueData.xml').read_text()
        self.assertIn('CBehaviorBuff id="APRogueSupportCrewRange005"',data)
        self.assertIn('<Modification WeaponRange="0.05"/>',data)
    def test_manifest_matches_actual_prebuilt_binary(self):
        m=json.loads((ROOT/'launcher_manifest.json').read_text())
        s=(ROOT/'Tools'/'slay_launcher_windows.go').read_text()
        self.assertIn('runtimeRevision = "'+m['runtime_revision']+'"',s)
        self.assertIn('v1.2.0',m['runtime_revision'])

if __name__=='__main__':unittest.main()
