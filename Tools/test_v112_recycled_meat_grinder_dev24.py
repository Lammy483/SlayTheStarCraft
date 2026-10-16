"""Dev25: independently classify uncommandable infantry for reduced recycle refunds."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")


def func(name):
    match = re.search(r"(?m)^(?:void|bool|int|unit|fixed)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", GALAXY)
    assert match, name
    depth = 0
    for i in range(match.end() - 1, len(GALAXY)):
        if GALAXY[i] == "{":
            depth += 1
        elif GALAXY[i] == "}":
            depth -= 1
            if depth == 0:
                return GALAXY[match.end() - 1 : i + 1]
    raise AssertionError(name)


class RecycledMeatGrinder(unittest.TestCase):
    def test_recycled_armor_requires_ownership_and_infantry(self):
        death = func("APRG_Death_Func")
        self.assertIn("owner == player && APRG_HasExtension4(APRG_EXT4_BOON_RECYCLED_ARMOR) && APRG_IsInfantryBoonType(unitType, player)", death)

    def test_reduced_refund_for_uncommandable_infantry_not_boon_combination(self):
        death = func("APRG_Death_Func")
        m = re.search(r"if \(owner == player && APRG_HasExtension4\(APRG_EXT4_BOON_RECYCLED_ARMOR\).*?\n    }", death, re.S)
        self.assertIsNotNone(m)
        block = m.group(0)
        self.assertIn('DataTableGetBool(true, "APRG_Uncommandable_" + IntToString(UnitGetTag(dead)))', block)
        self.assertNotIn('APRG_HasExtension4(APRG_EXT4_BOON_MEAT_GRINDER)', block)
        self.assertRegex(block, r"if \(DataTableGetBool.*?\{[^{}]*c_playerPropMinerals\) \+ 8\)[^{}]*c_playerPropVespene\) \+ 2\)")
        self.assertRegex(block, r"else\s*\{[^{}]*c_playerPropMinerals\) \+ 25\)[^{}]*c_playerPropVespene\) \+ 10\)")

    def test_uncommandable_marker_is_shared_by_all_relevant_spawns(self):
        self.assertIn('DataTableSetBool(true, "APRG_Uncommandable_" + IntToString(UnitGetTag(u)), true)', func("APRG_MakeGroupUncommandable"))
        self.assertIn("APRG_MakeGroupUncommandable(created);", func("APRG_TryCloneProducedUnit"))
        self.assertIn("APRG_MakeGroupUncommandable(created);", func("APRG_SpawnMeatGrinderExtra"))
        self.assertIn("APRG_AddAlliedSupport(created, p, player, true);", func("APRG_ResolveWarfieldDrop"))
        self.assertIn("APRG_MakeGroupUncommandable(created);", func("APRG_AddAlliedSupport"))

    def test_catalog_description_and_meat_grinder_spawning_unchanged(self):
        catalog = (ROOT / "Payload" / "BOON_CATALOG.csv").read_text(encoding="utf-8")
        self.assertIn('Recycled Armor Suits,"Whenever one of your terran infantry dies, gain 25 minerals and 10 gas",400', catalog)
        self.assertIn('APRG_CreatePlayerUnitsAtPoint(1, unitType, player',func("APRG_SpawnMeatGrinderExtra"))
        self.assertIn('g_aprgMeatGrinderRemaining[slot] = 5;',func("APRG_EnqueueMeatGrinderMarines"))

    def test_runtime_revision_synced(self):
        rev = json.loads((ROOT / "launcher_manifest.json").read_text(encoding="utf-8"))["runtime_revision"]
        self.assertEqual(rev, "v1.2.0-release")
        self.assertIn(f'runtimeRevision = "{rev}"', (ROOT / "Tools" / "slay_launcher_windows.go").read_text(encoding="utf-8"))
        self.assertIn(f'$RuntimeRevision = "{rev}"', (ROOT / "Tools" / "bootstrap_slay_runtime.ps1").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
