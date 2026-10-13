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

    def test_tosh_spectres_have_telegraphed_scripted_nuke_not_ammo_dependent(self):
        tosh = section('void APRG_TickToshAndHisBoys(', 'bool APRG_IsOdinDefensiveStructure(')
        self.assertIn('g_aprgNextToshSpectreTime = g_aprgMacroReadyTime + 300.0;', tosh)
        self.assertIn('g_aprgNextToshSpectreTime = now + 60.0;', tosh)
        self.assertIn('g_aprgToshSpectreNextOrderTime[slot] = now + 4.0;', tosh)
        self.assertIn('g_aprgToshSpectreNukeTime[i] = now + 12.0;', tosh)
        self.assertIn('"GhostNukeIndicator"',tosh)
        self.assertIn('"PingWarning"',tosh)
        self.assertIn('APRG_CreateObjectiveSafeSlayEffect(UnitGetOwner(spec), "NukeDamage", targetPoint, 12.0);', tosh)
        self.assertIn('if (!UnitIsAlive(spec)) {', tosh)
        self.assertIn('g_aprgToshSpectrePhase[i] = 3;', tosh)
        self.assertIn('ActorSend(g_aprgToshSpectreNukeIndicator[i], "Destroy")', tosh)
        self.assertIn('APRG_NearestPathablePlayerStructure(spec, player)',tosh)
        self.assertIn('RandomFixed(0.0, 5.0)',tosh)
        self.assertIn('AISetUnitScriptControlled(spec, true)',tosh)
        self.assertIn('AISetUnitScriptControlled(spec, false)',tosh)
        self.assertNotIn('APRG_TryUnitAbilityKeyword(spec, "Nuke"',tosh)
        self.assertNotIn('UnitMagazineArm(',tosh)
        self.assertNotIn('GhostAcademy',tosh.split('void APRG_TickToshAndHisBoys(',1)[-1].replace('enemy Ghost Academy',''))
        # No more unsafe march into the player base to reach a 9-range nuke target.
        self.assertNotIn('DistanceBetweenPoints(UnitGetPosition(spec), targetPoint) > 9.0', tosh)
        self.assertNotIn('APRG_OrderAttackMove(spec, targetPoint)', tosh)

if __name__ == '__main__': unittest.main()
