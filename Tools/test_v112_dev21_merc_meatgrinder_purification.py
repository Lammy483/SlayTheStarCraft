"""Dev21 offline regressions: merc cooldown bounds, Marines AI and objectives."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def f(name):
    m = re.search(r'(?m)^(?:void|bool|int|unit|fixed)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', G)
    assert m, name
    depth = 0
    for i in range(m.end()-1,len(G)):
        if G[i] == '{': depth += 1
        if G[i] == '}':
            depth -= 1
            if depth == 0: return G[m.end()-1:i+1]
    raise AssertionError(name)


class MercCoolDownFloor(unittest.TestCase):
    def test_repeat_contractor_floor_one(self):
        x=f('APRG_ReduceMercenaryCooldownField')
        self.assertIn('APRG_ClampMercenaryCooldownField',x)
        self.assertIn('MaxF(1.0, value - reduction)',x)
        self.assertNotIn('MaxF(0.0, value - reduction)',x)

    def test_AP_other_upgrades_floor_and_does_not_overwrite_legitimate_zero(self):
        x=f('APRG_ClampMercenaryCooldownField')
        self.assertIn('CatalogFieldValueGet(c_gameCatalogAbil, abilityType, field, 0)',x)
        self.assertIn('value > 0.0 && value < 1.0',x)
        self.assertIn('value <= 0.0 && unmodified > 0.0',x)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogAbil, abilityType, field, player, "1")',x)
        self.assertIn('if (value > 500.0)',x)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogAbil, abilityType, field, player, "10")',x)

    def test_watchdog_restores_catalog_bounds_and_overflow(self):
        x=f('APRG_SanitizeContractStructureTimers')
        self.assertIn('APRG_ReduceMercenaryCooldownField(player, abilityType,',x)
        self.assertIn('APRG_ClearSuspiciousMercenaryTimerLink',x)
        y=f('APRG_TickContractStructures')
        self.assertIn('now + 3.0',y)
        self.assertIn('APRG_SanitizeContractStructureTimers(g_aprgTerranContractStructure',y)
        self.assertIn('APRG_SanitizeContractStructureTimers(g_aprgZergContractStructure',y)
        self.assertIn('UnitModifyCooldown(structure, link, 10.0',f('APRG_ClearSuspiciousMercenaryTimerLink'))

    def test_horde_halving_does_not_create_zero_duration_for_mercs(self):
        x=f('APRG_HordeHalveAbilityField')
        self.assertIn('APRG_IsMercenaryRecruitAbility',x)
        self.assertIn('MaxF(1.0, value * 0.5)',x)

    def test_meat_grinder_marines_periodically_retarget_even_without_cloning(self):
        x=f('APRG_SpawnMeatGrinderExtra')
        self.assertIn('UnitGroupAdd(g_aprgClonedUnits, extra)',x)
        self.assertIn('APRG_OrderGroupTowardNearestEnemyStructure(created, p, player)',x)
        tick=f('APRG_RetargetClonedUnits')
        self.assertIn('g_aprgNextCloneRetargetTime = now + 10.0',tick)
        self.assertIn('APRG_OrderCloneTowardValidTarget(clone, player)',tick)
        self.assertIn('APRG_HasExtension4(APRG_EXT4_BOON_MEAT_GRINDER)) { APRG_RetargetClonedUnits(player, now); }',G)

    def test_objectives_ignore_slays_explosive_armor_and_direct_damage(self):
        self.assertIn('if (APRG_IsCampaignNullCircuit(target)) { continue; }',f('APRG_DealExplosiveArmorDamage'))
        self.assertIn('APRG_IsCampaignNullCircuit(target)',f('APRG_DealDirectDamage'))
        self.assertIn('UnitGetType(u)',f('APRG_IsCampaignNullCircuit'))

    def test_slays_aoe_effects_skip_circuits_but_do_not_change_native_mission_damage(self):
        self.assertIn('APRG_SlayEffectOverlapsNullCircuit(p, radius)',f('APRG_CreateObjectiveSafeSlayEffect'))
        self.assertIn('PlayerCreateEffectPoint(owner, effectType, p)',f('APRG_CreateObjectiveSafeSlayEffect'))
        self.assertIn('APRG_IsCampaignNullCircuit(u)',f('APRG_SlayEffectOverlapsNullCircuit'))
        self.assertEqual(G.count('PlayerCreateEffectPoint('),1, 'all scripted area effects should go through the wrapper')
        for effect in ('NukeDamage','PsiStormPersistent'):
            self.assertIn(f'APRG_CreateObjectiveSafeSlayEffect(player, "{effect}"',G)

if __name__ == '__main__': unittest.main()
