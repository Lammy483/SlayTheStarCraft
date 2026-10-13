"""HF5: Domination Baneling nests accept any eligible ground unit via the shared flag."""
import ast
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / 'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
GALAXY = (ROOT / 'Payload/APRogue.galaxy').read_text(encoding='utf-8')
INSTALL = (ROOT / 'Payload/install_slay.py').read_text(encoding='utf-8')

class DominationAnyPickerHF5(unittest.TestCase):
    def test_mission_flag_sent_only_for_domination(self):
        tree = ast.parse(RUNTIME)
        node = next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='mission_flags_for_mission')
        code = ast.get_source_segment(RUNTIME,node)
        self.assertIn('mission_name.casefold() == "domination"',code)
        self.assertIn('flags |= MISSION_FLAG_DOMINATION_ANY_PICKER',code)
        self.assertIn('MISSION_FLAG_DOMINATION_ANY_PICKER = 65536',RUNTIME)
        self.assertIn('const int APRG_MISSION_FLAG_DOMINATION_ANY_PICKER = 65536;',GALAXY)
        self.assertNotIn('MISSION_FLAG_DOMINATION_ANY_PICKER',GALAXY.split('bool APRG_Config_Func',1)[1].split('bool APRG_Load_Func',1)[0])

    def test_normal_kerrigan_startup_preserved_and_override_is_mission_scoped(self):
        body = GALAXY.split('void APRG_TickDominationAnyPicker(fixed now)',1)[1].split('bool APRG_Tick_Func(',1)[0]
        self.assertIn('(g_aprgMissionFlags & APRG_MISSION_FLAG_DOMINATION_ANY_PICKER) == 0',body)
        self.assertIn('now < g_aprgActivationTime + 4.0',body)
        self.assertIn('libABFE498B_gv_aP_Triggers_Option_KerriganPresence = 0;',body)
        self.assertEqual(GALAXY.count('APRG_TickDominationAnyPicker(now);'),1)
        self.assertIn('    APRG_TickDominationAnyPicker(now);',GALAXY.split('bool APRG_Tick_Func(',1)[1])

    def test_no_map_source_patching_installer(self):
        self.assertNotIn('prepare_optional_domination_patch(',INSTALL)
        self.assertNotIn('patch_domination_kerrigan_picker(',INSTALL)
        self.assertNotIn('domination_map_script.write_text(',INSTALL)
        self.assertNotIn('domination_map_script.read_bytes(',INSTALL)
        self.assertIn('domination_map_script',INSTALL)  # HF3 uninstall backup support


    def test_launcher_source_matches_release_manifest(self):
        import json
        manifest=json.loads((ROOT/'launcher_manifest.json').read_text(encoding='utf-8'))
        go=(ROOT/'Tools/slay_launcher_windows.go').read_text(encoding='utf-8')
        self.assertTrue(manifest['runtime_revision'])
        self.assertIn('runtimeRevision = "'+manifest['runtime_revision']+'"',go)
        self.assertIn('$RuntimeRevision = "'+manifest['runtime_revision']+'"', (ROOT/'Tools/bootstrap_slay_runtime.ps1').read_text(encoding='utf-8'))

    def test_core_other_mission_flags_unmodified(self):
        for flag in ('LAB_RAT_OPENING = 8192','TOSH_AND_HIS_BOYS = 32768'):
            self.assertIn(flag,GALAXY)
        self.assertNotIn('MISSION_FLAG_DOMINATION_ANY_PICKER',RUNTIME.split('def mission_flags_for_mission(',1)[1].split('def ',1)[0].split('mutation_flag_bits = ',1)[1])

if __name__ == '__main__': unittest.main()
