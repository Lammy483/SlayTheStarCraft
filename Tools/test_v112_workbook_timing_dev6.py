"""Dev6 source contracts for the October 11 workbook timing/balance update.

These are static regression checks; only live SC2 can verify Galaxy behavior.
"""
import csv
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
S=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')


def section(start,end):
    return G.split(start,1)[1].split(end,1)[0]


class WorkbookDev6(unittest.TestCase):
    def test_torrasque_remains_visible_across_respawns(self):
        self.assertIn('APRG_RegisterAlwaysVisibleUnit(g_aprgTorrasque, player)',G)
        func=section('void APRG_RegisterAlwaysVisibleUnit(', 'void APRG_RegisterAlwaysVisibleGroup(')
        self.assertIn('!UnitIsAlive(g_aprgAlwaysVisibleUnits[i])',func)
        self.assertIn('VisRevealerUpdate(g_aprgAlwaysVisibleRevealers[i])',func)
        self.assertIn('APRG_TickAlwaysVisibleUnits();',G)

    def test_saving_grace_has_named_reveal_and_persists(self):
        self.assertIn('"saving_grace_pending": []',S)
        start=S.index('    elif kind=="saving_grace":',S.index('def _purchase_boon('))
        end=S.index('    elif kind=="reroll":',start)
        block=S[start:end]
        self.assertIn('"Saving Grace Blessings"',block)
        self.assertIn('[_blessing_reveal_row(e) for e in chosen]',block)
        self.assertIn('pending.append(chosen)',block)
        assign=S[S.index('def _assign_saving_grace('):S.index('def _owned_race_unit_unlock_count(')]
        self.assertIn('s["saving_grace_pending"] = pending[1:]',assign)
        self.assertIn('temp[str(mission_id)] = chosen',assign)

    def test_mission_message_after_base_once_never_clears_chat(self):
        self.assertIn('g_aprgEffectsSummaryAfterBaseDisplayed',G)
        self.assertIn('now >= g_aprgMacroReadyTime + 3.0',G)
        self.assertEqual(G.count('APRG_DisplayActiveEffects(player);'),1)

    def test_normal_armada_six_twelve(self):
        block=section('void APRG_RetargetGoldenArmada(', 'bool APRG_EnsureAirReachableToPlayer(')
        for x in ('< 720.0','>= 360.0','clearance = 24.0','clearance = 12.0'):
            self.assertIn(x,block)

    def test_true_armada_ten_fifteen_twenty(self):
        block=section('void APRG_RetargetTrueGoldenArmada(', 'unit APRG_TrueGoldenAnchorUnit(')
        for x in ('< 1200.0','>= 600.0','>= 900.0','clearance = 40.0','clearance = 30.0','clearance = 20.0'):
            self.assertIn(x,block)
        oracle=section('void APRG_TickTrueGoldenOracles(', 'void APRG_TrueGoldenAddCreated(')
        self.assertIn('< 1200.0',oracle)

    def test_ground_patrol_samples_short_routes_and_ignores_tumors(self):
        route=section('bool APRG_GoldenPatrolRouteSafe(', 'point APRG_GroundSafePatrolDestination(')
        hop=section('point APRG_GroundSafePatrolDestination(', 'point APRG_FindGoldenSafeAirPoint(')
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(sample, player, clearance)',route)
        self.assertIn('RandomFixed(3.0, 8.0)',hop)
        self.assertIn('APRG_GoldenPatrolRouteSafe(origin, candidate, player, clearance)',hop)
        self.assertIn('!APRG_IsSlayStructureEffectEligibleType(UnitGetType(allied))',G)

    def test_wraith_viking_dt_and_drop_first_wave_from_base(self):
        clocks=section('void APRG_StartMacroRelativeEffectClocks(', 'void APRG_UpdateMacroBaseReady(')
        for x in ('g_aprgNextWraithTime = established + 120.0',
                  'g_aprgNextVikingRaidTime = established + 180.0',
                  'g_aprgNextDarkTemplarTime = established + 300.0'):
            self.assertIn(x,clocks)
        self.assertIn('g_aprgMacroReadyTime + 240.0',section('bool APRG_Tick_Func(', 'void APRogue_Init('))

    def test_drill_delayed_and_visible(self):
        drill=section('void APRG_TrySpawnEnemyDrill(', 'void APRG_TickEnemyDrillTargetLimit(')
        self.assertIn('APRG_TimeSinceMacroBase(GameGetMissionTime()) < 180.0',drill)
        self.assertIn('APRG_RegisterAlwaysVisibleUnit(g_aprgEnemyMutationDrill, player)',drill)

    def test_leviathan_orbit_first_drop_and_cadence(self):
        tick=section('bool APRG_Tick_Func(', 'void APRogue_Init(')
        self.assertIn('g_aprgLeviathanRampStartTime = g_aprgMacroReadyTime + 240.0;',tick)
        self.assertIn('g_aprgNextLeviathanTime = g_aprgLeviathanRampStartTime;',tick)
        start=section('fixed APRG_BaseLeviathanMutaliskInterval(', 'bool APRG_LeviathanDestructiveAbility(')
        self.assertIn('return 30.0 - (28.0 * progress)',start)
        self.assertIn('return 55.0 - (50.5 * progress)',start)
        self.assertIn('1200.0 - (g_aprgMacroReadyTime + 300.0)',start)

    def test_ultimate_harassment_respects_component_delays(self):
        combined=section('void APRG_TickCombinedRaids(', 'string APRG_BrakkType(')
        for x in ('g_aprgMacroReadyTime + 120.0','g_aprgMacroReadyTime + 180.0',
                  'g_aprgMacroReadyTime + 240.0','APRG_VikingRaidIntervalMinimum(now)'):
            self.assertIn(x,combined)

    def test_explicit_mission_mark_is_not_base_shifted(self):
        self.assertIn('g_aprgNextZagaraBanelingTime = 600.0;',G)
        self.assertIn('now < 1200.0',G)

    def test_user_description_and_prices(self):
        def rows(fname,key):
            with (ROOT/'Payload'/fname).open(encoding='utf-8-sig',newline='') as fp:
                return {x[key]:x for x in csv.DictReader(fp)}
        b=rows('BOON_CATALOG.csv','Boon Title')
        s=rows('SPEAR_OF_ADUN_SHOP_CATALOG.csv','Item Title')
        m=rows('MERCENARY_SHOP_CATALOG.csv','Item Title')
        p=rows('POTION_CATALOG.csv','Name')
        self.assertEqual(b['Shop Expansion']['Cost'],'200')
        self.assertEqual(s['Temporal Field (Spear of Adun)']['Cost'],'200')
        self.assertEqual(m['Elite Mercenaries']['Cost'],'500')
        self.assertEqual(m['Repeat Contractor']['Cost'],'300')
        self.assertEqual(p['Spear of Adun Recharge']['Rarity (price is 125 x rarity)'],'1')
        self.assertEqual(p['Hyperion in a Bottle']['Effect Description'],'Spawn the WoL hyperion, but you cannot control it')

if __name__ == '__main__': unittest.main()
