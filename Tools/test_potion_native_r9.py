"""Source-side regression guard for potion targeting and hero reuse."""
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).parents[1]/"Payload"
GALAXY=(ROOT/"APRogue.galaxy").read_text(encoding="utf-8")
RUNTIME=(ROOT/"slay_the_starcraft.py").read_text(encoding="utf-8")

class PotionNativeR9Tests(unittest.TestCase):
    def test_native_target_cursor_and_order_consumption(self):
        for token in ("UISetTargetingOrder(", 'TriggerAddEventUnitOrder(g_aprgPotionOrderTrigger, null, AbilityCommand("move", 0))',
            "OrderGetTargetUnit(issued)","OrderGetTargetPosition(issued)","APRG_PotionNativeOrder_Func", "APRG_PotionEndNativeTarget", "g_aprgPotionPendingSlot",
            "APRG_PotionConsume(player, slot)"):
            self.assertIn(token,GALAXY)
        self.assertNotIn('TriggerAddEventMouseClicked(g_aprgPotionMouseTrigger, player, c_mouseButtonLeft',GALAXY)
        self.assertNotIn('APRG_PotionUnitAt(',GALAXY)
        # A unit is not a unitref; this erroneous native call broke APRogue's
        # compilation in the potion update and disabled all three races.
        self.assertNotIn('TriggerAddEventUnitOrder(g_aprgPotionOrderTrigger, g_aprgPotionTargetCaster,', GALAXY)

    def test_native_cursor_unit_registered_in_xml(self):
        root=ET.parse(ROOT/"APRogueData.xml").getroot()
        caster=root.find('.//CUnit[@id="APRoguePotionTargetCaster"]')
        self.assertIsNotNone(caster)
        self.assertEqual(caster.attrib.get("parent"),"Marine")
        self.assertIn('UnitCreate(1, "APRoguePotionTargetCaster", c_unitCreateIgnorePlacement',GALAXY)

    def test_bottles_reuse_boon_variants_and_cooldowns(self):
        start=GALAXY.index('bool APRG_PotionActivate(')
        end=GALAXY.index('bool APRG_PotionDamage_Func(',start)
        block=GALAXY[start:end]
        for symbol in ('APRG_LeviathanBoonType()', 'APRG_NormalizeLeviathanBoon(u, player)',
                       'APRG_HyperionBoonType()', 'APRG_NormalizeHyperionBoon(u, player)'):
            self.assertIn(symbol,block)
        self.assertNotIn('APRG_TryLeviathanMutationSpawn(g_aprgPotionLeviathan',GALAXY)
        self.assertNotIn('g_aprgPotionLeviNextSpawn',GALAXY)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogAbil, abilityType, "Cost.Cooldown.TimeUse", player, "60")', GALAXY)

    def test_price_in_source(self):
        self.assertIn('price=severity * 125',RUNTIME)
        self.assertNotIn('price=rarity * 100',RUNTIME)

if __name__ == "__main__": unittest.main()
