"""English SC2 campaign presentation layer for Slay the StarCraft v1.1.0.

Ported from Wangfeng's themed launcher while preserving the current launcher
controls and callbacks. This module only changes presentation/navigation.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import time
import traceback

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

ASSETS = Path(__file__).with_name("slay_assets")
BLUE = (0.28, 0.76, 1, 1)
_SOUNDS = {}
_LAST_SOUND = 0.0


def _theme_log(message: str) -> None:
    root = os.environ.get("SLAY_PORTABLE_ROOT", "").strip()
    if not root:
        return
    try:
        path = Path(root) / "Runtime" / "Logs" / "SlayTheme.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def preload_sounds(*_args) -> None:
    for kind, filename in {
        "click": "ui_pushbuttonselect.wav",
        "nav": "ui_navbuttonselect.wav",
        "command": "ui_commandcardbuttonselect.wav",
    }.items():
        if kind in _SOUNDS:
            continue
        try:
            source = ASSETS / "sounds" / filename
            sound = SoundLoader.load(str(source)) if source.is_file() else None
            if sound:
                sound.volume = 0.08
            _SOUNDS[kind] = sound
        except Exception:
            _SOUNDS[kind] = None


def play_button_sound(widget, *_args) -> None:
    global _LAST_SOUND
    now = time.monotonic()
    if now - _LAST_SOUND < 0.075:
        return
    _LAST_SOUND = now
    sound = _SOUNDS.get(getattr(widget, "slay_sound", "click"))
    if sound:
        sound.stop()
        sound.play()


def bind_button_sound(widget) -> None:
    if not getattr(widget, "_slay_sound_bound", False):
        widget.bind(on_release=play_button_sound)
        widget._slay_sound_bound = True


if not getattr(ButtonBehavior, "_slay_audio_installed", False):
    _button_init = ButtonBehavior.__init__

    def _init_with_sound(self, **kwargs):
        _button_init(self, **kwargs)
        bind_button_sound(self)

    ButtonBehavior.__init__ = _init_with_sound
    ButtonBehavior._slay_audio_installed = True
Clock.schedule_once(preload_sounds, 0)


def installation_root() -> Path:
    portable = Path(os.environ.get("SLAY_PORTABLE_ROOT", Path(__file__).parents[2]))
    config = portable / "Config" / "slay_install.json"
    try:
        cfg = json.loads(config.read_text(encoding="utf-8"))
        selected = Path(cfg.get("sc2_root", ""))
        if cfg.get("sc2_root_user_selected") and (selected / "Versions").is_dir():
            return selected
    except (OSError, ValueError):
        pass
    env_root = Path(os.environ.get("SC2PATH", r"C:\Program Files (x86)\StarCraft II"))
    return env_root


def select_installation(candidate, persist: bool = True):
    candidate = Path(candidate).expanduser().resolve()
    from worlds._sc2common.bot.paths import Paths, latest_executeble

    if not (candidate / "Versions").is_dir():
        raise ValueError("Select the StarCraft II installation folder that contains the Versions folder.")
    executable = latest_executeble(candidate / "Versions")
    if not executable.is_file():
        raise ValueError("Could not find the active SC2_x64.exe in that installation.")
    if persist:
        portable = Path(os.environ["SLAY_PORTABLE_ROOT"])
        config = portable / "Config" / "slay_install.json"
        try:
            cfg = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
        except (OSError, ValueError):
            cfg = {}
        backup = config.with_name("slay_install.before-directory-selection.json")
        if config.exists() and not backup.exists():
            shutil.copy2(config, backup)
        cfg.update(sc2_root=str(candidate), sc2_root_user_selected=True)
        config.parent.mkdir(parents=True, exist_ok=True)
        temp = config.with_suffix(".json.tmp")
        temp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        temp.replace(config)
    os.environ["SC2PATH"] = str(candidate)
    Paths.BASE, Paths.EXECUTABLE = candidate, executable
    Paths.CWD, Paths.MAPS, Paths.REPLAYS = candidate / "Support64", candidate / "Maps", candidate / "Replays"
    missing = []
    if not (candidate / "Mods" / "ArchipelagoPlayer.SC2Mod").exists():
        missing.append("Archipelago player mod")
    if not (candidate / "Maps" / "ArchipelagoCampaign").is_dir():
        missing.append("Archipelago campaign maps")
    return candidate, missing


def directory_picker(path_label) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
    path_input = TextInput(text=str(installation_root()), multiline=False, size_hint_y=None, height=dp(42))
    chooser = FileChooserListView(path=path_input.text, dirselect=True)
    chooser.bind(path=lambda _, value: setattr(path_input, "text", value))
    message = Label(
        text="Select the StarCraft II installation folder, or type its path above.",
        size_hint_y=None,
        height=dp(60),
        halign="left",
    )
    message.bind(size=lambda w, v: setattr(w, "text_size", v))
    controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
    browse, accept, cancel = Button(text="Go to Path"), Button(text="Use This Folder"), Button(text="Cancel")
    for b in (browse, accept, cancel):
        button(b)
        controls.add_widget(b)
    for w in (path_input, chooser, message, controls):
        content.add_widget(w)
    popup = Popup(title="Select StarCraft II Installation", content=content, size_hint=(0.85, 0.85))

    def navigate(*_args):
        if Path(path_input.text).is_dir():
            chooser.path = path_input.text
        else:
            message.text = "That directory does not exist. Check the path and try again."

    def accept_path(*_args):
        try:
            path, missing = select_installation(path_input.text)
            suffix = "  ·  Missing: " + ", ".join(missing) if missing else "  ·  Maps and mods found"
            path_label.text = f"Game Directory: {path}{suffix}"
            popup.dismiss()
        except (OSError, ValueError) as exc:
            message.text = str(exc)

    browse.bind(on_release=navigate)
    accept.bind(on_release=accept_path)
    cancel.bind(on_release=lambda *_: popup.dismiss())
    popup.open()


def panel(widget, image=None, color=(0.025, 0.055, 0.10, 0.98), border=True):
    source = ASSETS / image if image else None
    with widget.canvas.before:
        Color(*color)
        bg = Rectangle(source=str(source) if source and source.is_file() else "", pos=widget.pos, size=widget.size)
        Color(0.15, 0.38, 0.53, 0.8)
        edge = Line(rectangle=(*widget.pos, *widget.size), width=1) if border else None

    def resize(*_args):
        bg.pos, bg.size = widget.pos, widget.size
        if image and bg.texture and widget.width > 0 and widget.height > 0:
            tw, th = bg.texture.size
            source_ratio, view_ratio = tw / th, widget.width / widget.height
            x, y = (source_ratio / view_ratio, 1) if source_ratio > view_ratio else (1, view_ratio / source_ratio)
            crop_x, crop_y = 1 / x, 1 / y
            left, bottom = (1 - crop_x) / 2, (1 - crop_y) / 2
            bg.tex_coords = (
                left, 1 - bottom,
                left + crop_x, 1 - bottom,
                left + crop_x, 1 - bottom - crop_y,
                left, 1 - bottom - crop_y,
            )
        if edge:
            edge.rectangle = (*widget.pos, *widget.size)

    widget.bind(pos=resize, size=resize)
    resize()


def button(widget):
    bind_button_sound(widget)
    up = ASSETS / "sc2_ui_glues_bluebuttons_taskbarbuttonup.png"
    down = ASSETS / "sc2_ui_glues_bluebuttons_taskbarbuttondown.png"
    widget.background_normal = str(up) if up.is_file() else ""
    widget.background_down = str(down) if down.is_file() else ""
    widget.background_color = (1, 1, 1, 1) if up.is_file() else (0.025, 0.12, 0.20, 1)
    widget.color = (0.88, 0.96, 1, 1)
    widget.font_size = dp(15)


def _style_setup(manager, container) -> None:
    for widget in container.walk():
        if isinstance(widget, ButtonBehavior):
            bind_button_sound(widget)
    try:
        manager.theme_cls.theme_style = "Dark"
    except Exception:
        pass
    panel(container, color=(0.012, 0.025, 0.045, 1), border=False)

    root = manager.slay_setup_tab.content
    children = list(reversed(root.children))
    if len(children) == 7:
        title, instructions, form, race_row, status, actions, spacer = children
    elif len(children) == 6:
        title, instructions, form, status, actions, spacer = children
        race_row = None
    else:
        _theme_log(f"Setup theme skipped: expected 6 or 7 root widgets, found {len(children)}")
        return

    root.clear_widgets()
    root.padding = [dp(24), dp(16)]
    root.spacing = dp(16)

    hero = BoxLayout(orientation="vertical", padding=[dp(30), dp(16)], size_hint_y=None, height=dp(118))
    panel(hero, "ui_screen_mainmenurebrandlow.png", color=(0.62, 0.73, 0.88, 1))
    title.text = "[b]SLAY THE STARCRAFT[/b]  [size=16]v1.1.0[/size]"
    title.halign = "left"
    title.bind(size=lambda w, v: setattr(w, "text_size", v))
    hero.add_widget(title)
    root.add_widget(hero)

    installation = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
    path_label = Label(
        text=f"Game Directory: {installation_root()}",
        halign="left",
        font_size=dp(13),
        shorten=True,
        shorten_from="left",
    )
    path_label.bind(size=lambda w, v: setattr(w, "text_size", v))
    choose = Button(text="Select StarCraft II Folder", size_hint_x=None, width=dp(230))
    button(choose)
    choose.bind(on_release=lambda *_: directory_picker(path_label))
    installation.add_widget(path_label)
    installation.add_widget(choose)
    root.add_widget(installation)

    body = BoxLayout(spacing=dp(18))
    settings = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12), size_hint_x=0.68)
    panel(settings)
    settings.add_widget(
        Label(
            text="[b]ADVENTURE CONFIGURATION[/b]",
            markup=True,
            color=BLUE,
            font_size=dp(21),
            size_hint_y=None,
            height=dp(32),
            halign="left",
        )
    )

    # Keep the current v1.1.0 launcher controls and callbacks. We only restyle
    # and reposition them, including the new playable-race row.
    form.spacing = [dp(18), dp(12)]
    form.height = dp(350)
    form.size_hint_y = None
    settings_scroll = ScrollView(do_scroll_x=False)
    settings_scroll.add_widget(form)
    settings.add_widget(settings_scroll)

    if race_row is not None:
        race_row.size_hint_y = None
        race_row.height = dp(42)
        settings.add_widget(race_row)

    status.size_hint_y = None
    status.height = dp(42)
    settings.add_widget(status)
    settings.add_widget(actions)
    body.add_widget(settings)

    guide = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(14), size_hint_x=0.32)
    panel(guide, color=(0.035, 0.075, 0.115, 1))
    credits_button = Button(text="Acknowledgements", size_hint_y=None, height=dp(40))
    button(credits_button)

    def show_contributors(*_args):
        entries = (
            ("Lammy", "Original author · Mod design, development, balance and bug fixes."),
            ("Wangfeng", "Chinese localization and the StarCraft-style launcher, route, shop and inventory presentation."),
            ("SC2 Archipelago Team", "Provided the base campaign randomizer, race-swapped missions, units and upgrades."),
        )
        popup_body = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(14))
        panel(popup_body)
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(20), padding=dp(12))
        content.bind(minimum_height=content.setter("height"))
        for name, description_text in entries:
            heading = Label(text=name, color=BLUE, font_size=dp(20), size_hint_y=None, height=dp(34), halign="left")
            heading.bind(size=lambda widget, value: setattr(widget, "text_size", value))
            content.add_widget(heading)
            description = Label(text=description_text, size_hint_y=None, halign="left", valign="top", font_size=dp(16))
            description.bind(width=lambda widget, value: setattr(widget, "text_size", (value, None)))
            description.bind(texture_size=lambda widget, value: setattr(widget, "height", value[1] + dp(8)))
            content.add_widget(description)
        scroll.add_widget(content)
        popup_body.add_widget(scroll)
        close = Button(text="Close", size_hint_y=None, height=dp(42))
        button(close)
        popup_body.add_widget(close)
        popup = Popup(title="Acknowledgements", content=popup_body, size_hint=(0.78, 0.78))
        close.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    credits_button.bind(on_release=show_contributors)
    guide.add_widget(credits_button)
    guide.add_widget(
        Label(
            text="[b]DIFFICULTY DESCRIPTION[/b]",
            markup=True,
            color=BLUE,
            font_size=dp(21),
            size_hint_y=None,
            height=dp(32),
        )
    )
    brief = instructions.children[0] if getattr(instructions, "children", None) else instructions
    if brief.parent is instructions:
        instructions.remove_widget(brief)
    brief.font_size = dp(15)
    brief.size_hint_y = None
    brief.bind(texture_size=lambda w, v: setattr(w, "height", v[1] + dp(16)))
    brief.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    guide_scroll = ScrollView(do_scroll_x=False)
    guide_scroll.add_widget(brief)
    guide.add_widget(guide_scroll)
    body.add_widget(guide)
    root.add_widget(body)

    for w in root.walk():
        if isinstance(w, Button):
            button(w)
        elif isinstance(w, TextInput):
            w.background_color = (0.04, 0.09, 0.15, 1)
            w.foreground_color = (0.86, 0.94, 1, 1)
            w.cursor_color = BLUE
            w.padding = [dp(12), dp(10)]
        elif isinstance(w, Label):
            w.color = (0.84, 0.92, 0.98, 1)


def _install_navigation(manager) -> None:
    # Preserve the original tab/screen objects because connection and launcher
    # logic still reference them; only hide the stock tab strip and add themed
    # navigation buttons.
    parent = manager.tabs.parent
    manager.tabs.height = 0
    manager.tabs.opacity = 0
    manager.tabs.disabled = True
    if getattr(manager, "slay_theme_nav", None) is not None:
        return
    nav = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8), padding=[dp(24), dp(6)])
    panel(nav, color=(0.025, 0.065, 0.105, 1), border=False)
    # Keep the underlying Archipelago tab text unchanged. MDScreenManagerBase
    # uses tab.text as the screen key, so renaming the actual tab objects breaks
    # both manual navigation and the launcher's automatic post-generation switch.
    # The custom themed buttons below provide the user-facing names/order instead.
    log_tab = next((t for t in manager.tabs.children if getattr(t, "text", "") == "Archipelago"), None)
    tabs = []
    if log_tab:
        tabs.append((log_tab, "Console Log"))
    tabs.extend(((manager.slay_mission_tab, "Missions"), (manager.slay_setup_tab, "Settings")))
    for tab, caption in tabs:
        b = Button(text=caption)
        b.slay_sound = "nav"
        button(b)
        b.bind(on_release=lambda _, target=tab: manager.screens.switch_screens(target))
        nav.add_widget(b)
    parent.add_widget(nav, index=len(parent.children))
    manager.slay_theme_nav = nav


def decorate(manager, container) -> None:
    _style_setup(manager, container)
    _install_navigation(manager)
    campaign = manager.slay_mission_tab.content
    panel(campaign, "ui_screens_zeratul_prologue_starfield_generic_diff.png", color=(0.45, 0.6, 0.75, 1), border=False)
    _theme_log("English v1.1.0 SC2 theme installed")


def install(module) -> None:
    cls = module.SC2Manager
    if getattr(cls, "_slay_theme_installed", False):
        return
    original = cls.build

    def build(manager):
        container = original(manager)
        try:
            decorate(manager, container)
        except Exception:
            _theme_log("Theme decoration failed:\n" + traceback.format_exc())
        return container

    cls.build = build
    cls._slay_theme_installed = True

    # The command UI expects the themed mission screen to exist first, matching
    # the lifecycle used by Wangfeng's working themed package.
    import slay_command_ui
    slay_command_ui.install(module)
