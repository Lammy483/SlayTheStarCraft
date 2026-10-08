"""Endless route adapter; preserves native launch and victory interfaces."""
def install(module):
    from worlds.sc2 import slay_the_starcraft as slay
    import slay_command_ui as command
    from kivy.metrics import dp
    from kivy.clock import Clock
    cls=module.SC2Manager
    if getattr(cls,'_slay_endless_ui',False):return
    original=cls.build_mission_table
    original_positions=command.resolve_route_positions
    def positions(nodes,width,preferred):
        if not any(n.get('_endless_floor') for n in nodes.values()):return original_positions(nodes,width,preferred)
        layers=sorted({int(n['layer']) for n in nodes.values()})
        result={}
        for mid,n in nodes.items():
            count=max(1,int(n.get('lane_count',3)))
            lane=int(n.get('lane',0))
            result[mid]=(dp(140)+(width-dp(280))*((lane+.5)/count),dp(30+layers.index(int(n['layer']))*205))
        return result
    command.resolve_route_positions=positions
    def build(manager,dt):
        if not (slay.endless_mode(manager.ctx) and slay.state_ready(manager.ctx)) or manager.launching:
            return original(manager,dt)
        manager.mission_buttons=[]
        for mid,node in slay.nodes(manager.ctx).items():
            status=slay.node_status(manager.ctx,mid)
            b=module.MissionButton(text=str(node['mission_name']),mission_id=mid)
            b.tooltip_text=slay.mission_tooltip_section(manager.ctx,mid,[]) if mid>0 else str(node['mission_name'])
            b.disabled=status not in ('available','selected')
            if mid>0:b.bind(on_press=manager.mission_callback)
            manager.mission_buttons.append(b)
        manager._slay_refresh_header()
        command.build_chart(manager)
        chart=manager.slay_chart
        for i,layer in enumerate(chart.layers):
            chart.add_widget(command.label('Floor '+str(layer+1),size_hint=(None,None),size=(dp(100),dp(30)),pos=(dp(4),dp(95+i*205))))
    cls.build_mission_table=build
    cls._slay_endless_ui=True
