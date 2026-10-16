"""Dev5 regression checks for Zagara, worker tech limits, mutation gates and Armada."""
from pathlib import Path
import csv
import unittest

ROOT=Path(__file__).resolve().parents[1]
G=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
CLIENT=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')

def section(first, next_):
    return G.split(first,1)[1].split(next_,1)[0]

class Dev5Regression(unittest.TestCase):
    def test_enemy_and_commander_zagara_six_hp(self):
        kill=section('void APRG_TickEnemyZagaraFatalHp(', 'string APRG_AlarakHeroType(')
        self.assertIn('APRG_EnemyAllUnits(player)',kill)
        self.assertIn('APRG_PlayerAllUnits(player)',kill)
        self.assertIn('> 6.0',kill)
        self.assertIn('UnitKill(zagara)',kill)
        hero=section('void APRG_TickGeneratedHeroNoRevive(', 'void APRG_TickEnemyZagaraFatalHp(')
        self.assertIn('<= 6.0',hero)

    def test_tosh_workers_keep_existing_player_tech_tree(self):
        body=section('void APRG_RestrictToshMinerSCVBuild(', 'bool APRG_PotionActivate(')
        self.assertIn('APRG_ContractProducedUnitAllowed(player, targetType)',body)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogAbil, abilityType, path, player, "")',body)
        self.assertIn('CardLayouts[',body)
        self.assertIn('path + ".AbilCmd", player, ""',body)
        potion=section('bool APRG_PotionActivate(', 'void APRG_TickPotionSpawnQueues(')
        self.assertIn('APRG_RestrictToshMinerSCVBuild(player, UnitGroupUnitFromEnd(created, i))',potion)
        self.assertNotIn('TechTreeUnitAllow(player,',body)

    def test_hyperion_notes_not_shown(self):
        with (ROOT/'Payload/POTION_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
            potions={r['Name']:r['Effect Description'] for r in csv.DictReader(f)}
        self.assertEqual('Spawn the WoL hyperion, but you cannot control it', potions['Hyperion in a Bottle'])
        self.assertIn("'Spawn the WoL hyperion, but you cannot control it'", CLIENT)

    def test_creep_tumors_do_not_count_as_base_buildings(self):
        body=section('bool APRG_PointNearPlayerOrAlliedBuilding(', 'point APRG_FindStaticPatrolGroundPointWithBuildingClearance(')
        self.assertIn('!APRG_IsSlayStructureEffectEligibleType(UnitGetType(allied))',body)
        self.assertIn('UnitGroupRemove(alliedStructures, allied)',body)

    def test_mutations_and_regeneration_are_base_gated(self):
        body=section('bool APRG_Tick_Func(', 'void APRogue_Init(')
        for name in ('APRG_ApplyEnemyRegeneration(player)','APRG_TickTrueGoldenArmada(player, now)',
                     'APRG_TickNuclearAnnihilation(player, now)','APRG_TickMarauderKillTeams(player, now)',
                     'APRG_TickImmortalZergling(player, now)'):
            self.assertIn(name,body)
        self.assertIn('APRG_PlayerMacroBaseReady(player) && APRG_HasMutation(APRG_MUT_ENEMY_REGENERATION)',body)
        death=section('bool APRG_Death_Func(', 'void APRG_ApplyGloriousMartyrs(') if False else section('bool APRG_Death_Func(', 'void APRG_')
        self.assertIn('if (!APRG_PlayerMacroBaseReady(player)) { return true; }',death)
        deferred=section('void APRG_ActivateDeferredMutationCatalog(', 'void APRG_TickAllInEliminationVictory(')
        self.assertIn('!APRG_PlayerMacroBaseReady(player)',deferred)

    def test_golden_three_patrol_stages(self):
        normal=section('void APRG_RetargetGoldenArmada(', 'bool APRG_EnsureAirReachableToPlayer(')
        for text in ('< 720.0','>= 360.0','clearance = 24.0','clearance = 12.0','RegionRandomPoint(RegionPlayableMap())'):
            self.assertIn(text,normal)
        true=section('void APRG_RetargetTrueGoldenArmada(', 'unit APRG_TrueGoldenAnchorUnit(')
        for text in ('< 1200.0','>= 600.0','clearance = 40.0','clearance = 20.0'):
            self.assertIn(text,true)
        phoenix=section('void APRG_TickTrueGoldenPhoenixes(', 'unit APRG_TrueGoldenNearestCloakedPlayerUnit(')
        self.assertIn('< 1200.0',phoenix)
        self.assertIn('clearance = 20.0',phoenix)
        oracle=section('void APRG_TickTrueGoldenOracles(', 'void APRG_TrueGoldenAddCreated(')
        self.assertIn('APRG_TimeSinceMacroBase(now) < 1200.0',oracle)

if __name__=='__main__': unittest.main()
