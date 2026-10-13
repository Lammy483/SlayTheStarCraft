"""Dev13: player-owned Odin loses nuclear abilities; blessing text stays distinct."""
import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT/'Payload'/'APRogue.galaxy').read_text(encoding='utf-8')


def func(name):
    m=re.search(r'(?m)^(?:void|bool|point|fixed|unit|int)\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{', SCRIPT)
    if not m: raise AssertionError('Function missing: '+name)
    start=m.end()-1; depth=0
    for i in range(start,len(SCRIPT)):
        if SCRIPT[i]=='{':depth+=1
        elif SCRIPT[i]=='}':
            depth-=1
            if depth==0:return SCRIPT[start:i+1]
    raise AssertionError('Unclosed '+name)


class PlayerOdinDev13(unittest.TestCase):
    def test_blessing_description_exact_and_mutation_unmodified(self):
        with (ROOT/'Payload'/'EFFECT_CATALOG.csv').open(encoding='utf-8-sig',newline='') as handle:
            rows=list(csv.DictReader(handle))
        rows=[r for r in rows if r['Title']=='Odin']
        self.assertEqual(len(rows),2)
        texts={r['Mutation or Blessing']:r['Description'] for r in rows}
        self.assertEqual(texts['Blessing'],'You start with the odin')
        self.assertEqual(next(r for r in rows if r['Mutation or Blessing']=='Blessing')['Severity'],'4')
        self.assertIn('enemy base',texts['Mutation'])
        self.assertNotEqual(texts['Blessing'],texts['Mutation'])

    def test_removal_is_player_scoped_and_removes_button(self):
        body=func('APRG_RemovePlayerOdinNuclearStrike')
        self.assertIn('UnitGetOwner(odin) != player',body)
        self.assertIn('"Odin"',body)
        self.assertIn('"OdinNuclearStrike"',body)  # documented campaign ID
        self.assertIn('UnitAbilityRemove(odin, abilityType)',body)
        self.assertIn('UnitAbilityShow(odin, abilityType, false)',body)
        self.assertIn('"Nuke"',body)
        self.assertIn('"Nuclear"',body)
        self.assertIn('CatalogFieldValueSet(c_gameCatalogUnit, unitType',body)
        self.assertIn('player, "")',body)
        self.assertNotIn('TechTreeAbilityAllow',body)

    def test_blessing_and_bottle_immediately_disable_nukes(self):
        self.assertIn('APRG_RemovePlayerOdinNuclearStrike(UnitGroupUnitFromEnd(created, 1), player)',func('APRG_GiveOdinIfReady'))
        self.assertIn('if (kind == 3) { APRG_RemovePlayerOdinNuclearStrike(u, player); }',func('APRG_PotionActivate'))

    def test_live_watchdog_catches_added_variants_without_touching_enemy(self):
        tick=func('APRG_TickPlayerOdinNoNukes')
        self.assertIn('g_aprgNextPlayerOdinNukeCheckTime = now + 3.0',tick)
        self.assertIn('APRG_PlayerAllUnits(player)',tick)
        self.assertIn('APRG_RemovePlayerOdinNuclearStrike(candidate, player)',tick)
        self.assertIn('APRG_TickPlayerOdinNoNukes(player, now);',func('APRG_MainTick')) if 'APRG_MainTick' in SCRIPT else self.assertIn('APRG_TickPlayerOdinNoNukes(player, now);',SCRIPT)
        self.assertIn('g_aprgNextPlayerOdinNukeCheckTime = 0.0;',func('APRG_Load_Func'))
        enemy=func('APRG_TickDelayedOdin')
        self.assertNotIn('APRG_RemovePlayerOdinNuclearStrike',enemy)
        self.assertIn('OdinBarrage',enemy)

if __name__=='__main__':unittest.main()
