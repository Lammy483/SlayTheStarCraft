"""Dev12 regression checks for Leviathan-in-Orbit target selection and mercenary timer repair."""
import re
import unittest
from pathlib import Path

GALAXY = (Path(__file__).resolve().parents[1] / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def body(name):
    match = re.search(r'(?m)^(?:void|bool|point|fixed|unit|int)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', GALAXY)
    if match is None:
        raise AssertionError(f'Function not found: {name}')
    start = match.end() - 1
    depth = 0
    for i in range(start, len(GALAXY)):
        if GALAXY[i] == '{': depth += 1
        elif GALAXY[i] == '}':
            depth -= 1
            if not depth: return GALAXY[start:i + 1]
    raise AssertionError(f'Unclosed function: {name}')


class Dev12Regressions(unittest.TestCase):
    def test_leviathan_targets_own_or_allied_units_and_structures(self):
        f=body('APRG_FindLeviathanDropPoint')
        self.assertIn('APRG_PlayerAllUnits(player)',f)
        self.assertIn('c_unitAllianceAlly',f)
        self.assertIn('UnitGroupAdd(targets, candidate)',f)
        self.assertIn('UnitGroupRandomUnit(targets, c_unitCountAlive)',f)
        self.assertIn('APRG_IsCreepTumorType(UnitGetType(candidate))',f)
        self.assertIn('APRG_IsRakShirObjectiveUnit(candidate)',f)
        self.assertIn('APRG_FindGroundPointNear(UnitGetPosition(target)',f)
        self.assertNotIn('APRG_FindRandomGroundPoint()',f)
        self.assertIn('PointPathingIsConnected(p, UnitGetPosition(home))',f)
        self.assertIn('if (home == null) { return null; }',f)

    def test_all_leviathan_pods_use_new_destination(self):
        f=body('APRG_SpawnLeviathanRaid')
        self.assertIn('APRG_FindLeviathanDropPoint(player)',f)
        self.assertIn('APRG_QueueRealDropPod(APRG_DROP_KIND_LEVIATHAN_HOSTILE',f)
        self.assertIn('APRG_ResolveLeviathanHostileDrop(player, owner, p)',f)

    def test_bad_mercenary_catalog_and_active_timers_reset_to_ten(self):
        field=body('APRG_ClampMercenaryCooldownField')
        self.assertIn('if (value > 500.0)',field)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogAbil, abilityType, field, player, "10")',field)
        helper=body('APRG_ClearSuspiciousMercenaryTimerLink')
        self.assertIn('if (remaining > 500.0)',helper)
        self.assertIn('UnitModifyCooldown(structure, link, 10.0, c_cooldownOperationSet)',helper)
        self.assertIn('UnitAbilityAddChargeRegen(structure, abilityType, link, 10.0 - remaining)',helper)

    def test_sanitizer_covers_per_command_and_global_fields(self):
        f=body('APRG_SanitizeContractStructureTimers')
        for part in ('"Cooldown.TimeUse"','"Cooldown.TimeStart"','"Charge.TimeUse"',
                     '"Cost.Cooldown.TimeUse"','"Cost.Charge.TimeStart"',
                     'basePath + ".Cooldown.TimeUse"','basePath + ".Cost.Cooldown.TimeUse"',
                     'costPath + ".Cooldown.TimeUse"','costPath + ".Charge.TimeStart"'):
            self.assertIn(part,f)
        self.assertIn('APRG_MercenaryCommandProducesUnit(abilityType, infoIndex, player)',f)
        self.assertIn('APRG_IsMercenaryRecruitAbility(abilityType, player)',f)

    def test_watchdog_every_three_seconds_on_both_contract_buildings(self):
        f=body('APRG_TickContractStructures')
        self.assertIn('checkMercenaryCooldowns = now >= g_aprgNextMercenaryCooldownWatchTime',f)
        self.assertIn('g_aprgNextMercenaryCooldownWatchTime = now + 3.0',f)
        self.assertIn('APRG_SanitizeContractStructureTimers(g_aprgTerranContractStructure, player)',f)
        self.assertIn('APRG_SanitizeContractStructureTimers(g_aprgZergContractStructure, player)',f)
        self.assertIn('g_aprgNextMercenaryCooldownWatchTime = 0.0',body('APRG_Load_Func'))

if __name__=='__main__': unittest.main()
