import csv
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GAL=(ROOT/'Payload'/'APRogue.galaxy').read_text(encoding='utf-8')
RUN=(ROOT/'Payload'/'slay_the_starcraft.py').read_text(encoding='utf-8')
GEN=(ROOT/'Payload'/'generate_slay_run.py').read_text(encoding='utf-8')

class TestHybridResearch(unittest.TestCase):
    def test_catalog(self):
        with (ROOT/'Payload'/'EFFECT_CATALOG.csv').open(newline='',encoding='utf-8') as f:
            matches=[row for row in csv.DictReader(f) if row['Title']=='Hybrid Research']
        self.assertEqual(len(matches),1)
        row=matches[0]
        self.assertEqual(row['Mutation or Blessing'],'Mutation')
        self.assertEqual(row['Description'],'Each enemy structure releases a random hybrid when destroyed')
        self.assertEqual(row['Severity'],'4')

    def test_bit_unique_and_active_in_galaxy(self):
        self.assertIn('const int APRG_EXT3_MUT_HYBRID_RESEARCH = 268435456;',GAL)
        self.assertIn('EFFECT_BANK_BITS["hybrid_research"] = (4, 268435456)',RUN)
        self.assertIn('"hybrid_research": 4',GEN)
        self.assertIn('"hybrid_research": 4',RUN)
        self.assertIn('APRG_HasExtension3(APRG_EXT3_MUT_HYBRID_RESEARCH)',GAL)
        self.assertEqual(len(re.findall(r'^const int APRG_EXT3_\w+ = 268435456;',GAL,re.M)),1)

    def test_probability_ranges(self):
        f=GAL.split('string APRG_HybridResearchChooseType() {',1)[1].split('\n}\n',1)[0]
        for phrase in ['RandomInt(1, 100)', 'roll <= 40','roll <= 80','roll <= 90','roll <= 95',
                       '"HybridReaver"','"HybridDestroyer"','"HybridNemesis"','"HybridBehemoth"','"HybridDominator"']:
            self.assertIn(phrase,f)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, hybridType)',f)

    def test_structure_death_filter_and_attack_ai(self):
        death=GAL.split('bool APRG_Death_Func(',1)[1].split('bool APRG_',1)[0]
        self.assertIn('APRG_HasExtension3(APRG_EXT3_MUT_HYBRID_RESEARCH)',death)
        self.assertIn('libNtve_gf_PlayerIsEnemy(owner, player, libNtve_ge_PlayerRelation_Enemy)',death)
        self.assertIn('UnitTypeTestAttribute(unitType, c_unitAttributeStructure)',death)
        self.assertIn('APRG_IsSlayStructureEffectEligibleType(unitType)',death)
        self.assertIn('APRG_HybridResearchStructureDeath(p, owner, player);',death)
        self.assertIn('APRG_AddHostileRaiders(spawned, deathPoint, player);',GAL)
        self.assertIn('TriggerAddEventUnitDied(g_aprgDeathTrigger, null)',GAL)

    def test_defense_exclusions_both_paths(self):
        self.assertIn('effect == "hybrid_research" and bool(data.get("timed_defense", False))',RUN)
        self.assertIn('forbidden_mutators.add("hybrid_research")',GEN)
        self.assertIn('"hybrid_research", "purifier"',RUN)  # Crucible safeguards

    def test_no_reserved_wave_declaration(self):
        self.assertNotRegex(GAL,r'\bunitgroup\s+wave\s*;')

if __name__=='__main__':unittest.main()
