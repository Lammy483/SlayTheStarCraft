"""v1.1.2 Dev2 contract tests for base-establishment clock and Lab Rat fixes."""
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAL = (ROOT / 'Payload/APRogue.galaxy').read_text(encoding='utf-8')
GEN = (ROOT / 'Payload/generate_slay_run.py').read_text(encoding='utf-8')

def between(start, end):
    return GAL.split(start, 1)[1].split(end, 1)[0]

class MacroTimeAndLabRat(unittest.TestCase):
    def test_macro_ready_initializes_timers_exactly_once(self):
        update = between('void APRG_UpdateMacroBaseReady(', 'bool APRG_PlayerMacroBaseReady(')
        self.assertIn('if (g_aprgMacroBaseReady && g_aprgMacroPlayer == player)', update)
        self.assertIn('APRG_StartMacroRelativeEffectClocks(g_aprgMacroReadyTime);', update)
        clocks = between('void APRG_StartMacroRelativeEffectClocks(', 'void APRG_UpdateMacroBaseReady(')
        for key in ('Wraith','VikingRaid','DarkTemplar','AirSupport','LostViking',
                    'Warfield','ZagaraAid','JetpackWave','HeroesOfStormPatrol',
                    'HordeLarva','ArmsRace','OccasionalThor','Compound','TowerDefense','EnemyRegeneration'):
            self.assertIn('g_aprgNext' + key + 'Time = established +', clocks, key)
        self.assertIn('g_aprgNextZagaraBanelingTime = 600.0;', clocks)
        for key in ('InvasionFleetDrop','TaldarimWave'):
            self.assertNotIn('g_aprgNext' + key + 'Time = established +', clocks)

    def test_wraith_spawns_and_rate_clock_use_macro_time(self):
        tick = between('bool APRG_Tick_Func(', 'void APRogue_Init()')
        self.assertIn('APRG_HasMutation(APRG_MUT_TOO_MANY_WRAITHS) &&\n        APRG_PlayerMacroBaseReady(player)', tick)
        interval = between('fixed APRG_WraithRaidNextInterval(', 'point APRG_FindPlayerMineralLinePoint(')
        self.assertIn('now = APRG_TimeSinceMacroBase(now);', interval)

    def test_catalog_mission_mark_exceptions_preserved(self):
        effects = {r['Title']: r['Description'] for r in csv.DictReader((ROOT/'Payload/EFFECT_CATALOG.csv').open(encoding='utf-8-sig'))}
        boons = {r['Boon Title']: r['Description'] for r in csv.DictReader((ROOT/'Payload/BOON_CATALOG.csv').open(encoding='utf-8-sig'))}
        self.assertIn('20 minute mark', effects["Tal'darim Reinforcements"])
        self.assertIn('5 minute mark', boons['Invasion Fleet'])
        self.assertIn('5 minute mark', boons['Purifier Alliance'])
        self.assertIn('now < 1200.0', between('void APRG_TickTaldarimReinforcements(', 'void APRG_ApplyGloriousMartyrs('))
        self.assertIn('now < 300.0 || now >= 420.0', between('void APRG_TickInvasionFleet(', 'void APRG_TickHellionRunBy('))
        self.assertIn('now < 300.0', between('void APRG_TickPurifierAlliance(', 'void APRG_TickReflectiveArmor(') if 'void APRG_TickReflectiveArmor(' in GAL else 'void APRG_TickPurifierAlliance(' + GAL.split('void APRG_TickPurifierAlliance(',1)[1][:1500])

    def test_lab_rat_excludes_tower_defense_from_all_selection_paths(self):
        exclusions = GEN.split('def _effect_exclusions_for_mission(',1)[1].split('def ',1)[0]
        self.assertIn('mission_short_name.strip().casefold() == "lab rat"', exclusions)
        self.assertIn('forbidden_mutators.add("tower_defense")', exclusions)
        self.assertGreaterEqual(GEN.count('_effect_exclusions_for_mission('), 5)

    def test_lab_rat_horde_bonus_is_once_and_only_25_minerals(self):
        tick = between('bool APRG_Tick_Func(', 'void APRogue_Init(')
        self.assertIn('!g_aprgLabRatHordeMineralsGiven', tick)
        self.assertIn('APRG_MISSION_FLAG_LAB_RAT_OPENING', tick)
        self.assertIn('APRG_EXT_BLESS_HORDE_MODE', tick)
        self.assertIn('c_playerPropOperAdd, 25', tick)
        self.assertIn('g_aprgLabRatHordeMineralsGiven = true;', tick)
        self.assertIn('g_aprgLabRatHordeMineralsGiven = false;', between('bool APRG_Load_Func(', 'bool APRG_Tick_Func('))

    def test_early_base_time_safety_for_armada_heroes(self):
        self.assertIn('APRG_TimeSinceMacroBase(GameGetMissionTime()) >= 360.0',GAL)
        self.assertIn('APRG_TimeSinceMacroBase(GameGetMissionTime()) >= 600.0',GAL)
        self.assertIn('minutes = FixedToInt(APRG_TimeSinceMacroBase(GameGetMissionTime()) / 60.0);',GAL)

if __name__ == '__main__': unittest.main()
