"""Regression checks for r18 theme setup-widget ordering and r19 card opacity.

These run without Kivy by executing the real themed setup function against a
small widget-hierarchy model that preserves Kivy's reverse children ordering.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'Payload'
THEME_SOURCE = (ROOT / 'slay_theme.py').read_text(encoding='utf-8')
CHART_SOURCE = (ROOT / 'slay_command_ui.py').read_text(encoding='utf-8')


class Widget:
    def __init__(self, **kwargs):
        self.children = []
        self.parent = None
        self.width = 700
        self.height = 450
        self.pos = (0, 0)
        self.size = (700, 450)
        self.text = ''
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_widget(self, widget, **kwargs):
        if widget.parent is not None:
            widget.parent.remove_widget(widget)
        self.children.insert(0, widget)
        widget.parent = self

    def remove_widget(self, widget):
        self.children.remove(widget)
        widget.parent = None

    def clear_widgets(self):
        for widget in self.children:
            widget.parent = None
        self.children.clear()

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def bind(self, **kwargs):
        pass


class BoxLayout(Widget):
    pass


class GridLayout(Widget):
    pass


class Label(Widget):
    pass


class ButtonBehavior:
    pass


class Button(Widget, ButtonBehavior):
    pass


class TextInput(Widget):
    pass


class ScrollView(Widget):
    pass


class Popup(Widget):
    pass


def style_setup():
    tree = ast.parse(THEME_SOURCE)
    method = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_style_setup')
    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    scope = dict(BoxLayout=BoxLayout, GridLayout=GridLayout, Label=Label,
                 Button=Button, ButtonBehavior=ButtonBehavior, TextInput=TextInput,
                 ScrollView=ScrollView, Popup=Popup, dp=lambda n: n,
                 panel=lambda *args, **kwargs: None,
                 button=lambda *args, **kwargs: None,
                 bind_button_sound=lambda *args, **kwargs: None,
                 installation_root=lambda: Path('C:/StarCraft II'),
                 directory_picker=lambda *args: None,
                 BLUE=(.28, .76, 1, 1), _theme_log=lambda *args: None)
    exec(compile(module, str(ROOT / 'slay_theme.py'), 'exec'), scope)
    return scope['_style_setup']


def make_setup(order):
    title = Label(text='Title')
    instructions = BoxLayout()
    instructions.add_widget(Label(text='The difficulty description'))
    form = GridLayout(cols=4)
    form.add_widget(Button(text='Brutal'))
    race_row = BoxLayout()
    race_row.add_widget(Button(text='Terran'))
    race_row.add_widget(Button(text='Zerg'))
    race_row.add_widget(Button(text='Protoss'))
    status = Label(text='Ready')
    actions = BoxLayout()
    actions.add_widget(Button(text='Generate Run'))
    spacer = Label(text='')
    by_name = dict(title=title, instructions=instructions, form=form,
                   race_row=race_row, status=status, actions=actions, spacer=spacer)
    root = BoxLayout()
    for key in order:
        root.add_widget(by_name[key])
    manager = SimpleNamespace(slay_setup_tab=SimpleNamespace(content=root),
                              theme_cls=SimpleNamespace(theme_style='Light'))
    return manager, root, by_name


class SetupAndOpacityTests(unittest.TestCase):
    def test_launcher_options_survive_race_row_above_or_below_form(self):
        for arrangement in (
            ('title', 'instructions', 'race_row', 'form', 'status', 'actions', 'spacer'),
            ('title', 'instructions', 'form', 'race_row', 'status', 'actions', 'spacer'),
            ('title', 'instructions', 'form', 'status', 'actions', 'spacer'),
        ):
            with self.subTest(arrangement=arrangement):
                manager, root, widgets = make_setup(arrangement)
                style_setup()(manager, Widget())
                self.assertEqual(len(root.children), 3)  # hero, folder, main settings/guide
                grid = widgets['form']
                race = widgets['race_row']
                self.assertIsInstance(grid.parent, ScrollView)
                settings = grid.parent.parent
                self.assertIsInstance(settings, BoxLayout)
                self.assertIs(widgets['status'].parent, settings)
                self.assertIs(widgets['actions'].parent, settings)
                self.assertEqual(grid.cols, 4)
                self.assertEqual(len(grid.children), 1)  # existing option preserved
                if 'race_row' in arrangement:
                    self.assertIs(race.parent, settings)
                    # Kivy stores children reversed; race row placed above the scroll area.
                    self.assertGreater(settings.children.index(race),
                                       settings.children.index(grid.parent))
                else:
                    self.assertIsNone(race.parent)

    def test_race_tinted_card_backgrounds_are_fifty_percent_opacity(self):
        tree = ast.parse(CHART_SOURCE)
        values = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'race_fills' for t in node.targets):
                values = ast.literal_eval(node.value)
        self.assertEqual(set(values), {'Terran', 'Zerg', 'Protoss'})
        for race, fill in values.items():
            with self.subTest(race=race):
                self.assertEqual(fill[3], .5)
        self.assertIn('fill=race_fills.get(race,(.10,.12,.14,.50))', CHART_SOURCE)


if __name__ == '__main__':
    unittest.main()
