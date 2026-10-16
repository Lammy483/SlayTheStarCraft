"""Dev10 Crucible exclusion, icon identity, and price contracts."""
from __future__ import annotations
import ast
import csv
import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=ROOT/'Payload'


def source_constant(path: Path, constant: str) -> set[str]:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    for statement in tree.body:
        if isinstance(statement,ast.Assign) and any(isinstance(x,ast.Name) and x.id==constant for x in statement.targets):
            return set(ast.literal_eval(statement.value.args[0]))
    raise AssertionError(f'{constant} not found')


class CrucibleDev10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('slay_dev10_generator',PAYLOAD/'generate_slay_run.py')
        cls.gen=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gen)

    def test_generator_and_runtime_have_identical_enemy_structure_exclusions(self):
        excluded=self.gen.CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS
        runtime=source_constant(PAYLOAD/'slay_the_starcraft.py','CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS')
        self.assertEqual(set(excluded),runtime)
        self.assertGreater(len(excluded),20)
        self.assertTrue({'conga_line','nexus_shield','nuclear_structures','drakken_laser_drill_enemy',
                         'golden_armada','true_golden_armada','tower_defense','tosh_and_his_boys',
                         'dehakas_pack','odin_delayed_assault','brakk_primal_army','drop_pods'}<=excluded)
        self.assertTrue(set(excluded)<=set(self.gen.MUTATORS))

    def test_excludes_for_crucible_race_variants_and_does_not_block_other_missions(self):
        for mission_name in ('The Crucible','The Crucible (Terran)','The Crucible (Zerg)','The Crucible (Protoss)'):
            banned,_ =self.gen._effect_exclusions_for_mission({'name':mission_name,'short_name':mission_name,'race':'terran'})
            self.assertTrue(self.gen.CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS <= banned)
        banned,_=self.gen._effect_exclusions_for_mission({'name':'The Outlaws','race':'terran'})
        self.assertNotIn('golden_armada',banned)

    def test_crucible_rolls_never_get_enemy_structure_mutations(self):
        forbidden,_=self.gen._effect_exclusions_for_mission({'name':'The Crucible','race':'protoss'})
        for seed in range(80):
            effects=self.gen.roll_effects(8,12,'brutal',random.Random(seed),
                                         forbidden_mutators=forbidden,mutation_frequency=2.0,blessing_frequency=1.0)
            self.assertFalse(set(effects[0]) & self.gen.CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS)

    def test_stretchy_spines_uses_identical_unlock_icon_from_shop_art(self):
        assets=PAYLOAD/'slay_assets'
        icon_tables=[PAYLOAD/'slay_ui_icons.json',assets/'item_btn_icons.json']
        aliases=('Stretchy Spines','boon_stretchy_spines','BOON::stretchy_spines',
                 'Permanent Blessing: Stretchy Spines','BOON::permanent_blessing::boon_stretchy_spines')
        for table in icon_tables:
            mapping=json.loads(table.read_text(encoding='utf-8'))
            icon=mapping['Spine Crawler']
            self.assertEqual(icon,'btn-building-zerg-spinecrawler.png')
            self.assertTrue((assets/'icons'/icon).is_file())
            for alias in aliases:
                self.assertEqual(icon,mapping[alias],alias)

    def test_unlimited_power_is_fourteen_hundred_in_shop_catalog_and_fallback(self):
        with (PAYLOAD/'BOON_CATALOG.csv').open(encoding='utf-8-sig',newline='') as stream:
            rows={r['Boon Title']:r for r in csv.DictReader(stream)}
        self.assertEqual(rows['Unlimited Power']['Cost'],'1400')
        self.assertIn('"unlimited_power":1400',(PAYLOAD/'slay_the_starcraft.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
