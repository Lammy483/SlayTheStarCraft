"""r37: the Slay Purifiers may Vortex only visible enemy mobile units."""
from pathlib import Path
import re
import unittest

SRC = (Path(__file__).resolve().parents[1] / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def fn(name):
    match = re.search(r'^(?:void|bool)\s+' + re.escape(name) + r'\([^)]*\)\s*\{', SRC, re.M)
    if match is None:
        raise AssertionError(f'Missing Galaxy function {name}')
    begin = SRC.index('{', match.start())
    depth = 0
    for offset in range(begin, len(SRC)):
        if SRC[offset] == '{':
            depth += 1
        elif SRC[offset] == '}':
            depth -= 1
            if depth == 0:
                return SRC[begin:offset + 1]
    raise AssertionError('Unclosed Galaxy function ' + name)


class PurifierVortexRegression(unittest.TestCase):
    def test_slays_mutation_and_boon_only(self):
        selector = fn('APRG_TrySlayPurifierVortex')
        self.assertIn('purifier != g_aprgPurifier && purifier != g_aprgPurifierAlliance', selector)
        self.assertIn('"VortexPurifier"', selector)

    def test_target_visible_nonstruc_enemy_within_native_range(self):
        selector = fn('APRG_TrySlayPurifierVortex')
        self.assertIn('APRG_AIOpposingTargetsNear(purifier, player, friendlyToPlayer, 10.0)', selector)
        self.assertGreaterEqual(selector.count('UnitTypeTestAttribute(UnitGetType(target), c_unitAttributeStructure)'), 2)
        self.assertGreaterEqual(selector.count('libNtve_gf_UnitIsVisibleToPlayer(target, owner)'), 2)
        self.assertIn('if (UnitGroupCount(targets, c_unitCountAlive) <= 0) { return false; }', selector)
        self.assertIn('DistanceBetweenPoints(origin, UnitGetPosition(target)) > 10.0', selector)
        self.assertIn('APRG_TryAutonomousPointOrder(purifier, abilityType, commandIndex, UnitGetPosition(target))', selector)
        self.assertNotIn('APRG_AIClosestOpposingTarget', selector)
        self.assertNotIn('APRG_NearestPlayerStructure', selector)

    def test_no_generic_building_fallback(self):
        generic = fn('APRG_TryCategorizedAutonomousAbility')
        self.assertIn('APRG_TrySlayPurifierVortex(caster, player, friendlyToPlayer)', generic)
        self.assertIn('if ((caster == g_aprgPurifier || caster == g_aprgPurifierAlliance) &&', generic)
        self.assertIn('APRG_AIHas(abilityType, "Vortex")) { continue; }', generic)
        # Other spellcasters keep the standard fallback behavior.
        self.assertIn('APRG_TryAutonomousOffensiveOrder(caster, offensiveTargets', generic)

    def test_mutation_uses_unit_only_selector_without_interrupting_planet_cracker(self):
        mutation = fn('APRG_TickPurifier')
        ally = fn('APRG_TickFriendlyAutonomousAbilities')
        self.assertIn('if (!g_aprgPurifierCrackerIssued) { APRG_TrySlayPurifierVortex(g_aprgPurifier, player, false); }', mutation)
        self.assertIn('APRG_TryFriendlyAutonomousAbility(g_aprgPurifierAlliance, player)', ally)

    def test_combat_order_and_vortex_throttle_preserved(self):
        selector = fn('APRG_TrySlayPurifierVortex')
        self.assertIn('APRG_AICastThrottleReady(purifier, abilityType, APRG_AI_ULTIMATE)', selector)
        self.assertIn('APRG_QueuePriorAutonomousOrder(purifier, previousOrder, hadPreviousOrder)', selector)
        self.assertIn('APRG_RecordAICast(purifier, abilityType)', selector)


if __name__ == '__main__':
    unittest.main()
