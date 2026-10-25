"""Regression: all eleven v1.2.2 added boons must have real shop prices and descriptions."""
from __future__ import annotations
import ast, csv, re, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'Payload'/'slay_the_starcraft.py').read_text(encoding='utf-8')
with (ROOT/'Payload'/'BOON_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
    row_list=list(csv.DictReader(f))
rows={x['Boon Title']:x for x in row_list}
EXPECTED={
 'eternal_perdition':('Eternal Perdition',400),
 'speedy_buildings':('Speedy Buildings',300),
 'enhanced_allies':('Enhanced Allies',600),
 'explosive_predators':('Explosive Predators',400),
 'harvesting_equipment':('Harvesting Equipment',400),
 'refective_diamondbacks':('Refective Diamondbacks',400),
 'psionic_guardians':('Psionic Guardians',400),
 'improved_morphs':('Improved morphs',600),
 'psionic_lords':('Psionic Lords',800),
 'unlimited_scarabs':('Unlimited Scarabs',500),
 'armor_disintegration':('Armor Disintegration',500)
}
tree=ast.parse(src)
funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
titles=next(ast.literal_eval(x.value) for x in tree.body
    if isinstance(x,ast.AnnAssign) and isinstance(x.target,ast.Name) and x.target.id=='_NEW_BOON_TITLES')
def context():
    e=dict(BOON_PREFIX='BOON::',_NEW_BOON_TITLES=titles,
      _BOON_CATALOG_ROWS=rows,EFFECT_DISPLAY_NAMES={},SHOP_DESCRIPTION_OVERRIDES={},
      POTION_CATALOG={},PROGRESSION_DESCRIPTIONS={},_KERRIGAN_SHOP_CATALOG_ROWS={},
      _SPEAR_SHOP_CATALOG_ROWS={},TERRAN_CONTRACTS='_terrans_',ZERG_CONTRACTS='_zergs_',
      SPEAR_UNLOCK='_spear_',REPEATABLE_BOON_KINDS={'deadly_weapons','auto_repair'},re=re)
    funcs_needed=['_boon_id','_parse_boon','boon_display_name','shop_entry_description',
                  '_price_for_item_before_track_discount']
    module=ast.fix_missing_locations(ast.Module(body=[funcs[x] for x in funcs_needed],type_ignores=[]))
    exec(compile(module,'<actual source price functions>','exec'),e)
    return e
class AddedBoonPricingTests(unittest.TestCase):
    def test_prices_and_descriptions(self):
        e=context()
        for kind,(title,cost) in EXPECTED.items():
            with self.subTest(kind=kind):
                item=e['_boon_id'](kind)
                self.assertEqual(e['boon_display_name'](item),title)
                self.assertEqual(int(rows[title]['Cost']),cost)
                self.assertEqual(e['_price_for_item_before_track_discount'](item),cost)
                self.assertEqual(e['shop_entry_description'](item),rows[title]['Description'])
                self.assertGreater(len(rows[title]['Description']),20)
    def test_price_fallback_even_if_catalog_missing(self):
        e=context()
        e['_BOON_CATALOG_ROWS']={}
        for kind,(title,cost) in EXPECTED.items():
            self.assertEqual(e['_price_for_item_before_track_discount'](e['_boon_id'](kind)),cost)
    def test_every_added_kind_has_a_unique_catalog_row(self):
        self.assertEqual(len(rows),len(row_list))
        self.assertEqual(set(EXPECTED),set(EXPECTED)&set(titles))
if __name__=='__main__':unittest.main()
