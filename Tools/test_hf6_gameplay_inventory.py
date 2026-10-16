"""HF6 source/behavior contracts including icon identity and unchanged text."""
import ast
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALAXY = (ROOT / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')
GEN = (ROOT / 'Payload' / 'generate_slay_run.py').read_text(encoding='utf-8')
CLIENT = (ROOT / 'Payload' / 'slay_the_starcraft.py').read_text(encoding='utf-8')
UI = (ROOT / 'Payload' / 'slay_command_ui.py').read_text(encoding='utf-8')
ASSETS = ROOT / 'Payload' / 'slay_assets'


def galaxy_body(name, return_type='void'):
    start = GALAXY.index(f'{return_type} {name} (') if f'{return_type} {name} (' in GALAXY else GALAXY.index(f'{return_type} {name}(')
    # Forward prototypes are legal Galaxy declarations; inspect the definition.
    while ';' in GALAXY[start:GALAXY.index('{',start)]:
        start = GALAXY.index(f'{return_type} {name}(',start+1)
    begin = GALAXY.index('{',start)
    depth = 0
    for i in range(begin,len(GALAXY)):
        if GALAXY[i]=='{':depth+=1
        elif GALAXY[i]=='}':
            depth-=1
            if depth==0:return GALAXY[start:i+1]
    raise AssertionError(name)


class HF6(unittest.TestCase):
    def test_crucible_cannot_roll_meat_grinder(self):
        self.assertIn('CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS = frozenset({', GEN)
        self.assertIn('forbidden_mutators.update(crucible_mutation_exclusions(mission_short_name))', GEN)
        self.assertIn('mission_name.casefold().startswith("the crucible") and effect in CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS', CLIENT)
        self.assertIn('return False', CLIENT.split('mission_name.casefold().startswith("the crucible") and effect in CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS:')[1][:40])

    def test_decay_skips_all_worker_types(self):
        tick=galaxy_body('APRG_TickDecay')
        self.assertIn('APRG_IsWorkerTypeForDeath(UnitGetType(u))',tick)
        self.assertLess(tick.index('APRG_IsWorkerTypeForDeath(UnitGetType(u))'),tick.index('APRG_FindDecaySlot(u, now)'))
        worker=galaxy_body('APRG_IsWorkerTypeForDeath','bool')
        for name in ('SCV','Drone','Probe','MULE','Worker'):
            self.assertIn(name,worker)

    def test_fire_squad_prefers_actual_ap_purifier_colossus(self):
        body=galaxy_body('APRG_GiveFireSquadIfReady')
        self.assertIn('"AP_ColossusPurifier"',body)
        self.assertLess(body.index('"AP_ColossusPurifier"'),body.index('"ColossusPurifier"'))
        self.assertNotIn('"Colossus"',body)
        self.assertNotIn('"PurifierColossus"',body)

    def test_sniper_thor_safe_spawn_and_defense_attack(self):
        spawn=galaxy_body('APRG_FindSniperThorPoint','point')
        self.assertIn('APRG_PointNearPlayerOrAlliedBuilding(p, player, 20.0)',spawn)
        body=galaxy_body('APRG_TickSniperThorDefenseAttack')
        self.assertIn('APRG_MISSION_FLAG_TIMED_DEFENSE',body)
        self.assertIn('APRG_TimeSinceMacroBase(now) < 960.0',body)
        self.assertIn('APRG_OrderAttackPlayer(g_aprgSniperThor, player)',body)
        self.assertIn('g_aprgSniperThorDefenseAttackOrdered = true',body)
        self.assertIn('APRG_TickSniperThorDefenseAttack(player, now);',GALAXY)

    def test_inventory_uses_same_canonical_art_as_shop(self):
        self.assertIn('"canonical_name": item_name',CLIENT)
        self.assertIn('"canonical_name": str(slot["id"])',CLIENT)
        self.assertIn('canonical=row.get(\'canonical_name\',row[\'name\'])',UI)
        self.assertIn("shop_icon_texture(entry.get('canonical_name',entry['id'])",UI)
        tree=ast.parse(UI)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='local_icon')
        env={'Path':Path, 'ASSETS':ASSETS,
             'DOCS_ICON_MAP':json.loads((ROOT/'Payload/slay_docs_icon_overrides.json').read_text()),
             'ICON_MAP':json.loads((ROOT/'Payload/slay_ui_icons.json').read_text()),
             '_queue_documented_icon':lambda _:None}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<icon-test>','exec'),env)
        local_icon=env['local_icon']
        # A general-upgrade non-BTN icon must survive the inventory:idx synthetic identifier.
        for name in ('Additional Starting Minerals','Progressive Terran Weapon Upgrade','Additional Starting Vespene'):
            self.assertTrue(Path(local_icon(name)).is_file(),name)
            self.assertEqual(local_icon(name),local_icon(name,local_icon(name),'General Upgrades'))
        mineral=ASSETS/'icons'/'icon-mineral-nobg.png'
        self.assertEqual(local_icon('inventory:12',str(mineral),'General Upgrades'),str(mineral))

    def test_original_catalog_descriptions_never_edit_for_mechanics(self):
        with (ROOT/'Payload/BOON_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
            boons={r['Boon Title']:r['Description'] for r in csv.DictReader(f)}
        with (ROOT/'Payload/POTION_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:
            potions={r['Name']:r['Effect Description'] for r in csv.DictReader(f)}
        self.assertEqual(boons['Energized Queens'],'Your swarm queens and brood queens have 10x energy regeneration')
        self.assertEqual(potions['Hyperion in a Bottle'],'Spawn the WoL hyperion, but you cannot control it')
        self.assertIn('"Hyperion in a Bottle", 4, \'Spawn the WoL hyperion, but you cannot control it\'',CLIENT)


if __name__=='__main__':unittest.main()
