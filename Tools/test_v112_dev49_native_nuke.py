import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
G=(ROOT/'Payload'/'APRogue.galaxy').read_text(encoding='utf8')
B=G[G.index('void APRG_TickToshAndHisBoys('):G.index('bool APRG_IsOdinDefensiveStructure(')]

class NativeToshNukeTest(unittest.TestCase):
    def test_normal_five_minute_first_spectre_and_one_minute_cadence(self):
        self.assertIn('const fixed APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY = 300.0;',G)
        self.assertIn('g_aprgMacroReadyTime + APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY',B)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;',B)
    def test_native_nuke_abilities_have_campaign_signatures(self):
        for value in ('CatalogEntryIsValid(c_gameCatalogAbil, "TacNukeStrike")',
                      'UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);',
                      'OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)',
                      'castAccepted = UnitIssueOrder(spec, castOrder, c_orderQueueReplace);',
                      'UnitOrderHasAbil(spec, "TacNukeStrike")'):
            self.assertIn(value,B)
    def test_no_simulated_explosion_or_marker(self):
        self.assertNotIn('APRG_CreateObjectiveSafeSlayEffect',B)
        self.assertNotIn('libNtve_gf_CreateModelAtPoint',B)
    def test_temporary_silo_is_removed_on_both_lifecycle_paths(self):
        self.assertGreaterEqual(B.count('UnitRemove(g_aprgToshSpectreNukeSilo[i])'),2)
        self.assertIn('g_aprgToshSpectreNukeTime[i] = now + 23.0;',B)
        self.assertIn('UnitSetState(silo, c_unitStateTargetable, false);',B)
        self.assertIn('UnitSetState(silo, c_unitStateSelectable, false);',B)
    def test_no_global_dependency_change(self):
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, "GhostAcademy")',B)

if __name__=='__main__': unittest.main()
