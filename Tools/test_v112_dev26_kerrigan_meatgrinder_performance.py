"""Dev26: verify a robust death timer and amortized spawn/retarget scheduling."""
from pathlib import Path
import unittest
from test_v112_recycled_meat_grinder_dev24 import func

G=(Path(__file__).resolve().parents[1]/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

class KerriganRespawn(unittest.TestCase):
    def test_retries_keep_original_death_timer(self):
        tick=func('APRG_TickShopKerrigan')
        block=tick.split('if (g_aprgShopKerriganDeathTime >= 0.0)')[1].split('fresh = APRG_FindShopKerrigan(player);\n    if (fresh != null')[0]
        self.assertNotIn('g_aprgShopKerriganDeathTime = now',block)
        self.assertIn('g_aprgShopKerriganNextRetryAt = now + 2.0;',tick)
        self.assertIn('APRG_CreateShopKerriganAtHome(player, g_aprgShopKerriganType)',tick)
        self.assertNotIn('UnitRevive(',tick)
    def test_success_message_after_live_playable_check_and_second_delay(self):
        confirm=func('APRG_ConfirmShopKerriganRespawn')
        tick=func('APRG_TickShopKerrigan')
        self.assertEqual(confirm.count('Kerrigan has respawned'),1)
        self.assertNotIn('Kerrigan has respawned',tick)
        self.assertIn('now >= g_aprgShopKerriganVerifyAt',tick)
        self.assertIn('APRG_KerriganSpawnPresent(g_aprgShopKerrigan, player)',tick)
        self.assertIn('g_aprgShopKerriganVerifyAt = now + 1.0;',tick)
        self.assertIn('RegionContainsPoint(RegionPlayableMap(), p)',func('APRG_KerriganSpawnPresent'))
        self.assertIn('UnitTestState(u, c_unitStateSelectable)',func('APRG_KerriganSpawnPresent'))
        self.assertIn('APRG_RemoveKerriganReviveCocoons(player);',confirm)
    def test_inherited_reckless_delay_and_native_grace(self):
        tick=func('APRG_TickShopKerrigan')
        self.assertIn('respawnDelay - 2.0',tick)
        self.assertIn('respawnElapsed < respawnDelay',tick)
        self.assertIn('APRG_KerriganRecklessPowerStacks()',func('APRG_KerriganRespawnDelay'))

class LagMitigation(unittest.TestCase):
    def test_meat_grinder_is_production_queue_not_immediate_batch(self):
        produced=func('APRG_TryMeatGrinderProducedUnit')
        enqueue=func('APRG_EnqueueMeatGrinderMarines')
        process=func('APRG_ProcessMeatGrinderQueue')
        spawn=func('APRG_SpawnMeatGrinderExtra')
        self.assertNotIn('UnitCreate(',produced)
        self.assertNotIn('UnitCreate(',enqueue)
        self.assertIn('APRG_EnqueueMeatGrinderMarines(produced, player);',produced)
        self.assertIn('g_aprgMeatGrinderRemaining[slot] = 5;',enqueue)
        self.assertIn('count < 2',process)
        self.assertIn('APRG_CreatePlayerUnitsAtPoint(1, unitType, player',spawn)
        self.assertIn('APRG_MakeGroupUncommandable(created)',spawn)
        self.assertIn('UnitGroupAdd(g_aprgClonedUnits, extra)',spawn)
        self.assertIn('APRG_OrderGroupTowardNearestEnemyStructure(created, p, player)',spawn)
        self.assertIn('if (g_aprgMeatGrinderQueued > 0) { APRG_ProcessMeatGrinderQueue(); }',func('APRG_FastBoonTick_Func'))
    def test_all_five_marines_survive_queue_capacity_or_overflow(self):
        enqueue=func('APRG_EnqueueMeatGrinderMarines')
        process=func('APRG_ProcessMeatGrinderQueue')
        self.assertEqual(enqueue.count('APRG_SpawnMeatGrinderExtra('),5)
        self.assertIn('g_aprgMeatGrinderQueued >= 1024',enqueue)
        self.assertIn('g_aprgMeatGrinderRemaining[slot] -= 1;',process)
        # Simulated real FIFO scheduler: no count loss at 1, 2, or 20 completions.
        for completions in (1,2,20):
            pending=[5]*completions; created=0; tickmax=0
            while pending:
                at_this_tick=0
                while pending and at_this_tick < 2:
                    pending[0]-=1; at_this_tick+=1;created+=1
                    if pending[0]==0: pending.pop(0)
                tickmax=max(tickmax,at_this_tick)
            self.assertEqual(created,5*completions)
            self.assertLessEqual(tickmax,2)
    def test_retarget_batched_and_target_snapshot_shared(self):
        tick=func('APRG_RetargetClonedUnits')
        select=func('APRG_CloneAttackTarget')
        self.assertIn('work < 40',tick)
        self.assertIn('g_aprgNextCloneRetargetTime = now + 10.0',tick)
        self.assertIn('APRG_OrderCloneTowardValidTarget(clone, player);',tick)
        self.assertIn('g_aprgCloneTargetBuildings = APRG_EnemyTargetableStructures(player)',tick)
        self.assertIn('g_aprgCloneTargetMobile = APRG_EnemyMobileUnits(player)',tick)
        self.assertIn('g_aprgCloneTargetCacheActive = false',tick)
        self.assertIn('g_aprgCloneTargetCacheActive',select)
        self.assertIn('UnitPathableToPoint',select)

if __name__=='__main__':unittest.main()
