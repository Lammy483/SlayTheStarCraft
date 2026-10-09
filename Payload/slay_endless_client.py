"""Small client hooks for recurring mission IDs. Standard-mode behavior is unchanged."""
def patch_endless_client(text):
    def replace(old,new):
        nonlocal text
        if new in text:return
        if text.count(old)!=1:raise RuntimeError("Endless client hook did not match: "+old[:80])
        text=text.replace(old,new,1)
    replace('    def is_mission_completed(self, mission_id: int) -> bool:\n', '    def is_mission_completed(self, mission_id: int) -> bool:\n        if slay.endless_mode(self):\n            return int(mission_id) < 0\n')
    replace('        self.mission_id = mission_id\n', '        self.mission_id = mission_id\n        self.slay_floor_token = slay.state(ctx).get("endless", {}).get("floor", -1)\n')
    replace('                            self.mission_id in self.ctx.final_mission_ids and', '                            not slay.endless_mode(self.ctx) and\n                            self.mission_id in self.ctx.final_mission_ids and')
    replace('                            self.mission_completed = True\n\n                        if send_victory:', '                            self.mission_completed = True\n                            if slay.endless_mode(self.ctx):\n                                slay.complete_endless_mission(self.ctx, self.mission_id, self.slay_floor_token)\n\n                        if send_victory:')
    replace('    def missions_beaten_count(self) -> int:\n', '    def missions_beaten_count(self) -> int:\n        if slay.endless_mode(self.ctx):\n            return slay.victory_count(self.ctx)\n')
    return text
