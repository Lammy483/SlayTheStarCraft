"""v1.1.2 Dev18: commander Artanis must resolve to LotV ground hero and request its catalog."""
from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLIENT = (ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
GALAXY = (ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')


def galaxy_function(name: str) -> str:
    match = re.search(r'^(?:bool|int|string|void|unitgroup)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', GALAXY, re.M)
    if not match:
        raise AssertionError(f'missing Galaxy function {name}')
    opening = GALAXY.index('{', match.start())
    depth = 1
    for i in range(opening+1, len(GALAXY)):
        if GALAXY[i] == '{': depth += 1
        elif GALAXY[i] == '}':
            depth -= 1
            if depth == 0:
                return GALAXY[opening:i+1]
    raise AssertionError(f'unclosed Galaxy function {name}')


def load_dependency_picker(index: int, campaign: str = 'Wings of Liberty', name: str='Zero Hour'):
    prog = ast.parse(CLIENT)
    node = next(n for n in prog.body if isinstance(n,ast.FunctionDef) and n.name=='dependency_variant_for_mission')
    globals_: dict[str, Any] = {
        'Any': Any,
        'enabled': lambda ctx: True,
        'node': lambda ctx, mid: {'campaign': campaign, 'mission_name': name},
        '_mission_base_name': lambda n: n,
        'DEPENDENCY_SENSITIVE_MISSIONS': {'safe haven', "haven's fall"},
        'KERRIGAN_UNLOCK': 'kerrigan_unlock',
        '_progression_owned': lambda ctx, item: False,
        '_effective_mutations': lambda ctx, mid: [],
        '_effective_blessings': lambda ctx, mid: ['general'],
        'SWARM_DEPENDENCY_MUTATIONS': set(),
        'SWARM_DEPENDENCY_BLESSINGS': set(),
        'VOID_DEPENDENCY_MUTATIONS': set(),
        '_logic_owned_item_counts': lambda ctx: {},
        'ZERG_MERCENARY_ITEMS': set(),
        'VOID_NATIVE_CAMPAIGNS': {'Legacy of the Void','Prologue','Epilogue'},
        'commander_hero_index': lambda ctx, mid: index,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<dependency test>', 'exec'), globals_)
    return globals_['dependency_variant_for_mission'](None, 99)


class ArtanisCommanderDev18(unittest.TestCase):
    def test_native_lotv_artanis_unit_resolves_before_any_other(self):
        lookup = galaxy_function('APRG_ArtanisHeroType')
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, "ArtanisVoid")', lookup)
        self.assertIn('return "ArtanisVoid"', lookup)
        self.assertNotIn('return "Artanis"', lookup, 'Bare Artanis is the WoL mothership')
        self.assertNotIn('Urun', lookup)

    def test_index_nine_routes_to_real_artanis_no_random_fallback(self):
        self.assertIn('if (index == 9) { return APRG_ArtanisHeroType(); }',galaxy_function('APRG_HeroCandidate'))
        self.assertIn('if (slot == 3) { return APRG_ArtanisHeroType(); }',galaxy_function('APRG_CommanderFallbackCandidate'))
        selector=galaxy_function('APRG_FindValidHeroTypeFromIndex')
        self.assertIn('if (preferredIndex == 9) { return APRG_ArtanisHeroType(); }',selector)
        self.assertLess(selector.index('if (preferredIndex == 9)'),selector.index('return APRG_FindValidCommanderHeroType()'))

    def test_native_artanis_spawns_directly_and_respawns_same_type(self):
        source = galaxy_function('APRG_GiveGeneralIfReady')
        self.assertIn('g_aprgCommanderHeroType == "ArtanisVoid"', source)
        self.assertIn('heroType == "ArtanisVoid"', source)
        self.assertEqual(source.count('APRG_CreatePlayerUnitsVanillaSafe'),2)
        self.assertIn('g_aprgCommanderHeroIndex == 9',source)
        self.assertIn('Artanis could not spawn', source)

    def test_non_lotv_mission_requests_void_for_artanis(self):
        self.assertEqual(load_dependency_picker(9), 'void')
        self.assertEqual(load_dependency_picker(9,'Heart of the Swarm'), 'void')
        self.assertEqual(load_dependency_picker(9,'Legacy of the Void'), 'base')
        self.assertEqual(load_dependency_picker(10), 'void')
        self.assertEqual(load_dependency_picker(30), 'void')
        self.assertEqual(load_dependency_picker(7), 'base')

    def test_haven_dependency_exclusion_not_overridden(self):
        self.assertEqual(load_dependency_picker(9, name='Safe Haven'), 'base')
        self.assertEqual(load_dependency_picker(9, name="Haven's Fall"), 'base')

    def test_revision_matches_manifest_and_bootstrap(self):
        rev = json.loads((ROOT/'launcher_manifest.json').read_text(encoding='utf-8'))['runtime_revision']
        self.assertIn('dev27',rev)
        self.assertIn(f'runtimeRevision = "{rev}"',(ROOT/'Tools/slay_launcher_windows.go').read_text(encoding='utf-8'))
        self.assertIn(f'$RuntimeRevision = "{rev}"',(ROOT/'Tools/bootstrap_slay_runtime.ps1').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
