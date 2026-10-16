"""Dev9 regression tests: persistent Kill Team vision and reliable Tosh Spectre nukes."""
from __future__ import annotations
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT/'Payload/APRogue.galaxy').read_text(encoding='utf-8')

def section(first, end):
    return G.split(first,1)[1].split(end,1)[0]

class Dev9Regressions(unittest.TestCase):
    def test_kill_teams_are_visible_without_pings(self):
        spawn = section('unitgroup APRG_SpawnOneMarauderKillTeam(', 'void APRG_TickMarauderKillTeams(')
        tick = section('void APRG_TickMarauderKillTeams(', 'void APRG_ApplyNewBoonStats(')
        self.assertIn('APRG_RegisterAlwaysVisibleGroup(team, player);', spawn)
        for text in (spawn, tick):
            self.assertNotIn('MinimapPing(', text)
            self.assertNotIn('PingCreate(', text)
        for token in ('const int APRG_MAX_ALWAYS_VISIBLE = 128;',
                      'unit[128] g_aprgAlwaysVisibleUnits;',
                      'region[128] g_aprgAlwaysVisibleRegions;',
                      'revealer[128] g_aprgAlwaysVisibleRevealers;'):
            self.assertIn(token, G)
        vision=section('void APRG_RegisterAlwaysVisibleUnit(', 'unit APRG_NearestPlayerStructure(')
        self.assertIn('RegionSetCenter(r, UnitGetPosition(u));',vision)
        self.assertIn('VisRevealerUpdate(rv);', vision)

    def test_tosh_spectres_use_blizzard_native_nuke_with_temporary_ammo(self):
        tosh = section('void APRG_TickToshAndHisBoys(', 'bool APRG_IsOdinDefensiveStructure(')
        self.assertIn('g_aprgNextToshSpectreTime = g_aprgMacroReadyTime + APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY;',tosh)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;',tosh)
        self.assertIn('g_aprgToshSpectreNextOrderTime[slot] = now;',tosh)
        self.assertIn('if (!UnitIsAlive(spec)) {',tosh)
        self.assertIn('UnitMagazineArm(silo, AbilityCommand("ArmSiloWithNuke", 0), 1);',tosh)
        self.assertIn('UnitMagazineCount(silo, "ArmSiloWithNuke")',tosh)
        self.assertIn('OrderTargetingPoint(AbilityCommand("TacNukeStrike", 0), targetPoint)',tosh)
        self.assertIn('UnitOrderIsValid(spec, castOrder)',tosh)
        self.assertIn('UnitIssueOrder(spec, castOrder, c_orderQueueReplace)',tosh)
        self.assertIn('UnitOrderHasAbil(spec, "TacNukeStrike")',tosh)
        self.assertIn('UnitRemove(g_aprgToshSpectreNukeSilo[i])',tosh)
        self.assertIn('AISetUnitScriptControlled(spec, true)',tosh)
        self.assertIn('AISetUnitScriptControlled(spec, false)',tosh)
        self.assertNotIn('APRG_CreateObjectiveSafeSlayEffect(UnitGetOwner(spec), "NukeDamage"',tosh)
        self.assertNotIn('libNtve_gf_CreateModelAtPoint("GhostNukeIndicator"',tosh)
        self.assertNotIn('UnitIssueOrder(spec, Order(AbilityCommand("stop"',tosh)

if __name__ == '__main__': unittest.main()
