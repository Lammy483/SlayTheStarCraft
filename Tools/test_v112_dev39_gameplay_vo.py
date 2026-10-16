import csv
import pathlib
import re
import unittest
import xml.etree.ElementTree as ET
P=pathlib.Path(__file__).resolve().parents[1]
s=(P/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

class TestVoice39(unittest.TestCase):
 def test_reserved_keyword_fix(self):
  self.assertIn('unitgroup spawnedBanelings;',s)
  self.assertNotIn('unitgroup wave;',s)
 def test_gameplay_queues(self):
  for name in ['TTychus02Tychus00008','TTychus02Raynor00020','TTychus05Horner00013','THanson03AHorner00001','TTychus05Horner00032','TValerian01Raynor00043','THorner02Orlan00012','THorner02Orlan00019','TValerian02BAdjutant00035','TValerian02BAdjutant00017','THanson02BriefingHanson00001']:
   self.assertRegex(s,r'APRG_QueueCampaignVO\("'+name+r'",')
  self.assertIn('"TValerian01Raynor00043", 2.5',s)
 def test_horner_drop_pod_prewarning(self):
  self.assertIn('g_aprgDropPodVOCount > 0',s)
  self.assertIn('RegionCircle(landing, 8.0)',s)
  self.assertIn('g_aprgDropPodVORelease = GameGetMissionTime() + 5.0;',s)
  self.assertIn('g_aprgNextDropPodTime = g_aprgDropPodVORelease;',s)
  for n in ['15','27','31','32','36','37']:
   self.assertIn('TValerian01Horner000'+n,s)
 def test_only_archangel_tested(self):
  test=s[s.index('string APRG_VOTestId(int idx) {'):s.index('bool APRG_VOTestChat_Func(',s.index('string APRG_VOTestId(int idx) {'))]
  self.assertIn('zmission_lab02_lab02mech_123.ogg',test)
  self.assertIn('zmission_lab02_lab02mech_124.ogg',test)
  self.assertIn('i < 2',test)
  self.assertNotIn('TTychus02Tychus00008',test)
 def test_catalog_preserved(self):
  root=ET.parse(P/'Payload/APRogueData.xml').getroot()
  entries=[e for e in root if e.tag=='CSound' and e.attrib.get('id','').startswith('APRogueVO_')]
  self.assertEqual(len(entries),25)

if __name__=='__main__': unittest.main()
