"""Offline regression for Slay's themed tab buttons (requires no Kivy or AP)."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
theme = ast.parse((ROOT / 'Payload/slay_theme.py').read_text(encoding='utf-8'))
function = next(node for node in theme.body if isinstance(node, ast.FunctionDef) and node.name == '_install_navigation')

class FakeWidget:
    def __init__(self, **kwargs):
        self.children=[]
        self.kwargs=kwargs
    def add_widget(self, widget, index=0):
        self.children.insert(index, widget)

class FakeButton(FakeWidget):
    def __init__(self, text):
        super().__init__()
        self.text=text
    def bind(self, **callbacks):
        self.callback=callbacks['on_release']
    def click(self):
        self.callback(self)

class FakeScreens:
    """Match Archipelago kvui.MDScreenManagerBase.switch_screens lookup."""
    def __init__(self):
        self.local_screen_names=['Archipelago','Starcraft 2 Launcher','Slay Setup']
        self.current_screen=SimpleNamespace(name='Archipelago')
        self.current_tab=SimpleNamespace(text='Archipelago')
        self.transition=SimpleNamespace(direction=None)
    def switch_screens(self, tab):
        name=tab.text
        if self.local_screen_names.index(name) > self.local_screen_names.index(self.current_screen.name):
            self.transition.direction='left'
        else:
            self.transition.direction='right'
        self.current_screen.name=name
        self.current_tab=tab

namespace={'BoxLayout':FakeWidget,'Button':FakeButton,'dp':lambda v:v,'panel':lambda *a, **kw:None,'button':lambda b:None}
exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(ROOT/'Payload/slay_theme.py'),'exec'),namespace)

class ThemeNavigationTests(unittest.TestCase):
    def test_visible_names_do_not_replace_original_screen_keys(self):
        log=SimpleNamespace(text='Archipelago')
        mission=SimpleNamespace(text='Starcraft 2 Launcher')
        setup=SimpleNamespace(text='Slay Setup')
        holder=FakeWidget()
        manager=SimpleNamespace(tabs=SimpleNamespace(parent=holder,children=[setup,mission,log],height=40,opacity=1,disabled=False),
                                screens=FakeScreens(),slay_mission_tab=mission,slay_setup_tab=setup,slay_theme_nav=None)
        namespace['_install_navigation'](manager)
        nav=manager.slay_theme_nav
        self.assertEqual([b.text for b in reversed(nav.children)],['Console Log','Missions','Settings'])
        self.assertEqual([log.text,mission.text,setup.text],manager.screens.local_screen_names)
        for button, original in zip(reversed(nav.children),manager.screens.local_screen_names):
            with self.subTest(button=button.text):
                button.click()
                self.assertEqual(manager.screens.current_screen.name,original)
        # Both launcher-generated and manually-loaded runs use the underlying mission tab.
        manager.screens.switch_screens(mission)
        self.assertEqual(manager.screens.current_screen.name,'Starcraft 2 Launcher')
        namespace['_install_navigation'](manager)
        self.assertIs(manager.slay_theme_nav,nav)
        self.assertEqual(len(holder.children),1)

    def test_mission_race_label_is_only_race(self):
        source=(ROOT/'Payload/slay_command_ui.py').read_text(encoding='utf-8')
        self.assertIn("race_label=Label(text=tr(race),",source)
        self.assertNotIn("race_label=label('Playing as '+race,",source)

if __name__=='__main__':
    unittest.main()
