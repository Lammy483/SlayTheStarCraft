"""Guard controllable named-unit consumables against automated attack AI."""
from pathlib import Path
import re
import unittest
G=(Path(__file__).resolve().parents[1]/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

def fn(name):
 m=re.search(r'^(?:bool|void|int|fixed|string|unit|unitgroup|actor)\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',G,re.M)
 assert m is not None,name
 start=G.index('{',m.start());level=1
 for i in range(start+1,len(G)):
  if G[i]=='{':level+=1
  elif G[i]=='}':
   level-=1
   if not level:return G[start:i+1]
 raise AssertionError(name)

class R26ControllableConsumables(unittest.TestCase):
 def test_named_unit_variant_resolved_only_once(self):
  q=fn('APRG_PotionStartSpawnQueue')
  self.assertIn('APRG_PotionUnlockedUnitType(kind, APRG_GetPrimaryPlayer())',q)
  self.assertIn('g_aprgPotionQueueResolvedUnitType[i]',q)
  self.assertIn('g_aprgPotionQueueResolvedUnitType[slot]',fn('APRG_TickPotionSpawnQueues'))
 def test_unlocked_ap_variants_and_default_council_selection(self):
  u=fn('APRG_PotionUnlockedUnitType')
  for name in ('AP_StalkerShakuras','AP_ZealotAiur','AP_ImmortalAiur','AP_VoidRayShakuras'):
   self.assertIn(name,u)
  self.assertIn('APRG_PlayerSpawnCandidateHealthy(player, preferred, true)',u)
  self.assertIn('APRG_FindPlayerAPProductionVariant(player, nativeType)',u)
  self.assertIn('APRG_PlayerSpawnSameUnitShape',u)
 def test_auto_orders_limited_to_uncontrollable_mass_waves(self):
  f=fn('APRG_TickPotionSpawnQueues')
  self.assertIn('if (kind == 17 || kind == 18) {\n                // Only Mass Marines',f)
  chunk=f.split('if (kind == 17 || kind == 18) {\n                // Only Mass Marines',1)[1].split('\n            }\n        }',1)[0]
  self.assertIn('APRG_MakeGroupUncommandable(created)',chunk)
  self.assertIn('UnitGroupAdd(g_aprgPotionAutoUnits, spawned)',chunk)
  self.assertIn('APRG_OrderAttackMove(spawned',chunk)
  outside=f.replace(chunk,'')
  # After removing the mass-wave block, the only remaining orders are the
  # periodic AI retargeter applied exclusively to g_aprgPotionAutoUnits.
  self.assertIn('UnitGroupUnitFromEnd(g_aprgPotionAutoUnits, i)',outside)
  self.assertNotIn('UnitGroupAdd(g_aprgPotionAutoUnits, spawned)',outside)
 def test_ap_placeholder_falls_back_to_native_unit(self):
  f=fn('APRG_TickPotionSpawnQueues')
  self.assertIn('UnitGetPropertyFixed(spawned, c_unitPropLifeMax',f)
  self.assertIn('UnitCreate(1, APRG_PotionRandomUnitType(kind)',f)
 def test_mass_spellcasters_remain_exact_native_with_full_energy(self):
  f=fn('APRG_TickPotionSpawnQueues')
  self.assertIn('APRG_CreatePlayerUnitsVanillaSafe(1, unitType',f)
  self.assertIn('UnitGetPropertyFixed(spawned, c_unitPropEnergyMax',f)

if __name__=='__main__':unittest.main()
