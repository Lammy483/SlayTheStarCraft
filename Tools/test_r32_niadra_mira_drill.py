"""r32 safety regressions for Niadra births, Mira camps and drill channels.

Static checks intentionally focus on the exact mission-script actions; they do
not claim to replace compiling or playing the Galaxy code within StarCraft II.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def body(name: str) -> str:
    m = re.search(r'(?:void|point|bool)\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', SOURCE)
    if not m:
        raise AssertionError(f'{name} not declared')
    depth = 1
    for index in range(m.end(), len(SOURCE)):
        depth += (SOURCE[index] == '{') - (SOURCE[index] == '}')
        if depth == 0:
            return SOURCE[m.end():index]
    raise AssertionError(f'{name} is unbalanced')


class R32Regression(unittest.TestCase):
    def test_niadra_uses_actual_train_ability_and_all_nine_birth_commands(self):
        src = body('APRG_NormalizeNiadraBirthCooldown')
        self.assertIn('"SwarmQueenTrain"', src)
        self.assertIn('"SwarmQueenTrainLarva"', src)
        self.assertIn('birthIndex <= 9', src)
        self.assertIn('"InfoArray[Train" + IntToString(birthIndex) + "]"', src)
        self.assertIn('path + ".Cooldown.Link", owner,', src)
        self.assertIn('path + ".Cooldown.TimeUse", owner, "60"', src)
        self.assertIn('path + ".Cooldown.TimeStart", owner, "60"', src)
        self.assertNotIn('"Cost.Cooldown.TimeUse", owner, "60"', src)
        self.assertNotIn('.Cost.Cooldown', src)
        self.assertIn('APRG_NormalizeNiadraBirthCooldown(u);', body('APRG_RegisterGeneratedHero'))

    def test_mira_spawn_has_building_buffer_pathing_and_no_unsafe_fallback(self):
        src = body('APRG_FindMiraCampPoint')
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(candidate, player, 40.0)', src)
        self.assertIn('APRG_GroundSpawnsNeedPlayerPathing()', src)
        self.assertIn('PointPathingIsConnected(candidate, UnitGetPosition(home))', src)
        self.assertNotIn('return APRG_FindStaticPatrolGroundPoint(', src)
        self.assertRegex(src, r'return\s+null\s*;\s*$')
        self.assertIn('if (campPoint == null) { return; }', body('APRG_SpawnMiraMercenaries'))

    def test_hostile_drill_cuts_beam_at_nine_seconds_and_resumes_after_two(self):
        src = body('APRG_TickEnemyDrillTargetLimit')
        self.assertIn('g_aprgEnemyMutationDrill == null', src)
        self.assertIn('AbilityCommand("stop", 0)', src)
        self.assertIn('libNtve_gf_PauseUnit(g_aprgEnemyMutationDrill, true)', src)
        self.assertIn('libNtve_gf_PauseUnit(g_aprgEnemyMutationDrill, false)', src)
        self.assertIn('g_aprgEnemyDrillResumeTime = now + 2.0', src)
        self.assertIn('g_aprgEnemyDrillNextInterrupt = now + 9.0', src)
        spawn = body('APRG_TrySpawnEnemyDrill')
        self.assertIn('g_aprgEnemyMutationDrill = UnitGroupUnitFromEnd(created, 1)', spawn)
        self.assertIn('g_aprgEnemyDrillNextInterrupt = GameGetMissionTime() + 9.0', spawn)
        self.assertIn('APRG_TickEnemyDrillTargetLimit(now);', SOURCE)


if __name__ == '__main__':
    unittest.main()
