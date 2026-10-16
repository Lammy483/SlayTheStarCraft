"""Regression contracts for Spear of Adun autonomous caster gating."""
import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT/'Payload'/'APRogue.galaxy').read_text(encoding='utf-8')
RUNTIME = (ROOT/'Payload'/'slay_the_starcraft.py').read_text(encoding='utf-8')
INSTALLER = (ROOT/'Payload'/'install_slay.py').read_text(encoding='utf-8')


def body(name):
    match = re.search(r'\b(?:bool|void|unit|fixed)\s+' + re.escape(name) + r'\([^\n]*\)\s*\{', GALAXY)
    if not match:
        raise AssertionError('Missing Galaxy function ' + name)
    depth = 1
    i = match.end()
    while depth and i < len(GALAXY):
        if GALAXY[i] == '{': depth += 1
        elif GALAXY[i] == '}': depth -= 1
        i += 1
    if depth: raise AssertionError('Unbalanced Galaxy function '+name)
    return GALAXY[match.end():i - 1]

class SpearAutonomousPassiveDev11(unittest.TestCase):
    def test_pre_base_disables_both_casters_and_base_restores_both(self):
        gate = body('APRG_TickSpearBaseGate')
        self.assertIn('APRG_PinSpearPreBase(caster, player);',gate)
        self.assertIn('APRG_PinSpearPreBase(autonomousCaster, player);',gate)
        self.assertIn('APRG_ReleaseSpearCooldownsAtBase(caster, player);',gate)
        self.assertIn('APRG_ReleaseSpearAutonomousAbilitiesAtBase(autonomousCaster);',gate)
        self.assertLess(gate.index('if (!APRG_PlayerMacroBaseReady(player))'),gate.index('APRG_ReleaseSpearAutonomousAbilitiesAtBase(autonomousCaster);'))
    def test_autonomous_caster_regains_abilities_without_cooldown_reset(self):
        gate = body('APRG_ReleaseSpearAutonomousAbilitiesAtBase')
        self.assertIn('UnitAbilityEnable(caster, abilityType, true);',gate)
        self.assertNotIn('APRG_SetSpearCooldownLink(',gate)
        self.assertNotIn('UnitModifyCooldown(',gate)
        self.assertIn('UnitAbilityEnable(caster, abilityType, false);',body('APRG_PinSpearPreBase'))
    def test_spear_purchase_is_still_injected_into_ap_tech(self):
        self.assertIn('"Reconstruction Beam (Spear of Adun)"',RUNTIME)
        self.assertIn('def augment_network_items(',RUNTIME)
        self.assertIn('for item_name,bought_raw in state(ctx).get("purchases",{}).items():',RUNTIME)
        self.assertIn('slay.augment_network_items(ctx, items, item_list)',INSTALLER)
        self.assertIn('result |= 0b111111',RUNTIME)
if __name__ == '__main__': unittest.main()
