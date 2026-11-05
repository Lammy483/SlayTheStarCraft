"""Regression: SC2 load callback cannot erase early event chat packets.

The AP client transmits ?APRogue followed immediately by ?SlayEvent and
?SlayMech. They may arrive before LOAD_FINISHED_EVENT. Old Galaxy initialized
only the event values to zero in APRG_Load_Func, silently disabling all events
while older mutation masks kept working.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")
INSTALLER = (ROOT / "Payload" / "install_slay.py").read_text(encoding="utf-8")
EVENTS = (ROOT / "Payload" / "slay_events.py").read_text(encoding="utf-8")


def section(signature):
    return GALAXY.split(signature, 1)[1].split("\n}\n", 1)[0]


class EventsDev16HandshakeTests(unittest.TestCase):
    def test_load_does_not_clear_early_event_packet_values(self):
        load = section("bool APRG_Load_Func(")
        for name in ("g_aprgEventMask", "g_aprgEventUnit", "g_aprgEventCount",
                     "g_aprgEventMechUnitIndex", "g_aprgEventMechCount",
                     "g_aprgEventMechMode", "g_aprgEventMechCheckpoint",
                     "g_aprgEventBank", "g_aprgEventSection"):
            self.assertNotIn(name + " =", load,
                             f"SC2 load must retain packet value {name}")
        # Per-mission ACTOR state still needs its regular reset.
        self.assertIn("g_aprgEventNovaSpawned = false;", load)
        self.assertIn("g_aprgEventMechSpawned = false;", load)

    def test_event_packets_are_accepted_and_visible_in_test_build(self):
        event = section("bool APRG_EventConfig_Func(")
        mechanical = section("bool APRG_EventMechConfig_Func(")
        self.assertIn("g_aprgEventMask = StringToInt(StringWord(EventChatMessage(false), 2))", event)
        self.assertIn("Event effects activated (mask", event)
        self.assertIn("g_aprgEventMechMode = StringToInt(StringWord(EventChatMessage(false), 4))", mechanical)
        self.assertIn("Swann trial activated (mode", mechanical)
        self.assertIn('"?SlayEvent"', GALAXY)
        self.assertIn('"?SlayMech"', GALAXY)

    def test_client_sends_both_packets_after_normal_config(self):
        config = INSTALLER.index('current_send + event_send')
        self.assertGreater(config, 0)
        self.assertIn('slay.event_native_values_for_mission(self.ctx, self.mission_id)', INSTALLER)
        self.assertIn('slay.event_mechanical_values_for_mission(self.ctx, self.mission_id)', INSTALLER)
        self.assertIn('await self.chat_send(f"?SlayEvent', INSTALLER)
        self.assertIn('await self.chat_send(f"?SlayMech', INSTALLER)
        self.assertIn('mask |= NOVA_ALLY | TOSH_ENEMY', EVENTS)
        self.assertIn('mask |= ORGANISM_TEST', EVENTS)


if __name__ == "__main__":
    unittest.main()
