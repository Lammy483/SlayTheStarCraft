"""Engine of Destruction's protected docked Loki must become vulnerable once approached."""
import unittest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
GALAXY=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
CLIENT=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')

class LokiHF7(unittest.TestCase):
    def test_gate_is_engine_of_destruction_only(self):
        self.assertIn('MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI = 131072',CLIENT)
        self.assertIn('if mission_name.casefold() == "engine of destruction":',CLIENT)
        self.assertIn('flags |= MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI',CLIENT)
        self.assertIn('const int APRG_MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI = 131072;',GALAXY)
        self.assertIn('if ((g_aprgMissionFlags & APRG_MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI) == 0) { return; }',GALAXY)
    def test_original_activation_and_mission_identity(self):
        a=GALAXY.index('void APRG_TickEngineOfDestructionLoki(')
        b=GALAXY.index('bool APRG_Tick_Func(',a)
        fn=GALAXY[a:b]
        for snippet in ['UnitFromId(835)', 'UnitGetType(loki) != "Loki"', 'RegionFromId(23)',
                        'RegionCircle(UnitGetPosition(loki), 22.0)',
                        'g_aprgLokiReachedTime + 2.5',
                        'UnitGetOwner(loki) == player']:
            self.assertIn(snippet,fn)
        self.assertLess(fn.index('g_aprgLokiReachedTime + 2.5'),fn.index('libNtve_gf_MakeUnitInvulnerable(loki, false);'))
    def test_invulnerability_removed_and_valid_hp_unchanged(self):
        a=GALAXY.index('void APRG_TickEngineOfDestructionLoki(')
        b=GALAXY.index('bool APRG_Tick_Func(',a)
        fn=GALAXY[a:b]
        for snippet in ['UnitBehaviorRemove(loki, "InvulnerabilityShield", c_unitBehaviorCountAll);',
                        'libNtve_gf_MakeUnitInvulnerable(loki, false);',
                        'UnitSetState(loki, c_unitStateInvulnerable, false);',
                        'AISetUnitScriptControlled(loki, false);']:
            self.assertIn(snippet,fn)
        self.assertIn('if (maxLife < 1.0 || maxLife > 100000.0)',fn)
        self.assertIn('APRG_TickEngineOfDestructionLoki(player, now);',GALAXY)
    def test_package_revision(self):
        manifest=json.loads((ROOT/'launcher_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['slay_version'],'1.2.0')
        self.assertEqual(manifest['runtime_revision'],'v1.2.0-release')
        for path in ['Tools/slay_launcher_windows.go','Tools/bootstrap_slay_runtime.ps1']:
            self.assertIn('v1.2.0-release',(ROOT/path).read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
