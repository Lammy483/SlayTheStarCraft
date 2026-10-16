"""Dev30: same-named mutation and blessing catalog descriptions must remain distinct.

Expected descriptions are copied verbatim from the October 11 balance workbook.
"""
import ast
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"
SOURCE = (PAYLOAD / "slay_the_starcraft.py").read_text(encoding="utf-8")
PAIRS = {
    "Drakken Laser Drill": {
        "Mutation": "The enemy has a Drakken Laser Drill",
        "Blessing": "Workers can construct a Drakken Laser Drill for 800 minerals and gas",
    },
    "Zombies": {
        "Mutation": "Whenever any unit dies, they spawn a hostile infested terran",
        "Blessing": "Whenever any unit dies, they spawn an allied infested terran",
    },
    "Occasional Thor": {
        "Mutation": "Some enemy units are actually Thors",
        "Blessing": "Whenever you train a unit, you have a 4% chance of training a Thor instead",
    },
    "Occasional Ultralisk": {
        "Mutation": "Some enemy units are actually Ultralisks",
        "Blessing": "Whenever you train a unit, you have a 4% chance of training an Ultralisk instead",
    },
    "Occasional Colossus": {
        "Mutation": "Some enemy units are actually Colossi",
        "Blessing": "Whenever you train a unit, you have a 4% chance of training a Colossus instead",
    },
    "ANOTHER GORGON": {
        "Mutation": "The enemy sends many gorgons at you, but they are quite fragile",
        "Blessing": "Warfield is sending gorgon after gorgon to assist you, but they are quite fragile",
    },
    "Odin": {
        "Mutation": "The enemy base has an odin in it. After about 14 minutes it attacks your base.",
        "Blessing": "You start with the odin",
    },
}


def catalog_rows():
    with (PAYLOAD / "EFFECT_CATALOG.csv").open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def static_effect_dict(name):
    for item in ast.parse(SOURCE).body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == name:
            return ast.literal_eval(item.value)
    raise AssertionError(f"Missing {name}")


class SameNamedEffectsDev30(unittest.TestCase):
    def test_each_shared_title_uses_its_own_verbatim_description(self):
        rows = catalog_rows()
        for title, by_kind in PAIRS.items():
            with self.subTest(title=title):
                matches = [r for r in rows if r["Title"] == title]
                self.assertEqual(len(matches), 2)
                self.assertEqual({r["Mutation or Blessing"]: r["Description"] for r in matches}, by_kind)
                self.assertNotEqual(by_kind["Mutation"], by_kind["Blessing"])

    def test_no_other_shared_titles_escaped_the_audit(self):
        by_title = {}
        for row in catalog_rows():
            by_title.setdefault(row["Title"], set()).add(row["Mutation or Blessing"])
        self.assertEqual({name for name, kinds in by_title.items() if kinds == {"Mutation", "Blessing"}}, set(PAIRS))

    def test_runtime_mapping_keeps_kind_and_canonical_effect_id_separate(self):
        self.assertIn('rows[(title, kind)] = row', SOURCE)
        self.assertIn('_row = _EFFECT_CATALOG_ROWS.get((_title, _kind))', SOURCE)
        self.assertIn('EFFECT_DESCRIPTIONS[_effect_id] = _description', SOURCE)
        display = static_effect_dict('EFFECT_DISPLAY_NAMES')
        descriptions = static_effect_dict('EFFECT_DESCRIPTIONS')
        expected_effect_ids = {
            "Drakken Laser Drill": ("drakken_laser_drill_enemy", "drakken_laser_drill_blessing"),
            "Zombies": ("zombies_mutation", "zombies_blessing"),
            "Occasional Thor": ("occasional_thor_mutation", "occasional_thor_blessing"),
            "Occasional Ultralisk": ("occasional_ultralisk_mutation", "occasional_ultralisk_blessing"),
            "Occasional Colossus": ("occasional_colossus_mutation", "occasional_colossus_blessing"),
            "ANOTHER GORGON": ("another_gorgon_mutation", "another_gorgon_blessing"),
            "Odin": ("odin_delayed_assault", "odin"),
        }
        extra_mutations = static_effect_dict('_V1024_MUTATIONS')
        for title, (mutation_id, blessing_id) in expected_effect_ids.items():
            with self.subTest(title=title):
                if mutation_id in extra_mutations:
                    self.assertEqual(extra_mutations[mutation_id][0], title)
                    # The override layer replaces its earlier hardcoded description.
                    self.assertNotIn(mutation_id, descriptions)
                else:
                    self.assertEqual(display[mutation_id], title)
                    self.assertEqual(descriptions[mutation_id], PAIRS[title]["Mutation"])
                self.assertEqual(display[blessing_id], title)
                self.assertEqual(descriptions[blessing_id], PAIRS[title]["Blessing"])

    def test_occasional_ultralisk_mission_text_uses_effect_id(self):
        block = SOURCE.split('def _mission_effect_description(', 1)[1].split('\ndef ', 1)[0]
        self.assertIn('return EFFECT_DESCRIPTIONS.get(effect_id, "")', block)
        self.assertIn("'occasional_ultralisk_blessing'", SOURCE)


if __name__ == '__main__':
    unittest.main()
