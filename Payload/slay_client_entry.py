



from __future__ import annotations



import multiprocessing

import os

import sys

import traceback

from pathlib import Path





def _portable_root() -> Path | None:

    raw = os.environ.get("SLAY_PORTABLE_ROOT", "").strip()

    return Path(raw).resolve() if raw else None





def _write_crash_log(text: str) -> None:

    root = _portable_root()

    if root is None:

        return

    try:

        path = root / "Runtime" / "Logs" / "SlayPythonCrash.log"

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(text, encoding="utf-8", errors="replace")

    except Exception:

        pass





def main() -> None:

    multiprocessing.freeze_support()







    if os.environ.get("SKIP_REQUIREMENTS_UPDATE", "").lower() not in {"1", "true", "yes"}:

        import ModuleUpdate

        ModuleUpdate.update()





    portable_root = _portable_root()

    if portable_root is not None:

        import Utils

        cache_root = portable_root / "Runtime" / "APCache"

        cache_root.mkdir(parents=True, exist_ok=True)

        try:

            Utils.cache_path.cached_path = str(cache_root)

        except Exception:

            pass



    from worlds.sc2 import client as sc2_client

    if os.environ.get("SLAY_UI_STYLE", "command").casefold() != "classic":
        from worlds.sc2 import client_gui
        import slay_command_ui
        slay_command_ui.install(client_gui)
    from worlds.sc2 import client_gui
    import slay_endless_ui
    slay_endless_ui.install(client_gui)












    if os.environ.get("SLAY_LAUNCHER_MODE", "").lower() in {"1", "true", "yes", "on"}:

        original_run_gui = sc2_client.SC2Context.run_gui



        def _slay_run_gui_with_failure_reporting(ctx):

            original_run_gui(ctx)

            task = getattr(ctx, "ui_task", None)

            if task is None:

                raise RuntimeError("Archipelago did not create the Kivy UI task")



            def _ui_done(done_task):

                if done_task.cancelled():

                    return

                try:

                    exc = done_task.exception()

                except BaseException:

                    exc = sys.exc_info()[1]

                if exc is None:

                    return

                detail = "Kivy UI task failed:\n" + "".join(

                    traceback.format_exception(type(exc), exc, exc.__traceback__)

                )

                _write_crash_log(detail)

                print(detail, file=sys.stderr, flush=True)

                try:

                    ctx.exit_event.set()

                except Exception:

                    pass



            task.add_done_callback(_ui_done)



        sc2_client.SC2Context.run_gui = _slay_run_gui_with_failure_reporting









    if os.environ.get("SLAY_ENTRY_SMOKE", "").lower() in {"1", "true", "yes"}:

        if not callable(getattr(sc2_client, "launch", None)):

            raise RuntimeError("worlds.sc2.client.launch is missing or not callable")

        print("Slay portable entry preflight passed")

        return



    sc2_client.launch()





if __name__ == "__main__":

    try:

        main()

    except BaseException:

        detail = traceback.format_exc()

        _write_crash_log(detail)

        print(detail, file=sys.stderr, flush=True)

        raise

