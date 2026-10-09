"""Regression test for the planet-route renderer's Endless monkey-patch.

Run from any directory: python Tools/test_endless_chart_adapter_r12.py
No Kivy, Archipelago, or SC2 installation is required.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
endless_ast = ast.parse((ROOT / 'Payload' / 'slay_endless_ui.py').read_text(encoding='utf-8'))
install = next(n for n in endless_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'install')
wrapper_ast = next(n for n in install.body if isinstance(n, ast.FunctionDef) and n.name == 'positions')


def wrapper_with_spy():
    calls = []
    def original(*args):
        calls.append(args)
        return {'original': True}
    namespace = {'original_positions': original, 'dp': lambda value: value}
    unit = ast.fix_missing_locations(ast.Module(body=[wrapper_ast], type_ignores=[]))
    exec(compile(unit, '<actual-endless-chart-wrapper>', 'exec'), namespace)
    return namespace['positions'], calls


class EndlessChartAdapterTests(unittest.TestCase):
    def test_adventure_forwards_widened_mission_geometry(self):
        positions, calls = wrapper_with_spy()
        nodes = {2: {'layer': 0, 'lane': 1}, 7: {'layer': 0, 'lane': 2}}
        preferred = {2: .3, 7: .7}
        widths = {2: 260., 7: 490.}
        self.assertEqual(positions(nodes, 1400, preferred, widths), {'original': True})
        self.assertEqual(calls, [(nodes, 1400, preferred, widths)])

    def test_old_three_argument_call_still_works(self):
        positions, calls = wrapper_with_spy()
        nodes = {1: {'layer': 0, 'lane': 0}}
        self.assertEqual(positions(nodes, 950, None), {'original': True})
        self.assertEqual(calls, [(nodes, 950, None, None)])

    def test_endless_chart_accepts_four_arguments_without_using_adventure_positions(self):
        positions, calls = wrapper_with_spy()
        nodes = {
            15: {'layer': 3, 'lane': 0, 'lane_count': 2, '_endless_floor': True},
            18: {'layer': 3, 'lane': 1, 'lane_count': 2, '_endless_floor': True},
        }
        result = positions(nodes, 950, {}, {15: 285, 18: 300})
        self.assertAlmostEqual(result[15][0], 307.5)
        self.assertAlmostEqual(result[18][0], 642.5)
        self.assertEqual(result[15][1], 30)
        self.assertEqual(calls, [])

    def test_renderer_supplies_measured_widths_as_fourth_argument(self):
        code = (ROOT / 'Payload' / 'slay_command_ui.py').read_text(encoding='utf-8')
        self.assertIn('positions=resolve_route_positions(graph_data,chart.width,preferred,{int(b.mission_id):b.width for b in buttons})', code)


if __name__ == '__main__':
    unittest.main()
