import pathlib
import unittest
import xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]

class VoiceCatalog38(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gal=(ROOT/"Payload/APRogue.galaxy").read_text(encoding="utf-8")
        cls.root=ET.parse(ROOT/"Payload/APRogueData.xml").getroot()
        cls.inst=(ROOT/"Payload/install_slay.py").read_text(encoding="utf-8")
    def test_catalog_count_and_parent(self):
        sound=[x for x in self.root if x.tag=="CSound" and x.attrib.get("id", "").startswith("APRogueVO_")]
        self.assertEqual(len(sound),25)
        self.assertEqual(sum(x.attrib.get("parent")=="Campaign2D" for x in sound),23)
        self.assertEqual(sum(x.attrib.get("parent")=="VO" for x in sound),2)
    def test_audio_paths(self):
        for x in self.root:
            if x.tag=="CSound" and x.attrib.get("id","").startswith("APRogueVO_"):
                asset=x.find('AssetArray')
                self.assertIsNotNone(asset)
                self.assertIn('LocalizedData\\Sounds\\',asset.attrib['File'])
                self.assertTrue(asset.attrib['File'].endswith('.ogg'))
    def test_lookup_and_native_fallback(self):
        self.assertIn('APRG_ResolveSelectedCampaignVOSound', self.gal)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogSound, nativeId)', self.gal)
        self.assertIn('localId = "APRogueVO_" + nativeId;', self.gal)
        self.assertIn('soundId = APRG_ResolveSelectedCampaignVOSound(suffix)', self.gal)
    def test_keyword_and_dependencies(self):
        self.assertIn('unitgroup spawnedBanelings;',self.gal)
        self.assertNotIn('unitgroup wave;',self.gal)
        self.assertNotIn('file:Campaigns\\Liberty.SC2Campaign',self.inst)

if __name__=='__main__': unittest.main()
