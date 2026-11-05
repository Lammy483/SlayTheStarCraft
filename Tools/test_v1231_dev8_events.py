"""Events Dev8 behavior tests: direct AP grants, Vortex refunds, forced mutations."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"


def load_events():
    spec = importlib.util.spec_from_file_location("slay_events_test", PAYLOAD / "slay_events.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StubSlay:
    KERRIGAN_UNLOCK = "Kerrigan"
    @staticmethod
    def events_enabled(ctx): return True
    @staticmethod
    def state_ready(ctx): return True
    @staticmethod
    def state(ctx): return ctx.state
    @staticmethod
    def victory_count(ctx): return 0
    @staticmethod
    def _persist_state(ctx): ctx.saves += 1
    @staticmethod
    def _raw_logic_owned_item_counts(ctx):
        return Counter({"Zergling": 1, "Marine": 1, "Upgrade": 2})
    @staticmethod
    def _logic_owned_item_counts(ctx): return Counter()
    @staticmethod
    def _item_table(): return {}
    @staticmethod
    def _progression_owned(ctx, name):
        return bool(ctx.state.get("purchases", {}).get(name))
    @staticmethod
    def _one_kerrigan_level_item(table): return "1 Kerrigan Level"


class EventsDev8(unittest.TestCase):
    def test_vortex_wipes_items_and_refunds_without_resetting_progress(self):
        ev = load_events()
        state = {
            "chosen": [44, 55],
            "event_assignments": {"0": "vortex"},
            "purchases": {"Marine": 1, "Kerrigan": 1},
            "event_awarded_items": {"1 Kerrigan Level": 3},
            "event_forfeited_ap_counts": {"Zergling": 1},
            "spent": 1234,
            "boon_purchases": {"boon1": 1},
            "permanent_boons": ["boon1"],
            "permanent_blessings": ["buff"],
            "permanent_mutations": ["debuff"],
            "potion_inventory": [{"id": "potion1", "serial": 1}],
            "event_crystalis_checkpoint": 0,
            "shop_stock": ["Marine", "Raven", "Upgrade"],
            "shop_cycle": 2,
            "shop_stock_logic_version": 114,
            "shop_sale_items": ["Raven"],
            "shop_reroll_nonce": 7,
            "shop_rerolls_this_cycle": 2,
            "shop_potions_bought": ["potionA"],
            "shop_cycle_purchase_victory_count": 2,
            "shop_frozen_item": "Marine",
            "shop_expansion": 2,
        }
        ctx = SimpleNamespace(slay_config={"campaign_length": 12}, state=state, saves=0)
        with patch.object(ev, "_slay", return_value=StubSlay):
            ok, msg, done = ev.apply_choice(ctx, 0)
        self.assertTrue(ok and done)
        self.assertEqual(state["spent"], 0)
        self.assertIn("1234", msg)
        self.assertEqual(state["chosen"], [44, 55])
        self.assertEqual(state["purchases"], {})
        self.assertEqual(state["event_awarded_items"], {})
        self.assertEqual(state["event_forfeited_ap_counts"],
                         {"Zergling": 1, "Marine": 1, "Upgrade": 2})
        self.assertEqual(state["potion_inventory"], [])
        self.assertEqual(state["boon_purchases"], {})
        self.assertEqual(state["event_crystalis_checkpoint"], -1)
        self.assertEqual(state["event_resolutions"]["0"]["id"], "vortex")
        # Vortex removes inventory but must NOT trigger a new shop roll.
        self.assertEqual(state["shop_stock"], ["Marine", "Raven", "Upgrade"])
        self.assertEqual(state["shop_cycle"], 2)
        self.assertEqual(state["shop_stock_logic_version"], 114)
        self.assertEqual(state["shop_sale_items"], ["Raven"])
        self.assertEqual(state["shop_reroll_nonce"], 7)
        self.assertEqual(state["shop_rerolls_this_cycle"], 2)
        self.assertEqual(state["shop_potions_bought"], ["potionA"])
        self.assertEqual(state["shop_cycle_purchase_victory_count"], 2)
        self.assertEqual(state["shop_frozen_item"], "Marine")
        self.assertEqual(state["shop_expansion"], 0)
        self.assertEqual(ctx.saves, 1)

    def test_shop_refreshes_prices_but_not_stock_after_event(self):
        runtime = (PAYLOAD / "slay_the_starcraft.py").read_text(encoding="utf-8")
        installer = (PAYLOAD / "install_slay.py").read_text(encoding="utf-8")
        gui = (PAYLOAD / "slay_command_ui.py").read_text(encoding="utf-8")
        events = (PAYLOAD / "slay_events.py").read_text(encoding="utf-8")
        # The shop is keyed to mission victories, not event resolution.
        stock = ast.parse(runtime)
        shop = next(x for x in stock.body if isinstance(x, ast.FunctionDef) and x.name == "shop_stock")
        self.assertIn('cycle = victory_count(ctx)', ast.get_source_segment(runtime, shop))
        resolve = next(x for x in ast.parse(events).body if isinstance(x, ast.FunctionDef) and x.name == "apply_choice")
        resolution_code = ast.get_source_segment(events, resolve)
        self.assertNotIn('_roll_shop_stock(', resolution_code)
        self.assertNotIn('shop_stock(ctx)', resolution_code)
        self.assertNotIn('shop_reroll_nonce"] =', resolution_code)
        # Existing stock is preserved, but price changes and AP item grants
        # invalidate the cache and prompt the live bot to read fresh items.
        self.assertIn('tuple(state.get("event_price_penalties", ()))', installer)
        self.assertIn('tuple(sorted(state.get("event_awarded_items", {}).items()))', installer)
        self.assertIn("invalidate(0.05)", gui)
        self.assertIn("_request_live_item_refresh(ctx)", ast.get_source_segment(runtime,
            next(x for x in stock.body if isinstance(x, ast.FunctionDef)
                 and x.name == "event_apply_choice")))

    def test_crystalis_grants_ap_levels_never_boons(self):
        ev = load_events()
        state = {
            "event_assignments": {"0": "crystalis"},
            "purchases": {"Kerrigan": 1},
            "event_awarded_items": {"1 Kerrigan Level": 5},
        }
        ctx = SimpleNamespace(slay_config={"campaign_length": 12},
                              state=state, saves=0)
        with patch.object(ev, "_slay", return_value=StubSlay):
            view = ev.display(ctx)
            self.assertTrue(view["options"][0]["enabled"])
            ok, msg, done = ev.apply_choice(ctx, 0)
        self.assertTrue(ok and done)
        self.assertEqual(state["event_awarded_items"]["1 Kerrigan Level"], 75)
        self.assertNotIn("permanent_boons", state)
        self.assertEqual(state["event_crystalis_checkpoint"], 0)
        self.assertIn("70 Archipelago levels", msg)

    def test_crystalis_mission_augmentation_does_not_increase_credits(self):
        source = (PAYLOAD / "slay_the_starcraft.py").read_text(encoding="utf-8")
        self.assertIn('merged["_event_crystalis_mutation"] = names[-1]', source)
        self.assertIn('"event_crystalis_reroll_nonce"', source)
        self.assertIn('x in forced or _mutation_allowed_for_mission', source)
        # Constrains event injection to mutators; not mutation severity or credit reward.
        tree = ast.parse(source)
        merged = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "_merged_nodes")
        segment = ast.get_source_segment(source, merged)
        self.assertNotIn('merged["credit_reward"]', segment)
        self.assertNotIn('merged["mutation_value"]', segment)

if __name__ == "__main__":
    unittest.main()
