"""HF2: Energized Queens applies to all Queen-named units, including AP_Queen."""
from __future__ import annotations
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
CLIENT = (ROOT / "Payload" / "slay_the_starcraft.py").read_text(encoding="utf-8")


class EnergizedQueensHF2(unittest.TestCase):
    def test_native_queen_type_and_display_name_both_supported(self):
        body = GALAXY.split("bool APRG_IsEnergizedQueenType(string unitType)", 1)[1].split("void APRG_TickEnergizedQueens(", 1)[0]
        self.assertIn('StringContains(unitType, "Queen", c_stringAnywhere, c_stringNoCase)', body)
        self.assertIn('TextToString(UnitTypeGetName(unitType))', body)
        self.assertIn('"Queen", c_stringAnywhere, c_stringNoCase)', body)
        self.assertIn('DataTableGetString(true, cacheKey)', body)
        self.assertIn('DataTableSetString(true, cacheKey, "0")', body)
        self.assertIn('DataTableSetString(true, cacheKey, "1")', body)
        self.assertNotIn('"SwarmQueen"', body)
        self.assertNotIn('"BroodQueen"', body)

    def test_energy_tick_applies_to_matched_queens_with_existing_factor(self):
        tick = GALAXY.split("void APRG_TickEnergizedQueens(int player, fixed now)", 1)[1].split("string APRG_GuidedShellsRemoveFilterWord(", 1)[0]
        self.assertIn('unitType = UnitGetType(u);', tick)
        self.assertIn('if (!APRG_IsEnergizedQueenType(unitType)) { continue; }', tick)
        self.assertIn('UnitGetPropertyFixed(u, c_unitPropEnergyRegen, c_unitPropCurrent)', tick)
        self.assertIn('energy + baseline * 9.0 * elapsed', tick)
        self.assertIn('MinF(maximum,', tick)
        self.assertIn('DataTableSetFixed(true, key, now)', tick)

    def test_shop_eligibility_matches_every_queen_name(self):
        self.assertIn('("energized_queens","boon_energized_queens",owns(("Queen",)))', CLIENT)
        self.assertNotIn('owns(("Swarm Queen","SwarmQueen","Brood Queen","BroodQueen"))', CLIENT)

    def test_boon_description_and_price(self):
        with (ROOT / "Payload" / "BOON_CATALOG.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        entries = [r for r in rows if r["Boon Title"] == "Energized Queens"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["Description"], "Your swarm queens and brood queens have 10x energy regeneration")
        self.assertEqual(entries[0]["Cost"], "400")


if __name__ == "__main__":
    unittest.main()
