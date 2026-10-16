"""Dev29 regression: conditional commander assets, graceful Zagara fallback, bounded Baneling AI."""
import unittest
from pathlib import Path
from test_v112_lab_rat_zagara_dev28 import function
from test_v112_artanis_commander_dev18 import load_dependency_picker

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / 'Payload/APRogue.galaxy').read_text(encoding='utf-8')
P = (ROOT / 'Payload/slay_the_starcraft.py').read_text(encoding='utf-8')

class Dev29ZagaraBehavior(unittest.TestCase):
    def test_dependencies_remain_conditional_and_sensitive(self):
        block = P[P.index('def dependency_variant_for_mission('):P.index('def dependency_variant_for_mission(')+5500]
        self.assertIn('if "general" in blessings and commander_hero_index(ctx, mission_id) == 18:', block)
        self.assertIn('if mission_name in DEPENDENCY_SENSITIVE_MISSIONS',block)
        self.assertLess(block.index('if mission_name in DEPENDENCY_SENSITIVE_MISSIONS'),block.index('commander_hero_index(ctx, mission_id) == 18'))
        self.assertEqual(load_dependency_picker(18),'swarm')
        self.assertEqual(load_dependency_picker(18,'Heart of the Swarm'),'base')
        self.assertEqual(load_dependency_picker(18,'Legacy of the Void'),'swarm')
        self.assertEqual(load_dependency_picker(18,name='Safe Haven'),'base')
        self.assertEqual(load_dependency_picker(18,name="Haven's Fall"),'base')
        self.assertEqual(load_dependency_picker(7),'base')
        self.assertEqual(load_dependency_picker(9),'void')

    def test_only_zagara_has_failure_fallback(self):
        source = function('APRG_FindValidHeroTypeFromIndex')
        self.assertIn('if (preferredIndex == 9) { return APRG_ArtanisHeroType(); }',source)
        self.assertIn('candidate = APRG_ZagaraHeroType();',source)
        self.assertIn('return APRG_FindValidCommanderHeroFallbackExcept("ZaGara");',source)
        fallback = function('APRG_FindValidCommanderHeroFallbackExcept')
        self.assertIn('APRG_CommanderFallbackCandidate',fallback)
        self.assertIn('candidate == excludedType',fallback)
        self.assertIn('CatalogEntryIsValid',fallback)
        self.assertNotIn('"TychusCommando"',fallback)

    def test_zagara_spawn_failure_retries_another_real_commander(self):
        source = function('APRG_GiveGeneralIfReady')
        self.assertIn('g_aprgCommanderHeroType == "ZaGara" && (g_aprgCommanderHero == null || !UnitIsAlive(g_aprgCommanderHero))',source)
        self.assertIn('heroType == "ZaGara" && (g_aprgCommanderHero == null || !UnitIsAlive(g_aprgCommanderHero))',source)
        self.assertEqual(source.count('APRG_FindValidCommanderHeroFallbackExcept("ZaGara")'),2)
        self.assertIn('g_aprgCommanderHeroType = heroType;',source)
        self.assertIn('Zagara unavailable; deployed',source)

    def test_baneling_retarget_bounded_and_round_robin(self):
        source = function('APRG_RetargetZagaraBanelings')
        self.assertIn('if (batchCount > 25) { batchCount = 25; }',source)
        self.assertIn('g_aprgZagaraBanelingRetargetCursor',source)
        self.assertIn('(g_aprgZagaraBanelingRetargetCursor + batchCount) % count',source)
        self.assertIn('APRG_OrderBanelingStreamAttackMove',source)
        self.assertIn('APRG_NearestPathablePlayerStructureFromGroup',source)
        tick = function('APRG_TickZagarasBanelings')
        self.assertIn('g_aprgNextZagaraBanelingRetargetTime = now + 1.0;',tick)
        self.assertIn('UnitCreate(20, "Baneling"',tick)
        self.assertIn('batch < 5',tick)
        self.assertEqual(tick.count('APRG_RetargetZagaraBanelings(player);'),2)

    def test_baneling_cursor_reset_per_mission(self):
        self.assertIn('g_aprgZagaraBanelingRetargetCursor = 0;',G)
        self.assertIn('g_aprgZagaraBanelingRetargetCursor = 0;',G[G.index('g_aprgNextZagaraBanelingTime = 600.0;', G.index('g_aprgNextZagaraBanelingTime = 600.0;')+1):])

if __name__ == '__main__':
    unittest.main()
