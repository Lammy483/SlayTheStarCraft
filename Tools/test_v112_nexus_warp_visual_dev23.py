"""Dev23: all scripted Protoss warp-ins use a campaign-proven model visual."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")


def func(name):
    start = GALAXY.index("actor " + name + "(") if name == "APRG_CreateWarpVisual" else GALAXY.index("void " + name + "(")
    body = GALAXY[start:]
    return body[:body.index("\n}\n") + 3]


class TestScriptedWarpVisual(unittest.TestCase):
    def test_native_purifier_ref_origin_visibility_attachment(self):
        visual = func("APRG_CreateWarpVisual")
        self.assertIn('libNtve_gf_AttachModelToUnitInheritVisibility(u, "ProtossGenericWarpInOut", "Ref_Origin")', visual)
        self.assertNotIn('"Ref_Center"', visual)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogModel, "ProtossGenericWarpInOut")', visual)

    def test_cross_campaign_fallback_is_real_model_before_marker(self):
        visual = func("APRG_CreateWarpVisual")
        self.assertIn('CatalogEntryIsValid(c_gameCatalogModel, "MothershipTeleportIn")', visual)
        self.assertIn('libNtve_gf_AttachModelToUnitInheritVisibility(u, "MothershipTeleportIn", "Ref_Origin")', visual)
        self.assertLess(visual.index('"MothershipTeleportIn"'), visual.index('libNtve_gf_CreateActorAtPoint("ProtossFastWarpinMarker"'))

    def test_ally_and_hostile_share_visual_and_keep_stun(self):
        for name in ("APRG_ProcessAllyWarpQueue", "APRG_ProcessPurifierHostileWarpQueue"):
            body = func(name)
            self.assertIn('APRG_CreateWarpVisual(u, spawnPoint)', body)
            self.assertIn('libNtve_gf_PauseUnit(u, true)', body)
            self.assertIn('libNtve_gf_SetOpacity(1.0, 5.0)', body)
            self.assertIn('now + 5.0', body)
            self.assertIn('libNtve_gf_PauseUnit(u, false)', body)

    def test_nexus_shields_uses_hostile_warp_queue(self):
        body = func('APRG_TickNexusShield')
        self.assertIn('APRG_QueuePurifierHostileWarp', body)
        self.assertNotIn('UnitCreate(1, "Stalker"', body)


if __name__ == '__main__':
    unittest.main()
