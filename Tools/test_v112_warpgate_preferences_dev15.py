"""Dev15 Warp Gate preference: edited INI survives Download Data and launch."""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"
SPEC = importlib.util.spec_from_file_location("slay_installer_preferences", PAYLOAD / "install_slay.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class WarpgatePreferencesDev15(unittest.TestCase):
    def test_default_ini_and_custom_value(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)
            self.assertEqual(installer.read_warpgate_preference(root), 'W')
            pref=root/'Config/slay_preferences.ini'
            self.assertEqual(pref.read_text(), '[Hotkeys]\nWarpgate=W\n')
            pref.write_text('; player comment\n[Hotkeys]\nWarpgate=E\n')
            self.assertEqual(installer.read_warpgate_preference(root), 'E')
            self.assertEqual(pref.read_text(), '; player comment\n[Hotkeys]\nWarpgate=E\n')

    def test_invalid_hotkey_does_not_silently_reset_to_w(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)
            pref=root/'Config/slay_preferences.ini'
            pref.parent.mkdir()
            pref.write_text('[Hotkeys]\nWarpgate=NOT_A_KEY\n')
            with self.assertRaisesRegex(ValueError,'Invalid'):
                installer.read_warpgate_preference(root)
            self.assertEqual(pref.read_text(), '[Hotkeys]\nWarpgate=NOT_A_KEY\n')

    def test_mod_local_override_and_duplicate_cleanup(self):
        patcher=installer.patch_mod_game_hotkeys
        self.assertEqual(patcher('', 'E'), 'UI/Hotkey/WarpIn=E\n')
        self.assertEqual(patcher('Other=K\nUI/Hotkey/WarpIn=W\n', 'E'), 'Other=K\nUI/Hotkey/WarpIn=E\n')
        self.assertEqual(patcher('UI/Hotkey/WarpIn=W\nUI/Hotkey/WarpIn=W\n', 'E').count('WarpIn='), 1)

    def test_redownload_then_relaunch_use_user_key_not_bundled_w(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t)/'Slay'
            sc2=pathlib.Path(t)/'SC2'
            prefs=root/'Config/slay_preferences.ini'
            prefs.parent.mkdir(parents=True)
            prefs.write_text('; important\n[Hotkeys]\nWarpgate=E\n')
            target=sc2/'Mods/ArchipelagoTriggers.SC2Mod/enUS.SC2Data/LocalizedData/GameHotkeys.txt'
            target.parent.mkdir(parents=True)
            target.write_text('Other=J\nUI/Hotkey/WarpIn=W\n')
            # Simulate Download Data applying the installer override twice.
            for _ in range(2):
                key=installer.read_warpgate_preference(root)
                target.write_text(installer.patch_mod_game_hotkeys(target.read_text(),key))
                self.assertIn('UI/Hotkey/WarpIn=E',target.read_text())
            # Simulate a new data payload having restored W on disk, then launch.
            target.write_text('UI/Hotkey/WarpIn=W\n')
            cmd=[sys.executable,str(PAYLOAD/'slay_hotkeys.py'),'--portable-root',str(root),'--sc2-root',str(sc2)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(target.read_text(),'UI/Hotkey/WarpIn=E\n')
            self.assertEqual(prefs.read_text(),'; important\n[Hotkeys]\nWarpgate=E\n')
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(second.returncode,0,second.stderr)
            self.assertIn('mod updated=False', second.stdout)

    def test_custom_hotkey_profiles_use_same_key(self):
        with tempfile.TemporaryDirectory() as t:
            home=pathlib.Path(t)
            profile=home/'Documents/StarCraft II/Hotkeys/MyProfile.SC2Hotkeys'
            profile.parent.mkdir(parents=True)
            profile.write_text('[Hotkeys]\nWarpIn=W\nOther=G\n[Settings]\nFoo=Bar\n')
            with patch.object(installer.pathlib.Path, 'home', return_value=home):
                self.assertEqual(installer.patch_warpgate_hotkey('E'),[profile])
                self.assertEqual(installer.patch_warpgate_hotkey('E'),[])
            self.assertIn('WarpIn=E\n',profile.read_text())
            self.assertIn('Other=G\n',profile.read_text())

    def test_package_contains_config_and_starts_sync_from_both_launchers(self):
        go=(ROOT/'Tools/slay_launcher_windows.go').read_text()
        self.assertGreaterEqual(go.count('syncWarpgatePreference(sc2Root)'),2)  # manual and auto
        self.assertIn('read_warpgate_preference(source.parent)',(PAYLOAD/'install_slay.py').read_text())
        self.assertIn('Warpgate=W',(ROOT/'Config/slay_preferences.ini.example').read_text())


if __name__ == '__main__':
    unittest.main()
