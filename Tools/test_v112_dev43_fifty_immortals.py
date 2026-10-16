import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'Payload'
GAL = (PAYLOAD / 'APRogue.galaxy').read_text(encoding='utf-8')
RUN = (PAYLOAD / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GEN = (PAYLOAD / 'generate_slay_run.py').read_text(encoding='utf-8')

class TestFiftyImmortals(unittest.TestCase):
    def test_metadata_exactly_as_supplied(self):
        with (PAYLOAD / 'EFFECT_CATALOG.csv').open(newline='', encoding='utf-8') as h:
            rows = [row for row in csv.DictReader(h) if row['Title'] == 'Immortals']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {'Title':'Immortals','Mutation or Blessing':'Mutation','Description':'There are 30 immortals patrolling around the map','Severity':'3'})

    def test_effect_bit_unique_and_transport(self):
        self.assertIn('const int APRG_EXT3_MUT_FIFTY_IMMORTALS = 536870912;', GAL)
        self.assertIn('EFFECT_BANK_BITS["fifty_immortals"] = (4, 536870912)',RUN)
        self.assertEqual(len(re.findall(r'^const int APRG_EXT3_\w+ = 536870912;', GAL, re.M)),1)
        self.assertIn('APRG_HasExtension3(APRG_EXT3_MUT_FIFTY_IMMORTALS)', GAL)
        self.assertIn('"fifty_immortals": 3', RUN)
        self.assertIn('"fifty_immortals": 3', GEN)
        self.assertIn('EFFECT_DISPLAY_NAMES["fifty_immortals"] = "Immortals"',RUN)

    def test_30_immortals_with_archon_logic(self):
        f = GAL.split('void APRG_TrySpawnFiftyImmortals(int player) {', 1)[1].split('\n}\n',1)[0]
        for phrase in ['g_aprgMacroReadyTime + 120.0', 'g_aprgImmortalPatrolsSpawned >= 30',
                       'CatalogEntryIsValid(c_gameCatalogUnit, "Immortal")',
                       'APRG_FindStaticPatrolGroundPointWithBuildingClearance(player, 15.0)',
                       'APRG_FindHostileOwnerNearPoint(player, p)',
                       'UnitCreate(1, "Immortal", c_unitCreateIgnorePlacement, owner, p, libNtve_gf_RandomAngle())',
                       'APRG_RegisterMutationEnemyGroup(created)',
                       'g_aprgImmortalPatrolsSpawned += 1',
                       'UnitGroupAddUnitGroup(g_aprgHostilePatrollers, created)',
                       'APRG_RetargetHostilePatrollers()']:
            self.assertIn(phrase, f)
        self.assertIn('APRG_TrySpawnFiftyImmortals(player);',GAL)
        self.assertEqual(GAL.count('APRG_TrySpawnFiftyImmortals(player);'),1)

    def test_archon_mutations_unchanged(self):
        self.assertIn('int g_aprgDarkArchonsSpawned = 0;',GAL)
        self.assertIn('if (APRG_HasExtension4(APRG_EXT4_MUT_DARK_ARCHONS_X5)) { targetCount = 50; }', GAL)
        self.assertIn('g_aprgDarkArchonsSpawned += 1;',GAL)
        self.assertIn('APRG_TrySpawnDarkArchons(player);',GAL)

    def test_no_broken_reserved_variable(self):
        self.assertNotRegex(GAL,r'\bunitgroup\s+wave\s*;')

if __name__=='__main__': unittest.main()
