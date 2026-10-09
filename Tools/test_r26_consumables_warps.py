"""Regression coverage for r26 consumables and scripted warp staging."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')
INSTALL = (ROOT / 'Payload' / 'install_slay.py').read_text(encoding='utf-8')


def fn(name):
    m = re.search(r'^(?:bool|void|int|fixed|string|unit|unitgroup|actor)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', GALAXY, re.M)
    if m is None: raise AssertionError('Missing function: ' + name)
    start = m.start()
    brace = GALAXY.index('{', start)
    depth = 1
    for i in range(brace + 1, len(GALAXY)):
        if GALAXY[i] == '{': depth += 1
        elif GALAXY[i] == '}':
            depth -= 1
            if not depth: return GALAXY[brace:i+1]
    raise AssertionError('Unclosed function ' + name)


class R26ConsumableTests(unittest.TestCase):
    def test_early_commander_mapping_unchanged(self):
        self.assertIn('return "RaynorCommando"', GALAXY)
        self.assertIn('return "TychusCommando"', GALAXY)

    def test_potion_ui_shift_without_info_notice(self):
        self.assertIn('DialogCreate(544, 60, c_anchorTopLeft, 320, 0, false)', GALAXY)
        self.assertNotIn('APRG_ConsumableNotice(', GALAXY)
        self.assertNotIn('g_aprgConsumableNoticeUntil', fn('APRG_TickPotions'))
        self.assertNotIn('[Slay] Used ', GALAXY)

    def test_native_spellcasters_and_energy(self):
        self.assertIn('APRG_CreatePlayerUnitsVanillaSafe(1, unitType, player, p', fn('APRG_TickPotionSpawnQueues'))
        self.assertIn('UnitGetPropertyFixed(spawned, c_unitPropEnergyMax', fn('APRG_TickPotionSpawnQueues'))
        self.assertIn('APRG_PlayerSpawnCandidateHealthy(player, "DefilerMP", false)', fn('APRG_TickPotionSpawnQueues'))
        self.assertIn('return "Infestor"', fn('APRG_PotionSpellcasterType'))

    def test_spear_recharge_only_restores_energy(self):
        f = fn('APRG_PotionRechargeSpearCaster')
        self.assertIn('c_unitPropEnergyMax', f)
        self.assertNotIn('ModifyCooldown', f)
        self.assertNotIn('PlayerRemoveCooldown', f)
        self.assertIn('APRG_PotionRechargeSpearCaster(autonomous, player)', fn('APRG_PotionRechargeSpear'))

    def test_merc_favor_uses_actual_units_and_squad_sizes(self):
        f = fn('APRG_PotionMercType')
        self.assertIn('return "WarPig"', f)
        self.assertIn('return "DevilDog"', f)
        self.assertNotIn('return "WarPigs"', f)
        self.assertIn('if (mercUnitType == "WarPig") { return 4; }', fn('APRG_PotionMercSquadCount'))
        self.assertIn('APRG_PotionMercSquadCount(player, unitType)', fn('APRG_PotionActivate'))

    def test_warp_visual_and_five_second_pause(self):
        self.assertIn('g_aprgAllyWarpTime[best] = now + 5.0', fn('APRG_ProcessAllyWarpQueue'))
        self.assertIn('g_aprgPurifierWarpTime[best] = now + 5.0', fn('APRG_ProcessPurifierHostileWarpQueue'))
        self.assertIn('libNtve_gf_AttachModelToUnit', fn('APRG_CreateWarpVisual'))
        self.assertIn('APRG_CreateWarpVisual(u, spawnPoint)', fn('APRG_ProcessPurifierHostileWarpQueue'))

    def test_hyperion_native_energy_pool(self):
        f = fn('APRG_NormalizeHyperionBoon')
        self.assertIn('c_unitPropEnergyMax, 200.0', f)
        self.assertIn('c_unitPropEnergy, 200.0', f)
        self.assertIn('"Cost[0].Vital[2]"', f)

    def test_installer_recognizes_actor_returned_helpers(self):
        self.assertIn('unitgroup|point|actor', INSTALL)


if __name__ == '__main__':
    unittest.main()
