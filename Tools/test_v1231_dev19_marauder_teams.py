"""Dev19: connected-ground Marauder Kill Teams with shared attack-move waypoints."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")

def fn(name):
    m = re.search(r"(?m)^(?:void|bool|point|unitgroup)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", G)
    assert m, name
    depth = 0
    for i in range(m.end()-1, len(G)):
        if G[i] == "{": depth += 1
        if G[i] == "}":
            depth -= 1
            if depth == 0: return G[m.end()-1:i+1]
    raise AssertionError(name)

class KillTeamDev19(unittest.TestCase):
    def test_only_connected_ground_spawns(self):
        f = fn("APRG_MarauderKillTeamSpawnPoint")
        self.assertIn("APRG_KerriganSafeHomePoint(player)", f)
        self.assertIn("PointPathingIsConnected(candidate, homeGround)", f)
        self.assertIn("PointPathingPassable(candidate)", f)
        self.assertIn("APRG_PointNearPlayerOrAlliedBuilding(candidate, player, 12.0)", f)
        spawn = fn("APRG_SpawnOneMarauderKillTeam")
        self.assertIn("APRG_MarauderKillTeamSpawnPoint(player, otherTeam)", spawn)
        self.assertNotIn("p = UnitGetPosition(anchor)", spawn)

    def test_tight_spawn_cluster(self):
        f = fn("APRG_SpawnOneMarauderKillTeam")
        self.assertIn("groupIndex < 3", f)
        self.assertIn("UnitCreate(5, marauderType", f)
        self.assertIn("RandomFixed(0.8, 1.8)", f)
        self.assertIn('UnitCreate(3, "Medic"', f)

    def test_shared_waypoint_and_all_members_arrived(self):
        order = fn("APRG_OrderMarauderKillTeamGroup")
        self.assertIn("APRG_OrderAttackMove(u, destination);", order)
        self.assertNotIn("APRG_RandomFixedPatrolPointForUnit", order)
        arrival = fn("APRG_MarauderKillTeamArrived")
        self.assertIn("DistanceBetweenPoints(UnitGetPosition(u), destination) > 9.0", arrival)
        waypoint = fn("APRG_MarauderKillTeamNextWaypoint")
        self.assertIn("PointPathingIsConnected(origin, candidate)", waypoint)
        self.assertIn("UnitPathableToPoint(leader, candidate", waypoint)
        tick = fn("APRG_TickOneMarauderKillTeam")
        self.assertIn("APRG_MarauderKillTeamArrived(team, waypoint)", tick)
        self.assertIn("APRG_OrderMarauderKillTeamGroup(team, next)", tick)
        self.assertIn("APRG_OrderMarauderKillTeamGroup(team, waypoint)", tick)
        self.assertIn("now >= issuedAt + 90.0", tick)

    def test_two_teams_one_time_spawning(self):
        tick = fn("APRG_TickMarauderKillTeams")
        self.assertIn("!g_aprgMarauderKillTeamOneCreated", tick)
        self.assertIn("!g_aprgMarauderKillTeamTwoCreated", tick)
        self.assertIn("g_aprgMarauderKillTeamOneCreated && g_aprgMarauderKillTeamTwoCreated", tick)
        self.assertIn("APRG_TickOneMarauderKillTeam(g_aprgMarauderKillTeamOne", tick)
        self.assertIn("APRG_TickOneMarauderKillTeam(g_aprgMarauderKillTeamTwo", tick)
        self.assertNotIn("now + 30.0", tick)

if __name__ == "__main__":
    unittest.main()
