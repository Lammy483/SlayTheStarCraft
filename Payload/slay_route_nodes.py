"""Standard-mode event/chest route augmentation.

Dev25 uses branch-local encounter nodes: every possible route receives the
same reward count, but a chest can occur on different map rows depending on
which combat branch the player chooses. No Archipelago mission IDs change.

A paired encounter uses the SAME intervening combat as its identity anchor:
  before combat X: left branch chest / right branch event
  after  combat X: left branch event / right branch chest
Thus even when earlier/later routes merge, both have exactly one chest and
one event; all native combat-to-combat branching is retained.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

VIRTUAL_BASE = -990000
DEV25_BASE = -259000000


def enabled(config: Mapping[str, Any]) -> bool:
    return (str(config.get('game_mode', 'adventure')) == 'adventure'
            and bool(config.get('node_encounters', False)))


def _legacy_schedule(combats: int, *, events: bool, chests: bool) -> dict[int, str]:
    """Preserve existing Dev24 saved routes, including their synthetic IDs."""
    n = max(1, int(combats))
    candidates = list(range(1, max(1, n - 2)))
    if not candidates:
        return {}
    chest_count = max(1, round(n / 12)) if chests and n >= 8 else 0
    chest_count = min(chest_count, len([i for i in candidates if i >= 3]))
    chest_slots: set[int] = set()
    available_chests = [i for i in candidates if i >= 3]
    if chest_count:
        for index in range(chest_count):
            target = int(round((index + 1) * (n - 3) / (chest_count + 1)))
            chosen = min((x for x in available_chests if x not in chest_slots),
                         key=lambda x: (abs(x - target), x))
            chest_slots.add(chosen)
    remaining = [i for i in candidates if i not in chest_slots]
    event_count = min(len(remaining), round(n * 0.58)) if events else 0
    event_slots: set[int] = set()
    if event_count:
        for k in range(event_count):
            target = remaining[min(len(remaining) - 1,
                                   int((k + 0.5) * len(remaining) / event_count))]
            chosen = min((x for x in remaining if x not in event_slots),
                         key=lambda x: (abs(x - target), x))
            event_slots.add(chosen)
    return {i: ('chest' if i in chest_slots else 'event')
            for i in sorted(chest_slots | event_slots)}


def _stages(combats: int, *, events: bool, chests: bool) -> list[tuple[int, str, int]]:
    """(after_completed_combats, stage_kind, pair_index).

    Pairs occupy adjacent combat gaps, allowing the same intervening combat
    node to guarantee one chest even when its incoming/outgoing paths branch.
    """
    n = max(1, int(combats))
    available = max(0, n - 3)
    if not available:
        return []
    events_count = (available + 1) // 2 if events else 0
    chest_count = (available + 4) // 5 if chests and n >= 6 else 0
    # No short run can violate the last-three-combats or first-three-floors
    # rules in order to force a chest into an impossible layout.
    while events_count + chest_count > available:
        if chest_count:
            chest_count -= 1
        elif events_count:
            events_count -= 1
        else:
            break
    pairs = min(events_count, chest_count)
    singles = events_count - pairs
    chest_singles = chest_count - pairs
    blocks: list[tuple[str, int]] = []
    for i in range(max(singles, pairs)):
        if i < singles:
            blocks.append(('event', -1))
        if i < pairs:
            blocks.append(('pair', i))
    blocks.extend(('chest', -1) for _ in range(chest_singles))
    total = events_count + chest_count
    if not total:
        return []
    # Prefer to start after three combats; earlier single events are allowed
    # when small campaigns cannot fit otherwise.
    start = max(1, min(3, available - total + 1))
    spare = available - (start - 1) - total
    result: list[tuple[int, str, int]] = []
    boundary = start
    for index, (kind, pair_id) in enumerate(blocks):
        if kind == 'pair':
            result.append((boundary, 'pair_before', pair_id))
            result.append((boundary + 1, 'pair_after', pair_id))
            boundary += 2
        else:
            result.append((boundary, kind, -1))
            boundary += 1
        # Spread optional gaps between blocks, never INSIDE a pair.
        if index < len(blocks) - 1 and spare:
            remaining_blocks = len(blocks) - 1 - index
            if spare >= remaining_blocks:
                boundary += 1
                spare -= 1
    return result


def schedule(combats: int, *, events: bool = True, chests: bool = True) -> dict[int, str]:
    """A representative route: counts are exact but chest rows can vary."""
    return {after: ('chest' if kind in ('chest', 'pair_before') else 'event')
            for after, kind, _ in _stages(combats, events=events, chests=chests)}


def virtual_id(after_combats: int) -> int:
    return VIRTUAL_BASE - int(after_combats)


def _blank(graph: Mapping[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(mid): dict(data, next=list(data.get('next', [])),
                           node_type='combat', combat_layer=int(data.get('layer', 0)))
            for mid, data in graph.items()}


def _augment_legacy(out: dict[int, dict[str, Any]], config: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """Old saves keep the Dev24 routing and stable negative node IDs."""
    if not out:
        return out
    combats = max(int(data['combat_layer']) for data in out.values()) + 1
    placements = _legacy_schedule(combats, events=bool(config.get('events', False)),
                                  chests=bool(config.get('chests', True)))
    by_layer: dict[int, list[int]] = defaultdict(list)
    for mid, data in out.items():
        by_layer[int(data['combat_layer'])].append(mid)
    for after, kind in placements.items():
        parents = by_layer.get(after-1, [])
        children = by_layer.get(after, [])
        if not parents or not children:
            continue
        mid = virtual_id(after)
        downstream = sorted({dest for parent in parents
                             for dest in out[parent]['next'] if dest in children})
        if not downstream:
            continue
        for parent in parents:
            out[parent]['next'] = [mid]
        out[mid] = {
            'mission_id': mid,
            'mission_name': 'Treasure Chest' if kind == 'chest' else 'Event',
            'node_type': kind, 'combat_layer': after,
            'layer': after, 'lane': 1.5, 'next': downstream,
            'after_combats': after, 'credit_reward': 0,
            'mutators': [], 'blessings': [],
        }
    extra = 0
    for layer in range(combats):
        for mid in by_layer.get(layer, []):
            out[mid]['map_layer'] = layer + extra
        after = layer + 1
        sid = virtual_id(after)
        if sid in out:
            extra += 1
            out[sid]['map_layer'] = layer + extra
    return out


def augment(graph: Mapping[int, dict[str, Any]], config: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    out = _blank(graph)
    if not enabled(config) or not out:
        return out
    if int(config.get('node_map_version', 24)) < 25:
        return _augment_legacy(out, config)

    combats = max(int(data['combat_layer']) for data in out.values()) + 1
    stages = _stages(combats, events=bool(config.get('events', False)),
                     chests=bool(config.get('chests', True)))
    by_layer: dict[int, list[int]] = defaultdict(list)
    for mid, data in out.items():
        by_layer[int(data['combat_layer'])].append(mid)
    for mids in by_layer.values():
        mids.sort(key=lambda mid: (float(out[mid].get('lane', 0)), mid))
    id_counter = 0
    pair_anchors: dict[int, dict[int, int]] = {}

    def create(kind: str, after: int, lane: float, downstream: list[int]) -> int:
        nonlocal id_counter
        id_counter += 1
        mid = DEV25_BASE - id_counter
        out[mid] = {
            'mission_id': mid,
            'mission_name': 'Treasure Chest' if kind == 'chest' else 'Event',
            'node_type': kind, 'combat_layer': after, 'layer': after,
            'lane': lane, 'next': list(downstream),
            'after_combats': after, 'credit_reward': 0,
            'mutators': [], 'blessings': [],
        }
        return mid

    for after, stage, pair_id in stages:
        parents = by_layer.get(after - 1, [])
        children = by_layer.get(after, [])
        if not parents or not children:
            continue
        if stage == 'pair_before':
            # Decide the reward using the DESTINATION combat node. The same
            # combat determines the opposite reward at the next checkpoint.
            anchors = {mid: index % 2 for index, mid in enumerate(children)}
            pair_anchors[pair_id] = anchors
            for child in children:
                kind = 'chest' if anchors[child] == 0 else 'event'
                sid = create(kind, after, float(out[child].get('lane', 0)), [child])
                for parent in parents:
                    out[parent]['next'] = [sid if dest == child else dest
                                           for dest in out[parent]['next']]
        else:
            anchors = pair_anchors.get(pair_id, {}) if stage == 'pair_after' else {}
            for parent in parents:
                downstream = list(out[parent]['next'])
                if not downstream:
                    continue
                if stage == 'pair_after':
                    kind = 'event' if anchors.get(parent, 0) == 0 else 'chest'
                else:
                    kind = stage
                sid = create(kind, after, float(out[parent].get('lane', 0)), downstream)
                out[parent]['next'] = [sid]

    stage_boundaries = [after for after, _, _ in stages]
    for mid, data in out.items():
        if data['node_type'] == 'combat':
            layer = int(data['combat_layer'])
            data['map_layer'] = layer + sum(after <= layer for after in stage_boundaries)
        else:
            after = int(data['after_combats'])
            data['map_layer'] = after + stage_boundaries.index(after)
    return out


def path_special_counts(graph: Mapping[int, dict[str, Any]]) -> set[tuple[int, int]]:
    """Enumerate distinct (chest, event) suffix counts without path explosion."""
    incoming = {mid: 0 for mid in graph}
    for data in graph.values():
        for next_id in data.get('next', ()):
            if next_id in incoming:
                incoming[next_id] += 1
    starts = [mid for mid, count in incoming.items() if count == 0]
    memo: dict[int, set[tuple[int, int]]] = {}
    active: set[int] = set()
    def suffix(mid: int) -> set[tuple[int, int]]:
        if mid in memo:
            return memo[mid]
        if mid in active:
            raise ValueError('Route contains a cycle')
        active.add(mid)
        node = graph[mid]
        children = [x for x in node.get('next', ()) if x in graph]
        downstream = set().union(*(suffix(x) for x in children)) if children else {(0, 0)}
        chest = int(node.get('node_type') == 'chest')
        event = int(node.get('node_type') == 'event')
        result = {(c + chest, e + event) for c, e in downstream}
        active.remove(mid)
        memo[mid] = result
        return result
    return set().union(*(suffix(mid) for mid in starts)) if starts else set()
