"""v1.1.0: retire Endless run creation and prevent stranded tooltip widgets.

All tests use source functions with headless stand-ins; no installed Kivy or
Archipelago runtime needed. Existing Endless saves remain intact.
"""
from __future__ import annotations

import ast
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = ROOT / "Payload" / "slay_launcher.py"
ENDLESS_PATH = ROOT / "Payload" / "slay_endless_ui.py"


def extract_function(path: Path, name: str):
    program = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in program.body if isinstance(n, ast.FunctionDef) and n.name == name)
    mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {}
    exec(compile(mod, str(path), "exec"), scope)
    return scope[name]


class FakeMissionButton:
    all_buttons = []

    def __init__(self, text, mission_id):
        self.text = text
        self.mission_id = mission_id
        self.tooltip_text = ""
        self.disabled = False
        self.visible_tooltip = False
        self.tooltip_removals = 0
        self.bound = False
        self.__class__.all_buttons.append(self)

    def bind(self, **kwargs):
        assert 'on_press' in kwargs
        self.bound = True

    def remove_tooltip(self):
        self.visible_tooltip = False
        self.tooltip_removals += 1


class FakeChart:
    def __init__(self, layers):
        self.layers = sorted(layers)
        self.parent = object()
        self.children = []

    def add_widget(self, child):
        self.children.append(child)


class FakeManager:
    def __init__(self, data):
        self.ctx = types.SimpleNamespace(data=data, endless=True, slay_config={"run_id": "test-run-1"})
        self.launching = False
        self.mission_buttons = []
        self.slay_chart = None
        self.slay_chart_buttons = ()
        self.last_shown_tooltip = -1
        self.redraws = 0
        self.native_calls = 0
        self.tooltip_clears = 0

    def build_mission_table(self, _dt):
        self.native_calls += 1

    def clear_tooltip(self):
        self.tooltip_clears += 1
        for button in self.mission_buttons:
            button.remove_tooltip()

    def _slay_refresh_header(self):
        pass

    def mission_callback(self, button):
        pass


class EndlessRetirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = LAUNCHER_PATH.read_text(encoding='utf-8')
        cls.endless = ENDLESS_PATH.read_text(encoding='utf-8')

    def test_no_game_mode_selector_or_endless_generation(self):
        self.assertNotIn('game_mode_button', self.launcher)
        self.assertNotIn('add_field(0, "Game Mode"', self.launcher)
        self.assertIn('if game_mode != "adventure":', self.launcher)
        self.assertIn('run_data["game_mode"] = "adventure"', self.launcher)
        self.assertNotIn('"Endless Mode (ALPHA)"', self.launcher)

    def test_api_rejects_endless_before_touching_runtime(self):
        node = next(n for n in ast.parse(self.launcher).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'generate_run')
        early = ast.fix_missing_locations(ast.Module(body=[ast.FunctionDef(
            name=node.name, args=node.args, body=node.body[:2],
            decorator_list=[], returns=node.returns,
            type_params=getattr(node, 'type_params', []))], type_ignores=[]))
        scope = {'normalize_races': lambda races: races}
        # Any optional defaults in the signature are resolved by this scope.
        prefix = self.launcher[:self.launcher.index('def generate_run(')]
        defaults = {
            'DEFAULT_MUTATION_FREQUENCY_MULTIPLIER': 1.0,
            'DEFAULT_BLESSING_FREQUENCY_MULTIPLIER': 1.0,
            'DEFAULT_VICTORY_CREDIT_REWARD_MULTIPLIER': 1.0,
            'DEFAULT_ITEM_CREDIT_REWARD': 60,
            'DEFAULT_GAME_SPEED': 'default',
            'DEFAULT_CAMPAIGN_LENGTH': 12,
            'DEFAULT_EXTRA_SHOP_SLOTS': 0,
            'DEFAULT_START_WITH_SPEAR': False,
            'DEFAULT_START_WITH_KERRIGAN': False,
            'DEFAULT_RACES': ('terran', 'zerg', 'protoss'),
        }
        scope.update(defaults)
        exec(compile(early, '<generate_run_mode_guard>', 'exec'), scope)
        with self.assertRaisesRegex(ValueError, 'Endless Mode is no longer available'):
            scope['generate_run'](600, 'brutal', game_mode='endless')
        self.assertIsNone(scope['generate_run'](600, 'brutal', game_mode='adventure'))

    def _install_fake(self):
        data = {
            3: {'mission_name': 'Lab Rat', 'layer': 0, 'lane': 0, 'lane_count': 2, '_endless_floor': True},
            5: {'mission_name': 'The Outlaws', 'layer': 0, 'lane': 1, 'lane_count': 2, '_endless_floor': True},
        }
        class TestManager(FakeManager):
            _slay_endless_ui = False

        mgr = TestManager(data)
        sc2 = types.ModuleType('worlds.sc2')
        sc2.slay_the_starcraft = types.SimpleNamespace(
            endless_mode=lambda ctx: ctx.endless,
            state_ready=lambda ctx: True,
            nodes=lambda ctx: ctx.data,
            node_status=lambda ctx, mid: ctx.data[mid].get('status', 'available'),
            mission_tooltip_section=lambda ctx, mid, _: ctx.data[mid]['mission_name'] + ' description',
        )
        worlds = types.ModuleType('worlds')
        worlds.sc2 = sc2
        command = types.ModuleType('slay_command_ui')
        command.resolve_route_positions = lambda *args: ('standard-route', args)

        def build_chart(manager):
            manager.redraws += 1
            manager.slay_chart = FakeChart({n['layer'] for n in manager.ctx.data.values()})
            manager.slay_chart_buttons = tuple(manager.mission_buttons)

        command.build_chart = build_chart
        command.label = lambda text, **kwargs: text
        kivy = types.ModuleType('kivy')
        metrics = types.ModuleType('kivy.metrics')
        metrics.dp = lambda x: x
        self._patch = patch.dict(sys.modules, {
            'worlds': worlds, 'worlds.sc2': sc2,
            'slay_command_ui': command, 'kivy': kivy, 'kivy.metrics': metrics,
        })
        self._patch.start()
        self.addCleanup(self._patch.stop)
        adapter = extract_function(ENDLESS_PATH, 'install')
        module = types.SimpleNamespace(SC2Manager=TestManager, MissionButton=FakeMissionButton)
        # Isolate the original method because this test suite installs the patch.
        TestManager.build_mission_table = lambda self, _dt: setattr(
            self, 'native_calls', self.native_calls + 1)
        adapter(module)
        return mgr, command

    def test_no_repeated_rebuild_for_stationary_cursor(self):
        manager, _ = self._install_fake()
        manager.build_mission_table(.5)
        buttons = manager.mission_buttons[:]
        buttons[0].visible_tooltip = True
        for _ in range(20):
            manager.build_mission_table(.5)
        self.assertEqual(manager.redraws, 1)
        self.assertIs(manager.mission_buttons[0], buttons[0])
        self.assertTrue(buttons[0].visible_tooltip)
        self.assertEqual(buttons[0].tooltip_removals, 0)

    def test_real_floor_change_discards_old_tooltips(self):
        manager, _ = self._install_fake()
        manager.build_mission_table(.5)
        old = manager.mission_buttons[:]
        old[0].visible_tooltip = True
        manager.ctx.data = {
            7: {'mission_name': 'All-In', 'layer': 1, 'lane': 0, 'lane_count': 1,
                '_endless_floor': True},
        }
        manager.build_mission_table(.5)
        self.assertEqual(manager.redraws, 2)
        self.assertEqual([b.text for b in manager.mission_buttons], ['All-In'])
        self.assertFalse(old[0].visible_tooltip)
        self.assertGreaterEqual(old[0].tooltip_removals, 1)
        self.assertEqual(len(manager.slay_chart.children), 1)
        self.assertEqual(manager.slay_chart.children[0], 'Floor 2')

    def test_new_run_with_identical_nodes_rebuilds(self):
        manager, _ = self._install_fake()
        manager.build_mission_table(.5)
        old = manager.mission_buttons[0]
        old.visible_tooltip = True
        manager.ctx.slay_config["run_id"] = "test-run-2"
        manager.build_mission_table(.5)
        self.assertEqual(manager.redraws, 2)
        self.assertFalse(old.visible_tooltip)

    def test_leaving_endless_clears_tooltip_and_restores_native_route(self):
        manager, command = self._install_fake()
        manager.build_mission_table(.5)
        old = manager.mission_buttons[:]
        old[0].visible_tooltip = True
        manager.ctx.endless = False
        manager.build_mission_table(.5)
        self.assertEqual(manager.native_calls, 1)
        self.assertFalse(old[0].visible_tooltip)
        self.assertIsNone(manager._slay_endless_chart_snapshot)
        self.assertEqual(command.resolve_route_positions({3: {'layer': 0}}, 800)[0], 'standard-route')

    def test_launch_clears_endless_tooltip(self):
        manager, _ = self._install_fake()
        manager.build_mission_table(.5)
        old = manager.mission_buttons[0]
        old.visible_tooltip = True
        manager.launching = True
        manager.build_mission_table(.5)
        self.assertFalse(old.visible_tooltip)
        self.assertEqual(manager.native_calls, 1)


if __name__ == '__main__':
    unittest.main()
