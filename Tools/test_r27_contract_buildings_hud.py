"""r27: contracts must not respawn after death; consumables avoid AP chat."""
import re
import unittest
from pathlib import Path

G = (Path(__file__).resolve().parents[1] / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")


def function(name):
    match = re.search(r"^(?:void|bool|unit|fixed|int)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", G, re.M)
    if match is None:
        raise AssertionError(f"Missing Galaxy function: {name}")
    start = G.index("{", match.start())
    depth = 1
    for i in range(start + 1, len(G)):
        if G[i] == "{":
            depth += 1
        elif G[i] == "}":
            depth -= 1
            if depth == 0:
                return G[start:i + 1]
    raise AssertionError(f"Unclosed Galaxy function: {name}")


class R27RegressionTests(unittest.TestCase):
    def test_contract_structures_only_resolve_once_per_mission(self):
        tick = function("APRG_TickContractStructures")
        initialization = function("APRG_Load_Func")
        for race, name in (("Terran", "Merc Compound"), ("Zerg", "Predator Nest")):
            flag = f"g_aprg{race}ContractStructureResolved"
            unit = f"g_aprg{race}ContractStructure"
            self.assertIn(f"bool {flag} = false;", G, name)
            self.assertIn(f"if (!{flag})", tick, name)
            self.assertIn(f"if ({unit} != null) {{ {flag} = true; }}", tick, name)
            self.assertIn(f"{flag} = false;", initialization, name)
            self.assertNotIn(f"if ({unit} == null || !UnitIsAlive({unit}))", tick, name)
        self.assertIn("if (!APRG_PlayerMacroBaseReady(player)) { return; }", tick)
        self.assertIn("if (g_aprgTerranContractStructure != null && UnitIsAlive(g_aprgTerranContractStructure))", tick)
        self.assertIn("if (g_aprgZergContractStructure != null && UnitIsAlive(g_aprgZergContractStructure))", tick)

    def test_potion_buttons_top_left_and_ap_overlay_untouched(self):
        tick = function("APRG_TickPotions")
        self.assertIn("DialogCreate(490, 60, c_anchorTopLeft, 320, 0, false)", tick)
        self.assertNotIn("c_anchorTopRight", tick)
        self.assertIn("for (i = 0; i < 2; i += 1)", tick)
        self.assertIn("DialogControlSetSize(g_aprgPotionButton[i], players, 235, 44)", tick)
        self.assertIn("g_aprgConsumableNoticeUntil", tick)


if __name__ == "__main__":
    unittest.main()
