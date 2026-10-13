"""Spider mines should not count as structures for Slay blessings."""
import unittest
from pathlib import Path

GAL=(Path(__file__).parents[1]/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

def body(function_name):
    for kind in ['bool','void','unitgroup']:
        prefix=kind+' '+function_name+'('
        idx=GAL.find(prefix)
        while idx>=0:
            begin=GAL.find('{',idx)
            terminator=GAL.find(';',idx)
            if terminator>=0 and terminator<begin:
                idx=GAL.find(prefix,terminator+1)
                continue
            break
        if idx>=0:
            depth=1
            at=begin+1
            while depth and at<len(GAL):
                if GAL[at]=='{':depth+=1
                if GAL[at]=='}':depth-=1
                at+=1
            return GAL[begin:at]
    raise AssertionError('missing '+function_name)

class SpiderMineStructureExclusions(unittest.TestCase):
    def test_all_spider_mine_type_variants(self):
        self.assertIn('StringContains(unitType, "SpiderMine", c_stringAnywhere, c_stringNoCase)',body('APRG_IsSpiderMineType'))
        self.assertIn('!APRG_IsSpiderMineType(unitType)',body('APRG_IsSlayStructureEffectEligibleType'))

    def test_shared_structure_collections_exclude_mines(self):
        for name in ['APRG_PlayerStructures','APRG_EnemyStructures','APRG_EnemyTargetableStructures','APRG_EnemyTargetableGroundStructures','APRG_PlayerTargetableStructures']:
            with self.subTest(collection=name):
                self.assertIn('!APRG_IsSlayStructureEffectEligibleType(UnitGetType(u))',body(name))

    def test_building_overcharge_excludes_mines_and_existing_proxies(self):
        content=body('APRG_ApplyBuildingOvercharge')
        self.assertEqual(content.count('APRG_IsSpiderMineType(UnitGetType(u))'),2)
        self.assertIn('UnitRemove(proxy)',content)
        self.assertIn('structures = APRG_PlayerStructures(player)',content)

    def test_mines_not_counted_for_building_clearance(self):
        self.assertIn('!APRG_IsSlayStructureEffectEligibleType(UnitGetType(allied))',body('APRG_PointNearPlayerOrAlliedBuilding'))

    def test_nuclear_structures_does_not_count_mines(self):
        self.assertIn('APRG_IsSlayStructureEffectEligibleType(unitType)',GAL)

if __name__=='__main__':unittest.main()
