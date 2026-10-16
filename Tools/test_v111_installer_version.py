"""Regression: a version bump cannot break pre-install patch verification."""
import importlib.util
import tempfile
from pathlib import Path
import unittest
import io
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"

spec = importlib.util.spec_from_file_location("slay_preinstall_release_check", PAYLOAD / "verify_release.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

class InstallerVersionPreflightTests(unittest.TestCase):
    def test_installer_matches_actual_bundled_sources(self):
        verifier.check_installer_bundled_preinstall_postchecks(PAYLOAD)

    def test_warns_for_stale_installer_version_but_continues(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            (folder / "VERSION.txt").write_text("1.1.1\n")
            p = folder / "Payload"
            p.mkdir()
            for name in ("install_slay.py", "slay_launcher.py", "generate_slay_run.py",
                         "slay_the_starcraft.py", "APRogue.galaxy"):
                (p / name).write_bytes((PAYLOAD / name).read_bytes())
            broken = (p / "install_slay.py").read_text(encoding="utf-8")
            needle = "f'PACKAGE_VERSION = \"{package_version}\"'"
            self.assertIn(needle, broken)
            broken = broken.replace(needle, "'PACKAGE_VERSION = \"1.1.0\"'")
            (p / "install_slay.py").write_text(broken, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                verifier.check_installer_bundled_preinstall_postchecks(p)
            self.assertIn("WARNING:", output.getvalue())
            self.assertIn("version", output.getvalue())

if __name__ == "__main__":
    unittest.main()
