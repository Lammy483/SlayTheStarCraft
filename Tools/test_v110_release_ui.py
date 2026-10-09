"""Public v1.1.0: acknowledgements and responsive campaign-length caption."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class V110ReleaseUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher=(ROOT/'Payload/slay_launcher.py').read_text(encoding='utf-8')
        cls.theme=(ROOT/'Payload/slay_theme.py').read_text(encoding='utf-8')
        cls.verifier=(ROOT/'Payload/verify_release.py').read_text(encoding='utf-8')

    def test_acknowledgement_exact_text(self):
        self.assertIn('("Wangfeng", "Chinese localization and improved UI")',self.theme)
        self.assertNotIn('Chinese localization and the StarCraft-style launcher', self.theme)

    def test_campaign_note_wraps_and_expands_to_show_all_lines(self):
        self.assertIn(r'Campaign Length\n(changing run length may alter difficulty in unexpected ways)',self.launcher)
        self.assertIn('"text_size", (max(dp(1), width), None)',self.launcher)
        self.assertIn('"height", max(dp(46), texture[1] + dp(10))',self.launcher)
        self.assertIn('caption.bind(height=',self.launcher)
        self.assertIn('column.bind(minimum_height=column.setter("height"))',self.launcher)
        self.assertIn('form.bind(minimum_height=',self.launcher)
        self.assertIn('form.height = max(form.height, dp(350))',self.theme)
        self.assertNotIn('form.height = dp(350)',self.theme)

    def test_release_metadata(self):
        self.assertEqual((ROOT/'VERSION.txt').read_text().strip(),'1.1.0')
        self.assertIn('"release_channel": "stable"',(ROOT/'launcher_manifest.json').read_text())
        self.assertIn('"release_channel": "stable"',self.verifier)
        self.assertIn('release_branch=release/v1.1.0',(ROOT/'INTEGRATION_BUILD.txt').read_text())
        self.assertTrue((ROOT/'RELEASE_NOTES.md').is_file())

if __name__=='__main__': unittest.main()
