"""r34 regressions for F2 army selection and silencing consumable-use chatter."""
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[1]
GAL = (BASE / 'Payload' / 'APRogue.galaxy').read_text(encoding='utf-8')


def func(name):
    match = re.search(r'^(?:void|bool)\s+' + re.escape(name) + r'\([^)]*\)\s*\{', GAL, re.M)
    if not match:
        raise AssertionError('Missing Galaxy function ' + name)
    brace = GAL.index('{', match.start())
    depth = 0
    for i in range(brace, len(GAL)):
        if GAL[i] == '{':
            depth += 1
        elif GAL[i] == '}':
            depth -= 1
            if depth == 0:
                return GAL[brace:i+1]
    raise AssertionError('Unbalanced braces in ' + name)


class R34Regressions(unittest.TestCase):
    def test_both_leviathan_types_army_select_at_base_and_player_catalog(self):
        f = func('APRG_EnableLeviathanArmySelection')
        for unit_type in ('"Leviathan"', '"LeviathanHOTS"'):
            self.assertIn(unit_type, f)
        self.assertIn('CatalogEntryIsValid(c_gameCatalogUnit, leviathanType)', f)
        for scope in ('c_playerAny', 'player'):
            self.assertIn('"FlagArray[ArmySelect]", ' + scope + ', "1"', f)

    def test_flag_applied_before_spawn_and_on_boon_and_bottle(self):
        self.assertIn('APRG_EnableLeviathanArmySelection(player)', func('APRG_ActivateEffects'))
        self.assertIn('APRG_EnableLeviathanArmySelection(player)', func('APRG_NormalizeLeviathanBoon'))
        self.assertIn('APRG_NormalizeLeviathanBoon(replacement, player)', func('APRG_NewBoonTrain_Func'))
        potion = func('APRG_PotionActivate')
        self.assertIn('if (kind == 4)', potion)
        self.assertIn('APRG_NormalizeLeviathanBoon(u, player)', potion)

    def test_no_consumable_use_messages_or_obsolete_notice_dialog(self):
        for old in ('APRG_ConsumableNotice(', 'g_aprgConsumableNoticeUntil',
                    'g_aprgConsumableNoticeDialog', '[Slay] Used ',
                    '[Slay] Choose a target for ', '[Slay] Select a valid unit.',
                    '[Slay] Invalid target.', '[Slay] Native consumable targeting unavailable.',
                    '[Slay] Test Consumable consumed'):
            self.assertNotIn(old, GAL)
        self.assertNotIn('UIDisplayMessage(', func('APRG_PotionClick_Func'))
        self.assertNotIn('UIDisplayMessage(', func('APRG_PotionNativeOrder_Func'))
        self.assertNotIn('UIDisplayMessage(', func('APRG_TestPotionClick_Func'))

    def test_target_cursor_and_consumption_still_function(self):
        click = func('APRG_PotionClick_Func')
        ordered = func('APRG_PotionNativeOrder_Func')
        cancel = func('APRG_PotionCancel_Func')
        self.assertIn('APRG_PotionArmNativeTarget(player)', click)
        self.assertIn('g_aprgPotionPendingSlot = slot', click)
        self.assertIn('APRG_PotionConsume(player, slot)', click)
        self.assertIn('APRG_PotionConsume(player, slot)', ordered)
        self.assertIn('APRG_PotionArmNativeTarget(player)', ordered)
        self.assertIn('APRG_PotionEndNativeTarget', cancel)
        self.assertIn('[TARGETING]', func('APRG_PotionRefreshButtons'))


if __name__ == '__main__':
    unittest.main()
