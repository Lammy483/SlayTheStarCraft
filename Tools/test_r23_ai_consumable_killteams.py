"""R23 regression checks for live consumable and autonomous combat fixes."""
from __future__ import annotations
import asyncio
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'Payload'
GAL = (P / 'APRogue.galaxy').read_text(encoding='utf-8')
INSTALL = (P / 'install_slay.py').read_text(encoding='utf-8')
XML = ET.parse(P/'APRogueData.xml')

def segment(start, end):
    return GAL.split(start,1)[1].split(end,1)[0]

class R23AIConsumables(unittest.TestCase):
    def test_banelings_use_standard_attack_move(self):
        f = segment('void APRG_OrderBanelingStreamUnit(', 'void APRG_TickBanelingStream(')
        self.assertIn('APRG_OrderAttackMove(u, destination)',f)
        self.assertNotIn('OrderTargetingUnit(AbilityCommand("attack", 0)',f)
        self.assertIn('APRG_RandomFixedPatrolPointForUnit(u, player, true)',f)
        self.assertIn('g_aprgNextBanelingStreamRetargetTime = now + 8.0;',GAL)
        self.assertIn('APRG_CreatePlayerUnitsVanillaSafe(1, "Baneling"',GAL)

    def test_mercenary_bc_native_id_is_priority(self):
        f = segment('string APRG_JacksonsRevengeType()', 'void APRG_SpawnOrlanFortress(')
        self.assertIn('"DukesRevenge"',f)
        self.assertLess(f.index('"DukesRevenge"'),f.index('"Battlecruiser"'))
        self.assertNotIn('"JacksonsRevenge"',f)
        self.assertNotIn('CatalogEntryCount',f)
        self.assertIn('return APRG_JacksonsRevengeType();',GAL)

    def test_standard_target_selection_skips_invulnerable(self):
        for a,b in [('unitgroup APRG_EnemyMobileUnits(', 'unitgroup APRG_PlayerWorkers('),
                    ('unitgroup APRG_AIOpposingTargetsNear(', 'unit APRG_AIClosestOpposingTarget('),
                    ('unit APRG_NearestPathablePlayerStructureFromGroup(unit mover, int player, unitgroup structures) {', 'bool APRG_EnsureAirReachableToPlayer('),
                    ('unit APRG_RandomPlayerStructure(int player) {', 'string APRG_DehakaPackType(')]:
            self.assertIn('c_unitStateInvulnerable', segment(a,b))
        self.assertIn('c_targetFilterInvulnerable',segment('unitgroup APRG_EnemyMobileUnits(', 'unitgroup APRG_PlayerWorkers('))

    def test_marauder_bonus_and_medic_armor(self):
        f=segment('unitgroup APRG_SpawnOneMarauderKillTeam(', 'void APRG_TickMarauderKillTeams(')
        self.assertIn('UnitBehaviorAdd(u, "APRogueKillTeamBonus", u, 1);',f)
        self.assertIn('UnitBehaviorAdd(u, "APRogueKillTeamArmor", u, 1);',f)
        root=XML.getroot()
        buff={x.get('id'):x for x in root.iter('CBehaviorBuff')}
        self.assertEqual(buff['APRogueKillTeamBonus'].find('Modification').get('LifeArmorBonus'),'3')
        self.assertEqual(buff['APRogueKillTeamBonus'].find('Modification').find('DamageDealtUnscaled').get('value'),'3')
        self.assertEqual(buff['APRogueKillTeamArmor'].find('Modification').get('LifeArmorBonus'),'3')

    def test_live_consumables_token_and_serial_safety(self):
        f=segment('bool APRG_PotionLiveUpdate_Func(', 'void APRG_PotionConsume(')
        self.assertIn('if (token != g_aprgTestPotionRunToken) { return true; }',f)
        self.assertIn('g_aprgPotionSerial[i] == serial',f)
        self.assertIn('g_aprgPotionUsed[i] = false',f)
        self.assertIn('APRG_PotionRefreshButtons',f)
        self.assertIn('TriggerAddEventChatMessage(g_aprgPotionLiveUpdateTrigger, c_playerAny, "?SlayConsumables", false);',GAL)
        self.assertNotIn('"?APRogueConsumables"', GAL)

    def test_installer_live_bot_patch_sends_only_on_change(self):
        spec=importlib.util.spec_from_file_location('installer_r23',P/'install_slay.py')
        assert spec and spec.loader
        installer=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        original='''class ArchipelagoBot:
    __slots__ = ('ctx','setup_done','want_close','sent')
    def __init__(self,ctx):
        self.ctx=ctx
        self.setup_done=True
        self.want_close=False
        self.sent=[]
    async def chat_send(self,msg):
        self.sent.append(msg)
    async def on_step(self, iteration: int):
        if self.want_close:
            return
'''
        patched=installer.patch_live_consumable_bot(original)
        self.assertEqual(patched,installer.patch_live_consumable_bot(patched))
        class FakeSlay:
            current=(3,10,0,0)
            @staticmethod
            def enabled(ctx):return True
            @staticmethod
            def state_ready(ctx):return True
            @staticmethod
            def test_potion_run_token(ctx):return 817
            @staticmethod
            def potion_handshake_slots(ctx):return FakeSlay.current
        class Ctx:pass
        ns={'slay':FakeSlay}
        exec(compile(patched,'<patched SC2 client>','exec'),ns)
        bot=ns['ArchipelagoBot'](Ctx())
        async def run():
            await bot.on_step(21)
            await bot.on_step(22)
            await bot.on_step(44)
            FakeSlay.current=(3,10,4,11)
            await bot.on_step(66)
        asyncio.run(run())
        self.assertEqual(bot.sent,['?SlayConsumables 817 3 10 0 0','?SlayConsumables 817 3 10 4 11'])

if __name__=='__main__':unittest.main()
