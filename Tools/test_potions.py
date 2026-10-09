"""Offline potion regression coverage without an Archipelago installation.

Run: python Tools/test_potions.py
"""
from __future__ import annotations
import ast
import hashlib
import json
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from typing import Any, Mapping, Sequence

SOURCE=Path(__file__).parents[1] / 'Payload' / 'slay_the_starcraft.py'
MODULE=ast.parse(SOURCE.read_text(encoding='utf-8'),str(SOURCE))
KEEP_FUNC={"_spear_unlocked_active_ability_count", "_potion_unlock_eligible", "potion_mercenary_mask", "_potion_bank_uses", "potion_inventory", "potion_handshake_slots", "can_buy_shop_item", "purchase", "price_for_item", "shop_category_for_item", "test_potion_run_token"}
KEEP_VARS={"POTION_PREFIX", "POTION_DEFINITIONS", "POTION_CATALOG", "POTION_CAPACITY", "POTION_MERC_NAMES", "_POTION_BANK_USE_CACHE", "POTION_RANDOM_UNITS", "POTION_VARIANT_PREFIX"}
body=[]
for item in MODULE.body:
    if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)) and item.name in KEEP_FUNC:
        body.append(item)
    if isinstance(item,(ast.Assign,ast.AnnAssign)) and any(t.id in KEEP_VARS for t in ([item.target] if isinstance(item,ast.AnnAssign) else item.targets) if isinstance(t,ast.Name)):
        body.append(item)
    if isinstance(item,ast.Expr) and isinstance(item.value,ast.Call) and isinstance(item.value.func,ast.Attribute) and isinstance(item.value.func.value,ast.Name) and item.value.func.value.id=='POTION_CATALOG' and item.value.func.attr=='update':
        body.append(item)
NS={"Any":Any,"Mapping":Mapping,"Sequence":Sequence,"Path":Path,"hashlib":hashlib}
exec(compile(ast.Module(body=body,type_ignores=[]),str(SOURCE),'exec'),NS)

class Ctx:
    slay_config={"run_seed":123}
    def __init__(self):
        self.state={"potion_inventory":[],"potion_serial":0,"spent":0}
        self.stock=list(NS['POTION_CATALOG'])
        self.owned=set()
        self.persist_count=0
        self.available_credits=2500

class PotionTests(unittest.TestCase):
    def setUp(self):
        self.ctx=Ctx()
        NS.update({"enabled":lambda ctx:True,"state_ready":lambda ctx:True,"state":lambda ctx:ctx.state,
                   "_potion_bank_uses":lambda ctx:set(),"_progression_owned":lambda ctx,name:name in ctx.owned,
                   "SPEAR_UNLOCK":"Spear", "KERRIGAN_UNLOCK":"Kerrigan",
                   "SPEAR_FALLBACK_ITEMS":{"Progressive Proxy Pylon (Spear of Adun)","Orbital Strike (Spear of Adun)","Guardian Shell (Spear of Adun)"},
                   "_purchased_count":lambda ctx,name:ctx.state.get('purchases',{}).get(name,0),
                   "shop_stock":lambda ctx:ctx.stock,"credits":lambda ctx:ctx.available_credits-ctx.state['spent'],
                   "_persist_state":lambda ctx:setattr(ctx,'persist_count',ctx.persist_count+1)})
    def test_every_potion_has_expected_fixed_price_and_target(self):
        expected=[("Mineral Reserves",1,"instant"),("Gas Reserves",1,"instant"),
                  ("Odin in a Bottle",2,"point"),("Leviathan in a Bottle",3,"point"),
                  ("Hyperion in a Bottle",4,"point"),("Drop Pod Wave",2,"point"),
                  ("Mass EMP",1,"instant"),("Tactical Nuke",1,"point"),
                  ("Tosh's Miners",1,"point"),("Stealth Protocol",2,"instant"),
                  ("Mass Stimpack",2,"instant"),("Spear of Adun Recharge",2,"instant"),
                  ("Second Kerrigan",2,"instant"),("Mercenary Favor",2,"instant"),
                  ("Guardian Matrix",1,"friendly"),("Corruption Spores",1,"unit"),
                  ("Mass Marines",1,"instant"),("Mass Spellcasters",1,"instant"),
                  ("Spawn [amount] [unit]",1,"point")]
        self.assertEqual(len(NS['POTION_DEFINITIONS']),19)
        self.assertEqual(len(NS['POTION_CATALOG']),19+len(NS['POTION_RANDOM_UNITS']))
        for i,(name,rarity,target) in enumerate(expected,1):
            info=NS['POTION_CATALOG']["slay_potion::"+str(i)]
            self.assertEqual((info['index'],info['name'],info['rarity'],info['target']), (i,name,rarity,target))
            self.assertEqual(NS['price_for_item']("slay_potion::"+str(i),self.ctx),125*rarity)
            self.assertEqual(info['price'],125*rarity)
            self.assertEqual(NS['shop_category_for_item']("slay_potion::"+str(i)),"Consumables")
    def test_random_variants_are_named_and_budgeted_at_shop_time(self):
        for i, (singular,plural,unit,minerals,gas) in enumerate(NS['POTION_RANDOM_UNITS'],1):
            potion=NS['POTION_CATALOG'][f'slay_potion::19::{i}']
            qty=2000//(minerals+gas)
            self.assertEqual(potion['index'],1900+i)
            self.assertEqual(potion['name'],f'Spawn {qty} {plural}')
            self.assertEqual(potion['unit'],unit)
            self.assertEqual(potion['amount'],qty)
            self.assertEqual(potion['price'],125)
            self.assertIn(str(qty),potion['description'])

    def test_random_variant_persists_as_single_potion_slot(self):
        variant='slay_potion::19::7'
        self.assertIn(variant,self.ctx.stock)
        ok,msg=NS['purchase'](self.ctx,variant)
        self.assertTrue(ok,msg)
        self.assertEqual(NS['potion_handshake_slots'](self.ctx),(1907,1,0,0))
        self.assertEqual(self.ctx.state['spent'],125)
        self.assertEqual(self.ctx.state['potion_inventory'][0]['id'],variant)

    def test_two_slot_limit_and_serial_allocation(self):
        for index in (1,2):
            ok,msg=NS['purchase'](self.ctx,"slay_potion::"+str(index))
            self.assertTrue(ok,msg)
        self.assertEqual(NS['potion_handshake_slots'](self.ctx),(1,1,2,2))
        self.assertFalse(NS['can_buy_shop_item'](self.ctx,"slay_potion::3"))
        self.assertFalse(NS['purchase'](self.ctx,"slay_potion::3")[0])
        self.assertEqual(self.ctx.state['spent'],250)
        self.assertEqual(self.ctx.persist_count,2)
    def test_consumption_reopens_slot_and_serial_never_reused(self):
        NS['purchase'](self.ctx,"slay_potion::1")
        NS['purchase'](self.ctx,"slay_potion::2")
        NS['_potion_bank_uses']=lambda ctx:{1}
        self.assertEqual(NS['potion_handshake_slots'](self.ctx),(2,2,0,0))
        self.assertTrue(NS['can_buy_shop_item'](self.ctx,"slay_potion::3"))
        ok,msg=NS['purchase'](self.ctx,"slay_potion::3")
        self.assertTrue(ok,msg)
        self.assertEqual(NS['potion_handshake_slots'](self.ctx),(2,2,3,3))
        self.assertEqual(self.ctx.state['potion_serial'],3)
    def test_unlock_conditions(self):
        self.assertFalse(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::12"))
        self.assertFalse(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::13"))
        self.assertFalse(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::14"))
        self.ctx.owned={"Spear","Kerrigan",*NS['POTION_MERC_NAMES'][:3]}
        self.assertFalse(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::12"))
        self.ctx.state['purchases']={'Progressive Proxy Pylon (Spear of Adun)':1}
        self.assertFalse(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::12"))
        self.ctx.state['purchases']['Orbital Strike (Spear of Adun)']=1
        self.assertTrue(all(NS['_potion_unlock_eligible'](self.ctx,"slay_potion::"+str(i)) for i in (12,13,14)))
        self.assertEqual(NS['potion_mercenary_mask'](self.ctx),7)
    def test_bank_xml_consumption_isolated_to_run_token(self):
        from xml.etree import ElementTree as ET
        original=NS['_potion_bank_uses']
        source=next(item for item in MODULE.body if isinstance(item,ast.FunctionDef) and item.name=='_potion_bank_uses')
        exec(compile(ast.Module(body=[source],type_ignores=[]),str(SOURCE),'exec'),NS)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'Documents'/'StarCraft II'/'123'/'Banks'
            root.mkdir(parents=True)
            token=NS['test_potion_run_token'](self.ctx)
            (root/'SlayTheStarCraftPotions.SC2Bank').write_text(
                f'<Bank><Section name="PotionUses"><Key name="Serial1"><Value int="{token}"/></Key>'
                '<Key name="Serial2"><Value int="456"/></Key></Section></Bank>',encoding='utf-8')
            with patch.object(Path,'home',return_value=Path(tmp)):
                with patch.dict('os.environ', {'USERPROFILE':'','OneDrive':'','OneDriveConsumer':''}):
                    self.assertEqual(NS['_potion_bank_uses'](self.ctx),{1})
        NS['_potion_bank_uses']=original

if __name__=='__main__':unittest.main()
