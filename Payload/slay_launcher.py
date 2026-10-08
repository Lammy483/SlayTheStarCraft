

















from __future__ import annotations



import datetime as _dt

import json

import logging
import math

import os

import shutil

import socket

import subprocess

import sys

import threading

import time

from pathlib import Path

from typing import Any



PACKAGE_VERSION = "1.0.2.17"

LAUNCHER_ENV = "SLAY_LAUNCHER_MODE"

RUN_DIR_ENV = "SLAY_RUN_DIR"

PORTABLE_ROOT_ENV = "SLAY_PORTABLE_ROOT"

RUNS_DIR_NAME = "Runs"

DEFAULT_STARTING_CREDITS = 700

DEFAULT_DIFFICULTY = "brutal"

DIFFICULTIES = ("brutal", "hard", "medium", "easy")

DEFAULT_GAME_SPEED = "default"

GAME_SPEEDS = ("default", "slower", "slow", "normal", "fast", "faster")

DEFAULT_MUTATION_FREQUENCY_MULTIPLIER = 1.0
DEFAULT_BLESSING_FREQUENCY_MULTIPLIER = 1.0
DEFAULT_CAMPAIGN_LENGTH = 12
MIN_CAMPAIGN_LENGTH = 2
MAX_CAMPAIGN_LENGTH = 31
DEFAULT_EXTRA_SHOP_SLOTS = 0
DEFAULT_START_WITH_SPEAR = False
DEFAULT_START_WITH_KERRIGAN = False
DEFAULT_RACES = ("terran", "zerg", "protoss")


def normalize_races(races: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Validate before invoking the generator; keep its canonical race order."""
    if not races or any(race not in DEFAULT_RACES for race in races):
        raise ValueError("Select at least one of Terran, Zerg, or Protoss.")
    return tuple(race for race in DEFAULT_RACES if race in races)

DEFAULT_VICTORY_CREDIT_REWARD_MULTIPLIER = 1.00

DEFAULT_ITEM_CREDIT_REWARD = 50

DEFAULT_PLAYER_NAME = "Player"

SERVER_START_TIMEOUT_SECONDS = 20.0



logger = logging.getLogger("Client")

_server_logger = logging.getLogger("Client")





def launcher_mode() -> bool:

    return os.environ.get(LAUNCHER_ENV, "").strip().lower() in {"1", "true", "yes", "on"}





def archipelago_root() -> Path:



    return Path(__file__).resolve().parents[2]





def portable_root() -> Path:

    raw = os.environ.get(PORTABLE_ROOT_ENV, "").strip()

    if raw:

        return Path(raw).expanduser().resolve()



    return (archipelago_root() / "SlayTheStarCraftPortable").resolve()





def runs_root() -> Path:

    root = portable_root() / RUNS_DIR_NAME

    root.mkdir(parents=True, exist_ok=True)

    return root





def _safe_int(value: Any, default: int = 0) -> int:

    try:

        return int(value)

    except (TypeError, ValueError):

        return default





def load_manifest(run_dir: Path) -> dict[str, Any]:

    path = run_dir / "manifest.json"

    if not path.is_file():

        return {}

    try:

        data = json.loads(path.read_text(encoding="utf-8"))

    except Exception:

        return {}

    return dict(data) if isinstance(data, dict) else {}





def list_runs() -> list[tuple[Path, dict[str, Any]]]:

    found: list[tuple[Path, dict[str, Any]]] = []

    root = runs_root()

    for child in root.iterdir():

        if not child.is_dir():

            continue

        if not (child / "run.json").is_file() or not (child / "seed.zip").is_file():

            continue

        manifest = load_manifest(child)

        if not manifest:

            try:

                run_data = json.loads((child / "run.json").read_text(encoding="utf-8"))

            except Exception:

                run_data = {}

            manifest = {

                "run_id": str(run_data.get("run_id", child.name)),

                "run_seed": _safe_int(run_data.get("run_seed", 0)),

                "difficulty": str(run_data.get("difficulty", "unknown")),

                "starting_credits": _safe_int(run_data.get("starting_credits", 0)),

                "player_name": str(run_data.get("player_name", DEFAULT_PLAYER_NAME)),

                "created_utc": "",

            }

        found.append((child, manifest))

    found.sort(

        key=lambda item: (

            str(item[1].get("last_played_utc", "")),

            str(item[1].get("created_utc", "")),

            item[0].name,

        ),

        reverse=True,

    )

    return found





def _port_available(port: int) -> bool:

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("127.0.0.1", port))

        return True

    except OSError:

        return False

    finally:

        sock.close()





def choose_local_port() -> int:





    if _port_available(38281):

        return 38281

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:

        sock.bind(("127.0.0.1", 0))

        return int(sock.getsockname()[1])

    finally:

        sock.close()





def _hidden_process_kwargs() -> dict[str, Any]:

    kwargs: dict[str, Any] = {}

    if os.name == "nt":

        kwargs["creationflags"] = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))

    return kwargs





def _run_streamed(command: list[str], cwd: Path, prefix: str) -> None:

    _server_logger.info("%s %s", prefix, " ".join(command))

    proc = subprocess.Popen(

        command,

        cwd=str(cwd),

        stdout=subprocess.PIPE,

        stderr=subprocess.STDOUT,

        text=True,

        encoding="utf-8",

        errors="replace",

        bufsize=1,

        **_hidden_process_kwargs(),

    )

    assert proc.stdout is not None

    for raw in proc.stdout:

        line = raw.rstrip()

        if line:

            _server_logger.info("%s %s", prefix, line)

    code = proc.wait()

    if code != 0:

        raise RuntimeError(f"{' '.join(command[:2])} exited with code {code}")





def _single_generated_zip(output_dir: Path) -> Path:

    zips = sorted(output_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime_ns, reverse=True)

    if len(zips) != 1:

        names = ", ".join(path.name for path in zips) or "none"

        raise RuntimeError(f"Expected exactly one generated Archipelago seed ZIP; found: {names}")

    return zips[0]





def generate_run(

    starting_credits: int, difficulty: str, *, seed: int | None = None,

    mutation_frequency: float = DEFAULT_MUTATION_FREQUENCY_MULTIPLIER,

    blessing_frequency: float = DEFAULT_BLESSING_FREQUENCY_MULTIPLIER,

    victory_credit_reward_multiplier: float = DEFAULT_VICTORY_CREDIT_REWARD_MULTIPLIER,

    item_credit_reward: int = DEFAULT_ITEM_CREDIT_REWARD,

    game_speed: str = DEFAULT_GAME_SPEED, campaign_length: int = DEFAULT_CAMPAIGN_LENGTH,
    extra_shop_slots: int = DEFAULT_EXTRA_SHOP_SLOTS,
    start_with_spear: bool = DEFAULT_START_WITH_SPEAR,
    start_with_kerrigan: bool = DEFAULT_START_WITH_KERRIGAN,
    selected_races: tuple[str, ...] = DEFAULT_RACES,

) -> tuple[Path, dict[str, Any]]:

    selected_races = normalize_races(selected_races)

    if difficulty not in DIFFICULTIES:

        raise ValueError(f"Unsupported difficulty: {difficulty}")

    if game_speed not in GAME_SPEEDS:

        raise ValueError(f"Unsupported game speed: {game_speed}")

    if not math.isfinite(float(mutation_frequency)) or float(mutation_frequency) < 0:
        raise ValueError("Mutation Frequency Multiplier must be a finite non-negative number.")
    if not math.isfinite(float(blessing_frequency)) or float(blessing_frequency) < 0:
        raise ValueError("Blessing Frequency Multiplier must be a finite non-negative number.")
    if not MIN_CAMPAIGN_LENGTH <= int(campaign_length) <= MAX_CAMPAIGN_LENGTH:
        raise ValueError(f"Campaign Length must be between {MIN_CAMPAIGN_LENGTH} and {MAX_CAMPAIGN_LENGTH}.")
    if int(extra_shop_slots) not in {0, 1, 2, 3}:
        raise ValueError("Extra Shop Slots must be 0, 1, 2, or 3.")

    if starting_credits < 0:

        raise ValueError("Starting credits cannot be negative.")

    if victory_credit_reward_multiplier < 0:

        raise ValueError("Victory Credit Reward Multiplier cannot be negative.")

    if item_credit_reward < 0:

        raise ValueError("Item Credit Reward cannot be negative.")



    ap_root = archipelago_root()

    generator = ap_root / "SlayTheStarCraft.py"

    generate_py = ap_root / "Generate.py"

    if not generator.is_file() or not generate_py.is_file():

        raise RuntimeError(f"Slay/Archipelago generator files are missing from {ap_root}")









    command = [

        sys.executable,

        str(generator),

        "--archipelago", str(ap_root),

        "--name", DEFAULT_PLAYER_NAME,

        "--difficulty", difficulty,

        "--game-speed", game_speed,

        "--starting-credits", str(starting_credits),

        "--layers", str(int(campaign_length) - 1),

        "--mutation-frequency-multiplier", str(float(mutation_frequency)),

        "--blessing-frequency-multiplier", str(float(blessing_frequency)),

        "--victory-credit-reward-multiplier", str(victory_credit_reward_multiplier),

        "--item-credit-reward", str(item_credit_reward),
        "--extra-shop-slots", str(int(extra_shop_slots)),

    ]
    command.extend(["--races", *selected_races])
    if start_with_spear:
        command.append("--start-with-spear")
    if start_with_kerrigan:
        command.append("--start-with-kerrigan")

    if seed is not None:

        command.extend(["--seed", str(seed)])

    _run_streamed(command, ap_root, "[Generator]")



    transient_run = ap_root / "slay_the_starcraft_run.json"

    player_yaml = ap_root / "SlayTheStarCraftPlayers" / "SlayTheStarCraft.yaml"

    if not transient_run.is_file() or not player_yaml.is_file():

        raise RuntimeError("Generator completed but did not create the expected Slay run/YAML files.")

    run_data = json.loads(transient_run.read_text(encoding="utf-8"))

    run_id = str(run_data.get("run_id", "")).strip()

    if not run_id:

        raise RuntimeError("Generated run has no run_id.")



    run_dir = runs_root() / run_id

    if run_dir.exists():





        raise RuntimeError(

            f"Run {run_id} already exists. Load that run instead of overwriting it."

        )

    run_dir.mkdir(parents=True)

    generated_dir = run_dir / "_generated"

    generated_dir.mkdir()



    try:

        shutil.copy2(transient_run, run_dir / "run.json")

        shutil.copy2(player_yaml, run_dir / "player.yaml")



        ap_command = [

            sys.executable,

            str(generate_py),

            "--player_files_path", str(player_yaml.parent),

            "--multi", "1",

            "--seed", str(int(run_data["run_seed"])),

            "--outputpath", str(generated_dir),

        ]

        _run_streamed(ap_command, ap_root, "[Archipelago Generator]")

        generated_zip = _single_generated_zip(generated_dir)

        shutil.move(str(generated_zip), str(run_dir / "seed.zip"))







        for extra in generated_dir.iterdir():

            if extra.is_file():

                shutil.move(str(extra), str(run_dir / extra.name))

        generated_dir.rmdir()



        now = _dt.datetime.now(_dt.timezone.utc).isoformat()

        manifest = {

            "format_version": 1,

            "slay_version": PACKAGE_VERSION,

            "run_id": run_id,

            "run_seed": int(run_data.get("run_seed", 0)),

            "player_name": str(run_data.get("player_name", DEFAULT_PLAYER_NAME)),

            "difficulty": str(run_data.get("difficulty", difficulty)),

            "game_speed": str(run_data.get("game_speed", game_speed)),

            "starting_credits": int(run_data.get("starting_credits", starting_credits)),

            "current_credits": int(run_data.get("starting_credits", starting_credits)),

            "mutation_frequency": float(run_data.get("mutation_frequency", mutation_frequency)),

            "blessing_frequency": float(run_data.get("blessing_frequency", blessing_frequency)),
            "campaign_length": int(run_data.get("campaign_length", campaign_length)),
            "extra_shop_slots": int(run_data.get("extra_shop_slots", extra_shop_slots)),
            "start_with_spear": bool(run_data.get("start_with_spear", start_with_spear)),
            "start_with_kerrigan": bool(run_data.get("start_with_kerrigan", start_with_kerrigan)),
            "races": list(run_data.get("races", selected_races)),

            "victory_credit_reward_multiplier": float(run_data.get("victory_credit_reward_multiplier", victory_credit_reward_multiplier)),

            "item_credit_reward": int(run_data.get("item_credit_reward", item_credit_reward)),

            "created_utc": now,

            "last_played_utc": "",

        }

        (run_dir / "manifest.json").write_text(

            json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"

        )

        return run_dir, manifest

    except Exception:

        shutil.rmtree(run_dir, ignore_errors=True)

        raise





def _touch_last_played(run_dir: Path) -> dict[str, Any]:

    manifest = load_manifest(run_dir)

    manifest["last_played_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()

    (run_dir / "manifest.json").write_text(

        json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"

    )

    return manifest





class ServerProcess:

    def __init__(self) -> None:

        self.process: subprocess.Popen[str] | None = None

        self.port: int | None = None

        self.run_dir: Path | None = None



    def stop(self) -> None:

        proc = self.process

        self.process = None

        self.port = None

        self.run_dir = None

        if proc is None or proc.poll() is not None:

            return







        try:

            if proc.stdin is not None:

                proc.stdin.write("/save\n/exit\n")

                proc.stdin.flush()

            proc.wait(timeout=6)

            return

        except Exception:

            pass

        try:

            proc.terminate()

            proc.wait(timeout=3)

        except Exception:

            try:

                proc.kill()

            except Exception:

                pass



    def _pump(self, pipe: Any) -> None:

        try:

            for raw in iter(pipe.readline, ""):

                line = raw.rstrip()

                if line:

                    _server_logger.info("[Server] %s", line)

        finally:

            try:

                pipe.close()

            except Exception:

                pass



    def start(self, run_dir: Path) -> int:

        self.stop()

        seed = run_dir / "seed.zip"

        if not seed.is_file():

            raise RuntimeError(f"Missing seed.zip in {run_dir}")

        ap_root = archipelago_root()

        port = choose_local_port()

        savefile = run_dir / "server.apsave"

        command = [

            sys.executable,

            str(ap_root / "MultiServer.py"),

            str(seed),

            "--host", "127.0.0.1",

            "--port", str(port),

            "--savefile", str(savefile),

        ]

        _server_logger.info("[Server] Starting private Slay server on 127.0.0.1:%d", port)

        proc = subprocess.Popen(

            command,

            cwd=str(ap_root),

            stdin=subprocess.PIPE,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            text=True,

            encoding="utf-8",

            errors="replace",

            bufsize=1,

            **_hidden_process_kwargs(),

        )

        self.process = proc

        self.port = port

        self.run_dir = run_dir

        if proc.stdout is not None:

            threading.Thread(target=self._pump, args=(proc.stdout,), daemon=True).start()



        deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS

        while time.monotonic() < deadline:

            if proc.poll() is not None:

                raise RuntimeError(f"Archipelago server exited with code {proc.returncode} while starting.")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.settimeout(0.2)

            try:

                if sock.connect_ex(("127.0.0.1", port)) == 0:

                    return port

            finally:

                sock.close()

            time.sleep(0.10)

        self.stop()

        raise RuntimeError("Archipelago server did not become ready.")





def _display_run_name(run_dir: Path, manifest: dict[str, Any]) -> str:

    created_raw = str(manifest.get("created_utc", "")).strip()

    created = created_raw[:10] or "Unknown date"

    if created_raw:

        try:





            parsed = _dt.datetime.fromisoformat(created_raw.replace("Z", "+00:00"))

            if parsed.tzinfo is not None:

                parsed = parsed.astimezone()

            created = parsed.date().isoformat()

        except (TypeError, ValueError):

            pass

    credits = _safe_int(manifest.get("current_credits", manifest.get("starting_credits", 0)))

    seed = _safe_int(manifest.get("run_seed", 0))

    return f"{created}  |  {credits} credits  |  seed {seed}  |  {run_dir.name}"





def install_launcher_tab(manager: Any) -> None:



    if not launcher_mode():

        return





    from kivy.clock import Clock

    from kivy.core.window import Window

    from kivy.metrics import dp

    from kivy.uix.boxlayout import BoxLayout

    from kivy.uix.button import Button
    from kivy.uix.checkbox import CheckBox

    from kivy.uix.spinner import Spinner, SpinnerOption

    from kivy.uix.gridlayout import GridLayout

    from kivy.uix.label import Label

    from kivy.uix.popup import Popup

    from kivy.uix.textinput import TextInput

    from kivy.graphics import Color, Line

    from Utils import async_start



    manager.title = "Slay the StarCraft"







    def _maximize_window(_dt: float = 0.0) -> None:

        try:

            maximize = getattr(Window, "maximize", None)

            if callable(maximize):

                maximize()

        except Exception:

            logger.debug("Could not maximize Slay window", exc_info=True)

    Clock.schedule_once(_maximize_window, 0.05)





    Clock.schedule_once(_maximize_window, 0.35)









    def _remove_hints_tab(_dt: float = 0.0) -> None:

        try:

            for tab in list(getattr(manager.tabs, "children", ())):

                if str(getattr(tab, "text", "")) == "Hints":

                    remove = getattr(manager, "remove_client_tab", None)

                    if callable(remove):

                        try:

                            remove(tab)

                            manager.log_panels.pop("Hints", None)

                            return

                        except Exception:

                            pass

                    try:

                        manager.tabs.remove_widget(tab)

                    except Exception:

                        pass

                    screen = None

                    for candidate in list(getattr(manager.screens, "children", ())):

                        if str(getattr(candidate, "name", "")) == "Hints":

                            screen = candidate

                            break

                    if screen is not None:

                        try:

                            manager.screens.remove_widget(screen)

                        except Exception:

                            pass

                    try:

                        manager.screens.local_screen_names.remove("Hints")

                    except Exception:

                        pass

                    manager.log_panels.pop("Hints", None)

                    return

        except Exception:

            logger.debug("Could not remove Hints tab", exc_info=True)

    Clock.schedule_once(_remove_hints_tab, 0)



    server = ServerProcess()

    manager.slay_launcher_server = server

    try:

        manager.bind(on_stop=lambda *_: server.stop())

    except Exception:

        pass







    if hasattr(manager, "connect_layout"):

        manager.connect_layout.height = 0

        manager.connect_layout.opacity = 0

        manager.connect_layout.disabled = True



    root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))

    title = Label(

        text=f"[b]Slay the StarCraft[/b]  [size=13sp][color=#A9ADB5]v{PACKAGE_VERSION}[/color][/size]",

        markup=True, font_size="28sp", size_hint_y=None, height=dp(50),

    )

    root.add_widget(title)



    instruction_shell = BoxLayout(

        orientation="horizontal", padding=[dp(120), 0, dp(120), 0],

        size_hint_y=None, height=dp(300),

    )

    instructions = Label(

        text=(

            "The default settings are intended for players who are familiar with the starcraft 2 campaigns and can beat "

            "them on Brutal difficulty relatively easily. This will provide a challenging playthrough and a significant "

            "chance of needing to restart entirely if too many mistakes are made, but still leave room for experimenting "

            "with different strategies and strange unit combinations. It will likely take you multiple attempts before "

            "beating your first SlayTheStarcraft campaign. This is the intended experience.\n\n"

            "If you are not comfortable playing the default campaigns on Brutal difficulty, or do not want the challenge "

            "described above, then it is recommended to reduce the Mutation Frequency Multiplier, increase the victory credit reward "

            "multiplier, and/or reduce the Gameplay Difficulty.\n\n"

            "When you are satisfied with your settings, click “Generate Run”. It will automatically save as you play, and "

            "when you open up this launcher again you can click “Load Existing Run” to resume your progress from any of your "

            "existing runs. To delete runs, delete their corresponding “Runs” folder."

        ),

        font_size="18sp", halign="left", valign="top",

    )

    instructions.bind(size=lambda inst, value: setattr(inst, "text_size", (value[0], None)))

    instruction_shell.add_widget(instructions)

    root.add_widget(instruction_shell)







    form = GridLayout(
        cols=4, spacing=(dp(30), dp(8)), size_hint_y=None, height=dp(330),
    )
    option_columns = [BoxLayout(orientation="vertical", spacing=dp(10)) for _ in range(4)]
    for column in option_columns:
        form.add_widget(column)

    def field_label(text: str) -> Label:
        label = Label(text=text, halign="left", valign="middle", size_hint_y=None, height=dp(28))
        label.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        return label

    def compact_text_input(**kwargs: Any) -> TextInput:
        return TextInput(size_hint_y=None, height=dp(42), **kwargs)

    def add_field(column_index: int, label_text: str, control: Any) -> None:
        field = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(70))
        field.add_widget(field_label(label_text))
        field.add_widget(control)
        option_columns[column_index].add_widget(field)

    credits_input = compact_text_input(text=str(DEFAULT_STARTING_CREDITS), multiline=False, input_filter="int")
    seed_input = compact_text_input(text="", multiline=False, input_filter="int")
    campaign_length_input = compact_text_input(text=str(DEFAULT_CAMPAIGN_LENGTH), multiline=False, input_filter="int")
    mutation_multiplier_input = compact_text_input(text=f"{DEFAULT_MUTATION_FREQUENCY_MULTIPLIER:.2f}", multiline=False)
    blessing_multiplier_input = compact_text_input(text=f"{DEFAULT_BLESSING_FREQUENCY_MULTIPLIER:.2f}", multiline=False)

    class SlaySpinnerOption(SpinnerOption):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.background_normal = ""
            self.background_down = ""
            self.background_color = (0.18, 0.20, 0.24, 1.0)
            self.color = (0.96, 0.97, 1.0, 1.0)
            with self.canvas.after:
                self._slay_border_color = Color(0.42, 0.50, 0.62, 1.0)
                self._slay_border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.0)
            self.bind(pos=self._sync_slay_border, size=self._sync_slay_border)

        def _sync_slay_border(self, *_args: Any) -> None:
            self._slay_border.rectangle = (self.x, self.y, self.width, self.height)

    def make_spinner(default_value: str, labels: dict[str, str]) -> Spinner:
        label_to_value = {label: value for value, label in labels.items()}
        spinner = Spinner(
            text=labels[default_value], values=tuple(labels.values()), option_cls=SlaySpinnerOption,
            sync_height=True, size_hint_y=None, height=dp(42),
        )
        spinner.slay_value = default_value
        def selected(instance: Spinner, text: str) -> None:
            instance.slay_value = label_to_value.get(text, default_value)
        spinner.bind(text=selected)
        return spinner

    difficulty_button = make_spinner(DEFAULT_DIFFICULTY, {value: value.title() for value in DIFFICULTIES})
    game_speed_button = make_spinner(DEFAULT_GAME_SPEED, {
        "default": "Default", "slower": "Slower", "slow": "Slow",
        "normal": "Normal", "fast": "Fast", "faster": "Faster",
    })
    extra_shop_slots_button = make_spinner(str(DEFAULT_EXTRA_SHOP_SLOTS), {str(i): str(i) for i in range(4)})
    start_spear_button = make_spinner("no", {"no": "No", "yes": "Yes"})
    start_kerrigan_button = make_spinner("no", {"no": "No", "yes": "Yes"})
    victory_multiplier_input = compact_text_input(text=f"{DEFAULT_VICTORY_CREDIT_REWARD_MULTIPLIER:.2f}", multiline=False)
    item_credit_input = compact_text_input(text=str(DEFAULT_ITEM_CREDIT_REWARD), multiline=False, input_filter="int")

    # Column 1: campaign/gameplay.
    add_field(0, "Gameplay Difficulty", difficulty_button)
    add_field(0, "Game Speed", game_speed_button)
    add_field(0, "Campaign Length", campaign_length_input)

    # Column 2: effect generation and seed.
    add_field(1, "Mutation Frequency Multiplier", mutation_multiplier_input)
    add_field(1, "Blessing Frequency Multiplier", blessing_multiplier_input)
    add_field(1, "Seed", seed_input)

    # Column 3: economy.
    add_field(2, "Starting Credits", credits_input)
    add_field(2, "Victory Credit Reward Multiplier", victory_multiplier_input)
    add_field(2, "Item Credit Reward", item_credit_input)

    # Column 4: starting progression.
    add_field(3, "Extra Shop Slots", extra_shop_slots_button)
    add_field(3, "Start with Spear of Adun", start_spear_button)
    add_field(3, "Start with Kerrigan", start_kerrigan_button)
    root.add_widget(form)

    race_row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(36))
    race_row.add_widget(Label(text="Available Races", size_hint_x=None, width=dp(150)))
    race_checks = {}
    for race in DEFAULT_RACES:
        choice = BoxLayout(spacing=dp(4))
        checkbox = CheckBox(active=True, size_hint_x=None, width=dp(32))
        race_checks[race] = checkbox
        choice.add_widget(checkbox)
        race_label = Button(text=race.title(), background_normal="", background_color=(0, 0, 0, 0))
        race_label.bind(on_release=lambda _button, check=checkbox: setattr(check, "active", not check.active))
        choice.add_widget(race_label)
        race_row.add_widget(choice)
    root.add_widget(race_row)



    status = Label(

        text="Create a new run or load one you already started.",

        size_hint_y=None, height=dp(54), halign="center", valign="middle",

    )

    status.bind(size=lambda inst, val: setattr(inst, "text_size", val))

    root.add_widget(status)



    button_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(52))

    generate_button = Button(text="Generate Run")

    load_button = Button(text="Load Existing Run")

    reset_button = Button(text="Reset to Default Settings")

    button_row.add_widget(generate_button)

    button_row.add_widget(load_button)

    button_row.add_widget(reset_button)

    root.add_widget(button_row)

    root.add_widget(Label(text="", size_hint_y=1))



    setup_tab = manager.add_client_tab("Slay Setup", root)

    manager.slay_setup_tab = setup_tab



    def set_busy(busy: bool, message: str) -> None:

        race_row.disabled = busy
        generate_button.disabled = busy

        load_button.disabled = busy

        reset_button.disabled = busy

        credits_input.disabled = busy

        seed_input.disabled = busy

        difficulty_button.disabled = busy

        game_speed_button.disabled = busy

        mutation_multiplier_input.disabled = busy
        blessing_multiplier_input.disabled = busy
        campaign_length_input.disabled = busy
        extra_shop_slots_button.disabled = busy
        start_spear_button.disabled = busy
        start_kerrigan_button.disabled = busy

        victory_multiplier_input.disabled = busy

        item_credit_input.disabled = busy

        status.text = message



    def show_error(message: str) -> None:

        set_busy(False, message)

        popup = Popup(title="Slay the StarCraft", content=Label(text=message), size_hint=(0.75, 0.35))

        popup.open()



    def switch_to_missions() -> None:

        tab = getattr(manager, "slay_mission_tab", None)

        if tab is not None and hasattr(manager, "screens"):

            try:

                manager.screens.switch_screens(tab)

                tab.active = True

                setup_tab.active = False





                if not getattr(manager, "slay_initial_map_scroll_done", False):

                    scroll = getattr(manager, "campaign_scroll_panel", None)

                    if scroll is not None:

                        scroll.scroll_y = 0.0

                        for delay in (0.05, 0.20):

                            Clock.schedule_once(

                                lambda _dt, view=scroll: setattr(view, "scroll_y", 0.0), delay

                            )

            except Exception:

                pass



    def activate_run_main_thread(run_dir: Path, manifest: dict[str, Any], port: int) -> None:



        os.environ[RUN_DIR_ENV] = str(run_dir)

        manifest = _touch_last_played(run_dir)

        player_name = str(manifest.get("player_name", DEFAULT_PLAYER_NAME)) or DEFAULT_PLAYER_NAME

        manager.ctx.username = player_name

        manager.ctx.auth = player_name

        manager.ctx.password = None

        set_busy(False, f"Run {run_dir.name} active. Connecting to the private server...")

        manager.slay_initial_map_scroll_done = False

        async_start(manager.ctx.connect(f"127.0.0.1:{port}"), name="Slay automatic local connection")

        switch_to_missions()



    def start_existing(run_dir: Path, manifest: dict[str, Any]) -> None:

        def worker() -> None:

            try:

                Clock.schedule_once(lambda _dt: set_busy(True, "Starting private Archipelago server..."), 0)

                os.environ[RUN_DIR_ENV] = str(run_dir)

                port = server.start(run_dir)

                Clock.schedule_once(lambda _dt: activate_run_main_thread(run_dir, manifest, port), 0)

            except Exception as exc:

                logger.exception("Slay launcher failed to start run")

                Clock.schedule_once(lambda _dt, msg=str(exc): show_error(msg), 0)

        threading.Thread(target=worker, name="Slay run starter", daemon=True).start()



    def reset_defaults(*_args: Any) -> None:

        credits_input.text = str(DEFAULT_STARTING_CREDITS)

        seed_input.text = ""

        difficulty_button.text = DEFAULT_DIFFICULTY.title()

        difficulty_button.slay_value = DEFAULT_DIFFICULTY

        game_speed_button.text = "Default"

        game_speed_button.slay_value = DEFAULT_GAME_SPEED

        mutation_multiplier_input.text = f"{DEFAULT_MUTATION_FREQUENCY_MULTIPLIER:.2f}"
        blessing_multiplier_input.text = f"{DEFAULT_BLESSING_FREQUENCY_MULTIPLIER:.2f}"
        campaign_length_input.text = str(DEFAULT_CAMPAIGN_LENGTH)
        extra_shop_slots_button.text = str(DEFAULT_EXTRA_SHOP_SLOTS)
        extra_shop_slots_button.slay_value = str(DEFAULT_EXTRA_SHOP_SLOTS)
        start_spear_button.text = "No"
        start_spear_button.slay_value = "no"
        start_kerrigan_button.text = "No"
        start_kerrigan_button.slay_value = "no"
        victory_multiplier_input.text = f"{DEFAULT_VICTORY_CREDIT_REWARD_MULTIPLIER:.2f}"

        item_credit_input.text = str(DEFAULT_ITEM_CREDIT_REWARD)

        for checkbox in race_checks.values():
            checkbox.active = True
        status.text = "Settings reset to defaults."



    def generate_pressed(*_args: Any) -> None:

        try:

            starting_credits = int(credits_input.text.strip() or DEFAULT_STARTING_CREDITS)

        except ValueError:

            show_error("Starting Credits must be a whole number.")

            return

        if starting_credits < 0:

            show_error("Starting Credits cannot be negative.")

            return

        seed_text = seed_input.text.strip()

        try:

            seed = int(seed_text) if seed_text else None

        except ValueError:

            show_error("Seed must be a whole number or left blank.")

            return

        if seed is not None and seed < 0:

            show_error("Seed cannot be negative.")

            return

        try:

            victory_multiplier = float(victory_multiplier_input.text.strip() or "1.00")

        except ValueError:

            show_error("Victory Credit Reward Multiplier must be a decimal number.")

            return

        if victory_multiplier < 0 or victory_multiplier == float("inf") or victory_multiplier != victory_multiplier:

            show_error("Victory Credit Reward Multiplier must be a finite non-negative number.")

            return

        try:

            item_credit_reward = int(item_credit_input.text.strip() or DEFAULT_ITEM_CREDIT_REWARD)

        except ValueError:

            show_error("Item Credit Reward must be a whole number.")

            return

        if item_credit_reward < 0:

            show_error("Item Credit Reward cannot be negative.")

            return
        try:
            campaign_length = int(campaign_length_input.text.strip() or DEFAULT_CAMPAIGN_LENGTH)
        except ValueError:
            show_error("Campaign Length must be a whole number.")
            return
        if not MIN_CAMPAIGN_LENGTH <= campaign_length <= MAX_CAMPAIGN_LENGTH:
            show_error(f"Campaign Length must be between {MIN_CAMPAIGN_LENGTH} and {MAX_CAMPAIGN_LENGTH}.")
            return
        try:
            mutation_frequency = float(mutation_multiplier_input.text.strip() or "1.0")
            blessing_frequency = float(blessing_multiplier_input.text.strip() or "1.0")
        except ValueError:
            show_error("Mutation and Blessing Frequency Multipliers must be decimal numbers.")
            return
        if (not math.isfinite(mutation_frequency) or mutation_frequency < 0 or
                not math.isfinite(blessing_frequency) or blessing_frequency < 0):
            show_error("Mutation and Blessing Frequency Multipliers must be finite non-negative numbers.")
            return
        extra_shop_slots = int(getattr(extra_shop_slots_button, "slay_value", str(DEFAULT_EXTRA_SHOP_SLOTS)))
        start_with_spear = str(getattr(start_spear_button, "slay_value", "no")) == "yes"
        start_with_kerrigan = str(getattr(start_kerrigan_button, "slay_value", "no")) == "yes"

        difficulty = str(getattr(difficulty_button, "slay_value", DEFAULT_DIFFICULTY))

        game_speed = str(getattr(game_speed_button, "slay_value", DEFAULT_GAME_SPEED))

        try:
            selected_races = normalize_races(tuple(race for race, check in race_checks.items() if check.active))
        except ValueError as exc:
            show_error(str(exc))
            return

        set_busy(True, "Generating Slay run...")



        def worker() -> None:

            try:

                run_dir, manifest = generate_run(

                    starting_credits, difficulty, seed=seed,

                    mutation_frequency=mutation_frequency, blessing_frequency=blessing_frequency,

                    victory_credit_reward_multiplier=victory_multiplier,

                    item_credit_reward=item_credit_reward,

                    game_speed=game_speed, campaign_length=campaign_length,
                    extra_shop_slots=extra_shop_slots, start_with_spear=start_with_spear,
                    start_with_kerrigan=start_with_kerrigan,
                    selected_races=selected_races,

                )

                Clock.schedule_once(lambda _dt: set_busy(True, "Starting private Archipelago server..."), 0)

                os.environ[RUN_DIR_ENV] = str(run_dir)

                port = server.start(run_dir)

                Clock.schedule_once(lambda _dt: activate_run_main_thread(run_dir, manifest, port), 0)

            except Exception as exc:

                logger.exception("Slay launcher run generation failed")

                Clock.schedule_once(lambda _dt, msg=str(exc): show_error(msg), 0)

        threading.Thread(target=worker, name="Slay run generator", daemon=True).start()



    def load_pressed(*_args: Any) -> None:

        available = list_runs()

        if not available:

            popup = Popup(

                title="Load Existing Run",

                content=Label(text="No launcher-created Slay runs were found yet."),

                size_hint=(0.72, 0.32),

            )

            popup.open()

            return



        list_layout = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)

        list_layout.bind(minimum_height=list_layout.setter("height"))

        from kivy.uix.scrollview import ScrollView

        scroll = ScrollView()

        scroll.add_widget(list_layout)

        popup = Popup(title="Load Existing Run", content=scroll, size_hint=(0.90, 0.80))

        for run_dir, manifest in available:

            button = Button(text=_display_run_name(run_dir, manifest), size_hint_y=None, height=dp(50))

            def choose(_btn: Any, rd: Path = run_dir, mf: dict[str, Any] = manifest) -> None:

                popup.dismiss()

                set_busy(True, f"Loading run {rd.name}...")

                start_existing(rd, mf)

            button.bind(on_release=choose)

            list_layout.add_widget(button)

        popup.open()



    generate_button.bind(on_release=generate_pressed)

    load_button.bind(on_release=load_pressed)

    reset_button.bind(on_release=reset_defaults)





    try:

        manager.screens.switch_screens(setup_tab)

        setup_tab.active = True

    except Exception:

        pass

