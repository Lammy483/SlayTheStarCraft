"""Fail-closed Crew Challenge mission/SC2 bridge primitives.

This is a *staging* bridge, not an SC2 implementation. Only the future trusted
SC2 adapter may submit verified deployment receipts or victory observations.
A unit with the right type but no receipt NEVER belongs to the Crew roster.

This module is intentionally independent of Kivy/Archipelago/SC2 so its
safety rules can be tested before a live mission is enabled.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Iterable, Mapping


def _session(ledger: Mapping[str, Any], mission_id: int) -> dict[str, Any]:
    active = ledger.get('active_mission')
    if not isinstance(active, dict) or active.get('mission_id') != int(mission_id):
        raise ValueError('Crew session is absent or belongs to a different mission')
    return active


def manifest(ledger: Mapping[str, Any], mission_id: int,
             catalog: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Construct a verified, per-copy list of possible deployments.

    Do not assume a bought unit is a valid SC2 spawn type. This bridge checks
    that the *particular* race/name/kind exists in the versioned cost catalog;
    otherwise it refuses to produce launch instructions. An unimplemented or
    unknown unit may be bought in a future catalog but MUST NOT be fabricated.
    """
    active = _session(ledger, mission_id)
    entries = {(str(e['race']), str(e['name']),
                'unit' if e['category'] == 'unit' or e['name'] in {'SCV', 'Drone', 'Probe'}
                else 'structure'): dict(e)
               for e in catalog if e.get('category') in {'unit', 'structure'}}
    by_id = {str(c['id']): c for c in ledger['copies']}
    result = []
    for copy_id in active.get('pending', []):
        c = by_id.get(copy_id)
        if c is None or c.get('status') != 'zone':
            raise ValueError(f'Crew pending copy missing or unavailable: {copy_id}')
        key = (str(c['race']), str(c['name']), str(c['kind']))
        entry = entries.get(key)
        if entry is None:
            raise ValueError(f'No verified Crew catalog entry for {key!r}')
        if float(c.get('supply', 0)) != float(entry.get('supply', 0)):
            raise ValueError(f'Crew copy supply disagrees with catalog: {copy_id}')
        result.append({'copy_id':copy_id, 'name':c['name'], 'race':c['race'],
                       'kind':c['kind'], 'supply':float(c['supply']),
                       'requires':str(entry.get('requires') or ''),
                       'status':'pending'})
    if len({e['copy_id'] for e in result}) != len(result):
        raise ValueError('duplicate Crew pending copy IDs')
    return result


def observe_receipt(ledger: dict[str, Any], mission_id: int, *, copy_id: str,
                    tag: int, observed_name: str, observed_owner: int,
                    player_id: int, provenance: str) -> bool:
    """Bind only *explicitly proven* roster deployments, never by type alone.

    `provenance` is a trusted SC2 adapter classification, NOT inferred from a
    unit merely appearing in the map. `crew-created` represents a spawn
    created specifically for this copy, while `crew-claimed-starting` is an
    explicitly selected native starting unit. Everything else is ignored.
    Repeated identical receipts are idempotent; conflicting receipts fail.
    """
    from .crew_challenge import bind_unit_tag

    active = _session(ledger, mission_id)
    if active.get('terminal_snapshot') is not None:
        raise RuntimeError('Cannot bind new Crew copies after terminal snapshot')
    if provenance not in {'crew-created', 'crew-claimed-starting'}:
        raise ValueError('unverified/non-Crew unit cannot enter the roster')
    if type(tag) is not int or tag <= 0 or int(player_id) <= 0 or observed_owner != player_id:
        raise ValueError('Crew deployment must be a valid player-owned SC2 unit')
    matching = [c for c in ledger['copies'] if c['id'] == copy_id]
    if len(matching) != 1 or matching[0]['name'] != observed_name:
        raise ValueError('Crew deployment receipt has wrong copy or unit type')
    assigned = active.setdefault('tags', {})
    if str(tag) in assigned:
        if assigned[str(tag)] == copy_id:
            return False  # same receipt delivered twice
        raise ValueError('SC2 tag claimed by another roster copy')
    if copy_id in active.get('deployed', []):
        raise ValueError('Roster copy already deployed under another SC2 tag')
    bind_unit_tag(ledger, copy_id, tag)
    return True


def record_observation(ledger: dict[str, Any], mission_id: int, *,
                       tag: int, observed_name: str, owner: int, player_id: int,
                       alive: bool, kills: int = 0) -> bool:
    """Record latest *authoritative* unit observation for an acknowledged tag.

    Kills are mission-local totals reported by an SC2 adapter, not synthetic
    estimates from damage. A dead unit cannot be resurrected by a later stale
    snapshot. The full victory snapshot is required before accounting.
    """
    active = _session(ledger, mission_id)
    if active.get('terminal_snapshot') is not None:
        raise RuntimeError('Cannot record post-terminal Crew observations')
    copy_id = active['tags'].get(str(tag))
    if copy_id is None:
        return False  # campaign freebies/unknown units must never be credited
    c = next((c for c in ledger['copies'] if c['id'] == copy_id), None)
    if c is None or c['name'] != observed_name or owner != player_id or player_id <= 0:
        raise ValueError('SC2 observation disagrees with bound Crew copy')
    if type(kills) is not int or kills < 0:
        raise ValueError('SC2 kill count must be a nonnegative integer')
    snapshots = active.setdefault('observations', {})
    old = snapshots.get(str(tag))
    if old is not None and not old['alive'] and alive:
        raise ValueError('stale observation attempted to revive dead roster copy')
    snapshots[str(tag)] = {'alive':bool(alive), 'kills':max(kills, old['kills'] if old else 0)}
    return True


def _verified_snapshot(active: Mapping[str, Any], ledger: Mapping[str, Any],
                       player_id: int, observations: Iterable[Any]) -> dict[int, Any]:
    """Validate a BotAI snapshot without claiming campaign or allied actors.

    Non-Crew tags are ignored; every bound tag present in this snapshot must
    have exactly the original native type and player owner. No guessed morph or
    owner substitution is allowed. This is not an authorization to claim units.
    """
    from .crew_sc2_adapter import CrewUnitObservation, NATIVE_TYPES
    if type(player_id) is not int or not 0 < player_id <= 16:
        raise ValueError('Invalid Crew snapshot player')
    copies={c['id']: c for c in ledger['copies']}
    bound=active.get('tags',{})
    seen={}
    for item in observations:
        if not isinstance(item,CrewUnitObservation):
            raise ValueError('Only live SC2 observations may be recorded')
        if item.tag in seen:
            raise ValueError('Duplicate SC2 observation tag')
        seen[item.tag]=item
        copy_id=bound.get(str(item.tag))
        if copy_id is None:continue
        copy_entry=copies.get(copy_id)
        if (copy_entry is None or item.owner!=player_id or
                item.native_type!=NATIVE_TYPES.get(copy_entry['name'])):
            raise ValueError('Crew tracked unit changed owner or native type')
    return seen


def record_live_snapshot(ledger: dict[str, Any], mission_id: int, *,
                         observations: Iterable[Any], player_id: int) -> int:
    """Record currently visible owned Crew units, never infer death from absence.

    In-progress BotAI observations might be missed due to disconnects or
    loading. Only the authoritative terminal snapshot may infer a lost unit.
    This does not record unverified kills or recruit campaign-granted units.
    """
    active=_session(ledger,mission_id)
    if active.get('terminal_snapshot') is not None:
        raise RuntimeError('Cannot update Crew after final roster snapshot')
    seen=_verified_snapshot(active,ledger,player_id,observations)
    copies={c['id']:c for c in ledger['copies']}
    updated=0
    for tag,copy_id in active.get('tags',{}).items():
        unit=seen.get(int(tag))
        if unit is None:continue
        previous=active.get('observations',{}).get(tag)
        if previous is not None and not previous['alive']:
            raise ValueError('Dead Crew tag reappeared in live observation')
        name=copies[copy_id]['name']
        if record_observation(ledger,mission_id,tag=int(tag),
                              observed_name=name,owner=unit.owner,
                              player_id=player_id,alive=True,
                              kills=int(previous['kills']) if previous else 0):
            updated+=1
    return updated


def record_terminal_snapshot(ledger: dict[str, Any], mission_id: int, *,
                             observations: Iterable[Any], player_id: int,
                             victory_confirmed: bool, complete: bool) -> dict[str,int]:
    """Finalize tag survival ONLY from a full, game-end owned-unit snapshot.

    Missing previously verified tags die; remaining tags return. This method
    must be called from an authoritative SC2 victory event and MUST NOT be
    called from periodic polling or last-known-alive data. Roster copies that
    never received a Galaxy receipt remain unspent in the deployment zone.
    """
    active=_session(ledger,mission_id)
    if not victory_confirmed or not complete:
        raise RuntimeError('Unconfirmed Crew victory or partial terminal snapshot')
    if active.get('terminal_snapshot') is not None:
        raise RuntimeError('Terminal Crew snapshot already recorded')
    auto=active.get('auto_transport')
    if (active.get('manual_pending') is not None or
            (auto is not None and (auto.get('pending') is not None or
                                      not auto.get('ended',False)))):
        raise RuntimeError('Crew deployment still in flight at victory')
    seen=_verified_snapshot(active,ledger,player_id,observations)
    copies={c['id']:c for c in ledger['copies']}
    # Validate the *entire* final view before modifying any tag.
    for tag in active.get('tags',{}):
        old=active.get('observations',{}).get(tag)
        if old is not None and not old['alive'] and int(tag) in seen:
            raise ValueError('Previously confirmed dead Crew unit reappeared')
    survived=0
    lost=0
    for tag,copy_id in active.get('tags',{}).items():
        unit=seen.get(int(tag))
        if unit is not None:survived+=1
        else:lost+=1
        old=active.get('observations',{}).get(tag)
        if unit is not None:
            record_observation(ledger,mission_id,tag=int(tag),
                observed_name=copies[copy_id]['name'],owner=player_id,
                player_id=player_id,alive=True,
                kills=int(old['kills']) if old else 0)
        else:
            # The tag was already verified at deployment; only a complete
            # end-of-mission view can prove its absence constitutes loss.
            active.setdefault('observations',{})[tag]={
                'alive':False,'kills':int(old['kills']) if old else 0}
    active['terminal_snapshot']={'player_id':player_id,
        'alive_tags':sorted(int(t) for t in active.get('tags',{}) if int(t) in seen),
        'bound_tags':len(active.get('tags',{}))}
    return {'survived':survived,'lost':lost}


def victory_readiness(ledger: Mapping[str, Any], mission_id: int) -> dict[str, Any]:
    active = _session(ledger, mission_id)
    # A clicked charge in flight cannot be declared unused or lost on victory.
    auto=active.get('auto_transport')
    unresolved = (active.get('manual_pending') is not None or
                  (auto is not None and (auto.get('pending') is not None or
                                         not auto.get('ended',False))))
    assigned = set(active.get('tags', {}))
    observed = set(active.get('observations', {}))
    missing = sorted(assigned-observed, key=int)
    terminal = active.get('terminal_snapshot')
    return {'mission_id':int(mission_id), 'pending':len(active.get('pending', [])),
            'deployed':len(assigned), 'observed':len(assigned & observed),
            'unobserved_tags':missing, 'ready':bool(terminal) and not missing and not unresolved,
            'terminal_recorded':bool(terminal), 'unresolved_click':unresolved}


def settle_confirmed_victory(ledger: dict[str, Any], mission_id: int,
                             *, victory_confirmed: bool,
                             terminal_snapshot_complete: bool) -> dict[str, int]:
    """Return ONLY proven live units, and only after AP-confirmed victory.

    Complete mission accounting must be atomic. On a disconnect or partial
    snapshot leave every copy and the active session untouched, for recovery.
    An initial unit with no explicit deployment receipt remains in zone.
    """
    from .crew_challenge import complete_mission

    active = _session(ledger, mission_id)
    if not victory_confirmed or not terminal_snapshot_complete:
        raise RuntimeError('Crew victory has not been safely confirmed')
    status = victory_readiness(ledger, mission_id)
    if not status['ready']:
        raise RuntimeError('Missing authoritative Crew terminal snapshot, incomplete tracked tags, or pending deployment: '+','.join(status['unobserved_tags']))
    survivors = {int(tag):obs['kills'] for tag, obs in active.get('observations', {}).items()
                 if obs['alive'] and tag in active['tags']}
    result = complete_mission(ledger, mission_id, survivors)
    # Durable replay marker: AP's LocationChecks message is sent *after* this
    # ledger commit. A process restart between these actions must not apply
    # losses/kills twice or prevent the same victory from being reported.
    key = str(int(mission_id))
    history = ledger.setdefault('settled_missions', {})
    if key in history:
        raise RuntimeError('Crew victory was already settled')
    history[key] = dict(result)
    return result


def copy_and_apply(ledger: Mapping[str, Any], fn, *args, **kwargs):
    """Convenience for state owners: never persist partially modified sessions."""
    updated = copy.deepcopy(ledger)
    value = fn(updated, *args, **kwargs)
    return updated, value
