"""v1.2.2.1: offline regression guards for mercenary cooldown recovery.

These tests inspect Galaxy source and model arithmetic. They do not execute
native SC2 cooldown, charge, or player timer functions.
"""
import re
import unittest
from pathlib import Path

GALAXY = (Path(__file__).resolve().parents[1] / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")

def function(name):
    match = re.search(r"(?m)^void " + re.escape(name) + r"\([^\n]*\) \{", GALAXY)
    if not match:
        raise AssertionError("Missing Galaxy function: " + name)
    end = GALAXY.find("\n}\n", match.end())
    if end < 0:
        raise AssertionError("Missing close brace: " + name)
    return GALAXY[match.start():end+2]

class MercenaryCooldownGuards(unittest.TestCase):
    def test_catalog_overflow_and_negative_clamps(self):
        body = function("APRG_ClampMercenaryCooldownField")
        for term in ('value > 1000.0', 'value < 0.0', 'initialTimer ? "0" : "1"',
                     'value > 0.0 && value < 1.0', 'if (rawValue == "") { return; }'):
            self.assertIn(term, body)
        self.assertNotIn('value > 500.0', body)

    def test_reduction_before_after_and_repair_is_not_reduced_again(self):
        body = function("APRG_ReduceMercenaryCooldownField")
        self.assertIn('value > 1000.0 || value < 0.0', body)
        self.assertIn('MaxF(1.0, value - reduction)', body)
        self.assertIn('APRG_ClampMercenaryCooldownField(player, abilityType, field);\n        return;', body)
        self.assertEqual(body.count('APRG_ClampMercenaryCooldownField('), 3)
        horde = function("APRG_HordeHalveAbilityField")
        self.assertIn('MaxF(1.0, value * 0.5)', horde)
        self.assertEqual(horde.count('APRG_ClampMercenaryCooldownField('), 2)

    def test_all_timer_scopes_above_1000_recovered_to_ten(self):
        body = function("APRG_ClearSuspiciousMercenaryTimerLink")
        self.assertGreaterEqual(body.count('remaining > 1000.0'), 6)
        for term in ('UnitAbilityGetCooldown(', 'UnitGetCooldown(', 'PlayerGetCooldown(',
                     'UnitAbilityGetChargeRegen(', 'UnitGetChargeRegen(', 'PlayerGetChargeRegen(',
                     'UnitModifyCooldown(structure, link, 10.0',
                     'PlayerAddCooldown(player, link, 10.0 - remaining)',
                     'PlayerAddChargeRegen(player, link, 10.0 - remaining)'):
            self.assertIn(term, body)

    def test_all_owned_merc_buildings_and_unknown_ap_abilities(self):
        scan = function("APRG_SanitizeAllOwnedContractStructureTimers")
        for term in ('APRG_PlayerAllUnits(player)', 'APRG_IsTerranContractStructureType(candidateType)',
                     'APRG_IsZergContractStructureType(candidateType)',
                     'APRG_SanitizeContractStructureTimers(candidate, player)'):
            self.assertIn(term, scan)
        watch = function("APRG_SanitizeContractStructureTimers")
        self.assertNotIn('!APRG_IsMercenaryRecruitAbility(abilityType, player)', watch)
        self.assertNotIn('!APRG_MercenaryCommandProducesUnit(abilityType, infoIndex, player)', watch)
        tick = function("APRG_TickContractStructures")
        self.assertIn('now + 3.0', tick)
        self.assertIn('APRG_SanitizeAllOwnedContractStructureTimers(player)', tick)

    def test_arithmetic_cases(self):
        def clamp(value, initial=False):
            if value > 1000: return 10
            if value < 0: return 0 if initial else 1
            if 0 < value < 1: return 1
            return value
        def reduce(value, subtract, initial=False):
            if value > 1000 or value < 0: return clamp(value, initial)
            value = clamp(value, initial)
            if subtract > 0 and value > 0: value = max(1, value - subtract)
            return clamp(value, initial)
        for start, subtract, expected in ((15, 60, 1), (15, 90, 1), (300, 30, 270),
                                           (1200, 30, 10), (-75, 30, 1),
                                           (1000, 30, 970)):
            self.assertEqual(reduce(start, subtract), expected)
        self.assertEqual(reduce(0, 60, True), 0)
        self.assertEqual(clamp(-4, True), 0)
        self.assertEqual(clamp(1000.01), 10)
        self.assertEqual(clamp(900), 900)

if __name__ == "__main__":
    unittest.main()
