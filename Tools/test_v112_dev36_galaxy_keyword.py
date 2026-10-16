"""Regression guard: Galaxy built-in types cannot be used as local identifiers."""
from pathlib import Path
import unittest
import re

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')

class Dev36GalaxyKeyword(unittest.TestCase):
    def test_reserved_wave_not_used_as_variable(self):
        self.assertNotRegex(G, r'(?m)^\s*(?:unit|unitgroup|point|int|fixed|string|bool)\s+wave\s*[;=]')

    def test_zagara_baneling_wave_identifier_fixed(self):
        idx = G.index('void APRG_TickZagarasBanelings(int player, fixed now) {')
        end = G.index('\n}', idx)
        body = G[idx:end]
        self.assertIn('unitgroup spawnedBanelings;', body)
        self.assertIn('UnitGroupAddUnitGroup(g_aprgZagaraBanelingUnits, spawnedBanelings);', body)
        self.assertNotRegex(body, r'\bwave\b')
        self.assertIn('APRG_RetargetZagaraBanelings(player);', body)
        self.assertIn('AISetUnitScriptControlled(baneling, false);', body)

if __name__ == '__main__': unittest.main()
