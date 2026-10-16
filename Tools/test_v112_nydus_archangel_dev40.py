from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')
CLIENT = (ROOT / 'Payload' / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GENERATOR = (ROOT / 'Payload' / 'generate_slay_run.py').read_text(encoding='utf-8')
CATALOG = (ROOT / 'Payload' / 'EFFECT_CATALOG.csv').read_text(encoding='utf-8')

class Dev40NydusAndArchangel(unittest.TestCase):
    def test_archangel_prefers_original_catalog(self):
        func = GALAXY.split('string APRG_VOTestFindHotSByExactAsset(string audioFilename) {', 1)[1].split('\n}\n', 1)[0]
        self.assertIn('CatalogEntryGet(c_gameCatalogSound, i)',func)
        self.assertIn('"AssetArray[0].File"',func)
        self.assertLess(func.index('count = CatalogEntryCount'),func.index('if (fallbackId != ""'))
        self.assertIn('entry == fallbackId',func)
    def test_nydus_bit_and_severity(self):
        self.assertIn('const int APRG_EXT3_MUT_NYDUS_WORMS = 1;',GALAXY)
        self.assertIn('EFFECT_BANK_BITS["nydus_worms"] = (4, 1)',CLIENT)
        self.assertIn('GOLDEN_GOOSE_MUTATIONS["nydus_worms"] = 3',CLIENT)
        self.assertIn('MUTATORS["nydus_worms"] = 3',GENERATOR)
        self.assertIn('Nydus Worms,Mutation,Nydus worms periodically spawn to send units towards your base,3',CATALOG)
    def test_templars_charge_exclusion(self):
        self.assertIn('mission_name.casefold().startswith("templar\'s charge")',CLIENT)
        self.assertIn('forbidden_mutators.add("nydus_worms")',GENERATOR)
    def test_native_eruption_and_unload(self):
        for phrase in ('"NydusCanal"', '"Birth 02"', '"NydusWorm_Birth"','"Spell"','"NydusWorm_Unload"'):
            self.assertIn(phrase,GALAXY)
    def test_spawn_rules_and_scheduling(self):
        self.assertIn('g_aprgMacroReadyTime + 238.0',GALAXY)
        self.assertIn('RandomFixed(58.0, 68.0)',GALAXY)
        self.assertIn('g_aprgNydusNextWaveTime[slot] = now + 10.0;',GALAXY)
        self.assertIn('g_aprgNydusNextWaveTime[slot] = now + RandomFixed(40.0, 50.0);',GALAXY)
        self.assertIn('25.0 + 5.0 * IntToFixed(g_aprgNydusSpawnCount)',GALAXY)
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))',GALAXY)
        self.assertIn('UnitGroupAddUnitGroup(buildings, UnitGroupAlliance(',GALAXY)
        self.assertIn('g_aprgNextNydusSpawnTime = now + 3.0;',GALAXY)
    def test_wave_units_attack_and_vision(self):
        for phrase in ('RandomInt(0, 8)','RandomInt(0, 1)','RandomInt(0, 2)','RandomInt(1, 4) == 1','now + 0.3333','APRG_RegisterAlwaysVisibleUnit(worm, player)','APRG_OrderAttackPlayer(troop, player)'):
            self.assertIn(phrase,GALAXY)
        self.assertNotIn('unitgroup wave;',GALAXY)
    def test_no_unscoped_dependency(self):
        dependency_definitions = GENERATOR.split('SWARM_DEPENDENCY_MUTATIONS =',1)[1].split('MUTATORS =',1)[0]
        self.assertNotIn('nydus_worms',dependency_definitions)

if __name__ == '__main__': unittest.main()
