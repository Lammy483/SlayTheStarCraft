"""Dev11 tests for the Rory Swann field-test event, AP unlocks, and Galaxy wire."""
import importlib.util
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"

def load_events():
    spec = importlib.util.spec_from_file_location("slay_events_dev11", PAYLOAD / "slay_events.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def item(name, code):
    return SimpleNamespace(code=code, type=SimpleNamespace(display_name="Unit"),
                           race=SimpleNamespace(name="terran"))

class FakeSlay:
    KERRIGAN_UNLOCK = "Kerrigan"
    SPEAR_UNLOCK = "Spear"
    @staticmethod
    def events_enabled(ctx): return True
    @staticmethod
    def state_ready(ctx): return True
    @staticmethod
    def state(ctx): return ctx.state
    @staticmethod
    def victory_count(ctx): return ctx.victories
    @staticmethod
    def _persist_state(ctx): ctx.saves += 1
    @staticmethod
    def _item_table():
        return {
            "Hellion": item("Hellion", 3),
            "Siege Tank": item("Siege Tank", 4),
            "Vulture": item("Vulture", 5),
        }
    @staticmethod
    def _logic_owned_item_counts(ctx):
        owned = Counter(ctx.owned)
        owned.update(ctx.state.get("event_awarded_items", {}))
        return owned
    @staticmethod
    def _item_race_key(name, data): return data.race.name
    @staticmethod
    def _is_unit_unlock_type(kind): return kind.lower() == "unit"
    @staticmethod
    def _progression_owned(ctx, name): return False
    @staticmethod
    def _request_live_item_refresh(ctx): ctx.refreshes += 1
    @staticmethod
    def node(ctx, mid):
        return {"layer": 0 if mid == 10 else 1}

class Dev11MechanicalTest(TestCase):
    def context(self):
        return SimpleNamespace(
            slay_config={"campaign_length": 12, "run_seed": 12345},
            state={"event_assignments": {"0": "mechanical"},
                   "event_resolutions": {}, "spent": 25, "shop_stock": ["item A", "item B"]},
            owned={"Vulture": 1}, victories=0, saves=0, refreshes=0
        )

    def test_offer_is_unowned_and_uses_1000_resource_budget(self):
        ev = load_events()
        ctx = self.context()
        with patch.object(ev, "_slay", return_value=FakeSlay):
            options = ev._mechanical_candidates(ctx)
            self.assertEqual(set(x[0] for x in options), {"Hellion", "Siege Tank"})
            self.assertIn(("Hellion", 1, 10), options)
            self.assertIn(("Siege Tank", 4, 3), options)
            info = ev.display(ctx)
            self.assertIn(info["name"], ["Hellion Field Test", "Siege Tank Field Test"])
            self.assertTrue(info["options"][0]["enabled"])
            self.assertNotIn("[Mechanical Ground Terran Unit]", info["description"])
            offer = ev._mechanical_offer(ctx, "0")
            ok, msg, done = ev.apply_choice(ctx, 0)
        self.assertTrue(ok and done)
        self.assertEqual(ctx.state["event_mechanical_checkpoint"], 0)
        self.assertEqual(ctx.state["event_mechanical_pending"], True)
        self.assertEqual(ctx.state["shop_stock"], ["item A", "item B"])
        self.assertIn(offer[0], msg)
        self.assertNotIn("permanent_boons", ctx.state)

    def test_kill_receipt_grants_ap_unlock_once_and_later_missions_buff_unit(self):
        ev = load_events()
        ctx = self.context()
        ctx.state.update({
            "event_mechanical_offers": {"0": {"name": "Hellion", "unit_code": 1, "quantity": 10}},
            "event_mechanical_checkpoint": 0,
            "event_mechanical_target": 10,
            "event_mechanical_rewarded": False,
            "event_mechanical_pending": False,
        })
        ctx.victories = 1
        with patch.object(ev, "_slay", return_value=FakeSlay):
            self.assertEqual(ev.mechanical_values(ctx, 10), (1, 10, 1, 0))
            with patch.object(ev, "native_bank_values", return_value={"MechStartedAt0": 1,
                                                                      "MechOutcome0": 1}):
                self.assertTrue(ev.sync_mechanical_quest(ctx))
                self.assertFalse(ev.sync_mechanical_quest(ctx))
                self.assertEqual(ev.mechanical_values(ctx, 11), (1, 10, 2, 0))
        self.assertEqual(ctx.state["event_awarded_items"], {"Hellion": 1})
        self.assertEqual(ctx.refreshes, 1)

    def test_failed_quest_spawns_enemy_patrol_and_does_not_unlock(self):
        ev = load_events()
        ctx = self.context()
        ctx.state.update({
            "event_mechanical_offers": {"0": {"name": "Siege Tank", "unit_code": 4, "quantity": 3}},
            "event_mechanical_checkpoint": 0,
            "event_mechanical_target": 10,
            "event_mechanical_rewarded": False,
        })
        ctx.victories = 1
        with patch.object(ev, "_slay", return_value=FakeSlay):
            with patch.object(ev, "native_bank_values", return_value={"MechStartedAt0": 1}):
                self.assertEqual(ev.mechanical_values(ctx, 11), (4, 3, 3, 0))
                self.assertFalse(ev.sync_mechanical_quest(ctx))
        self.assertNotIn("event_awarded_items", ctx.state)

    def test_failed_swann_patrols_reachable_enemy_territory(self):
        galaxy = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
        beginning = galaxy.index("void APRG_TickEventMechanical(int player, fixed now)")
        ending = galaxy.index("void APRG_TickEventMerchantRaid(", beginning)
        tick = galaxy[beginning:ending]
        self.assertIn("home = APRG_FindPlayerHomeStructure(player);", tick)
        self.assertIn("where = APRG_EventHostilePatrolPoint(player);", tick)
        self.assertIn("APRG_OrderAttackMove(u, where);", tick)
        self.assertNotIn("APRG_OrderAttackMove(u, UnitGetPosition(enemyAnchor));", tick)

    def test_event_heroes_spawn_on_pathable_ground_and_banelings_disperse(self):
        galaxy = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
        hero = galaxy.split("unit APRG_EventEnemyHero(", 1)[1].split("\n}\n", 1)[0]
        zagara = galaxy.split("void APRG_TickEventZagara(", 1)[1].split("\n}\n", 1)[0]
        # Both variants must avoid overlapping their hostile base anchor.
        self.assertIn("spawnPoint = APRG_EventHostileGroundPoint(player, anchor);", hero)
        self.assertIn("owner, spawnPoint,", hero)
        self.assertIn("spawnPoint = APRG_EventHostileGroundPoint(player, anchor);", zagara)
        self.assertIn("UnitGetOwner(anchor), spawnPoint,", zagara)
        self.assertNotIn("UnitGetOwner(anchor), UnitGetPosition(anchor),", hero)
        self.assertNotIn("UnitGetOwner(anchor), UnitGetPosition(anchor),", zagara)
        # A 100-Baneling wave is five groups, each with its own safe placement.
        self.assertIn("waveIndex < 5", zagara)
        self.assertIn("RandomFixed(3.0, 9.0)", zagara)
        self.assertIn('APRG_CreatePlayerUnitsSafe(20, "Baneling"', zagara)

    def test_swann_weapon_tree_is_cached_per_player(self):
        galaxy = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
        tree = galaxy.split("void APRG_EventMechBoostWeaponTree(", 1)[1].split("\n}\n", 1)[0]
        self.assertIn('key = "APRG_EventMechTree_" + IntToString(owner)', tree)
        self.assertIn("if (DataTableGetBool(true, key)) { return; }", tree)
        self.assertIn("DataTableSetBool(true, key, true);", tree)
        self.assertLess(tree.index("if (DataTableGetBool(true, key))"),
                        tree.index("for (i = 0; i < 22; i += 1)"))

    def test_solarite_success_receipt_prevents_double_charge(self):
        galaxy = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
        solarite = galaxy.split("void APRG_TickEventSolarite(", 1)[1].split("\n}\n", 1)[0]
        already_paid = solarite.index(
            "BankValueGetAsInt(g_aprgEventBank, g_aprgEventSection, successKey) == 1")
        debit = solarite.index("PlayerModifyPropertyInt(player, propertyType, c_playerPropOperSetTo, 0)")
        self.assertLess(already_paid, debit, "Replay may not charge an already-completed trial")
        self.assertIn("g_aprgEventSolariteResolved = true;", solarite[already_paid:debit])

    def test_galaxy_uses_real_kill_event_and_separate_event_packet(self):
        galaxy = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
        installer = (PAYLOAD / "install_slay.py").read_text(encoding="utf-8")
        self.assertIn('libNtve_gf_KillingUnit()', galaxy)
        self.assertIn('UnitGroupHasUnit(g_aprgEventMechTestUnits, killer)', galaxy)
        self.assertIn('TriggerAddEventUnitDied(TriggerCreate("APRG_EventMechKill_Func"), null);', galaxy)
        self.assertIn('APRG_TickEventMechanical(player, now);', galaxy)
        self.assertIn('MechOutcome', galaxy)
        self.assertIn('"?SlayMech', installer)
        self.assertIn('event_mechanical_values_for_mission(self.ctx, self.mission_id)', installer)

if __name__ == "__main__":
    main()
