"""Dev17: launch-time hotkey sync must work in embedded/isolated Python."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOTKEY_SCRIPT = ROOT / "Payload" / "slay_hotkeys.py"


class HotkeysIsolatedRuntimeDev17(unittest.TestCase):
    def test_isolated_launch_sync_and_repeat_no_download(self):
        with tempfile.TemporaryDirectory() as workdir:
            portable = Path(workdir) / "Slay"
            preferences = portable / "Config" / "slay_preferences.ini"
            preferences.parent.mkdir(parents=True)
            preferences.write_text("; Keep my personal setting\n[Hotkeys]\nWarpgate=E\n", encoding="utf-8")
            sc2 = Path(workdir) / "SC2"
            game_hotkeys = (sc2 / "Mods" / "ArchipelagoTriggers.SC2Mod"
                            / "enUS.SC2Data" / "LocalizedData" / "GameHotkeys.txt")
            game_hotkeys.parent.mkdir(parents=True)
            game_hotkeys.write_text("UI/Hotkey/WarpIn=W\n", encoding="utf-8")
            args = [sys.executable, "-I", str(HOTKEY_SCRIPT), "--portable-root", str(portable),
                    "--sc2-root", str(sc2)]
            first = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("Warp Gate hotkey=E", first.stdout)
            self.assertEqual(game_hotkeys.read_text(encoding="utf-8"), "UI/Hotkey/WarpIn=E\n")
            self.assertIn("Keep my personal setting", preferences.read_text(encoding="utf-8"))
            # Another Download Data could have reinstalled an older W value.
            game_hotkeys.write_text("UI/Hotkey/WarpIn=W\n", encoding="utf-8")
            second = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(game_hotkeys.read_text(encoding="utf-8"), "UI/Hotkey/WarpIn=E\n")
            self.assertEqual(preferences.read_text(encoding="utf-8"),
                             "; Keep my personal setting\n[Hotkeys]\nWarpgate=E\n")
            third = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertIn("mod updated=False", third.stdout)

    def test_missing_installer_is_reported_without_import_traceback(self):
        with tempfile.TemporaryDirectory() as workdir:
            root = Path(workdir)
            helper = root / "slay_hotkeys.py"
            shutil.copyfile(HOTKEY_SCRIPT, helper)
            result = subprocess.run(
                [sys.executable, "-I", str(helper), "--portable-root", str(root),
                 "--sc2-root", str(root)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Required Slay hotkey helper is missing", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_loader_uses_explicit_sibling_path(self):
        source = HOTKEY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('with_name("install_slay.py")', source)
        self.assertIn("importlib.util.spec_from_file_location", source)
        self.assertNotIn("\nfrom install_slay import (", source)
        self.assertIn("syncWarpgatePreference(sc2Root)",
                      (ROOT / "Tools" / "slay_launcher_windows.go").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
