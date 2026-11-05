"""Dev14 regression checks: Galaxy identifiers and missing UI texture recovery."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")


class Dev14GalaxyAndArtTests(unittest.TestCase):
    def test_no_galaxy_reserved_local_identifiers(self):
        # Galaxy 'native' is a declaration keyword, not a legal variable name.
        # The old Swann code declared 'string native;' twice, breaking all races.
        keywords = {"native", "const", "void", "int", "bool", "fixed", "unit",
                    "unitgroup", "point", "bank", "string", "text", "order",
                    "for", "while", "if", "else", "return", "break", "continue",
                    "switch", "case", "default", "true", "false", "include"}
        local = re.compile(
            r"(?m)^\s*(?:int|fixed|bool|string|point|unit|unitgroup|bank|trigger|order|text)\s+([A-Za-z_]\w*)\s*(?:[;=\[,])"
        )
        for match in local.finditer(SOURCE):
            self.assertNotIn(
                match.group(1), keywords,
                f"reserved Galaxy keyword at line {SOURCE.count(chr(10), 0, match.start())+1}"
            )
        mechanical = SOURCE.split("bool APRG_EventMechMatches(", 1)[1].split(
            "void APRG_TickEventMerchantRaid(", 1)[0]
        self.assertIn("string mechUnitType;", mechanical)
        self.assertNotRegex(mechanical, r"\bstring\s+native\b")

    def test_restore_older_install_assets_without_using_json_as_icons(self):
        spec = importlib.util.spec_from_file_location(
            "slay_asset_recovery", ROOT / "Payload" / "slay_asset_recovery.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            old = base / "Slay the StarCraft v1.2.3"
            images = old / "Payload" / "slay_assets"
            (images / "icons").mkdir(parents=True)
            for name in (module.THEME_BANNER, module.THEME_BUTTON):
                (images / name).write_bytes(b"\x89PNG\r\n\x1a\nexample")
            (images / "icons" / "marine.png").write_bytes(b"\x89PNG\r\n\x1a\nmarine")
            new = base / "Slay the StarCraft Events Dev14"
            targets = (
                new / "Payload" / "slay_assets",
                new / "Runtime" / "Archipelago" / "worlds" / "sc2" / "slay_assets"
            )
            new.mkdir()
            self.assertTrue(module.recover_from_siblings(new, targets))
            for dest in targets:
                self.assertTrue((dest / module.THEME_BANNER).is_file())
                self.assertTrue((dest / module.THEME_BUTTON).is_file())
                self.assertTrue((dest / "icons" / "marine.png").is_file())
            self.assertEqual(module.import_art(old, targets), 3)
            with self.assertRaises(ValueError):
                module.import_art(base / "missing", targets)

    def test_ui_provides_manual_art_import_and_installer_copies_helper(self):
        theme = (ROOT / "Payload" / "slay_theme.py").read_text(encoding="utf-8")
        installer = (ROOT / "Payload" / "install_slay.py").read_text(encoding="utf-8")
        self.assertIn('text="Restore UI Artwork"', theme)
        self.assertIn('else (0.06, 0.12, 0.20, 1)', theme)
        self.assertIn('"slay_asset_recovery.py"', installer)
        self.assertIn(
            'shutil.copytree(assets_source, ap_root / "slay_assets", dirs_exist_ok=True)',
            installer
        )


if __name__ == "__main__":
    unittest.main()
