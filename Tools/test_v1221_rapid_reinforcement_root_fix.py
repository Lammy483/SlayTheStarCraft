"""Dev2 source-level tests: AP Rapid Reinforcement ownership and bounded timers."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = (ROOT / "Payload" / "slay_the_starcraft.py").read_text("utf-8")
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text("utf-8")


def python_function(name):
    ast.parse(PYTHON)
    module = ast.parse(PYTHON)
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(PYTHON, node)


def galaxy_function(name):
    start = GALAXY.index("void " + name + "(")
    end = GALAXY.index("\n}\n", start)
    return GALAXY[start:end + 3]


class RapidReinforcementTest(unittest.TestCase):
    def test_native_upgrade_not_injected(self):
        body = python_function("augment_network_items")
        self.assertIn('item_list.get("Rapid Reinforcement (Terran)")', body)
        self.assertIn('items[:] = [item for item in items if item.item != rapid.code]', body)
        self.assertLess(body.index('items.append(NetworkItem'), body.index('items[:] = [item for item in items if item.item != rapid.code]'))

    def test_ownership_bit_uses_raw_inventory(self):
        body = python_function("mercenary_upgrade_packed2")
        self.assertIn('_logic_owned_item_counts(ctx).get("Rapid Reinforcement (Terran)", 0) > 0', body)
        self.assertIn('packed |= 1 << 10', body)

    def test_native_ap_mercenary_explicitly_recognized(self):
        body = galaxy_function("APRG_ApplyRepeatContractorCooldowns")
        self.assertIn('g_aprgMercenaryUpgradePacked2 & 1024', body)
        self.assertIn('reduction += 60.0', body)
        self.assertIn('if (abilityType == "AP_SummonMercenaries" &&', body)
        self.assertIn('APRG_ReduceActiveMercenaryCooldownOnce(', body)

    def test_no_negative_delta_for_active_player_timer(self):
        body = galaxy_function("APRG_ReduceActiveMercenaryCooldownOnce")
        self.assertIn('MaxF(0.0, remaining - reduction)', body)
        self.assertIn('libNtve_gf_PlayerRemoveCooldown(player, link)', body)
        self.assertIn('if (target > 0.0) { PlayerAddCooldown(player, link, target); }', body)
        self.assertNotIn('PlayerAddCooldown(player, link, -', body)

    def test_catalog_bounded(self):
        body = galaxy_function("APRG_ReduceMercenaryCooldownField")
        self.assertIn('MaxF(1.0, value - reduction)', body)
        self.assertIn('APRG_ClampMercenaryCooldownField', body)

    def test_player_watchdog_without_structure(self):
        watch = galaxy_function("APRG_SanitizeKnownAPMercenaryTimers")
        self.assertIn('AP_SummonMercenaries', watch)
        self.assertIn('PlayerGetCooldown(player, link)', watch)
        self.assertIn('remaining > 1000.0', watch)
        self.assertIn('PlayerAddCooldown(player, link, 10.0)', watch)
        tick = galaxy_function("APRG_TickContractStructures")
        self.assertIn('APRG_SanitizeKnownAPMercenaryTimers(player)', tick)

    def test_no_huge_negative_player_repair(self):
        body = galaxy_function("APRG_ClearSuspiciousMercenaryTimerLink")
        self.assertNotIn('PlayerAddCooldown(player, link, 10.0 - remaining)', body)
        self.assertNotIn('PlayerAddChargeRegen(player, link, 10.0 - remaining)', body)
        self.assertIn('libNtve_gf_PlayerRemoveCooldown(player, link)', body)


if __name__ == "__main__":
    unittest.main()
