"""Dev28: Lab Rat exclusion, hostile Baneling attack AI, native Zagara Commander."""
from pathlib import Path
import re
import unittest
from test_v112_artanis_commander_dev18 import load_dependency_picker

ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
P=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')


def function(name):
    m=re.search(r'^(?:bool|void|string|point|unit)\s+'+re.escape(name)+r'\([^)]*\)\s*\{',G,re.M)
    if not m:raise AssertionError('missing function '+name)
    a=G.index('{',m.start());depth=0
    for p in range(a,len(G)):
        if G[p]=='{':depth+=1
        if G[p]=='}':
            depth-=1
            if depth==0:return G[a:p+1]
    raise AssertionError('Unclosed '+name)

class Dev28LabRatZagara(unittest.TestCase):
    def test_lab_rat_position_guard_has_strict_15_radius(self):
        src=function('APRG_LabRatEnemySpawnAllowed')
        self.assertIn('APRG_MISSION_FLAG_LAB_RAT_OPENING',src)
        self.assertIn('APRG_FindPlayerHomeStructure(player)',src)
        self.assertIn('DistanceBetweenPoints(candidate, UnitGetPosition(home)) >= 15.0',src)
        self.assertIn('return true;',src) # unchanged other missions

    def test_lab_rat_safe_ground_spawn_never_falls_back_inside_base(self):
        src=function('APRG_FindHostileGroundPointNear')
        self.assertIn('APRG_LabRatEnemySpawnAllowed(candidate, player)',src)
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))',src)
        self.assertIn('APRG_MAX_POINT_ATTEMPTS * 2',src)
        self.assertIn('return null;',src)
        odin=function('APRG_TickDelayedOdin')
        self.assertIn('APRG_FindHostileGroundPointNear(player, UnitGetPosition(anchor)',odin)
        self.assertIn('if (p == null || !APRG_LabRatEnemySpawnAllowed(p, player)) { return; }',odin)
        self.assertNotIn('p = UnitGetPosition(anchor);',odin)

    def test_other_hostile_spawn_searches_respect_lab_rat(self):
        for fn in ('APRG_FindRaidOriginGroundPoint','APRG_FindRaidOriginAirPoint','APRG_FindHeroPatrolOrigin','APRG_FindStaticPatrolAirPoint'):
            self.assertIn('APRG_LabRatEnemySpawnAllowed(candidate, player)',function(fn),fn)

    def test_banelings_attack_move_and_reacquire_buildings_and_units(self):
        src=function('APRG_RetargetZagaraBanelings')
        self.assertIn('APRG_NearestPathablePlayerStructureFromGroup',src)
        self.assertIn('APRG_PlayerMobileUnits',src)
        self.assertIn('UnitPathableToPoint',src)
        self.assertIn('APRG_OrderBanelingStreamAttackMove',src)
        self.assertNotIn('APRG_OrderAttackMove(',src)
        tick=function('APRG_TickZagarasBanelings')
        self.assertIn('g_aprgNextZagaraBanelingRetargetTime = now + 1.0;',tick)

    def test_baneling_wave_keeps_100_and_distributes_spawns(self):
        src=function('APRG_TickZagarasBanelings')
        self.assertIn('batch < 5',src)
        self.assertIn('UnitCreate(20, "Baneling"',src)
        self.assertIn('initialSpawnPoint = APRG_FindHostileGroundPointNear',src)
        self.assertIn('spawnPoint = initialSpawnPoint',src)
        self.assertIn('AISetUnitScriptControlled(baneling, false)',src)
        self.assertIn('UnitGroupAddUnitGroup(g_aprgZagaraBanelingUnits, spawnedBanelings)',src)

    def test_zagara_prefers_campaign_id_but_allows_roster_fallback(self):
        lookup=function('APRG_ZagaraHeroType')
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, "ZaGara")',lookup)
        self.assertIn('return "ZaGara"',lookup)
        self.assertNotIn('return "Zagara"',lookup)
        self.assertIn('if (index == 18) { return APRG_ZagaraHeroType(); }',function('APRG_HeroCandidate'))
        selector=function('APRG_FindValidHeroTypeFromIndex')
        self.assertIn('if (preferredIndex == 18 || preferredIndex == 17)',selector)
        self.assertIn('APRG_FindValidCommanderHeroFallbackExcept("ZaGara")',selector)
        self.assertLess(selector.index('preferredIndex == 18'),selector.index('return APRG_FindValidCommanderHeroType()'))
        spawn=function('APRG_GiveGeneralIfReady')
        self.assertIn('heroType == "ZaGara"',spawn)
        self.assertIn('g_aprgCommanderHeroType == "ZaGara"',spawn)
        self.assertIn('Zagara could not spawn',spawn)

    def test_hot_s_catalog_requested_only_when_necessary(self):
        self.assertEqual(load_dependency_picker(18),'swarm')
        self.assertEqual(load_dependency_picker(18,'Heart of the Swarm'),'base')
        self.assertEqual(load_dependency_picker(18,'Legacy of the Void'),'swarm')
        self.assertEqual(load_dependency_picker(7),'base')
        self.assertEqual(load_dependency_picker(9),'void')
        self.assertEqual(load_dependency_picker(18,name='Safe Haven'),'base')

if __name__=='__main__':unittest.main()
