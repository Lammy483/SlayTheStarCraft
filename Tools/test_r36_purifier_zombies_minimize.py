"""r36 offline regressions: minimized consumable HUD, zombie tags, Purifier AI and shield."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
S = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def fn(name):
    m = re.search(r'^(?:void|bool)\s+' + re.escape(name) + r'\([^)]*\)\s*\{', S, re.M)
    if not m: raise AssertionError('Missing Galaxy function: ' + name)
    start = S.index('{', m.start())
    level = 0
    for pos in range(start, len(S)):
        if S[pos] == '{': level += 1
        if S[pos] == '}':
            level -= 1
            if not level: return S[start:pos+1]
    raise AssertionError('Unclosed function ' + name)


class R36Tests(unittest.TestCase):
    def test_hud_minimize_and_restore_with_small_dialog(self):
        self.assertIn('int g_aprgPotionMinimizeButton = 0;', S)
        self.assertIn('bool g_aprgPotionMinimized = false;', S)
        tick = fn('APRG_TickPotions')
        toggle = fn('APRG_PotionMinimize_Func')
        refresh = fn('APRG_PotionRefreshButtons')
        self.assertIn('g_aprgPotionMinimizeButton = DialogControlCreate(', tick)
        self.assertIn('g_aprgPotionMinimizeTrigger = TriggerCreate("APRG_PotionMinimize_Func")', tick)
        self.assertIn('DialogSetSize(g_aprgPotionDialog, 42, 44)', toggle)
        self.assertIn('DialogSetSize(g_aprgPotionDialog, 544, 60)', toggle)
        self.assertIn('!g_aprgPotionMinimized', refresh)
        self.assertIn('g_aprgPotionMinimized = false;', S)
        self.assertNotIn('UIDisplayMessage(', toggle)

    def test_zombie_generated_units_tagged_and_cross_excluded(self):
        self.assertIn('"APRG_BasicZombie_"', fn('APRG_SpawnZombie'))
        self.assertIn('"APRG_ZombieApocalypse_"', fn('APRG_TagZombieApocalypseGroup'))
        for name in ('APRG_BasicZombieDeathExcluded', 'APRG_ZombieApocalypseDeathExcluded'):
            body = fn(name)
            self.assertIn('"APRG_BasicZombie_"', body)
            self.assertIn('"APRG_ZombieApocalypse_"', body)
            self.assertIn('APRG_DeathSpawnExcluded(dead, unitType)', body)
            self.assertNotIn('StringContains(unitType, "InfestedTerran"', body)
            self.assertNotIn('StringContains(unitType, "InfestedCivilian"', body)

    def test_ally_warp_added_to_retarget_ai_after_unpause(self):
        ally = fn('APRG_ProcessAllyWarpQueue')
        self.assertIn('UnitGroupAdd(g_aprgAlliedSupport, u);', ally)
        self.assertIn('UnitGroupAdd(g_aprgPurifierAllianceReinforcements, u);', ally)
        self.assertLess(ally.index('libNtve_gf_PauseUnit(u, false)'), ally.index('UnitGroupAdd(g_aprgAlliedSupport, u)'))
        self.assertIn('APRG_OrderGroupTowardNearestEnemyStructure(ready', ally)
        self.assertIn('APRG_RetargetPurifierAllianceReinforcements(player);', fn('APRG_Tick_Func'))

    def test_enemy_purifier_escorts_and_ground_waves_retarget(self):
        hostile = fn('APRG_ProcessPurifierHostileWarpQueue')
        self.assertIn('APRG_AddHostileRaiders(ready, UnitGetPosition(u), player)', hostile)
        self.assertIn('APRG_AddHostileRaiders(created, spawnPoint, player)', hostile)
        self.assertIn('APRG_RetargetRaiders(player)', fn('APRG_Tick_Func'))

    def test_mutation_purifier_vulnerable_in_any_mission(self):
        remove = fn('APRG_RemoveMutationPurifierInvulnerability')
        tick = fn('APRG_TickPurifier')
        self.assertIn('UnitBehaviorRemove(purifier, "InvulnerabilityShield", c_unitBehaviorCountAll)', remove)
        self.assertIn('UnitSetState(purifier, c_unitStateInvulnerable, false)', remove)
        self.assertEqual(tick.count('APRG_RemoveMutationPurifierInvulnerability(g_aprgPurifier)'), 2)
        self.assertNotIn('APRG_RemoveMutationPurifierInvulnerability', fn('APRG_TickPurifierAlliance'))
        self.assertIn('if (u == g_aprgPurifier) { return false; }', fn('APRG_IsScriptedPurifier'))


if __name__ == '__main__':
    unittest.main()
