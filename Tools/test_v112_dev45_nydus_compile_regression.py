"""Dev45 - exact Dev39/Dev40 Galaxy compilation regression guard."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
GALAXY=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
class Dev45NydusCompileRegression(unittest.TestCase):
    def test_invalid_unit_group_accessor_is_absent(self):
        self.assertNotRegex(GALAXY, r'\bUnitGroupUnit\s*\(')
    def test_uses_supported_indexed_accessor(self):
        self.assertIn('anchor = UnitGroupUnitFromEnd(buildings, j);', GALAXY)
    def test_still_uses_random_selection_of_valid_anchors(self):
        self.assertIn('j = RandomInt(1, UnitGroupCount(buildings, c_unitCountAlive));',GALAXY)
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))',GALAXY)
    def test_nydus_works_with_all_later_effects(self):
        for name in ('APRG_TickNydusWorms','APRG_TickPointDefenseDrones',
                     'APRG_TickCovertAssistance','APRG_TickMultipleAirBogies',
                     'APRG_HybridResearchStructureDeath','APRG_TrySpawnFiftyImmortals'):
            self.assertIn(name+'(', GALAXY)
        self.assertIn('APRG_QueueCampaignVO("TTychus03Horner00033", 0.0);', GALAXY)
    def test_no_prior_wave_keyword_regression(self):
        self.assertNotRegex(GALAXY, r'(?m)^\s*unitgroup\s+wave\s*;')
if __name__=='__main__': unittest.main()
