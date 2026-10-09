"""r25 regression: correct per-Armada buffers and preflight check for stale installer tokens."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "Payload"
GALAXY = (PAYLOAD / "APRogue.galaxy").read_text(encoding="utf-8")
INSTALL = (PAYLOAD / "install_slay.py").read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("verify_release_r25", PAYLOAD / "verify_release.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def section(start: str, end: str) -> str:
    return GALAXY.split(start, 1)[1].split(end, 1)[0]


class R25Tests(unittest.TestCase):
    def test_normal_armada_uses_requested_40_spawn_and_20_patrol_protection(self):
        normal = section("void APRG_TrySpawnGoldenArmada(", "void APRG_OrderTrueGoldenAtPlayerBase(")
        self.assertIn("APRG_FindGoldenSafeAirPoint(player, 40.0)", normal)
        patrol = section("void APRG_RetargetGoldenArmada(", "bool APRG_EnsureAirReachableToPlayer(")
        # 24 at path center includes up to four range of spacing to protect all members.
        self.assertIn("g_aprgGoldenPatrolIndex, 24.0", patrol)
        self.assertIn('AbilityCommand("move", 0)', patrol)
        self.assertIn("GameGetMissionTime() < 240.0", patrol)
        self.assertNotIn("APRG_EnsureAirReachableToPlayer(probe", normal)

    def test_true_armada_buffers_are_unchanged(self):
        true_spawn = section("void APRG_TrySpawnTrueGoldenArmada(", "void APRG_TickTrueGoldenArmada(")
        self.assertIn("APRG_FindGoldenSafeAirPoint(player, 55.0)", true_spawn)
        true_patrol = section("void APRG_RetargetTrueGoldenArmada(", "unit APRG_TrueGoldenAnchorUnit(")
        self.assertIn("g_aprgTrueGoldenPatrolIndex, 40.0", true_patrol)
        self.assertIn("GameGetMissionTime() < 600.0", true_patrol)
        phoenix = section("void APRG_TickTrueGoldenPhoenixes(", "unit APRG_TrueGoldenNearestCloakedPlayerUnit(")
        self.assertIn("APRG_GoldenPatrolRouteSafe(UnitGetPosition(phoenix), destination, player, 40.0)", phoenix)

    def test_route_samples_path_and_checks_player_allied_structures(self):
        route = section("bool APRG_GoldenPatrolRouteSafe(", "point APRG_FindGoldenSafeAirPoint(")
        self.assertIn("FixedToInt(distance / 3.0)", route)
        self.assertIn("APRG_PointNearPlayerOrAlliedBuilding(sample, player, clearance)", route)
        destination = section("point APRG_GoldenSafePatrolDestination(", "void APRG_RetargetGoldenArmada(")
        self.assertEqual(destination.count("APRG_GoldenPatrolRouteSafe(origin, candidate, player, patrolClearance)"), 2)

    def test_installer_does_not_require_retired_armada_safety_routine(self):
        self.assertNotIn('"APRG_GoldenArmadaEarlySafety",', INSTALL)
        for marker in ("APRG_GoldenPatrolRouteSafe", "APRG_FindGoldenSafeAirPoint", "APRG_GoldenSafePatrolDestination"):
            self.assertIn(f'"{marker}"', INSTALL)
        verifier.check_installer_galaxy_postchecks(PAYLOAD)

    def test_release_verifier_rejects_missing_installer_marker(self):
        # Simulates an accidental refactor deleting a helper but leaving it in
        # install_slay.py's giant pre-install marker list, as happened in r24.
        with tempfile.TemporaryDirectory() as temp:
            sub = Path(temp)
            (sub / "APRogue.galaxy").write_text(GALAXY, encoding="utf-8")
            (sub / "install_slay.py").write_text(INSTALL.replace(
                '"APRG_GoldenPatrolRouteSafe", "APRG_FindGoldenSafeAirPoint"',
                '"APRG_GoldenArmadaEarlySafety", "APRG_FindGoldenSafeAirPoint"', 1,
            ), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "APRG_GoldenArmadaEarlySafety"):
                verifier.check_installer_galaxy_postchecks(sub)


if __name__ == "__main__":
    unittest.main()
