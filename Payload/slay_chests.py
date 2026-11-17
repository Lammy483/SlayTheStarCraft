"""Durable, fully disclosed Standard-mode chest offers and grants.

Offers are rolled ONCE when the chest is entered, written to the run-state,
then read verbatim for every popup redraw/reconnect. Claiming is idempotent.
Nothing is rolled after an option is selected.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import random
from typing import Any

CHEST_TYPES = (
    'Terran Unit Pack', 'Zerg Unit Pack', 'Protoss Unit Pack', 'Unit Unlocks',
    'Mercenaries', 'Unit Upgrades', 'Eco', 'Spear of Adun', 'Kerrigan',
    'Boon', 'Credits', 'Unit Specialization', 'Consumables',
)


def _slay():
    from . import slay_the_starcraft
    return slay_the_starcraft


def _rng(ctx: Any, node_id: int) -> random.Random:
    raw = f'{ctx.slay_config.get("run_seed", 0)}:chest:{int(node_id)}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big'))


def _price(slay, ctx, item: str) -> int:
    try:
        return int(slay._price_for_item_before_sale(item, ctx))
    except (KeyError, TypeError, ValueError):
        return 999999


def _item_pool(slay, ctx):
    table = slay._item_table()
    counts = slay._logic_owned_item_counts(ctx)
    purchases = slay.state(ctx).get('purchases', {})
    names = sorted(set(table) | set(slay.MERCENARY_CUSTOM_UPGRADE_ITEMS)
                   | set(slay.MERCENARY_GENERAL_UPGRADE_ITEMS)
                   | set(slay.SPEAR_CUSTOM_ITEMS) | set(slay.KERRIGAN_CUSTOM_ITEMS))
    selected_races = {str(x).casefold() for x in ctx.slay_config.get('races', ())}
    pool = []
    for name in names:
        data = table.get(name)
        if data is not None and getattr(data, 'code', None) is None:
            continue
        if data is not None and (slay._is_deprecated_item(name, data)
                                 or slay._is_nova_campaign_item(name, data)
                                 or slay._is_royal_guard_item(name, data, table)):
            continue
        if int(counts.get(name, 0)) or int(purchases.get(name, 0)):
            continue  # No previously owned item, even if it is stackable.
        if data is not None and name not in slay.SPEAR_OF_ADUN_ITEMS and name not in slay.KERRIGAN_ABILITY_ITEMS:
            race = slay._item_race_key(name, data)
            special = (slay._is_spear_item(name, data) or slay._is_kerrigan_item(name, data)
                       or slay._is_mercenary_unit(name, data)
                       or slay._mercenary_contract_for_item(name, data) is not None)
            if not special and race and race not in selected_races and race not in {'any', 'any race'}:
                continue
        price = _price(slay, ctx, name)
        if 1 <= price <= 900:
            pool.append((name, price))
    return pool, table


def _pack(rng: random.Random, items: list[tuple[str, int]], low: int = 700,
          high: int = 900, *, min_items: int = 1, max_items: int = 12,
          fixed: tuple[tuple[str, int], ...] = ()) -> list[tuple[str, int]] | None:
    """Bounded randomized subset sum: return exact displayed items, no reroll."""
    initial = sum(price for _, price in fixed)
    if initial > high:
        return None
    options = list({name: price for name, price in items if name not in dict(fixed)}.items())
    rng.shuffle(options)
    options = options[:130]
    # DP records actual names rather than just the total value. Randomized
    # ordering makes equally priced rewards vary deterministically by seed.
    best: dict[tuple[int, int], tuple[tuple[str, int], ...]] = {(initial, len(fixed)): fixed}
    for name, price in options:
        for (total, count), choice in list(best.items()):
            new_total = total + price
            if new_total > high or count >= max_items:
                continue
            key = (new_total, count + 1)
            if key not in best:
                best[key] = choice + ((name, price),)
    valid = [(key, items) for key, items in best.items()
             if low <= key[0] <= high and min_items <= key[1] <= max_items]
    if not valid:
        return None
    valid.sort(key=lambda pair: (abs(pair[0][0] - 800), abs(pair[0][1] - 5)))
    # Allow diverse rewards instead of always returning the same 800-credit set.
    return list(rng.choice(valid[:min(35, len(valid))])[1])


def _option(name: str, items: list[tuple[str, int]], *, credits: int = 0,
            potions: list[str] | None = None, note: str = '') -> dict[str, Any]:
    names = Counter(n for n, _ in items)
    line_items = [{'name': name, 'count': qty} for name, qty in sorted(names.items())]
    # Potion rewards include their own value as well as the top-up credits.
    potion_value = 700 - int(credits) if potions else 0
    return {'name': name, 'items': line_items, 'credits': int(credits),
            'potions': list(potions or ()),
            'value': sum(price for _, price in items) + int(credits) + potion_value,
            'note': note}


def _kerrigan_bundle(rng: random.Random, items: list[tuple[str, int]],
                     low: int, high: int, is_level) -> list[tuple[str, int]] | None:
    """Roll a Kerrigan bundle containing zero or one *type* of level reward."""
    nonlevels = [(name, price) for name, price in items if not is_level(name)]
    levels = [(name, price) for name, price in items if is_level(name)]
    bundles = []
    upgrades_only = _pack(rng, nonlevels, low, high)
    if upgrades_only:
        bundles.append(upgrades_only)
    rng.shuffle(levels)
    for level in levels[:18]:
        with_one_level = _pack(rng, nonlevels, low, high, fixed=(level,))
        if with_one_level:
            bundles.append(with_one_level)
    return rng.choice(bundles) if bundles else None


def _candidates(ctx: Any, rng: random.Random) -> list[dict[str, Any]]:
    slay = _slay()
    pool, table = _item_pool(slay, ctx)
    categories = {name: slay.shop_category_for_item(name, ctx) for name, _ in pool}
    units: dict[str, list[tuple[str, int]]] = defaultdict(list)
    mercs = []
    upgrades: dict[str, list[tuple[str, int]]] = defaultdict(list)
    eco = []
    spear = []
    kerrigan = []
    for name, price in pool:
        data = table.get(name)
        race = slay._item_race_key(name, data)
        typ = str(getattr(getattr(data, 'type', None), 'display_name', '')).casefold()
        category = categories[name]
        if name in slay.SPEAR_CUSTOM_ITEMS or (data and slay._is_spear_item(name, data)):
            spear.append((name, price))
        elif name in slay.KERRIGAN_CUSTOM_ITEMS or (data and slay._is_kerrigan_item(name, data)):
            kerrigan.append((name, price))
        elif category == 'Mercenaries' or slay._is_mercenary_unit(name, data):
            mercs.append((name, price))
        elif category == 'General Upgrades' and slay._is_general_upgrade_item(name):
            eco.append((name, price))
        elif data and slay._is_unit_or_morph_unlock_type(typ) and not slay._is_mercenary_unit(name, data):
            units[race].append((name, price))
        elif data and slay._is_unit_specific_upgrade(name, table):
            for parent in slay._unit_specific_parent_names(name, table):
                if parent in table and slay._is_unit_or_morph_unlock_type(
                        str(getattr(getattr(table[parent], 'type', None), 'display_name', ''))):
                    upgrades[parent].append((name, price))
    options: list[dict[str, Any]] = []
    for race in ('terran', 'zerg', 'protoss'):
        picked = _pack(rng, units[race])
        if picked:
            options.append(_option(f'{race.title()} Unit Pack', picked,
                                   credits=rng.choice((100, 150, 200))))
    picked = _pack(rng, [v for vals in units.values() for v in vals])
    if picked:
        options.append(_option('Unit Unlocks', picked,
                               credits=rng.choice((100, 150, 200))))
    picked = _pack(rng, mercs)
    if picked:
        options.append(_option('Mercenaries', picked,
                               credits=rng.choice((100, 150, 200))))
    # Exactly four different unit parents, with 2-4 *distinct* upgrades each.
    # Don't bias toward owned units and don't grant upgrades already owned.
    valid_parents = [p for p, u in upgrades.items() if len(set(name for name, _ in u)) >= 2]
    rng.shuffle(valid_parents)
    for _ in range(70):
        if len(valid_parents) < 4:
            break
        parents = rng.sample(valid_parents, 4)
        group_items = []
        used = set()
        for p in parents:
            choices = [(n, v) for n, v in upgrades[p] if n not in used]
            if len(choices) < 2:
                break
            rng.shuffle(choices)
            for n, v in choices[:rng.randint(2, min(4, len(choices)))]:
                group_items.append((n, v));used.add(n)
        if len(group_items) < 8:
            continue
        total = sum(v for _, v in group_items)
        if 700 <= total <= 900:
            options.append(_option('Unit Upgrades', group_items,
                                   credits=rng.choice((100, 150, 200)),
                                   note='Upgrades for ' + ', '.join(parents)))
            break
    if len(eco) >= 1:
        # Eight independently selected general upgrades, with duplicates
        # allowed WITHIN the chest but never items that were owned before it.
        eco_items = [rng.choice(eco) for _ in range(8)]
        options.append(_option('Eco', eco_items,
                               note='Eight general upgrades (duplicates possible)'))
    for kind, items, unlock, addon_range in (
        ('Spear of Adun', spear, slay.SPEAR_UNLOCK, (200, 400)),
        ('Kerrigan', kerrigan, slay.KERRIGAN_UNLOCK, (300, 500)),
    ):
        owned = slay._progression_owned(ctx, unlock)
        low, high = 700, 900
        if not owned:
            cost = _price(slay, ctx, unlock)
            lo, hi = addon_range
            low, high = max(lo, 700-cost), min(hi, 900-cost)
        if kind == 'Kerrigan':
            pick = _kerrigan_bundle(
                rng, items, low, high,
                lambda name: slay._is_kerrigan_level_item(name, table.get(name)))
        else:
            pick = _pack(rng, items, low, high)
        if pick:
            if not owned:
                pick.insert(0, (unlock, cost))
            options.append(_option(kind, pick))
    # Only concrete, non-random-boon permanent effects (no hidden rolls).
    boon_items = []
    for effect in sorted(slay.EFFECT_BANK_BITS):
        if not effect.startswith('boon_'):
            continue
        kind = effect[5:]
        if kind in slay.REPEATABLE_BOON_KINDS or kind in {
                'reroll', 'reroll_shop', 'random_blessing', 'saving_grace',
                'upgrade_pack', 'shop_expansion', 'risky_investment', 'golden_goose'}:
            continue
        item = slay._boon_id(kind)
        if effect in slay.state(ctx).get('permanent_boons', ()) or \
           item in slay.state(ctx).get('boon_purchases', {}):
            continue
        cost = _price(slay, ctx, item)
        if (700 <= cost <= 1000 and slay._parse_boon(item)[0] == kind
                and slay.can_buy_shop_item(ctx, item)):
            boon_items.append((item, cost))
    if boon_items:
        choice = rng.choice(boon_items)
        options.append(_option('Boon', [choice]))
    options.append(_option('Credits', [], credits=rng.randrange(400, 701, 50)))
    # Named unit specializations require a matching unlock and matching
    # item/boon upgrades. Include the unlock if the player lacks it.
    owned = slay._logic_owned_item_counts(ctx)
    candidates = [(p, us) for p, us in upgrades.items() if len(us) >= 3]
    rng.shuffle(candidates)
    for parent, parent_upgrades in candidates[:50]:
        if parent not in table:
            continue
        base = []
        if not owned.get(parent):
            unlock_cost = _price(slay, ctx, parent)
            if unlock_cost > 400:
                continue
            base = [(parent, unlock_cost)]
        unit_boons = [(n, v) for n, v in boon_items if
                      parent.casefold() in slay.shop_entry_description(n).casefold() or
                      parent.casefold() in slay.shop_entry_display_name(n).casefold()]
        pick = _pack(rng, parent_upgrades + unit_boons, fixed=tuple(base))
        if pick:
            options.append(_option(parent + ' Specialization', pick))
            break
    if not slay.potion_inventory(ctx):
        pots = [(pid, int(info.get('price', 0)))
                for pid, info in slay.POTION_CATALOG.items()
                if not pid.startswith(slay.POTION_VARIANT_PREFIX)
                and slay._potion_unlock_eligible(ctx, pid) and int(info.get('price', 0)) > 0]
        pairs = [(a, b, pa+pb) for a, pa in pots for b, pb in pots
                 if a != b and 300 <= pa + pb <= 600]
        if pairs:
            a, b, cost = rng.choice(pairs)
            # Resolve random-unit potion now, before presenting the choice.
            def resolved(pid):
                if pid == slay.POTION_PREFIX+'19':
                    return slay.POTION_VARIANT_PREFIX + str(rng.randint(1, len(slay.POTION_RANDOM_UNITS)))
                return pid
            options.append(_option('Consumables', [], credits=700-cost,
                                   potions=[resolved(a), resolved(b)],
                                   note=''))
    return options


def preview(ctx: Any, node_id: int) -> list[dict[str, Any]]:
    slay = _slay()
    state = slay.state(ctx)
    key = str(int(node_id))
    saved = state.setdefault('chest_offers', {}).get(key)
    if isinstance(saved, list) and len(saved) == 3:
        return saved
    rng = _rng(ctx, node_id)
    pool = _candidates(ctx, rng)
    rng.shuffle(pool)
    # Distinct chest reward types first; fallback credits only when the active
    # item pool has too few eligible non-owned options.
    choices = pool[:3]
    while len(choices) < 3:
        value = rng.randrange(400, 701, 50)
        choices.append(_option('Credits', [], credits=value))
    state['chest_offers'][key] = choices
    slay._persist_state(ctx)
    return choices


def display(ctx: Any, node_id: int) -> list[dict[str, Any]]:
    slay = _slay()
    results = []
    for option in preview(ctx, node_id):
        lines = []
        for item in option.get('items', ()):
            name = str(item['name'])
            display = slay.shop_entry_display_name(name)
            amount = int(item['count'])
            lines.append(f'• {amount} × {display}' if amount > 1 else f'• {display}')
        for pid in option.get('potions', ()):
            p = slay.POTION_CATALOG.get(pid, {})
            lines.append('• ' + str(p.get('name', pid)))
            desc = str(p.get('description', '')).strip()
            if desc:
                lines.append('    ' + desc)
        if int(option.get('credits', 0)):
            lines.append(f'• {option["credits"]} credits')
        results.append(dict(option, details='\n'.join(lines),
                            note='' if option.get('name') == 'Consumables' else option.get('note', '')))
    return results


def claim(ctx: Any, node_id: int, index: int) -> tuple[bool, str]:
    """Apply a fully saved option exactly once. No post-selection RNG."""
    slay = _slay()
    s = slay.state(ctx)
    key = str(int(node_id))
    if key in s.get('chest_claims', {}):
        return False, 'This chest has already been opened.'
    options = s.get('chest_offers', {}).get(key)
    if not isinstance(options, list) or len(options) != 3 or not 0 <= index < 3:
        return False, 'This chest has not been previewed.'
    option = options[index]
    potions = list(option.get('potions', ()))
    slots = slay.potion_inventory(ctx)
    if potions and slots:
        return False, 'Consumables require both consumable slots to be empty.'
    item_awards = dict(s.get('event_awarded_items', {}))
    purchases = dict(s.get('purchases', {}))
    boon_effects = list(s.get('permanent_boons', ()))
    boon_counts = dict(s.get('boon_purchases', {}))
    table = slay._item_table()
    for row in option.get('items', ()):
        name, count = str(row['name']), int(row['count'])
        if count < 1:
            return False, 'Chest item count invalid.'
        kind = slay._parse_boon(name)[0]
        if kind:
            # Chest boon choices are never random/consumable shop actions.
            effect = 'boon_' + kind
            if effect not in slay.EFFECT_BANK_BITS:
                return False, 'Chest boon is not a supported permanent effect.'
            if name in boon_counts or effect in boon_effects:
                return False, 'Chest boon is already owned.'
            boon_effects.append(effect)
            boon_counts[name] = 1
        elif name in table:
            item_awards[name] = int(item_awards.get(name, 0)) + count
        elif name == slay.SPEAR_UNLOCK or name == slay.KERRIGAN_UNLOCK or \
             name in slay.SPEAR_CUSTOM_ITEMS or name in slay.KERRIGAN_CUSTOM_ITEMS or \
             name in slay.MERCENARY_CUSTOM_UPGRADE_ITEMS or name in slay.MERCENARY_GENERAL_UPGRADE_ITEMS:
            purchases[name] = int(purchases.get(name, 0)) + count
        else:
            return False, 'Unknown chest item: ' + name
    if purchases.get(slay.SPEAR_UNLOCK, 0):
        purchases[slay.SPEAR_BASE_PYLON_ITEM] = max(1, int(purchases.get(slay.SPEAR_BASE_PYLON_ITEM, 0)))
    s['event_awarded_items'] = item_awards
    s['purchases'] = purchases
    s['permanent_boons'] = list(dict.fromkeys(boon_effects))
    s['boon_purchases'] = boon_counts
    if potions:
        serial = max([int(s.get('potion_serial', 0))] +
                     [int(x.get('serial', 0)) for x in slots])
        fresh = []
        for potion in potions:
            serial += 1
            fresh.append({'id': potion, 'serial': serial})
        s['potion_serial'] = serial
        s['potion_inventory'] = slots + fresh
    s['event_credit_bonus'] = int(s.get('event_credit_bonus', 0)) + int(option.get('credits', 0))
    s.setdefault('chest_claims', {})[key] = index
    s.setdefault('special_resolved', {})[key] = True
    slay._persist_state(ctx)
    slay._request_live_item_refresh(ctx)
    return True, str(option.get('name', 'Chest')) + ' claimed.'
