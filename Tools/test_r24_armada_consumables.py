"""r24 regression: safe Armada routing, invisible target caster, pricing, pacing."""
from __future__ import annotations
import csv
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=ROOT/'Payload'
GAL=(PAYLOAD/'APRogue.galaxy').read_text(encoding='utf-8')
UI=(PAYLOAD/'slay_command_ui.py').read_text(encoding='utf-8')
SLAY=(PAYLOAD/'slay_the_starcraft.py').read_text(encoding='utf-8')
INSTALL=(PAYLOAD/'install_slay.py').read_text(encoding='utf-8')
GEN=(PAYLOAD/'generate_slay_run.py').read_text(encoding='utf-8')

def segment(start,end):
    return GAL.split(start,1)[1].split(end,1)[0]

class R24Tests(unittest.TestCase):
    def test_spear_cost_is_500_in_catalog_and_fallback(self):
        with (PAYLOAD/'SPEAR_OF_ADUN_SHOP_CATALOG.csv').open(newline='',encoding='utf-8-sig') as file:
            entry=next(x for x in csv.DictReader(file) if x['Item Title']=='Unlock Spear of Adun')
        self.assertEqual(int(entry['Cost']),500)
        self.assertIn('SPEAR_SHOP_PRICE_OVERRIDES.get("Unlock Spear of Adun", 500)',SLAY)

    def test_new_mutation_slope_and_danger_prediction(self):
        spec=importlib.util.spec_from_file_location('r24_gen',PAYLOAD/'generate_slay_run.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        self.assertAlmostEqual(mod._base_effect_means(0,11)[0],3.20)
        self.assertAlmostEqual(mod._base_effect_means(9,11)[0],13.10)
        self.assertAlmostEqual(mod._base_effect_means(11,11,True)[0],18.87)
        self.assertAlmostEqual(mod._base_effect_means(0,2)[0],4.25)
        # Mean increase for mission 10 over r23 = exactly +2.5
        self.assertAlmostEqual(mod._base_effect_means(9,11)[0] - (9.60+1.0),2.5)
        self.assertIn('0.25 * mission_number',GEN)
        self.assertIn('0.25 * mission_number',SLAY)
        self.assertIn('0.25 * max(1, int(layer) + 1)',GEN)

    def test_armada_safe_spawn_not_relocated_toward_base(self):
        for start,end in [('void APRG_TrySpawnGoldenArmada(', 'void APRG_OrderTrueGoldenAtPlayerBase('),
                          ('void APRG_TrySpawnTrueGoldenArmada(', 'void APRG_TickTrueGoldenArmada(')]:
            sec=segment(start,end)
            self.assertRegex(sec, r'APRG_FindGoldenSafeAirPoint\(player, (?:40|55)\.0\)')
            self.assertNotIn('APRG_EnsureAirReachableToPlayer(',sec.split('void APRG_TrySpawn',1)[-1].split('g_aprgGoldenSpawned = true')[0].replace('// Do not call APRG_EnsureAirReachableToPlayer here:', ''))
            self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(formationPoint, player, 40.0)',sec)
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(candidate, player, spawnClearance)',GAL)
        safe_spawn=segment('point APRG_FindGoldenSafeAirPoint(', 'point APRG_GoldenSafePatrolDestination(')
        self.assertIn('hostileBuildings = APRG_EnemyStructures(player);',safe_spawn)
        self.assertIn('PointWithOffsetPolar(UnitGetPosition(anchor)',safe_spawn)

    def test_safe_patrol_route_checks_segment_and_stops_before_4_minutes(self):
        route=segment('bool APRG_GoldenPatrolRouteSafe(', 'point APRG_FindGoldenSafeAirPoint(')
        self.assertIn('MinI(160, FixedToInt(distance / 3.0) + 1)',route)
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(sample, player, clearance)',route)
        normal=segment('void APRG_RetargetGoldenArmada(', 'bool APRG_EnsureAirReachableToPlayer(')
        self.assertIn('GameGetMissionTime() < 240.0',normal)
        self.assertIn('AbilityCommand("move", 0)',normal)
        self.assertIn('AbilityCommand("attack", 0)',normal)
        self.assertNotIn('EarlySafety',GAL)
        self.assertNotIn('APRG_GoldenArmadaEarlySafety(',GAL)
        true=segment('void APRG_RetargetTrueGoldenArmada(', 'unit APRG_TrueGoldenAnchorUnit(')
        self.assertIn('APRG_GoldenSafePatrolDestination',true)
        self.assertIn('AbilityCommand("move", 0)',true)
        self.assertIn('GameGetMissionTime() >= 240.0',true)
        phoenixes=segment('void APRG_TickTrueGoldenPhoenixes(', 'unit APRG_TrueGoldenNearestCloakedPlayerUnit(')
        self.assertIn('APRG_GoldenPatrolRouteSafe(UnitGetPosition(phoenix), destination, player, 40.0)',phoenixes)
        oracles=segment('void APRG_TickTrueGoldenOracles(', 'void APRG_TrueGoldenAddCreated(')
        self.assertIn('now < 600.0',oracles)

    def test_dummy_marine_cannot_be_selected_targeted_or_seen(self):
        catalog=ET.parse(PAYLOAD/'APRogueData.xml').getroot()
        unit=next(x for x in catalog.iter('CUnit') if x.get('id')=='APRoguePotionTargetCaster')
        flags={x.get('index'):x.get('value') for x in unit.findall('FlagArray')}
        for flag in ('NoDraw','Unselectable','Unclickable','Uncursorable','Untargetable','Invulnerable'):
            self.assertEqual(flags.get(flag),'1')
        native=segment('bool APRG_PotionEnsureNativeCaster(', 'bool APRG_PotionArmNativeTarget(')
        for value in ('c_unitStateSelectable, false','c_unitStateTargetable, false','c_unitStateInvulnerable, true'):
            self.assertIn(value,native)
        self.assertNotIn('Uncommandable',native)
        for start,end in [('unitgroup APRG_PlayerMobileUnits(', 'unitgroup APRG_PlayerAllUnits('),
                          ('unitgroup APRG_PlayerAllUnits(', 'unitgroup APRG_EnemyAllUnits(')]:
            self.assertIn('u == g_aprgPotionTargetCaster',segment(start,end))

    def test_consumable_shop_count_is_authoritative(self):
        self.assertIn('slay.refresh_consumable_slots(manager.ctx)',UI)
        self.assertIn('Available slots:',UI)
        self.assertIn('POTION_CAPACITY - count',UI)
        self.assertIn('slay_consumable_slots_label',UI)
        self.assertIn('slay_consumable_slots_label',INSTALL)
        self.assertIn('_POTION_BANK_USE_CACHE.pop(test_potion_run_token(ctx), None)',SLAY)

    def test_instruction_no_native_sc2_wording(self):
        self.assertIn('[Slay] Choose a target for ',GAL)
        self.assertNotIn('[Slay] Choose a native SC2 target for ',GAL)

if __name__=='__main__':unittest.main()
