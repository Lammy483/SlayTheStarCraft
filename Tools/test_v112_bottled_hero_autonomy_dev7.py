"""Dev7 offline contract tests for bottled hero behavior and icon update."""
import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'Payload'
G = (P / 'APRogue.galaxy').read_text(encoding='utf-8')
CLIENT = (P / 'slay_the_starcraft.py').read_text(encoding='utf-8')

def body(name):
    m = re.search(r'^(?:void|bool|int)\s+' + re.escape(name) + r'\([^)]*\)\s*\{', G, re.M)
    assert m, name
    b = G.index('{', m.start())
    depth=0
    for i in range(b,len(G)):
        if G[i]=='{': depth+=1
        elif G[i]=='}':
            depth-=1
            if depth==0: return G[b:i+1]
    raise AssertionError('Unbalanced: '+name)

class BottledHeroesDev7(unittest.TestCase):
    def test_descriptions_and_notes_are_distinct(self):
        with (P/'POTION_CATALOG.csv').open(encoding='utf-8-sig', newline='') as f:
            rows={row['Name']:row for row in csv.DictReader(f)}
        self.assertEqual(rows['Leviathan in a Bottle']['Effect Description'],
                         'Spawn the WoL leviathan, but you cannot control it')
        self.assertEqual(rows['Hyperion in a Bottle']['Effect Description'],
                         'Spawn the WoL hyperion, but you cannot control it')
        for nm in ('Leviathan in a Bottle','Hyperion in a Bottle'):
            self.assertNotIn('legendary resistance',rows[nm]['Effect Description'].lower())
            self.assertIn(rows[nm]['Effect Description'],CLIENT)
        self.assertIn('legendary resistance removed',rows['Hyperion in a Bottle']['Development notes'])
        self.assertIn('60-second',rows['Leviathan in a Bottle']['Development notes'])
        self.assertEqual(rows['Leviathan in a Bottle']['Rarity (price is 125 x rarity)'],'3')
        self.assertEqual(rows['Hyperion in a Bottle']['Rarity (price is 125 x rarity)'],'4')

    def test_only_bottled_heroes_use_uncommandable_ai(self):
        potion=body('APRG_PotionActivate')
        self.assertIn('if (kind == 4 || kind == 5)',potion)
        self.assertIn('APRG_MakeGroupUncommandable(created);',potion)
        self.assertIn('UnitGroupAdd(g_aprgPotionAutoUnits, u);',potion)
        self.assertIn('UnitGroupAdd(g_aprgPotionAutoSpellcasters, u);',potion)
        self.assertIn('APRG_OrderGroupTowardNearestEnemyStructure(created, location, player);',potion)
        self.assertIn('APRG_NormalizeLeviathanBoon(u, player);',potion)
        self.assertIn('APRG_NormalizeHyperionBoon(u, player);',potion)
        self.assertNotIn('APRG_MakeGroupUncommandable(created);',body('APRG_NewBoonTrain_Func'))

    def test_leva_native_abilities_and_created_summons_auto(self):
        potion=body('APRG_PotionActivate')
        self.assertIn('TriggerAddEventUnitCreated(g_aprgPotionLeviathanSpawnTrigger, null, null, null);',potion)
        self.assertIn('UnitGroupAdd(g_aprgPotionAutoLeviathans, u);',potion)
        summon=body('APRG_TryPotionLeviathanSummon')
        for token in ('UnitAbilityGet(leviathan, i)','APRG_LeviathanMutationAbilityMatches(',
                      'UnitOrderIsValid(leviathan, castOrder)','UnitIssueOrder(leviathan, castOrder, c_orderQueueReplace)',
                      'now + 60.0','APRG_QueuePriorAutonomousOrder('):
            self.assertIn(token,summon)
        self.assertIn('"Cost.Cooldown.TimeUse", player, "60"',body('APRG_NormalizeLeviathanBoon'))
        tick=body('APRG_TickPotionSpawnQueues')
        self.assertIn('APRG_TryPotionLeviathanSummon(spawned, player, "Mutalisk", now)',tick)
        self.assertIn('APRG_TryPotionLeviathanSummon(spawned, player, "BroodLord", now)',tick)
        self.assertIn('APRG_TryFriendlyAutonomousAbility(spawned, player)',tick)
        created=body('APRG_PotionLeviathanSpawned_Func')
        self.assertIn('UnitGroupHasUnit(g_aprgPotionAutoLeviathans, creator)',created)
        self.assertIn('APRG_MakeGroupUncommandable(group)',created)
        self.assertIn('APRG_OrderAttackMove(child',created)

    def test_hyperion_yamato_and_resistance_existing(self):
        config=body('APRG_ConfigureHyperionYamato')
        self.assertIn('"Cost.Vital[Energy]", player, "100"', config)
        self.assertIn('"Cost.Cooldown.TimeUse", player, "15"', config)
        normalize=body('APRG_NormalizeHyperionBoon')
        self.assertIn('DamageReduction',normalize)
        self.assertIn('APRG_ConfigureHyperionYamato(player);',normalize)
        ai=body('APRG_AutonomousAbilityCategory')
        self.assertIn('APRG_AIHas(abilityType, "Yamato")',ai)

    def test_specialists_aliases_all_raven_icon(self):
        for file in ('slay_ui_icons.json','slay_assets/item_btn_icons.json'):
            icons=json.loads((P/file).read_text(encoding='utf-8'))
            for key in ('specialists','Specialists','BOON::specialists',
                        'BOON::permanent_blessing::specialists','Permanent Blessing: Specialists'):
                self.assertEqual(icons[key],'btn-unit-terran-raven.png')
        self.assertTrue((P/'slay_assets/icons/btn-unit-terran-raven.png').is_file())

if __name__=='__main__': unittest.main()
