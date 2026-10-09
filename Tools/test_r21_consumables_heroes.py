"""r21 regression: consumable labeling, catalog fidelity, controls, and HoTS safety."""
from __future__ import annotations
import ast
import csv
import unittest
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SLAY=(ROOT/'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')
UI=(ROOT/'Payload/slay_command_ui.py').read_text(encoding='utf-8')
GALAXY=(ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')
TREE=ast.parse(SLAY)

def assn(name):
    node=next(n for n in TREE.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(node.value)

class ConsumableAndHeroTests(unittest.TestCase):
    def test_every_catalog_description_is_exact_verbatim(self):
        with (ROOT/'Payload/POTION_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
            expected={row['Name']:row['Effect Description'] for row in csv.DictReader(f)}
        actual={name:description for name,rarity,description,target in assn('POTION_DEFINITIONS')}
        self.assertEqual(len(expected),19)
        self.assertEqual(actual,expected)
        self.assertEqual(actual['Drop Pod Wave'],'Call down 10 terran drop pods on target area.')
        self.assertNotIn('Warfield-style',actual['Drop Pod Wave'])
        self.assertIn('description=f"Spawn {2000 // (mineral + gas)} {plural} at target location that automatically attacks the enemy."',SLAY)

    def test_psi_disrupter_family_classified_as_defensive_structures(self):
        defensive=assn('DEFENSIVE_STRUCTURE_ITEMS')
        for item in ('Psi Disrupter','Sonic Disrupter (Psi Disrupter)','Psi Screen (Psi Disrupter)'):
            self.assertIn(item,defensive)
        source=SLAY[SLAY.index('def shop_category_for_item('):SLAY.index('\ndef shop_sections(')]
        self.assertLess(source.index('if item_name in DEFENSIVE_STRUCTURE_ITEMS or item_name in DETECTOR_ITEMS:'),source.index('if race == "terran":'))

    def test_user_facing_consumable_labels_and_shop_order(self):
        self.assertIn('"Consumables"',SLAY)
        self.assertNotIn('"Potions"',SLAY)
        self.assertIn("'Consumables'",UI)
        self.assertNotIn("'Potions'",UI)
        self.assertIn('Available slots:',UI)
        start=UI.index('class CardConsole:')
        end=UI.index('    def resize(',start)
        layout=UI[start:end]
        self.assertLess(layout.index('top.add_widget(self.view_button)'),layout.index("top.add_widget(control('Exit Shop'"))
        self.assertLess(layout.index('top.add_widget(self.view_button)'),layout.index("top.add_widget(control('Shop'"))
        self.assertLess(layout.index("top.add_widget(control('Shop'"),layout.index("top.add_widget(control('Exit Inventory'"))
        self.assertNotIn('Close Inventory',layout)
        self.assertIn('Both consumable slots are full',SLAY)
        self.assertIn('TEST CONSUMABLE', GALAXY)
        self.assertNotIn('[Slay] Used ', GALAXY)
        self.assertNotIn('Consumable not consumed', GALAXY)

    def test_high_risk_full_ring_and_red_text(self):
        decorate=UI[UI.index('def decorate_node('):UI.index('\ndef build_chart(')]
        self.assertIn('risk_suffix=',decorate)
        self.assertIn('[color=FF5353]· High Risk[/color]',decorate)
        self.assertIn('warning=Line(circle=(0,0,1)',decorate)
        self.assertIn('warning.circle=(cx,cy,radius+dp(11))',decorate)
        self.assertNotIn('25,155',decorate)

    def test_heroes_spawn_safely_and_patrol_outside_20_until_4_minutes(self):
        spawn=GALAXY[GALAXY.index('void APRG_TrySpawnHostileHero('):GALAXY.index('void APRG_SpawnWraithRaid(',GALAXY.index('void APRG_TrySpawnHostileHero('))]
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(candidate, player, 20.0)',spawn)
        self.assertLess(spawn.index('APRG_PointNearPlayerOrAlliedBuilding('),spawn.index('UnitCreate('))
        patrol=GALAXY[GALAXY.index('point APRG_RandomHeroesOfStormPatrolPoint('):GALAXY.index('bool APRG_OrderHeroesOfStormRandomPatrol(')]
        for marker in ('GameGetMissionTime() < 240.0','UnitPathableToPoint(hero, candidate',
                       'APRG_PointNearPlayerOrAlliedBuilding(candidate, player, 20.0)',
                       'APRG_PointNearPlayerOrAlliedBuilding(sample, player, 20.0)',
                       'if (crossesProtectedArea) { continue; }'):
            self.assertIn(marker,patrol)
        self.assertIn('g_aprgNextHeroesOfStormDefenseAttackTime = 240.0;',GALAXY)
        self.assertNotIn('for (int ',GALAXY)

if __name__=='__main__': unittest.main()
