"""Crew's future native worker-build entitlement ledger (no SC2 UI override yet).

Native worker buttons, rather than new buttons, will ultimately consume one
purchased structure copy per successful construction. This module is the
independent, fail-closed authorization and binding core. It does NOT activate
native construction: the current game-side production lock remains in place
until actual SC2 build-order/finished-unit receipts are implemented.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping
from .crew_sc2_adapter import NATIVE_TYPES, CrewUnitObservation
from .crew_challenge import WORKER_BY_RACE
from .crew_bridge import observe_receipt

@dataclass(frozen=True)
class BuildEntitlement:
    copy_id: str
    race: str
    name: str
    native_type: str


def eligible_builds(ledger: Mapping[str, Any], mission_id: int, worker_tag: int) -> tuple[BuildEntitlement,...]:
    """Only a verified purchased worker may spend unconsumed structure copies.

    A map-provided (unowned) SCV/Drone/Probe cannot consume the permanent Crew
    roster; no guessed worker ownership or name-only permissions are allowed.
    """
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        raise ValueError('No matching active Crew mission')
    if type(worker_tag) is not int or worker_tag<=0:
        raise ValueError('Invalid worker tag')
    worker_id=active.get('tags',{}).get(str(worker_tag))
    workers=[c for c in ledger.get('copies',()) if c.get('id')==worker_id and
             c.get('status')=='deployed' and c.get('name')==WORKER_BY_RACE.get(c.get('race'))]
    if len(workers)!=1:
        raise ValueError('Worker is not an individually acknowledged Crew member')
    race=workers[0]['race']
    auto=active.get('auto_transport') or {}
    if not auto.get('ended',False):
        return ()  # never race the automatic deployment/reconciliation protocol
    if active.get('terminal_snapshot') is not None:
        return ()
    reserved={item.get('copy_id') for item in active.get('field_build_reservations',())}
    return tuple(BuildEntitlement(c['id'],race,c['name'],NATIVE_TYPES[c['name']])
                 for c in ledger.get('copies',())
                 if (c.get('race')==race and c.get('kind')=='structure' and
                     c.get('status')=='zone' and
                     c.get('id') in (set(active.get('pending',())) |
                                     set(active.get('purchased_during_mission',()))) and
                     c.get('name') in NATIVE_TYPES and c.get('id') not in reserved))


def reserve_build(ledger: Mapping[str,Any], mission_id: int, *, worker_tag:int,
                  copy_id:str) -> dict[str,Any]:
    """Persist exactly one copy reservation, without altering credits or unit tags.

    The real builder adapter will have to associate this reservation with an
    authenticated SC2 build completion. Starting a construction is NOT proof
    that one finished; any failure leaves the copy available on recovery.
    """
    choices=eligible_builds(ledger,mission_id,worker_tag)
    if not any(c.copy_id==copy_id for c in choices):
        raise ValueError('Structure is not an available purchased build entitlement')
    reservations=ledger['active_mission'].get('field_build_reservations',())
    if any(r.get('worker_tag')==worker_tag for r in reservations):
        raise ValueError('Worker already has a Crew building reservation')
    updated=copy.deepcopy(ledger)
    active=updated['active_mission']
    active.setdefault('field_build_reservations',[]).append({'copy_id':copy_id,
                                                         'worker_tag':worker_tag})
    return updated


def accept_build_completion(ledger: Mapping[str,Any], mission_id: int, *,
                            worker_tag:int, copy_id:str, observed:CrewUnitObservation,
                            player_id:int, verified_galaxy_tag:int,
                            construction_complete:bool = False) -> dict[str,Any]:
    """Bind only a completed, SC2-observed structure with matching Galaxy tag.

    This caller MUST be reached from a future verified Galaxy bank receipt
    AND a separate confirmed construction-complete event. A partially built
    structure or a native starting building must not consume a paid copy.
    """
    from .crew_tags import wire_tag
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        raise ValueError('No active build session')
    rows=[r for r in active.get('field_build_reservations',())
          if r.get('copy_id')==copy_id and r.get('worker_tag')==worker_tag]
    if len(rows)!=1:
        raise ValueError('No uniquely reserved Crew construction')
    original=next((c for c in ledger['copies'] if c['id']==copy_id),None)
    if (original is None or original.get('kind')!='structure' or
        original.get('status')!='zone' or observed.owner!=player_id or
        not observed.is_structure or construction_complete is not True or
        str(observed.tag) in (active.get('auto_transport') or {}).get('native_starting',{}) or
        observed.native_type!=NATIVE_TYPES.get(original['name']) or
        type(verified_galaxy_tag) is not int or
        wire_tag(observed.tag)!=verified_galaxy_tag):
        raise ValueError('Constructed unit, owner or bank tag does not match entitlement')
    updated=copy.deepcopy(ledger)
    observe_receipt(updated,mission_id,copy_id=copy_id,tag=observed.tag,
                   observed_name=original['name'],observed_owner=player_id,
                   player_id=player_id,provenance='crew-created')
    updated['active_mission']['field_build_reservations'].remove(rows[0])
    return updated


def stock_commands(ledger: Mapping[str,Any], mission_id: int,
                   acknowledged: frozenset[int], *, batch_size: int=6) -> tuple[str,...]:
    """Advertise individually purchased, unspent buildings; only after End.

    Authorizations are idempotent for one session. No item is spent on send.
    """
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        return ()
    auto=active.get('auto_transport') or {}
    token=auto.get('token')
    if not auto.get('ended') or type(token) is not int or token<=0:
        return ()
    if active.get('terminal_snapshot') is not None:return ()
    if not (1<=batch_size<=6):raise ValueError('Invalid stock batch size')
    authorized=set(acknowledged)
    reservations={r['copy_id'] for r in active.get('field_build_reservations',())}
    # Reserves are authoritative. An unused purchased copy must remain
    # deployable even if an older reconciliation path moved its ID out of
    # active.pending. Existing on-field/lost copies are never advertised.
    rows=[]
    for c in ledger.get('copies',()):
        if (c.get('kind') not in ('structure','unit') or
            c.get('status')!='zone' or c.get('id') in reservations):continue
        native=NATIVE_TYPES.get(c.get('name'))
        from .crew_bank_receipts import WIRE_TYPES
        if native not in WIRE_TYPES:continue
        ident=str(c['id'])
        if not ident.startswith('crew_') or not ident[5:].isdecimal():raise ValueError('Invalid Crew copy ID')
        number=int(ident[5:])
        if not 0<number<=100000:raise ValueError('Crew copy ID outside bank range')
        if number not in authorized:rows.append((number,native))
    return tuple('?SlayCrewBuildStock '+str(token)+' '+str(len(chunk))+' '+
                 ' '.join(str(number)+' '+native for number,native in chunk)
                 for start in range(0,len(rows),batch_size)
                 for chunk in [rows[start:start+batch_size]])


def accept_galaxy_build(ledger: Mapping[str,Any], mission_id: int, *,
                        receipt: Any, observations: tuple[CrewUnitObservation,...],
                        ready_tags: frozenset[int], player_id: int,
                        death_tags: frozenset[int] = frozenset()) -> dict[str,Any]:
    """Atomic, idempotent binding of a Galaxy-finished native worker building.

    Receipt is from the validated SC2 bank but we additionally verify the
    full SC2 tag, exact native catalog type, owner and ready state. No receipt
    authorizes an unowned builder, a starting building or a fresh duplicate.
    """
    from .crew_tags import require_unique_tag
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        raise ValueError('No matching active Crew mission')
    auto=active.get('auto_transport') or {}
    if not auto.get('ended') or receipt.token!=auto.get('token'):
        raise ValueError('Field construction outside confirmed Crew session')
    copy_id=f'crew_{receipt.copy_number}'
    copied=next((c for c in ledger['copies'] if c['id']==copy_id),None)
    if copied is None or copied.get('kind')!='structure' or receipt.owner!=player_id:
        raise ValueError('Unowned or invalid field build entitlement')
    if NATIVE_TYPES.get(copied['name'])!=receipt.native_type:
        raise ValueError('Galaxy-built type does not match the purchased copy')
    from .crew_tags import matching_full_tags, wire_tag
    bound=[int(tag) for tag,identity in active.get('tags',{}).items() if identity==copy_id]
    if bound:
        if len(bound)!=1 or wire_tag(bound[0])!=receipt.tag or copied.get('status')!='deployed':
            raise ValueError('Crew building receipt conflicts with existing binding')
        return copy.deepcopy(ledger)
    if copy_id in active.get('confirmed_build_losses',()):
        return copy.deepcopy(ledger)
    actors={obs.tag:obs for obs in observations}
    matching=matching_full_tags(receipt.tag,actors)
    if len(matching)>1:
        raise ValueError('Ambiguous Crew field structure tag')
    if not matching:
        if receipt.tag in death_tags:
            # Bank-completed purchased structure, then separately banked death.
            # Require the original builder to have been independently observed.
            producers=matching_full_tags(receipt.worker_tag,
                tuple(actors)+tuple(int(tag) for tag in active.get('tags',{}))+
                tuple(int(tag) for tag in auto.get('native_starting',{})))
            if len(producers)!=1:
                return copy.deepcopy(ledger)
            if copied.get('status')!='zone' or copy_id not in (
                    set(active.get('pending',()))|set(active.get('purchased_during_mission',()))):
                raise ValueError('Dead structure does not have a purchased entitlement')
            updated=copy.deepcopy(ledger)
            member=next(c for c in updated['copies'] if c['id']==copy_id)
            member['status']='lost'
            stage=updated['active_mission']
            for key in ('pending','purchased_during_mission'):
                if copy_id in stage.get(key,()):stage[key].remove(copy_id)
            stage.setdefault('confirmed_build_losses',[]).append(copy_id)
            return updated
        # Bank complete can precede BotAI observation. Do not block later rows.
        return copy.deepcopy(ledger)
    full=matching[0]
    if receipt.native_type=='PlanetaryFortress':
        # A purchased PF copy is an entitlement to convert a Command Center,
        # NOT a structure that an SCV can place. A native Specialize receipt
        # must identify the original CC actor in the session snapshot and
        # the now-completed PF as the same unique SC2 actor/tag.
        from .crew_tags import wire_tag
        if (receipt.worker_tag!=receipt.tag or full not in ready_tags or
            actors[full].native_type!='PlanetaryFortress' or
            actors[full].owner!=player_id or not actors[full].is_structure):
            raise ValueError('Planetary morph lacks verified completed same-tag actor')
        origin=(auto.get('native_starting') or {}).get(str(full))
        purchased_source=active.get('tags',{}).get(str(full))
        original_cc=origin is not None and origin.get('owner')==player_id and origin.get('type') in (
            'CommandCenter','AP_CommandCenter')
        if purchased_source is not None:
            # A purchased command center cannot silently turn into an extra
            # purchasable unit without consuming the original source copy.
            prior=next((c for c in ledger['copies'] if c['id']==purchased_source),None)
            if not prior or prior.get('name')!='Command Center' or prior.get('status')!='deployed':
                raise ValueError('Planetary source is not a verified Command Center')
        elif not original_cc:
            raise ValueError('Planetary source was not a known starting Command Center')
        if copied.get('status')!='zone':
            raise ValueError('Planetary already spent its purchased entitlement')
        updated=copy.deepcopy(ledger)
        current=updated['active_mission']
        if purchased_source is not None:
            for c in updated['copies']:
                if c['id']==purchased_source:
                    c['status']='lost'
                    c['loss_reason']='converted-to-planetary'
            current['tags'].pop(str(full),None)
            current.setdefault('converted_purchased_sources',[]).append(purchased_source)
        if copy_id not in current.get('pending',()):current.setdefault('pending',[]).append(copy_id)
        observe_receipt(updated,mission_id,copy_id=copy_id,tag=full,
                        observed_name=copied['name'],observed_owner=player_id,
                        player_id=player_id,provenance='crew-created')
        current.setdefault('field_build_completed_ids',[]).append(copy_id)
        return updated
    try:
        worker=require_unique_tag(receipt.worker_tag,actors,label='native field builder')
    except ValueError:
        # A Zerg Drone is sacrificed by native construction. Its missing live
        # actor is expected, but its *old purchased tag* is mandatory.
        from .crew_tags import wire_tag
        # The fallback is only for a genuinely *absent* producer. Never
        # resolve a wire-tag collision between live actors by guessing Drone.
        if any(wire_tag(int(tag))==receipt.worker_tag for tag in actors):
            raise
        candidates=[int(tag) for tag,copy_id in active.get('tags',{}).items()
                    if wire_tag(int(tag))==receipt.worker_tag and
                    any(c.get('id')==copy_id and c.get('name')=='Drone'
                        for c in ledger.get('copies',()))]
        if len(candidates)!=1 or receipt.native_type=='TechLab':
            raise
        worker=candidates[0]
    build=actors[full]
    if full not in ready_tags:
        return copy.deepcopy(ledger)
    builder=actors.get(worker)
    consumed_drone=builder is None
    if (build.owner!=player_id or not build.is_structure or
        build.native_type!=receipt.native_type or full not in ready_tags or
        (builder is not None and builder.owner!=player_id) or
        (consumed_drone and receipt.native_type=='TechLab') or
        (builder is not None and
         (builder.native_type not in WORKER_BY_RACE.values() and
          not (receipt.native_type=='TechLab' and builder.native_type in
               {'Barracks','Factory','Starport'}))) or
        (builder is not None and
         builder.is_structure != (receipt.native_type=='TechLab'))):
        raise ValueError('SC2 independent owner, type or complete-state evidence missing')
    native_starting=auto.get('native_starting',{})
    if str(full) in native_starting:
        raise ValueError('Crew field build incorrectly refers to a starting actor')
    worker_id=active.get('tags',{}).get(str(worker))
    worker_copy=next((c for c in ledger['copies'] if c['id']==worker_id),None)
    # The original mission can supply a valid SCV/Probe/Drone without that
    # actor being purchased. Owner, exact CUnit, bank tag and ready building
    # remain independently verified. Absent consumed Drones still need their
    # original Crew tag; no speculative identity fallback.
    qualified=(worker_copy is not None and worker_copy.get('status')=='deployed' and
        (worker_copy.get('name')==WORKER_BY_RACE.get(worker_copy.get('race')) or
         (receipt.native_type=='TechLab' and worker_copy.get('name') in
          {'Barracks','Factory','Starport'})))
    qualified=qualified or (builder is not None and builder.owner==player_id and
        ((not builder.is_structure and builder.native_type in WORKER_BY_RACE.values()) or
         (receipt.native_type=='TechLab' and builder.is_structure and
          builder.native_type in {'Barracks','Factory','Starport'})))
    if not qualified or (consumed_drone and
        (worker_copy is None or worker_copy.get('name')!='Drone')):
        raise ValueError('Field building producer is not verified')
    existing=active.get('tags',{}).get(str(full))
    if existing is not None:
        if existing!=copy_id:raise ValueError('Field structure tag is claimed by another copy')
        if copied.get('status')!='deployed':raise ValueError('Bound Crew status mismatch')
        return copy.deepcopy(ledger)  # idempotent repeated bank receipt
    if copied.get('status')!='zone':raise ValueError('Spent or reserved Crew build entitlement')
    if copy_id not in set(active.get('pending',()))|set(active.get('purchased_during_mission',())):
        raise ValueError('Field build was never purchased for this mission')
    updated=copy.deepcopy(ledger)
    pending=updated['active_mission']['pending']
    if copy_id not in pending:pending.append(copy_id)
    observe_receipt(updated,mission_id,copy_id=copy_id,tag=full,
                    observed_name=copied['name'],observed_owner=player_id,
                    player_id=player_id,provenance='crew-created')
    updated['active_mission'].setdefault('field_build_completed_ids',[]).append(copy_id)
    return updated
