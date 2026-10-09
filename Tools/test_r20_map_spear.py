"""r20: preserve connected-planets layering, full title rendering, and Spear tiers."""
import ast
import csv
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'Payload'
UI=(ROOT/'slay_command_ui.py').read_text(encoding='utf-8')
SLAY=(ROOT/'slay_the_starcraft.py').read_text(encoding='utf-8')
SHOP=ROOT/'SPEAR_OF_ADUN_SHOP_CATALOG.csv'
PYTREE=ast.parse(SLAY)


def method(name):
    return next(n for n in PYTREE.body if isinstance(n,ast.FunctionDef) and n.name==name)


class MapAndSpearRegression(unittest.TestCase):
    def test_edges_are_over_cards_but_behind_planet_with_slightly_angled_stems(self):
        draw=UI[UI.index('def draw_edges('):UI.index('\n\ndef install(',UI.index('def draw_edges('))]
        self.assertIn('group.add(RoundedRectangle(pos=b.pos,size=b.size',draw)
        self.assertLess(draw.index('group.add(RoundedRectangle('),draw.index('for src,dst in slay.edge_pairs'))
        self.assertIn('chart.canvas.before.add(group)',draw)
        self.assertNotIn('chart.canvas.after.add(group)',draw)
        self.assertIn('NODE_PLANET_CENTER_Y+27',draw)
        self.assertIn('NODE_PLANET_CENTER_Y-27',draw)
        self.assertIn('sway=(dx-sx)*.18',draw)
        self.assertNotIn('arrowhead=',draw)

    def test_mission_titles_do_not_use_generic_clipping_label(self):
        decorate=UI[UI.index('def decorate_node('):UI.index('\ndef build_chart(')]
        self.assertIn('title=Label(',decorate)
        self.assertIn('title.text_size=(text_width,None)',decorate)
        self.assertIn('title.texture_update()',decorate)
        self.assertIn('title.pos=(text_x,b.y+dp(8))',decorate)
        self.assertIn('title.size=(text_width,dp(47))',decorate)
        self.assertNotIn('title=label(',decorate)
        self.assertNotIn('shorten=True',decorate)

    def test_free_first_pylon_tier_on_spear_unlock_and_new_runs(self):
        fresh=ast.get_source_segment(SLAY,method('_fresh_state_from_config'))
        purchase=ast.get_source_segment(SLAY,method('purchase'))
        sanitize=ast.get_source_segment(SLAY,method('_sanitize_state'))
        grant='purchases[SPEAR_BASE_PYLON_ITEM] = max(1,'
        for segment in (fresh,purchase,sanitize):
            self.assertIn(grant,segment)
        self.assertIn('for item_name,bought_raw in state(ctx).get("purchases",{}).items()',SLAY)
        self.assertIn('items.append(NetworkItem(data.code,0,0,int(data.classification)))',SLAY)

    def test_requested_descriptions_exist_and_are_prioritized(self):
        with SHOP.open(encoding='utf-8',newline='') as f:
            rows={r['Item Title']:r for r in csv.DictReader(f)}
        self.assertEqual(rows['Unlock Spear of Adun']['Description'],
                         'The Spear of Adun is available on all missions and starts with "Deploy Pylon".')
        self.assertEqual(rows['Progressive Proxy Pylon (Spear of Adun)']['Description'],
                         'Your pylon now comes with a squad of reinforcements')
        self.assertIn('Allows the next tier of armor and weapon upgrades to be purchased during a mission.',SLAY)
        description=ast.get_source_segment(SLAY,method('shop_entry_description'))
        self.assertLess(description.index('if item_name in SHOP_DESCRIPTION_OVERRIDES:'),
                        description.index('_AP_ITEM_DOCS.get('))


if __name__=='__main__':unittest.main()
