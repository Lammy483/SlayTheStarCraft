"""Dev15 regressions for updated event spawning, persistence, and full-install updates."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')
EVENTS = (ROOT / 'Payload' / 'slay_events.py').read_text(encoding='utf-8')
CATALOG = (ROOT / 'Payload' / 'BOON_CATALOG.csv').read_text(encoding='utf-8')
UPDATER = (ROOT / 'Tools' / 'Update-ExistingSlay.ps1').read_text(encoding='utf-8')


def fn(signature: str) -> str:
    return GALAXY.split(signature, 1)[1].split('\n}\n', 1)[0]


class EventsDev15Tests(unittest.TestCase):
    def test_psionic_lords_uses_real_psionic_tag_and_three_percent_per_damage_event(self):
        boon = fn('bool APRG_NewBoonDamage_Func(')
        self.assertIn('UnitTypeTestAttribute(sourceType, c_unitAttributePsionic)', boon)
        self.assertIn('RandomInt(1, 100) <= 3', boon)
        self.assertIn('APRG_MakeGroupUncommandable(convertedGroup)', boon)
        self.assertIn('EventUnitDamageSourceUnit()', boon)
        self.assertIn('EventUnitDamageAmount()', boon)
        self.assertIn('there is a 3% chance', CATALOG)
        self.assertIn('g_aprgMaskG != 0', fn('void APRG_ActivateEffects('))

    def test_no_dev_spawn_notes_in_user_event_popup_and_units_plural(self):
        self.assertIn('A Brutalisk will appear in the next mission.', EVENTS)
        self.assertNotIn('A hostile Brutalisk will spawn near enemy structures next mission.', EVENTS)
        self.assertIn('[amount] [Mechanical Ground Terran Unit]s', EVENTS)
        self.assertIn('test [Mechanical Ground Terran Unit]s in the field', EVENTS)
        self.assertIn('give [Mechanical Ground Terran Unit]s to the enemy team', EVENTS)

    def test_event_allies_spawn_real_heroes_after_base(self):
        for expression in ('"Nova", "NovaCovertOps", "NovaHero"',
                           '"Brakk", "PrimalBrakk", "BrakkHero"'):
            self.assertIn(expression, GALAXY)
        hero = fn('unit APRG_EventAlliedHero(')
        self.assertIn('APRG_KerriganSafeHomePoint(player)', hero)
        self.assertIn('UnitCreate(1, unitType, c_unitCreateIgnorePlacement, player', hero)
        self.assertNotIn('APRG_CreatePlayerUnitsSafe(', hero)
        nova = fn('void APRG_TickEventNova(')
        self.assertIn('APRG_PlayerMacroBaseReady(player)', nova)
        self.assertNotIn('APRG_EventActorFallen(', nova)
        ally_brakk = fn('void APRG_TickEventAllyBrakk(')
        self.assertIn('APRG_EventActorDead("BrakkAllyDead")', ally_brakk)

    def test_native_death_receipts_no_vortex_false_death(self):
        died = fn('bool APRG_EventUnitDied_Func(')
        for key in ('"NovaDead"', '"ToshDead"', '"ZagaraDead"',
                    '"BrakkAllyDead"', '"OrganismOutcome"'):
            self.assertIn(key, died)
        self.assertIn('fallen = EventUnit()', died)
        self.assertIn('TriggerAddEventUnitDied(TriggerCreate("APRG_EventUnitDied_Func"), null)', GALAXY)
        organism = fn('void APRG_TickEventOrganism(')
        self.assertNotIn('!UnitIsAlive(g_aprgEventTestBrutalisk)', organism)
        self.assertNotIn('APRG_EventActorFallen(', fn('void APRG_TickEventZagara('))

    def test_hostile_spawns_are_ground_connected_and_patrol_enemy_territory(self):
        helper = fn('point APRG_EventHostileGroundPoint(')
        self.assertIn('PointPathingIsConnected(candidate, homeGround)', helper)
        self.assertIn('PointWithOffsetPolar(UnitGetPosition(anchor)', helper)
        self.assertIn('APRG_KerriganSafeHomePoint(player)', helper)
        event_anchor = fn('unit APRG_EventHostileAnchor(')
        self.assertIn('APRG_EnemyStructures(player)', event_anchor)
        self.assertIn('APRG_EventHostileGroundPoint(player, candidate)', event_anchor)
        self.assertNotIn('APRG_HostileGroundAnchorConnectedToPlayer', event_anchor)
        for signature in ('unit APRG_EventEnemyHero(', 'void APRG_TickEventZagara(',
                          'void APRG_TickEventMechanical(', 'void APRG_TickEventOrganism('):
            self.assertIn('APRG_EventHostileGroundPoint(player, anchor)', fn(signature))
        organism = fn('void APRG_TickEventOrganism(')
        self.assertNotIn('pointToSpawn = UnitGetPosition(anchor)', organism)
        self.assertIn('APRG_EventHostilePatrolPoint(player)', organism)
        self.assertIn('APRG_EventCreateBrutalisk(owner, pointToSpawn)', organism)
        self.assertIn('APRG_EventHostilePatrolPoint(player)', fn('void APRG_TickEventMechanical('))

    def test_native_mechanical_field_test_units_not_ap_family_substitutions(self):
        mechanical = fn('void APRG_TickEventMechanical(')
        self.assertIn('UnitCreate(g_aprgEventMechCount, mechUnitType', mechanical)
        self.assertNotIn('APRG_CreatePlayerUnitsSafe(g_aprgEventMechCount', mechanical)
        self.assertIn('UnitGetPropertyFixed(u, c_unitPropLifeMax, c_unitPropCurrent) <= 3.0', mechanical)
        self.assertIn('Rory Swann\'s field test has begun', mechanical)

    def test_full_install_updater_replaces_all_program_directories(self):
        self.assertIn('foreach ($folderName in @("Payload", "Tools"))', UPDATER)
        self.assertIn('Move-Item -LiteralPath $oldFolder', UPDATER)
        self.assertIn('Copy-Item -LiteralPath $newFolder -Destination $oldFolder -Recurse -Force', UPDATER)
        self.assertIn('Get-ChildItem -LiteralPath $sourceRoot -File', UPDATER)
        self.assertIn('Get-ChildItem -LiteralPath $oldArt -Recurse -File', UPDATER)
        self.assertIn('slay_preferences.ini', UPDATER)
        self.assertIn('slay_install.json', UPDATER)
        self.assertNotIn('bootstrap_slay_runtime.ps1")', UPDATER)


if __name__ == '__main__':
    unittest.main()
