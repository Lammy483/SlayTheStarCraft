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
        self.assertIn(ev.deterministic_event(12345, 3), ev.REGULAR_ENABLED)
        from unittest.mock import patch
        with patch.object(ev, "REGULAR_ENABLED", ("merchant", "nova", "organism")):
            self.assertIn(ev.deterministic_event(12345, 3, ("merchant",)), ("nova", "organism"))
            self.assertEqual(ev.deterministic_event(12345, 3, ("merchant", "nova")), "organism")
            # Only when all available events were used may an event repeat.
            self.assertIn(ev.deterministic_event(12345, 3, ("merchant", "nova", "organism")),
                          ("merchant", "nova", "organism"))
    def test_options_cannot_silently_apply_unimplemented_effects(self):
        ev = load_events()
        for event_id in ev.REGULAR_ENABLED:
            self.assertIn(event_id, ev.EVENTS)
            self.assertEqual(len(ev.IMPLEMENTED_OPTIONS[event_id]),
                             len(ev.EVENTS[event_id]["options"]))
        self.assertIn("vortex", ev.REGULAR_ENABLED)
        self.assertIn("zagara", ev.REGULAR_ENABLED)
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
            @staticmethod
            def _item_table():
                return {}
            @staticmethod
            def _logic_owned_item_counts(ctx):
                return {}
            KERRIGAN_UNLOCK = "Kerrigan"
            SPEAR_UNLOCK = "Spear of Adun"
            @staticmethod
            def _progression_owned(ctx, name):
                return False
        ctx = SimpleNamespace(slay_config={"campaign_length": 12, "run_seed": 123},
                              state={}, persisted=0)
        with patch.object(ev, "_slay", return_value=FakeSlay), patch.object(ev, "REGULAR_ENABLED", ("merchant",)):
            self.assertEqual(ev.pending(ctx)["id"], "__test_select__")
            self.assertTrue(ev.select_test(ctx, "merchant")[0])
            self.assertEqual(ev.pending(ctx)["id"], "merchant")
            # Users can back out of an opening test event and select again.
            self.assertTrue(ev.select_test(ctx, "__test_select__")[0])
            self.assertEqual(ev.pending(ctx)["id"], "__test_select__")
            self.assertTrue(ev.select_test(ctx, "merchant")[0])
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
            # With Merchant as the only currently playable encounter, repeating is allowed.
            self.assertEqual(ev.pending(ctx)["id"], "merchant")
            credits_before_raid = FakeSlay.credits(ctx)
            spent_before_raid = ctx.state["spent"]
            ok, message, finished = ev.apply_choice(ctx, 3)
            self.assertTrue(ok and finished)
            self.assertIn("Mercenaries attack next mission", message)
            self.assertNotIn("credits", message)
            self.assertEqual(FakeSlay.credits(ctx), credits_before_raid)
            self.assertEqual(ctx.state["spent"], spent_before_raid)
            self.assertEqual(ctx.state.get("event_credit_bonus", 0), 0)
            self.assertTrue(ctx.state["event_merchant_raid_pending"])
            self.assertEqual(len(ev._slay().potion_inventory(ctx)), 2)
            self.assertGreater(ctx.persisted, 0)
    def test_abathur_evolution_changes_real_item_ledger(self):
        from collections import Counter
        from types import SimpleNamespace
        from unittest.mock import patch
        ev = load_events()
        unit_names = ("Zergling", "Roach", "Hydralisk", "Mutalisk")
        table = {}
        for i, name in enumerate(unit_names):
            table[name] = SimpleNamespace(code=100 + i, type=SimpleNamespace(display_name="Unit"),
                                          race=SimpleNamespace(name="zerg"), quantity=1)
            for upgrade in range(3):
                item = f"{name} Upgrade {upgrade}"
                table[item] = SimpleNamespace(code=200 + i * 3 + upgrade,
                                               type=SimpleNamespace(display_name="Upgrade"),
                                               race=SimpleNamespace(name="zerg"), quantity=1)
        class FakeSlay:
            KERRIGAN_UNLOCK = "Kerrigan"
            SPEAR_UNLOCK = "Spear of Adun"
            @staticmethod
            def _progression_owned(ctx, name): return False
            @staticmethod
            def events_enabled(ctx): return True
            @staticmethod
            def state_ready(ctx): return True
            @staticmethod
            def state(ctx): return ctx.state
            @staticmethod
            def victory_count(ctx): return 0
            @staticmethod
            def _persist_state(ctx): ctx.saved += 1
            @staticmethod
            def _item_table(): return table
            @staticmethod
            def _item_race_key(name, data): return data.race.name
            @staticmethod
            def _is_unit_unlock_type(typ): return typ.lower() == "unit"
            @staticmethod
            def _is_mercenary_unit(name, data): return False
            @staticmethod
            def _unit_specific_parent_names(name, table): return tuple(
                unit for unit in unit_names if name.startswith(unit + " Upgrade "))
            @staticmethod
            def _is_unit_specific_upgrade(name, table): return " Upgrade " in name
            @staticmethod
            def _raw_logic_owned_item_counts(ctx): return Counter({x: 1 for x in unit_names})
            @staticmethod
            def _logic_owned_item_counts(ctx):
                counts = Counter({x: 1 for x in unit_names})
                for name, amount in ctx.state.get("event_forfeited_ap_counts", {}).items():
                    counts[name] -= amount
                for name, amount in ctx.state.get("event_awarded_items", {}).items():
                    counts[name] += amount
                return counts
        ctx = SimpleNamespace(slay_config={"run_seed": 15, "campaign_length": 12},
                              state={"event_assignments": {"0": "abathur"}}, saved=0)
        with patch.object(ev, "_slay", return_value=FakeSlay):
            self.assertIn("abathur", ev.eligible_regular(ctx))
            self.assertTrue(ev.display(ctx)["options"][0]["enabled"])
            ok, message, finished = ev.apply_choice(ctx, 0)
            self.assertTrue(ok and finished)
            lost = ctx.state["event_forfeited_ap_counts"]
            self.assertEqual(len(lost), 2)
            self.assertTrue(set(lost) <= set(unit_names))
            self.assertEqual(sum(ctx.state["event_awarded_items"].values()), 6)
            self.assertTrue(message.startswith("Units removed:\\n- "))
            self.assertIn("Upgrades gained:\\n- ", message)
            self.assertNotIn("experiment completed", message.lower())
            for removed_unit in lost:
                self.assertIn(f"- {removed_unit}\\n", message)
            for granted_upgrade in ctx.state["event_awarded_items"]:
                self.assertIn(f"- {granted_upgrade}", message)
            self.assertEqual(len(ev._owned_zerg_units(ctx)), 2)
            self.assertNotIn("abathur", ev.eligible_regular(ctx))
            self.assertGreater(ctx.saved, 0)

            # Existing synthetic AP upgrades are included in logical counts.
            # The event may still grant a second copy when the AP item permits it.
            for unit in unit_names:
                table[f"{unit} Upgrade 0"].quantity = 2
            carried = {f"{unit} Upgrade 0": 1 for unit in unit_names}
            ctx2 = SimpleNamespace(
                slay_config={"run_seed": 15, "campaign_length": 12},
                state={"event_assignments": {"0": "abathur"},
                       "event_awarded_items": carried.copy()},
                saved=0,
            )
            success, _, finished = ev.apply_choice(ctx2, 0)
            self.assertTrue(success and finished)
            for survivor in ev._owned_zerg_units(ctx2):
                self.assertEqual(
                    ctx2.state["event_awarded_items"][f"{survivor} Upgrade 0"], 2,
                    "An already awarded AP upgrade should not be counted twice",
                )

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
        self.assertIn("if info['id'] == 'abathur' and index == 0:", ui)
        self.assertIn("_slay_show_abathur_results(result)", ui)
        self.assertIn("def _slay_show_abathur_results(message):", ui)
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
