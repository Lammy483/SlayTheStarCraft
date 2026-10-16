"""Dev48 static integration checks. Actual SC2 compile and runtime require live testing."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload'/'APRogue.galaxy').read_text()
X=ET.parse(ROOT/'Payload'/'APRogueData.xml').getroot()
def f(name):
 m=re.search(r'^(?:void|bool|int|fixed|point|unit|string)\s+'+name+r'\s*\([^;]*?\)\s*\{',G,re.M)
 assert m,name
 tail=G[m.start():]
 level=0; opened=False
 for pos,ch in enumerate(tail):
  if ch=='{': level+=1;opened=True
  elif ch=='}':
   level-=1
   if opened and level==0:return tail[:pos+1]
 raise RuntimeError(name)
class Dev48(unittest.TestCase):
 def test_no_known_galaxy_compile_regressions(self):
  self.assertNotRegex(G,r'\bunitgroup\s+wave\s*;')
  self.assertNotIn('void APRG_TickNydusWorms(int player, fixed now);',G)
  self.assertIn('APRG_FindNydusSpawnPoint',G)
 def test_nydus_wave_cadence_and_lead_time(self):
  self.assertIn('g_aprgNydusNextWaveTime[slot] = now + RandomFixed(40.0, 50.0)',f('APRG_StartNydusWave'))
  tick=f('APRG_TickNydusWorms')
  self.assertIn('g_aprgPendingNydusBirthTime = now + 2.0',tick)
  self.assertIn('g_aprgNextNydusSpawnTime = g_aprgMacroReadyTime + 238.0',tick)
  self.assertIn('g_aprgNextNydusSpawnTime = now + RandomFixed(58.0, 68.0)',tick)
  self.assertEqual(tick.count('APRG_QueueCampaignVO("TTychus03Horner00009"'),1)
 def test_roachling_zombie_exclusion(self):
  self.assertIn('StringContains(unitType, "Roachling", c_stringAnywhere, c_stringNoCase)',f('APRG_NoDeathsExcluded')) if 'APRG_NoDeathsExcluded' in G else self.assertIn('StringContains(unitType, "Roachling", c_stringAnywhere, c_stringNoCase)',G)
 def test_covert_tosh_reserve_in_shared_ai(self):
  self.assertIn('(caster == g_aprgCovertTosh || caster == g_aprgTosh)',f('APRG_TryCategorizedAutonomousAbility'))
  self.assertIn('c_unitPropEnergy, c_unitPropCurrent) < 200.0',f('APRG_TryCategorizedAutonomousAbility'))
  self.assertIn('>= 200.0',f('APRG_TickCovertAssistance'))
 def test_tosh_raid_paths_and_nuke(self):
  tosh=f('APRG_TickToshAndHisBoys')
  self.assertIn('g_aprgNextToshSpectreTime = g_aprgMacroReadyTime + APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY',tosh)
  self.assertIn('UnitGetPropertyFixed(g_aprgTosh, c_unitPropEnergy, c_unitPropCurrent) >= 200.0',tosh)
  self.assertIn('g_aprgToshSpectreNextOrderTime[slot] = now + 1.0;',tosh)
  self.assertIn('APRG_ArchonImmortalPatrolDestination(g_aprgTosh, player, 20.0)',tosh)
  self.assertIn('DistanceBetweenPoints(UnitGetPosition(spec), targetPoint) > 9.0',tosh)
  self.assertIn('g_aprgNextToshSpectreTime = now + 5.0',tosh)
  self.assertIn('UnitIssueOrder(spec, castOrder, c_orderQueueReplace)',tosh)
 def test_air_bogie_voice_whitelist_and_catalog(self):
  self.assertIn('APRG_QueueCampaignVO("TRaynor03Tychus00013", 0.0);',f('APRG_TickMultipleAirBogies'))
  self.assertIn('soundId == "TRaynor03Tychus00013"',f('APRG_IsApprovedCampaignVOSoundId'))
  sounds=[x for x in X if x.tag=='CSound' and x.attrib.get('id')=='APRogueVO_TRaynor03Tychus00013']
  self.assertEqual(len(sounds),1)
  self.assertIn('traynor03tychus00013.ogg',sounds[0][0].attrib['File'].lower())
if __name__=='__main__': unittest.main()
