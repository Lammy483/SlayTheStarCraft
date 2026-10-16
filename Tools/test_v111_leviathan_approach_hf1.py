"""Regression gates for the base-established Leviathan approach and spawn order."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
G = (ROOT / "Payload/APRogue.galaxy").read_text(encoding="utf-8")

def function(name: str) -> str:
    """Find a Galaxy function declaration and return its brace-balanced body."""
    import re
    m = re.search(r'(?m)^(?:bool|void|fixed) ' + re.escape(name) + r'\([^\n]*\)\s*\{', G)
    if not m:
        raise AssertionError(f"Missing function {name}")
    opened = m.end() - 1
    depth = 0
    for i in range(opened, len(G)):
        if G[i] == '{': depth += 1
        elif G[i] == '}':
            depth -= 1
            if depth == 0: return G[opened+1:i]
    raise AssertionError(f"Unclosed function {name}")

class LeviathanApproachHF1(unittest.TestCase):
    def test_spawn_is_base_ready_gated_and_not_four_minutes(self):
        body = function('APRG_TickBaseLeviathan')
        spawn = body.index('created = UnitCreate(1, leviathanType')
        gate = body.index('if (now < g_aprgMacroReadyTime + 300.0) { return; }')
        self.assertIn('!APRG_PlayerMacroBaseReady(player)', body[:spawn])
        self.assertLess(spawn, gate)
        self.assertIn('AISetUnitScriptControlled(g_aprgBaseLeviathan, true);', body[spawn:gate])
        self.assertIn('APRG_SetBaseLeviathanSpawnAbilitiesEnabled(g_aprgBaseLeviathan, false);', body[spawn:gate])
        self.assertNotIn('APRG_TryLeviathanMutationSpawn(',body[:gate])
        self.assertIn('g_aprgMacroReadyTime = GameGetMissionTime();', function('APRG_UpdateMacroBaseReady'))

    def test_no_spawn_before_stopping_near_player_building(self):
        body = function('APRG_TickBaseLeviathan')
        gate = body.index('if (now < g_aprgMacroReadyTime + 300.0) { return; }')
        dist = body.index('DistanceBetweenPoints(', gate)
        movement = body.index('AbilityCommand("move", 0)', dist)
        stop = body.index('UnitIssueOrder(g_aprgBaseLeviathan, stopOrder, c_orderQueueReplace);', movement)
        positioned = body.index('g_aprgBaseLeviathanPositioned = true;',stop)
        enabled = body.index('APRG_SetBaseLeviathanSpawnAbilitiesEnabled(g_aprgBaseLeviathan, true);',positioned)
        timed_spawn = body.index('APRG_TryLeviathanMutationSpawn(', enabled)
        self.assertIn('> 30.0',body[dist:movement]);self.assertLess(stop,positioned)
        self.assertLess(positioned,enabled);self.assertLess(enabled,timed_spawn)
        self.assertIn('g_aprgNextBaseLeviathanMutaliskTime = now;',body[enabled:timed_spawn])
        self.assertIn('g_aprgNextBaseLeviathanBroodLordTime = now;',body[enabled:timed_spawn])

    def test_damage_triggers_and_any_indirect_spawns_gated(self):
        burst=function('APRG_TickBaseLeviathanBurst')
        self.assertIn('!g_aprgBaseLeviathanPositioned) { return; }',burst)
        self.assertLess(burst.index('!g_aprgBaseLeviathanPositioned'),burst.index('APRG_TryLeviathanMutationSpawn('))
        spawn=function('APRG_TryLeviathanMutationSpawn')
        self.assertIn('|| !g_aprgBaseLeviathanPositioned) { return false; }',spawn)
        native=function('APRG_SetBaseLeviathanSpawnAbilitiesEnabled')
        self.assertIn('"Mutalisk"', native)
        self.assertIn('"BroodLord"', native)
        self.assertIn('UnitAbilityEnable(leviathan, abilityType, enabled);',native)
        general=function('APRG_TickEnemyCombatAbilities')
        self.assertIn('if (enemy == g_aprgBaseLeviathan && !g_aprgBaseLeviathanPositioned) { continue; }',general)

    def test_existing_mutation_only_and_package_revision(self):
        self.assertIn('if (APRG_PlayerMacroBaseReady(player) && (g_aprgMissionFlags & APRG_MISSION_FLAG_LEVIATHAN_OUTSIDE_BASE) != 0) { APRG_TickBaseLeviathan(player, now); }',G)
        self.assertEqual((ROOT/'VERSION.txt').read_text().strip(),'1.2.0')
        manifest=json.loads((ROOT/'launcher_manifest.json').read_text())
        rev='v1.2.0-release'
        self.assertEqual(manifest['runtime_revision'],rev)
        for f in ('Tools/bootstrap_slay_runtime.ps1','Tools/slay_launcher_windows.go'):
            self.assertIn(rev,(ROOT/f).read_text())
        # Preserve user-authored in-game description verbatim.
        source=(ROOT/'Payload/EFFECT_CATALOG.csv').read_text()
        self.assertIn('The Leviathan floats outside your base spawning mutalisks and brood lords',source)

if __name__=='__main__': unittest.main()
