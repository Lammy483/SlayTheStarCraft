"""Dev44 regression checks: catalog, queued voice, rate limit, and UI rename."""
from pathlib import Path
import csv
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'Payload'
G=(P/'APRogue.galaxy').read_text(encoding='utf-8')
RUN=(P/'slay_the_starcraft.py').read_text(encoding='utf-8')
GEN=(P/'generate_slay_run.py').read_text(encoding='utf-8')

class Dev44NydusVoRename(unittest.TestCase):
    def test_all_three_catalog_entries_include_exact_asset_path(self):
        catalog=ET.parse(P/'APRogueData.xml').getroot()
        for ident,filename in (
            ('TTychus03Horner00009','ttychus03horner00009.ogg'),
            ('TValerian03Adjutant00039','tvalerian03adjutant00039.ogg'),
            ('TTychus03Horner00033','ttychus03horner00033.ogg'),
        ):
            entries=[e for e in catalog if e.tag=='CSound' and e.get('id')=='APRogueVO_'+ident]
            self.assertEqual(len(entries),1)
            self.assertEqual(entries[0].get('parent'),'Campaign2D')
            self.assertEqual(entries[0].find('AssetArray').get('File'),
                             'LocalizedData\\Sounds\\TerranVO\\CampaignVO\\'+filename)
            self.assertIn('soundId == "'+ident+'"',G)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogSound, nativeId)',G)
        self.assertIn('localId = "APRogueVO_" + nativeId;',G)

    def test_appearance_voice_after_real_mutation_worm_creation(self):
        start=G.index('void APRG_TickNydusWorms(int player, fixed now) {')
        body=G[start:G.index('\n}\n',start)]
        voice=body.index('APRG_QueueCampaignVO("TTychus03Horner00009", 0.0);')
        countdown=body.index('g_aprgPendingNydusBirthTime = now + 2.0;')
        birth=body.index('created = UnitCreate(1, "NydusCanal"')
        added=body.index('g_aprgNydusSpawnCount += 1;')
        cooldown=body.index('g_aprgNextNydusSpawnTime = now + RandomFixed(58.0, 68.0);')
        self.assertTrue(countdown < voice < birth < added < cooldown)
        self.assertIn('APRG_QueueCampaignVO("TValerian03Adjutant00039", 0.0);',body)
        self.assertIn('if (RandomInt(0, 1) == 0)',body)

    def test_live_mutation_worm_count_and_four_minute_cooldown(self):
        start=G.index('void APRG_TickNydusWorms(int player, fixed now) {')
        body=G[start:G.index('\n}\n',start)]
        for clause in ('int aliveWorms;',
                       'if (now >= g_aprgNextNydusThreeWormVOCheck)',
                       'g_aprgNextNydusThreeWormVOCheck = now + 5.0;',
                       'for (i = 0; i < g_aprgNydusSlotCount; i += 1)',
                       'worm = g_aprgNydusWorms[i];',
                       'if (worm != null && UnitIsAlive(worm)) { aliveWorms += 1; }',
                       'aliveWorms >= 3 && now - g_aprgLastNydusThreeWormVOTime >= 240.0',
                       'APRG_QueueCampaignVO("TTychus03Horner00033", 0.0);',
                       'g_aprgLastNydusThreeWormVOTime = now;'):
            self.assertIn(clause,body)
        self.assertIn('g_aprgLastNydusThreeWormVOTime = -10000.0;',G)
        self.assertIn('g_aprgNextNydusThreeWormVOCheck = -1.0;',G)
        self.assertNotRegex(G,r'(?m)^\s*unitgroup\s+wave\s*;')

    def test_mutation_is_named_immortals_but_still_30_and_id_stable(self):
        with (P/'EFFECT_CATALOG.csv').open(encoding='utf-8',newline='') as f:
            matching=[row for row in csv.DictReader(f) if row['Title']=='Immortals']
        self.assertEqual(len(matching),1)
        self.assertEqual(matching[0]['Description'],'There are 30 immortals patrolling around the map')
        self.assertEqual(matching[0]['Severity'],'3')
        self.assertEqual(matching[0]['Mutation or Blessing'],'Mutation')
        self.assertIn('EFFECT_DISPLAY_NAMES["fifty_immortals"] = "Immortals"',RUN)
        self.assertIn('EFFECT_BANK_BITS["fifty_immortals"] = (4, 536870912)',RUN)
        self.assertIn('"fifty_immortals": 3',GEN)
        self.assertIn('result = result + "Immortals";',G)
        self.assertIn('g_aprgImmortalPatrolsSpawned >= 30',G)
        self.assertNotIn('result = result + "50 immortals";',G)

if __name__=='__main__':
    unittest.main()
