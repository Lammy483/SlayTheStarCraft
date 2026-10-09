"""r28 behavior regression: Templar Storm priority, Spear eligibility, mission exclusions, warp FX."""
import ast
import re
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')
CLIENT = (ROOT / 'Payload' / 'slay_the_starcraft.py').read_text(encoding='utf-8')
GENERATOR = (ROOT / 'Payload' / 'generate_slay_run.py').read_text(encoding='utf-8')


def galaxy_function(name):
    match = re.search(r'^(?:void|bool|int|fixed|string|unit|unitgroup|actor)\s+' +
                      re.escape(name) + r'\s*\([^)]*\)\s*\{', GALAXY, re.M)
    if match is None:
        raise AssertionError(f'Missing Galaxy function {name}')
    brace = GALAXY.index('{', match.start())
    depth = 1
    for i in range(brace + 1, len(GALAXY)):
        if GALAXY[i] == '{':
            depth += 1
        elif GALAXY[i] == '}':
            depth -= 1
            if depth == 0:
                return GALAXY[brace:i + 1]
    raise AssertionError(f'Unclosed Galaxy function {name}')


def python_function(source, name, scope):
    parsed = ast.parse(source)
    functions = [n for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(functions) == 1, name
    exec(compile(ast.Module(body=functions, type_ignores=[]), f'<{name}>', 'exec'), scope)
    return scope[name]


class R28RegressionTests(unittest.TestCase):
    def test_storm_is_prioritized_for_autonomous_high_templar(self):
        special = galaxy_function('APRG_TryHighTemplarStorm')
        generic = galaxy_function('APRG_TryCategorizedAutonomousAbility')
        self.assertIn('HighTemplar', special)
        self.assertIn('Signifier', special)
        self.assertIn('PsiStorm', special)
        self.assertIn('PsionicStorm', special)
        self.assertIn('APRG_AIOpposingTargetsNear', special)
        self.assertIn('DistanceBetweenPoints(candidatePoint, UnitGetPosition(other)) <= 2.5', special)
        self.assertIn('APRG_TryAutonomousPointOrder', special)
        self.assertIn('APRG_QueuePriorAutonomousOrder', special)
        self.assertLess(generic.index('APRG_TryHighTemplarStorm'), generic.index('APRG_AbilityUsesNativeAutocastCached'))
        potion_spawn = galaxy_function('APRG_TickPotionSpawnQueues')
        self.assertIn('UnitGroupAdd(g_aprgPotionAutoSpellcasters, spawned)', potion_spawn)
        self.assertIn('APRG_TryFriendlyAutonomousAbility(spawned, player)', potion_spawn)

    def test_recharge_changes_energy_only(self):
        recharge = galaxy_function('APRG_PotionRechargeSpearCaster')
        self.assertIn('c_unitPropEnergyMax', recharge)
        self.assertIn('c_unitPropEnergy', recharge)
        for token in ('Cooldown', 'cooldown', 'CatalogFieldValueSet', 'UnitAbility'): 
            self.assertNotIn(token, recharge)
        self.assertIn('APRG_PotionRechargeSpearCaster', galaxy_function('APRG_PotionRechargeSpear'))
        self.assertIn("Set the Spear of Adun's energy to maximum.", CLIENT)
        catalog = (ROOT / 'Payload' / 'POTION_CATALOG.csv').read_text(encoding='utf-8')
        self.assertIn("Spear of Adun Recharge,Set the Spear of Adun's energy to maximum.", catalog)

    def test_potion_needs_two_distinct_active_spear_abilities(self):
        purchased = {'Progressive Proxy Pylon (Spear of Adun)': 1}
        scope = {'Any': Any, 'SPEAR_UNLOCK': 'Spear Unlock',
                 'SPEAR_FALLBACK_ITEMS': {'Progressive Proxy Pylon (Spear of Adun)',
                                          'Orbital Strike (Spear of Adun)',
                                          'Solar Lance (Spear of Adun)',
                                          'Guardian Shell (Spear of Adun)',
                                          'Reconstruction Beam (Spear of Adun)',
                                          'Overwatch (Spear of Adun)'},
                 '_progression_owned': lambda ctx, item: ctx.get('unlocked', False),
                 '_purchased_count': lambda ctx, item: purchased.get(item, 0),
                 'POTION_CATALOG': {'potion12': {'index': 12}},
                 'KERRIGAN_UNLOCK': 'kerrigan', 'potion_mercenary_mask': lambda ctx: 0}
        count = python_function(CLIENT, '_spear_unlocked_active_ability_count', scope)
        eligible = python_function(CLIENT, '_potion_unlock_eligible', scope)
        self.assertEqual(count({'unlocked': False}), 0)
        self.assertFalse(eligible({'unlocked': False}, 'potion12'))
        self.assertEqual(count({'unlocked': True}), 1)
        self.assertFalse(eligible({'unlocked': True}, 'potion12'))
        purchased['Guardian Shell (Spear of Adun)'] = 1
        purchased['Overwatch (Spear of Adun)'] = 1
        self.assertFalse(eligible({'unlocked': True}, 'potion12'), 'Passive abilities must not count')
        purchased['Solar Lance (Spear of Adun)'] = 5
        self.assertEqual(count({'unlocked': True}), 2, 'Multiple levels are one distinct ability')
        self.assertTrue(eligible({'unlocked': True}, 'potion12'))
        purchased['Progressive Proxy Pylon (Spear of Adun)'] = 0
        self.assertFalse(eligible({'unlocked': True}, 'potion12'))

    def test_nexus_shields_blocked_on_smash_and_grab_generator_and_runtime(self):
        gscope = {'Any': Any, 'LIMITED_BANK_MISSION_EXCLUSIONS': set(),
                  'GORGON_MISSION_EXCLUSIONS': set(), 'ISLAND_MISSION_NAMES': set(),
                  'DESTRUCTION_MISSION_EXCLUSIONS': set(), 'DESTRUCTION_TIMED_DEFENSE_ALLOWLIST': set(),
                  'dependency_sensitive_effect_exclusions': lambda name: (set(), set()),
                  'RICH_MINERALS_MISSION_EXCLUSIONS': set()}
        exclusions = python_function(GENERATOR, '_effect_exclusions_for_mission', gscope)
        self.assertIn('nexus_shield', exclusions({'name': 'Smash and Grab'})[0])
        self.assertIn('nexus_shield', exclusions({'short_name': 'Smash and Grab', 'name': 'Smash and Grab (WoL)'})[0])
        self.assertNotIn('nexus_shield', exclusions({'name': 'The Outlaws'})[0])
        rscope = {'Any': Any, 'DISABLED_MUTATIONS': set(),
                  'node': lambda ctx, mission_id: {'mission_name': ctx['mission_name']},
                  '_mission_base_name': lambda name: name,
                  'GORGON_MISSION_EXCLUSIONS': set(), 'ISLAND_MISSION_NAMES': set(),
                  'DEPENDENCY_SENSITIVE_MISSIONS': set(),
                  'SWARM_DEPENDENCY_MUTATIONS': set(), 'VOID_DEPENDENCY_MUTATIONS': set()}
        allowed = python_function(CLIENT, '_mutation_allowed_for_mission', rscope)
        self.assertFalse(allowed({'mission_name': 'Smash and Grab'}, 1, 'nexus_shield'))
        self.assertTrue(allowed({'mission_name': 'The Outlaws'}, 1, 'nexus_shield'))
        self.assertTrue(allowed({'mission_name': 'Smash and Grab'}, 1, 'another_gorgon_mutation'))

    def test_warp_uses_campaign_proven_attached_model_and_preserves_stun(self):
        warp = galaxy_function('APRG_CreateWarpVisual')
        self.assertIn('libNtve_gf_AttachModelToUnit(u, "ProtossGenericWarpInOut", "Ref_Center")', warp)
        self.assertIn('libNtve_gf_ActorLastCreated()', warp)
        self.assertLess(warp.index('AttachModelToUnit'), warp.index('ProtossFastWarpinMarker'))
        for name in ('APRG_ProcessAllyWarpQueue', 'APRG_ProcessPurifierHostileWarpQueue'):
            body = galaxy_function(name)
            self.assertIn('APRG_CreateWarpVisual(u, spawnPoint)', body)
            self.assertIn('libNtve_gf_PauseUnit(u, true)', body)
            self.assertIn('libNtve_gf_SetOpacity(1.0, 5.0)', body)
            self.assertIn('libNtve_gf_PauseUnit(u, false)', body)


if __name__ == '__main__':
    unittest.main()
