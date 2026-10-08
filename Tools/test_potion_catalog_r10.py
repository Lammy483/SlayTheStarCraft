"""Source-level checks for the 19-pot catalog and stable randomized wire IDs."""
import ast
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
GALAXY = (ROOT / 'APRogue.galaxy').read_text(encoding='utf-8')
RUNTIME = (ROOT / 'slay_the_starcraft.py').read_text(encoding='utf-8')
TREE = ast.parse(RUNTIME)
KEEP = {'POTION_PREFIX','POTION_DEFINITIONS','POTION_CATALOG','POTION_RANDOM_UNITS','POTION_VARIANT_PREFIX'}
nodes=[]
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id in KEEP for t in node.targets):
        nodes.append(node)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='POTION_CATALOG' and node.value.func.attr=='update':
        nodes.append(node)
ns={}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ROOT/'slay_the_starcraft.py'),'exec'),ns)

class PotionCatalogTests(unittest.TestCase):
    def test_uploaded_catalog_matches_runtime_names_and_prices(self):
        with (ROOT/'POTION_CATALOG.csv').open(encoding='utf-8',newline='') as f:
            source=list(csv.DictReader(f))
        self.assertEqual(len(source),19)
        actual={value['name']:value for key,value in ns['POTION_CATALOG'].items() if key.count('::') == 1}
        self.assertEqual(len(actual),19)
        for row in source:
            potion=actual[row['Name']]
            self.assertEqual(potion['rarity'],int(row['Rarity (price is 125 x rarity)']))
            self.assertEqual(potion['price'],125*int(row['Rarity (price is 125 x rarity)']))

    def test_legacy_wire_ids_are_stable(self):
        expected=('Mineral Reserves','Gas Reserves','Odin in a Bottle','Leviathan in a Bottle',
            'Hyperion in a Bottle','Drop Pod Wave','Mass EMP','Tactical Nuke',"Tosh's Miners",
            'Stealth Protocol','Mass Stimpack','Spear of Adun Recharge','Second Kerrigan',
            'Mercenary Favor','Guardian Matrix','Corruption Spores')
        for i,name in enumerate(expected,1):
            self.assertEqual(ns['POTION_CATALOG'][f'slay_potion::{i}']['name'],name)
        self.assertEqual(len(ns['POTION_DEFINITIONS']),19)

    def test_random_offer_is_fixed_before_purchasing_and_activating(self):
        options=ns['POTION_RANDOM_UNITS']
        self.assertGreaterEqual(len(options),12)
        self.assertIn('POTION_VARIANT_PREFIX + str(rng.randint(1, len(POTION_RANDOM_UNITS)))',RUNTIME)
        for i,(_,plural,unit,minerals,gas) in enumerate(options,1):
            potion=ns['POTION_CATALOG'][f'slay_potion::19::{i}']
            self.assertEqual((potion['index'],potion['amount'],potion['unit']),
                (1900+i,2000//(minerals+gas),unit))
            self.assertIn(f'if (kind == {1900+i}) {{ return "{unit}"; }}',GALAXY)
            self.assertIn(f'if (kind == {1900+i}) {{ return {potion["amount"]}; }}',GALAXY)
            self.assertIn(f'if (kind == {1900+i}) {{ return "{potion["name"]}"; }}',GALAXY)

    def test_mass_spawns_are_bounded_and_use_autonomous_ability_ai(self):
        for part in ('APRG_PotionStartSpawnQueue', 'APRG_TickPotionSpawnQueues(player, now)',
                     'TriggerAddEventTimePeriodic(g_aprgFastBoonTrigger, 0.1, c_timeGame)',
                     'g_aprgPotionQueueKind[0] = 0;', 'g_aprgPotionQueueKind[1] = 0;',
                     'g_aprgPotionQueueTotal', 'MinI(25, expected - g_aprgPotionQueueDone[slot])',
                     'APRG_MakeGroupUncommandable(created);', 'APRG_TryFriendlyAutonomousAbility(spawned, player);',
                     'APRG_NearestPathableEnemyStructure(spawned, player)',
                     'if (kind == 17 || kind == 18)', 'kind >= 1901 && kind <= 1918'):
            self.assertIn(part,GALAXY)
        self.assertIn('SHOP_STOCK_LOGIC_VERSION = 112',RUNTIME)

if __name__=='__main__':
    unittest.main()
