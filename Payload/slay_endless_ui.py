"""Compatibility adapter for legacy Endless saves (new mode disabled v1.1.0).

Avoid rebuilding mission buttons on every 0.5-second client GUI refresh.
A replaced MissionButton can leave a KivyMD tooltip mounted on the Window,
which previously caused stacked, stationary mission descriptions.
"""

def install(module):
    from worlds.sc2 import slay_the_starcraft as slay
    import slay_command_ui as command
    from kivy.metrics import dp

    cls = module.SC2Manager
    if getattr(cls, "_slay_endless_ui", False):
        return
    original = cls.build_mission_table
    original_positions = command.resolve_route_positions

    def positions(nodes, width, preferred=None, node_widths=None):
        # Standard Mode always uses the normal planet chart. Preserve measured
        # mission widths and its existing layout algorithm exactly.
        if not any(n.get("_endless_floor") for n in nodes.values()):
            return original_positions(nodes, width, preferred, node_widths)
        layers = sorted({int(n["layer"]) for n in nodes.values()})
        result = {}
        for mid, n in nodes.items():
            count = max(1, int(n.get("lane_count", 3)))
            lane = int(n.get("lane", 0))
            result[mid] = (
                dp(140) + (width - dp(280)) * ((lane + .5) / count),
                dp(30 + layers.index(int(n["layer"])) * 205),
            )
        return result

    command.resolve_route_positions = positions

    def clear_existing_tooltips(manager):
        # Native Archipelago does this before rebuilding, but the old Endless
        # adapter discarded mission_buttons first and lost its references.
        clear = getattr(manager, "clear_tooltip", None)
        if callable(clear):
            clear()
        else:
            for previous in getattr(manager, "mission_buttons", ()):
                previous.remove_tooltip()
        manager.last_shown_tooltip = -1

    # Keep this callback name for Kivy's WeakMethod scheduled dispatcher.
    def build_mission_table(manager,dt):
        active = (not manager.launching and slay.endless_mode(manager.ctx)
                  and slay.state_ready(manager.ctx))
        if not active:
            if getattr(manager, "_slay_endless_chart_snapshot", None) is not None:
                clear_existing_tooltips(manager)
                manager._slay_endless_chart_snapshot = None
            return original(manager, dt)

        # The view depends on mission availability and tooltip contents, not
        # the half-second refresh cadence. Reading the current node/status
        # snapshot also handles floor changes and save/load transitions.
        current = []
        for mid, node in slay.nodes(manager.ctx).items():
            status = slay.node_status(manager.ctx, mid)
            title = str(node["mission_name"])
            tip = (slay.mission_tooltip_section(manager.ctx, mid, [])
                   if mid > 0 else title)
            current.append((mid, node, status, title, tip))
        run_key = str((getattr(manager.ctx, "slay_config", None) or {}).get("run_id", ""))
        signature = (run_key, tuple(sorted((int(mid), str(node.get("layer")),
                                  str(node.get("lane")),
                                  str(node.get("lane_count")),
                                  str(node.get("_endless_floor")),
                                  status, title, tip)
                                 for mid, node, status, title, tip in current)))
        chart = getattr(manager, "slay_chart", None)
        if (signature == getattr(manager, "_slay_endless_chart_snapshot", None)
                and chart is not None and chart.parent is not None
                and getattr(manager, "slay_chart_buttons", ()) == tuple(manager.mission_buttons)):
            return

        # Dismiss old tooltip widgets while their owners are still reachable,
        # before the chart removes the old MissionButton widgets from the UI.
        clear_existing_tooltips(manager)
        manager.mission_buttons = []
        for mid, node, status, title, tip in current:
            b = module.MissionButton(text=title, mission_id=mid)
            b.tooltip_text = tip
            b.disabled = status not in ("available", "selected")
            if mid > 0:
                b.bind(on_press=manager.mission_callback)
            manager.mission_buttons.append(b)
        manager._slay_refresh_header()
        command.build_chart(manager)
        chart = manager.slay_chart
        for i, layer in enumerate(chart.layers):
            chart.add_widget(command.label(
                "Floor " + str(layer + 1), size_hint=(None, None),
                size=(dp(100), dp(30)), pos=(dp(4), dp(95 + i * 205)),
            ))
        manager._slay_endless_chart_snapshot = signature

    cls.build_mission_table=build_mission_table
    cls._slay_endless_ui = True
