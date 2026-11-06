"""Dev18: event consequences, native logic, automatic installer launch."""
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "Payload"
G = (P / "APRogue.galaxy").read_text(encoding="utf-8")
UI = (P / "slay_command_ui.py").read_text(encoding="utf-8")

def events():
    spec = importlib.util.spec_from_file_location("slay_events_dev18", P / "slay_events.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

class Slay:
    @staticmethod
    def events_enabled(ctx): return True
    @staticmethod
    def state_ready(ctx): return True
    @staticmethod
    def state(ctx): return ctx.state
    @staticmethod
    def victory_count(ctx): return ctx.victories
    @staticmethod
    def node(ctx, mission): return ctx.nodes.get(mission, {})
    @staticmethod
    def _persist_state(ctx): ctx.saves += 1

def ctx(victories=1):
    return SimpleNamespace(state={"event_colonists_checkpoint": -1},
        slay_config={"campaign_length": 12, "run_seed": 33},
        nodes={10: {"layer": 0}, 11: {"layer": 1}},
        victories=victories, saves=0)

class EventsDev18(unittest.TestCase):
    def setUp(self):
        self.ev = events()
        self.mock = patch.object(self.ev, "_slay", return_value=Slay)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def test_hansen_requires_acceptance(self):
        c = ctx()
        with patch.object(self.ev, "native_bank_values", return_value={}):
            self.assertFalse(self.ev.native_values(c, 11)[0] & self.ev.COLONY_HUT)
            c.state["event_colonists_checkpoint"] = 0
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.COLONY_HUT)

    def test_swann_victory_without_start_receipt_fails_later(self):
        c = ctx()
        c.state.update({"event_mechanical_checkpoint": 0, "event_mechanical_target": 10,
            "event_mechanical_offers": {"0": {"name": "Hellion", "unit_code": 1, "quantity": 10}}})
        with patch.object(self.ev, "native_bank_values", return_value={}):
            self.assertEqual(self.ev.mechanical_values(c, 10), (1, 10, 1, 0))
            self.assertEqual(self.ev.mechanical_values(c, 11), (1, 10, 3, 0))
            c.victories = 0
            self.assertEqual(self.ev.mechanical_values(c, 11), (0, 0, 0, 0))

    def test_organism_victory_without_kill_is_failure(self):
        c = ctx()
        c.state.update({"event_organism_checkpoint": 0, "event_organism_target": 10})
        with patch.object(self.ev, "native_bank_values", return_value={}):
            self.assertTrue(self.ev.native_values(c, 10)[0] & self.ev.ORGANISM_TEST)
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.ORGANISM_ENEMY)
        with patch.object(self.ev, "native_bank_values", return_value={"OrganismOutcome": 1}):
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.ORGANISM_ALLY)

    def test_solarite_victory_without_conversion_is_failure(self):
        c = ctx()
        c.state.update({"event_solarite_checkpoint": 0, "event_solarite_target": 10,
                        "event_solarite_resource": 1})
        with patch.object(self.ev, "native_bank_values", return_value={}):
            self.assertTrue(self.ev.native_values(c, 10)[0] & self.ev.SOLARITE_TRIAL)
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.SOLARITE_ENERGY_LOSS)
        with patch.object(self.ev, "native_bank_values", return_value={"SolariteSuccess0": 1}):
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.SOLARITE_ENERGY_GAIN)

    def test_zagara_banelings_require_brakk_death(self):
        c = ctx()
        c.state.update({"event_zagara_checkpoint": 0, "event_zagara_side": "zagara",
                        "event_zagara_quest_target": 10})
        with patch.object(self.ev, "native_bank_values", return_value={}):
            self.assertTrue(self.ev.native_values(c, 10)[0] & self.ev.ZAGARA_BRAKK_QUEST)
            self.assertFalse(self.ev.native_values(c, 11)[0] & self.ev.ZAGARA_ALLIED_BANELINGS)
        with patch.object(self.ev, "native_bank_values", return_value={"BrakkDead": 1}):
            self.assertTrue(self.ev.native_values(c, 11)[0] & self.ev.ZAGARA_ALLIED_BANELINGS)

    def test_selector_at_later_checkpoint(self):
        c = ctx(victories=3)
        c.state.update({"event_assignments": {"0": "nova", "3": "colonists"},
                        "event_resolutions": {"0": {"id": "nova", "option": 0}}})
        self.assertTrue(self.ev.select_test(c, "__test_select__")[0])
        self.assertEqual(c.state["event_assignments"]["3"], "__test_select__")
        self.assertEqual(c.state["event_assignments"]["0"], "nova")
        self.assertEqual(len(self.ev.display(c)["selector_ids"]), len(self.ev.EVENTS))
        self.assertTrue(self.ev.select_test(c, "mechanical")[0])
        self.assertEqual(c.state["event_assignments"]["3"], "mechanical")

    def test_galaxy_hut_meat_grinder_and_swann(self):
        colony = G.split("void APRG_TickEventColony(", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("c_unitCreateIgnorePlacement, 0, where, 0.0", colony)
        self.assertIn("c_unitStateTargetable, true", colony)
        self.assertIn("1.5, 3.5", colony)
        grinder = G.split("void APRG_CongaSpawnFromBase(", 1)[1].split("\n}\n", 1)[0]
        self.assertIn('StringContains(race, "Prot"', grinder)
        self.assertIn('spawnType = "Zealot";', grinder)
        swann = G.split("bool APRG_EventMechKill_Func(", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("APRG_EventMechBoostUnit(rewarded);", swann)
        self.assertIn("g_aprgEventMechKills < 50", swann)

    def test_updaters_start_game_just_once(self):
        updater = (ROOT / "Tools" / "Update-ExistingSlay.ps1").read_text(encoding="utf-8")
        wrapper = (ROOT / "Tools" / "Install-Slay-From-Downloads.ps1").read_text(encoding="utf-8")
        self.assertIn('Start-Process -FilePath (Join-Path $targetRoot "SlayTheStarCraft.exe")', updater)
        self.assertNotIn("Start-Process", wrapper)
        self.assertIn("if info['id'] != '__test_select__':", UI)

if __name__ == "__main__":
    unittest.main()
