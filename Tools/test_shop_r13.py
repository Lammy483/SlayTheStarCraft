"""Offline regression tests for custom potion purchase states and shop UI chrome."""
import ast
from pathlib import Path
import unittest
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
RUNTIME = (ROOT/'slay_the_starcraft.py').read_text(encoding='utf-8')
UI = (ROOT/'slay_command_ui.py').read_text(encoding='utf-8')
TREE = ast.parse(RUNTIME)
FUNCTIONS={'shop_render_states','can_buy_shop_item','_spear_unlocked_active_ability_count','_potion_unlock_eligible'}
VARIABLES={'POTION_PREFIX','POTION_DEFINITIONS','POTION_CATALOG','POTION_CAPACITY','POTION_RANDOM_UNITS','POTION_VARIANT_PREFIX'}
nodes=[]
for node in TREE.body:
    if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS:
        nodes.append(node)
    elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in VARIABLES for t in node.targets):
        nodes.append(node)
    elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='POTION_CATALOG' and node.value.func.attr=='update':
        nodes.append(node)
NS={'Any':Any,'Sequence':Sequence}
exec(compile(ast.Module(body=nodes,type_ignores=[]), str(ROOT/'slay_the_starcraft.py'),'exec'),NS)

class Ctx:
    def __init__(self, slots=0, credits=999):
        self.slots=[{'id': 'slay_potion::1', 'serial': i+1} for i in range(slots)]
        self.owned=set()
        self.credits=credits
        self.state={'purchases':{}}

class ShopR13Tests(unittest.TestCase):
    def setUp(self):
        NS.update({
            'enabled':lambda ctx:True,
            'state_ready':lambda ctx:True,
            'state':lambda ctx:ctx.state,
            'potion_inventory':lambda ctx:ctx.slots,
            '_progression_owned':lambda ctx,name:name in ctx.owned,
            'SPEAR_UNLOCK':'Spear', 'KERRIGAN_UNLOCK':'Kerrigan',
            'SPEAR_FALLBACK_ITEMS':{'Progressive Proxy Pylon (Spear of Adun)','Orbital Strike (Spear of Adun)'},
            '_purchased_count':lambda ctx,name:ctx.state['purchases'].get(name,0),
            'purchased_count':lambda ctx,name:0,
            'price_for_item':lambda name,ctx,sale_items_override=None: int(NS['POTION_CATALOG'][name]['price']),
            '_parse_boon':lambda name:(None,None),
            '_is_progression_item':lambda name:False,
            '_item_table':lambda:{},  # Potions have no Archipelago item-table entry.
            '_logic_owned_item_counts':lambda ctx:{},
            '_owned_unlock_names':lambda ctx,counts=None:set(),
        })
    def states(self,ctx,names):
        return NS['shop_render_states'](ctx,names)
    def test_potions_buyable_with_empty_slots_and_zero_ap_table_entries(self):
        ctx=Ctx()
        states=self.states(ctx,['slay_potion::1','slay_potion::3'])
        self.assertEqual(states['slay_potion::1'],(0,True,125))
        self.assertEqual(states['slay_potion::3'],(0,True,250))
    def test_two_full_slots_block_potions(self):
        ctx=Ctx(slots=2)
        self.assertEqual(self.states(ctx,['slay_potion::1'])['slay_potion::1'],(0,False,125))
    def test_unlocks_still_apply(self):
        ctx=Ctx()
        self.assertFalse(self.states(ctx,['slay_potion::12'])['slay_potion::12'][1])
        ctx.owned.add('Spear')
        self.assertFalse(self.states(ctx,['slay_potion::12'])['slay_potion::12'][1])
        ctx.state['purchases']['Progressive Proxy Pylon (Spear of Adun)']=1
        ctx.state['purchases']['Orbital Strike (Spear of Adun)']=1
        self.assertTrue(self.states(ctx,['slay_potion::12'])['slay_potion::12'][1])
    def test_random_variants_also_use_potion_purchase_rules(self):
        ctx=Ctx()
        self.assertEqual(self.states(ctx,['slay_potion::19::7'])['slay_potion::19::7'], (0,True,125))
    def test_shop_has_dark_borderless_popup_and_reclaimed_category_space(self):
        self.assertIn('shop_popup_background.png',UI)
        self.assertIn('border=(0,0,0,0)',UI)
        self.assertIn('separator_height=0, title_size=0',UI)
        self.assertIn("self.heading.height=0 if overview and self.shop else dp(29)",UI)
        self.assertIn("self.heading.text='' if self.shop else 'All Categories'",UI)
        self.assertTrue((ROOT/'slay_assets/shop_popup_background.png').is_file())
    def test_shop_controls_renamed_and_no_extra_technology_button(self):
        self.assertIn("'[b]Shop[/b]' if shop",UI)
        self.assertIn("top.add_widget(control('Exit Shop'",UI)
        self.assertNotIn("control('Technology'",UI)
        self.assertNotIn("Return to Route",UI)
        self.assertNotIn("Supply Depot",UI)

if __name__=='__main__': unittest.main()
