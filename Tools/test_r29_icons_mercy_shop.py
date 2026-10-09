"""r29: AP source icons, consumable expansions, squad drops, warp and VO safety."""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'Payload'
CLIENT = (PAYLOAD / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GALAXY = (PAYLOAD / 'APRogue.galaxy').read_text(encoding='utf-8')
UI = (PAYLOAD / 'slay_command_ui.py').read_text(encoding='utf-8')
ICON_MAP = json.loads((PAYLOAD / 'slay_ui_icons.json').read_text(encoding='utf-8'))
DOC_OVERRIDES = json.loads((PAYLOAD / 'slay_docs_icon_overrides.json').read_text(encoding='utf-8'))
ASSETS = PAYLOAD / 'slay_assets/icons'

def galaxy_function(name):
    match = re.search(r'^(?:void|bool|int|fixed|string|unit|unitgroup|actor)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', GALAXY, re.M)
    if not match:
        raise AssertionError('No Galaxy function: ' + name)
    depth = 0
    for offset in range(GALAXY.index('{', match.start()), len(GALAXY)):
        if GALAXY[offset] == '{': depth += 1
        elif GALAXY[offset] == '}':
            depth -= 1
            if depth == 0: return GALAXY[match.start():offset + 1]
    raise AssertionError('Unbalanced function: ' + name)

class R29Regressions(unittest.TestCase):
    def test_all_consumables_have_distinct_appropriate_local_art(self):
        special = {
            4: 'btn-unit-zerg-leviathan.png',
            5: 'btn-unit-terran-battlecruiser.png',
            11: 'btn-ability-terran-stimpack-color.png',
            18: 'btn-unit-protoss-hightemplar.png',
        }
        for i in range(1, 20):
            icon = ICON_MAP.get(f'slay_potion::{i}')
            self.assertTrue(icon, i)
            self.assertTrue((ASSETS / icon).is_file(), (i, icon))
        for i in range(1, 19):
            icon = ICON_MAP.get(f'slay_potion::19::{i}')
            self.assertTrue((ASSETS / icon).is_file(), (i, icon))
        for i, expected in special.items():
            self.assertEqual(ICON_MAP[f'slay_potion::{i}'], expected)
        module = ast.parse(CLIENT)
        icon_function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'shop_entry_icon')
        self.assertIn('POTION_VARIANT_ICONS', ast.get_source_segment(CLIENT, icon_function))
        self.assertNotIn('common consumable icon', ast.get_source_segment(CLIENT, icon_function))

    def test_documented_upgrade_art_takes_precedence(self):
        self.assertGreaterEqual(len(DOC_OVERRIDES), 35)
        local_icon = UI[UI.index('def local_icon('):UI.index('def shop_icon_texture(')]
        self.assertLess(local_icon.index('docs_path=DOCS_ICON_MAP.get'), local_icon.index('mapped=ICON_MAP.get'))
        for name, path in DOC_OVERRIDES.items():
            self.assertTrue(path.startswith('icons/'), name)
            self.assertTrue(ICON_MAP.get(name), name)
        # At least all standard icons in the doc overrides are bundled offline.
        absent = [Path(path).name for path in DOC_OVERRIDES.values() if not (ASSETS / Path(path).name).is_file()]
        self.assertLessEqual(len(absent), 1, absent)

    def test_shop_expansion_adds_consumable_offers_not_inventory_capacity(self):
        stock = CLIENT[CLIENT.index('def _roll_shop_stock('):CLIENT.index('\ndef ', CLIENT.index('def _roll_shop_stock(')+4)]
        self.assertIn('potion_offer_count = 2 + expansion', stock)
        self.assertIn('if len(chosen_potions) >= potion_offer_count:', stock)
        self.assertIn('if len(chosen_potions) < potion_offer_count:', stock)
        self.assertIn('POTION_CAPACITY = 2', CLIENT)
        self.assertIn('including Consumables.', CLIENT)
        self.assertIn('SHOP_STOCK_LOGIC_VERSION = 113', CLIENT)

    def test_mercenary_favor_squad_sizes_and_contract_spawn(self):
        counts=galaxy_function('APRG_PotionMercSquadCount')
        for name, n in {'WarPig':4,'HammerSecurity':2,'DevilDog':2,'DevouringOne':4,'HunterKiller':3}.items():
            self.assertIn(f'if (mercUnitType == "{name}") {{ return {n}; }}', counts)
        self.assertIn('return 1;', counts)
        potion=galaxy_function('APRG_PotionActivate')
        self.assertIn('contractBuilding = g_aprgTerranContractStructure', potion)
        self.assertIn('contractBuilding = g_aprgZergContractStructure', potion)
        self.assertIn('if (contractBuilding == null || !UnitIsAlive(contractBuilding)) { continue; }', potion)
        self.assertIn('APRG_FindGroundPointNear(UnitGetPosition(contractBuilding)', potion)
        self.assertIn('APRG_CreatePlayerUnitsAtPoint(', potion)
        self.assertIn('if (mercSpawned == 0) { return false; }', potion)

    def test_warfield_potion_voice_is_once_not_per_pod(self):
        activate=galaxy_function('APRG_PotionActivate')
        tick=galaxy_function('APRG_TickPotionEffects')
        pending=galaxy_function('APRG_TickPendingDropPods')
        self.assertEqual(activate.count('APRG_PlayWarfieldVO("054")'), 1)
        self.assertNotIn('APRG_PlayWarfieldVO', tick)
        self.assertIn('APRG_DROP_KIND_WARFIELD_POTION', tick)
        potion_branch=pending.split('else if (kind == APRG_DROP_KIND_WARFIELD_POTION)',1)[1].split('else if (kind ==',1)[0]
        self.assertNotIn('APRG_PlayWarfieldVO', potion_branch)
        self.assertNotIn('g_aprgWarfieldNormalDropCount', potion_branch)

    def test_all_scripted_warps_reuse_five_second_visual(self):
        ally=galaxy_function('APRG_ProcessAllyWarpQueue')
        hostile=galaxy_function('APRG_ProcessPurifierHostileWarpQueue')
        visual=galaxy_function('APRG_CreateWarpVisual')
        for fn in [ally,hostile]:
            self.assertIn('APRG_CreateWarpVisual', fn)
            self.assertIn('libNtve_gf_PauseUnit(u, true)', fn)
            self.assertIn('libNtve_gf_SetOpacity(1.0, 5.0)', fn)
            self.assertIn('now + 5.0', fn)
        self.assertIn('ProtossGenericWarpInOut', visual)
        self.assertIn('libNtve_gf_AttachModelToUnit', visual)

if __name__ == '__main__': unittest.main()
