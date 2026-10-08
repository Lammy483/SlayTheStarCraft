"""Run with: python Tools/test_run_races.py (no game or AP installation needed)."""
import importlib.util
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("slay_launcher", Path(__file__).parents[1] / "Payload/slay_launcher.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class GeneratorReached(Exception):
    pass


class RaceSelectionTests(unittest.TestCase):
    def test_each_nonempty_selection_reaches_native_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("SlayTheStarCraft.py", "Generate.py"):
                (root / filename).touch()
            for count in range(1, 4):
                for selection in itertools.combinations(launcher.DEFAULT_RACES, count):
                    with self.subTest(selection=selection):
                        commands = []
                        def capture(command, *_args):
                            commands.append(command)
                            raise GeneratorReached
                        with patch.object(launcher, "archipelago_root", return_value=root), patch.object(launcher, "_run_streamed", side_effect=capture):
                            with self.assertRaises(GeneratorReached):
                                launcher.generate_run(700, "brutal", selected_races=selection)
                        command = commands[0]
                        self.assertEqual(command[command.index("--races") + 1:], list(selection))
                        self.assertIn("--mutation-frequency-multiplier", command)
                        self.assertIn("--extra-shop-slots", command)

    def test_invalid_selection_stops_before_generator(self):
        for selection in ((), ("random",), ("terran", "unknown")):
            with self.subTest(selection=selection), patch.object(launcher, "_run_streamed") as run:
                with self.assertRaises(ValueError):
                    launcher.generate_run(700, "brutal", selected_races=selection)
                run.assert_not_called()

    def test_duplicates_and_order_are_canonical(self):
        self.assertEqual(launcher.normalize_races(["protoss", "terran", "terran"]), ("terran", "protoss"))


if __name__ == "__main__":
    unittest.main()
