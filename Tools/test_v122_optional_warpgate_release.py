"""v1.2.2: guard against optional WarpIn=None installer rejection."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"
SPEC = importlib.util.spec_from_file_location("slay_v122_release_verify", PAYLOAD / "verify_release.py")
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class OptionalWarpgateReleaseTests(unittest.TestCase):
    def test_current_installer_handles_unset_and_custom_hotkey(self):
        VERIFY.check_installer_optional_warpgate_postcheck(PAYLOAD)

    def test_rejects_original_v122_warpin_none_bug(self):
        with tempfile.TemporaryDirectory() as root:
            payload = Path(root)
            (payload / "install_slay.py").write_text(
                'post_checks = {warpgate_game_hotkeys: [f"UI/Hotkey/WarpIn={warpgate_key}"]}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "optional key None"):
                VERIFY.check_installer_optional_warpgate_postcheck(payload)

    def test_rejects_installer_that_ignores_explicit_hotkey(self):
        with tempfile.TemporaryDirectory() as root:
            payload = Path(root)
            (payload / "install_slay.py").write_text(
                "post_checks = {warpgate_game_hotkeys: []}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "optional key 'E'"):
                VERIFY.check_installer_optional_warpgate_postcheck(payload)


if __name__ == "__main__":
    unittest.main()
