"""Standard Events Dev6 source/scheduler regressions.

python -m unittest Tools.test_v1231_dev6_events_framework
"""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"

def read(name):
    return (PAYLOAD / name).read_text(encoding="utf-8")

def load_events():
    spec = importlib.util.spec_from_file_location("slay_events_dev6_test", PAYLOAD / "slay_events.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

class EventsDev6(unittest.TestCase):
    def test_all_python_modules_compile(self):
        for name in ("slay_events.py", "slay_the_starcraft.py", "slay_launcher.py",
                     "generate_slay_run.py", "slay_command_ui.py", "install_slay.py"):
            with self.subTest(file=name):
                compile(read(name), name, "exec")
    def test_event_schedule(self):
        ev = load_events()
        self.assertEqual(ev.checkpoints(12), (0, 3, 6, 9, 11))
        self.assertEqual(ev.checkpoints(9), (0, 3, 6, 8))
        self.assertEqual(ev.checkpoints(3), (0, 2))
        self.assertEqual(ev.checkpoints(2), (0, 1))
        self.assertEqual(len(ev.EVENTS), 10)
        self.assertEqual(ev.deterministic_event(12345, 3), "merchant")
    def test_options_cannot_silently_apply_unimplemented_effects(self):
        ev = load_events()
        for event_id in ev.REGULAR_ENABLED:
            self.assertIn(event_id, ev.EVENTS)
            self.assertEqual(len(ev.IMPLEMENTED_OPTIONS[event_id]),
                             len(ev.EVENTS[event_id]["options"]))
        self.assertNotIn("vortex", ev.REGULAR_ENABLED)
        self.assertNotIn("zagara", ev.REGULAR_ENABLED)
    def test_opening_event_merchant_purchases_and_completion(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        ev = load_events()
        class FakeSlay:
            POTION_PREFIX = "slay_potion::"
            POTION_VARIANT_PREFIX = "slay_potion::19::"
            POTION_CAPACITY = 2
            POTION_RANDOM_UNITS = (1, 2, 3)
            POTION_CATALOG = {
                "slay_potion::1": {"name": "Mineral Reserves", "severity": 1},
                "slay_potion::2": {"name": "Gas Reserves", "severity": 1},
                "slay_potion::3": {"name": "Odin in a Bottle", "severity": 2},
            }
            completed = 0
            @staticmethod
            def events_enabled(ctx):
                return True
            @staticmethod
            def state_ready(ctx):
                return True
            @staticmethod
            def state(ctx):
                return ctx.state
            @staticmethod
            def victory_count(ctx):
                return FakeSlay.completed
            @staticmethod
            def _persist_state(ctx):
                ctx.persisted += 1
            @staticmethod
            def _potion_unlock_eligible(ctx, name):
                return True
            @staticmethod
            def potion_inventory(ctx):
                return list(ctx.state.get("potion_inventory", []))
            @staticmethod
            def credits(ctx):
                return 700 + int(ctx.state.get("event_credit_bonus", 0)) - int(ctx.state.get("spent", 0))
        ctx = SimpleNamespace(slay_config={"campaign_length": 12, "run_seed": 123},
                              state={}, persisted=0)
        with patch.object(ev, "_slay", return_value=FakeSlay):
            self.assertEqual(ev.pending(ctx)["id"], "__test_select__")
            self.assertTrue(ev.select_test(ctx, "merchant")[0])
            self.assertEqual(ev.pending(ctx)["id"], "merchant")
            view = ev.display(ctx)
            self.assertEqual(len(view["options"]), 5)
            self.assertTrue(all(o["enabled"] for o in view["options"]))
            bought = ev.apply_choice(ctx, 0)
            self.assertTrue(bought[0])
            self.assertFalse(bought[2])
            self.assertFalse(ev.display(ctx)["options"][0]["enabled"])
            self.assertFalse(ev.apply_choice(ctx, 0)[0], "Cannot buy same merchant offer twice")
            done = ev.apply_choice(ctx, 4)
            self.assertTrue(done[0] and done[2])
            self.assertEqual(ev.pending(ctx), None, "Initial event must not trigger twice")
            FakeSlay.completed = 3
            self.assertEqual(ev.pending(ctx)["checkpoint"], 3)
            self.assertGreater(ctx.persisted, 0)
    def test_standard_only_and_full_installation(self):
        launcher = read("slay_launcher.py")
        generator = read("generate_slay_run.py")
        runtime = read("slay_the_starcraft.py")
        installer = read("install_slay.py")
        ui = read("slay_command_ui.py")
        self.assertIn('events_checkbox = CheckBox(active=False', launcher)
        self.assertIn('events_checkbox.disabled = mode != "adventure"', launcher)
        self.assertIn('"events": bool(events) if game_mode == "adventure" else False', generator)
        self.assertIn('event_pending(ctx) is not None else _raw_frontier(ctx)', runtime)
        self.assertIn("slay.event_apply_choice(manager.ctx, index)", ui)
        self.assertIn("slay.event_checkpoints(manager.ctx)", ui)
        self.assertIn('bundled_events = source / "slay_events.py"', installer)
        self.assertIn('shutil.copy2(bundled_events, runtime_target.parent / "slay_events.py")', installer)
    def test_merchant_raid_galaxy_flags_and_ai(self):
        runtime = read("slay_the_starcraft.py")
        galaxy = read("APRogue.galaxy")
        self.assertIn('flags |= 268435456  # Event merchant raid', runtime)
        self.assertIn('APRG_MISSION_FLAG_EVENT_MERCHANT_RAID = 268435456', galaxy)
        self.assertIn('void APRG_TickEventMerchantRaid(int player, fixed now)', galaxy)
        self.assertIn('APRG_QueueRealDropPod(APRG_DROP_KIND_TERRAN_HOSTILE', galaxy)
        self.assertIn('StringToText("Mercenaries Incoming")', galaxy)
        self.assertIn('g_aprgEventMerchantRaidDone = true;', galaxy)
        # Existing Galaxy validator guards local decls and use-before-declaration,
        # two frequent causes of the game's 3-race critical error.
        spec = importlib.util.spec_from_file_location("slay_events_installer_test", PAYLOAD / "install_slay.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        installer.validate_galaxy_declaration_order(galaxy)
        installer.validate_galaxy_aprg_calls_declared(galaxy)

if __name__ == "__main__":
    unittest.main()
