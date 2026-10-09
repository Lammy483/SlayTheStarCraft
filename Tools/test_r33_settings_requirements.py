"""Regression coverage for r33 generator labels and read-only requirements handling."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class R33SettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = (ROOT / "Payload" / "slay_launcher.py").read_text(encoding="utf-8")
        cls.bootstrap = (ROOT / "Tools" / "bootstrap_slay_runtime.ps1").read_text(encoding="utf-8")

    def test_run_length_caption_no_longer_claims_easier(self):
        self.assertIn('Campaign Length\\n(changing run length may alter difficulty in unexpected ways)', self.launcher)
        self.assertNotIn('Longer campaign lengths makes the game easier', self.launcher)

    def test_alpha_only_labels_endless_mode(self):
        self.assertIn('"adventure": "Standard Mode", "endless": "Endless Mode (ALPHA)"', self.launcher)
        self.assertIn('game_mode not in {"adventure", "endless"}', self.launcher)
        self.assertNotIn('"endless": "Endless Mode"', self.launcher)

    def test_gitless_requirements_do_not_rewrite_unchanged_files(self):
        segment = self.bootstrap.split('function Make-RequirementsGitless {', 1)[1].split('\nfunction Ensure-PythonPackages {', 1)[0]
        self.assertIn('if ($text -cne $originalText) {', segment)
        self.assertIn('if ($requirementFile.IsReadOnly) { $requirementFile.IsReadOnly = $false }', segment)
        self.assertIn('Set-Content -LiteralPath $requirements -Value $text -Encoding ASCII', segment)
        self.assertIn('if ($rewritten -match \'git\\+\')', segment)


if __name__ == '__main__':
    unittest.main()
