"""Dev16: bundled preferences, Devil's Playground baseline, Purification objective safety."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
GAL=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
PY=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')

class Dev16Regression(unittest.TestCase):
    def test_ini_exists_in_initial_distribution_and_is_player_editable(self):
        ini=ROOT/'Config/slay_preferences.ini'
        self.assertEqual(ini.read_text(encoding='utf-8'), (ROOT/'Config/slay_preferences.ini.example').read_text(encoding='utf-8'))
        self.assertIn('Warpgate=W',ini.read_text(encoding='utf-8'))
        spec=importlib.util.spec_from_file_location('dev16installer',ROOT/'Payload/install_slay.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)
            (target/'Config').mkdir()
            (target/'Config/slay_preferences.ini').write_text('[Hotkeys]\nWarpgate=E\n')
            for _ in range(3):
                self.assertEqual(mod.read_warpgate_preference(target),'E')
                self.assertEqual((target/'Config/slay_preferences.ini').read_text(),'[Hotkeys]\nWarpgate=E\n')

    def test_devils_flag_matching_both_catalogs(self):
        self.assertIn('MISSION_FLAG_DEVILS_PLAYGROUND_ZERG_ELIMINATION = 524288',PY)
        self.assertIn('APRG_MISSION_FLAG_DEVILS_PLAYGROUND_ZERG_ELIMINATION = 524288', GAL)
        self.assertIn('mission_name.casefold() == "devil\'s playground"',PY)
        self.assertIn('flags |= MISSION_FLAG_DEVILS_PLAYGROUND_ZERG_ELIMINATION',PY)

    def test_devils_capture_nonempty_original_only_and_zerg_race(self):
        s=GAL.split('void APRG_TickDevilsPlaygroundZergVictory(',1)[1].split("// Domination's API4",1)[0]
        for fragment in ('g_aprgDevilsZergBaselineCaptured','g_aprgActivationTime + 3.0',
                'APRG_EnemyTargetableStructures(player)','"Race"', '"Zerg"',
                'APRG_IsCreepTumorType', 'g_aprgDevilsZergBaselineCount += 1;',
                'g_aprgDevilsZergBaselineCount <= 0',
                'UnitGroupCount(g_aprgDevilsOriginalZergStructures, c_unitCountAlive) > 0',
                'GameOver(player, c_gameOverVictory, true, false)'):
            self.assertIn(fragment,s,fragment)
        self.assertIn('APRG_TickDevilsPlaygroundZergVictory(player, now);', GAL)
        self.assertEqual(GAL.count('APRG_TickDevilsPlaygroundZergVictory(player, now);'),1)
        # No fallback check against all enemy structures, which include helper buildings.
        self.assertNotIn('UnitGroupCount(APRG_EnemyTargetableStructures',s)

    def test_null_circuits_are_not_replaced_or_removed(self):
        s=GAL.split('bool APRG_IsCampaignNullCircuit(',1)[1].split('unit APRG_NearestEnemyStructure(',1)[0]
        self.assertIn('"NullCircuit"',s)
        self.assertIn('APRG_IsCampaignNullCircuit(u)',s)
        self.assertNotIn('UnitRemove(u)',s)
        self.assertNotIn('UnitKill(u)',s)
        self.assertNotIn('UnitSetPropertyFixed(u',s)
        self.assertNotIn('GameOver',s)
        self.assertIn('APRG_ApplyEnemyRegeneration(player);',GAL)
        # The filter means the enemy regeneration group excludes all Null Circuit variants.
        enemy_all=s.split('unitgroup APRG_EnemyAllUnits(int player) {',1)[1]
        self.assertIn('APRG_IsCampaignNullCircuit(u)',enemy_all)

if __name__=='__main__': unittest.main()
