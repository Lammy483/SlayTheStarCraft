"""HF8 — preserve exact defaults and the one-time Smash and Grab worker grant."""
import json
import re
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload/generate_slay_run.py').read_text(encoding='utf-8')
L=(ROOT/'Payload/slay_launcher.py').read_text(encoding='utf-8')
C=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
S=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
class HF8(unittest.TestCase):
    def test_700_defaults(self):
        self.assertIn('DEFAULT_STARTING_CREDITS = 700',L)
        self.assertIn('starting_credits: int = 700,',G)
        self.assertIn('default=700, help="Starting shop credits (default 700)"',G)
    def test_flag_matches_python_and_galaxy(self):
        self.assertIn('MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS = 262144',C)
        self.assertIn('const int APRG_MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS = 262144;',S)
        section=C.split('def mission_flags_for_mission(',1)[1].split('mutation_flag_bits',1)[0]
        self.assertIn('if mission_name.casefold() == "smash and grab":',section)
        self.assertIn('flags |= MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS',section)
        self.assertEqual(section.count('flags |= MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS'),1)
    def test_one_time_safe_workers(self):
        fn=S.split('void APRG_GiveSmashGrabExtraWorkersIfReady(',1)[1].split('void APRG_GiveMultiClassIfReady(',1)[0]
        for code in ('g_aprgSmashGrabExtraWorkersGiven', 'APRG_PlayerMacroBaseReady(player)',
                     'APRG_FindPlayerHomeStructure(player)', 'APRG_PlayerWorkers(player)',
                     'APRG_FindGroundPointNear(UnitGetPosition(base), 4.0, 9.0)',
                     'APRG_CreatePlayerUnitsSafe(3, workerType, player',
                     'UnitGroupCount(created, c_unitCountAlive) > 0',
                     'StringContains(candidateType, "SCV"',
                     'StringContains(candidateType, "Drone"',
                     'StringContains(candidateType, "Probe"'):
            self.assertIn(code,fn)
        self.assertIn('g_aprgSmashGrabExtraWorkersGiven = false;',S.split('bool APRG_Load_Func(',1)[1])
        self.assertIn('APRG_GiveSmashGrabExtraWorkersIfReady(player);',S.split('bool APRG_Tick_Func(',1)[1])
    def test_updated_manifest_and_bootstrap(self):
        rev='v1.2.0-release'
        manifest=json.loads((ROOT/'launcher_manifest.json').read_text())
        self.assertEqual(manifest['slay_version'],'1.2.0')
        self.assertEqual(manifest['runtime_revision'],rev)
        self.assertIn(rev,(ROOT/'Tools/bootstrap_slay_runtime.ps1').read_text())
        self.assertIn(rev,(ROOT/'Tools/slay_launcher_windows.go').read_text())
if __name__=='__main__': unittest.main()
