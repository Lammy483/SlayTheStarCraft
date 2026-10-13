"""HF4: optional map and version-only checks must not block the installer."""
import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("installer_hf4", ROOT / "Payload" / "install_slay.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InstallerResilienceHF4(unittest.TestCase):
    def test_version_only_preinstall_is_warning(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            mod.check_installer_markers(Path("slay_launcher.py"),
                                        ['PACKAGE_VERSION = "1.1.1"'],
                                        "Pre-install package")
        self.assertIn("WARNING", capture.getvalue())

    def test_version_only_postinstall_is_warning(self):
        capture = io.StringIO()
        with redirect_stdout(capture):
            mod.check_installer_markers(Path("generate_slay_run.py"),
                                        ['PACKAGE_VERSION = "1.1.1"'],
                                        "Post-install")
        self.assertIn("WARNING", capture.getvalue())

    def test_missing_gameplay_marker_still_fails(self):
        with self.assertRaisesRegex(RuntimeError, "missing-galaxy-hook"):
            mod.check_installer_markers(Path("APRogue.galaxy"),
                                        ['PACKAGE_VERSION = "1.1.1"', "missing-galaxy-hook"],
                                        "Pre-install package")

    def test_mandatory_patch_failure_still_propagates(self):
        with self.assertRaisesRegex(RuntimeError, "critical"):
            mod.check_installer_markers(Path("slay_launcher.py"),
                                        ["critical"], "Post-install")

    def test_domination_is_not_a_map_source_dependency(self):
        installer=(ROOT / "Payload/install_slay.py").read_text(encoding="utf-8")
        self.assertNotIn("prepare_optional_domination_patch(",installer)
        self.assertNotIn("domination_map_script.write_text(",installer)
        self.assertNotIn('Domination API4 map script not found',installer)

if __name__ == "__main__":
    unittest.main()
