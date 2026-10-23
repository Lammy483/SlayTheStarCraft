"""Fail-closed, restartable Crew automatic-deployment transaction coordinator.

This is a transport/ledger adapter, not a generic SC2 spawning mechanism.
Requires an externally verified SC2 unit snapshot and SC2 BankSave report;
never infer ownership from unit names or from a bank record alone. The normal
bot uses none of this until Crew mission launching is separately enabled.

The `transport` state lives inside the saved active_mission dictionary, so
replaying a spawn command after a bot/process restart never consumes an extra
copy, and a lost ACK can be retried without duplicating the ledger receipt.
"""
from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from .crew_auto import automatic_plan
from .crew_bridge import manifest, observe_receipt
from .crew_sc2_adapter import CrewUnitObservation, NATIVE_TYPES
from .crew_bank_receipts import CrewAutoBankReceipt, validate_observed_receipt
from .crew_tags import wire_tag, require_unique_tag, matching_full_tags
from dataclasses import replace


class CrewObservationPending(RuntimeError):
    """Bank receipt exists, but the matching SC2 actor is not observable yet.

    This is not placement failure and not authorization to spend, skip, retry
    creation, or settle the copy. Wait for another complete BotAI snapshot.
    """


@dataclass(frozen=True)
class CrewBankStatus:
    ready: bool
    acknowledged: frozenset[int]
    receipts: tuple[CrewAutoBankReceipt, ...]
    native_receipts: tuple = ()
    native_acknowledged: frozenset[int] = frozenset()
    native_done: bool = False
    ended: bool = False
    skipped: frozenset[int] = frozenset()
    origin_tag: int | None = None
    death_tags: frozenset[int] = frozenset()
    build_receipts: tuple = ()
    build_authorized: frozenset[int] = frozenset()
    train_receipts: tuple = ()
    production_debug: tuple[tuple[str,int], ...] = ()
    production_claims: frozenset[int] = frozenset()
    free_building_deaths: tuple[tuple[int,int], ...] = ()
    adopted_tags: tuple[tuple[int,int], ...] = ()


def _get(ledger: Mapping[str, Any], mission_id: int) -> dict:
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id') != mission_id:
        raise ValueError('No active matching Crew mission')
    return active


def initialize(ledger: dict, mission_id: int, *, token: int, player_id: int,
               starting_observations: Iterable[CrewUnitObservation] | None = None) -> None:
    active=_get(ledger,mission_id)
    if type(token) is not int or not (0 < token < 2**31):
        raise ValueError('Invalid Crew session token')
    if type(player_id) is not int or not (0 < player_id <= 16):
        raise ValueError('Invalid Crew player')
    old=active.get('auto_transport')
    if old is not None:
        if (old['token'],old['player_id']) != (token,player_id):
            raise RuntimeError('Cannot replace existing Crew session identity')
        return
    # Pre-deployment snapshot is immutable for the entire Crew mission. Native
    # map-owned starters, gifted units, and campaign scripting cannot be
    # promoted into purchased Crew copies merely by matching their unit types.
    # The live BotAI must provide a complete owned-unit view when starting.
    baseline = tuple(starting_observations) if starting_observations is not None else ()
    if any(not isinstance(item, CrewUnitObservation) for item in baseline):
        raise ValueError('Only typed SC2 observations may establish Crew native baseline')
    starting = {str(item.tag):{'type':item.native_type,'owner':item.owner}
                for item in baseline if item.owner == player_id}
    if len(starting) != sum(item.owner == player_id for item in baseline):
        raise ValueError('Duplicate SC2 tags in native starting-unit baseline')
    structures=sorted((u for u in baseline if u.owner==player_id and u.is_structure),
                      key=lambda u:u.tag)
    active['auto_transport']={'token':token,'player_id':player_id,'sequence':0,
                              'pending':None,'settled_ids':[],'skipped_ids':[],'ended':False,'end_requested':False,
                              'native_starting': starting,
                              'native_structures':[{'tag':u.tag,'native_type':u.native_type}
                                                   for u in structures],
                              'native_plan':None,'native_pending':None,'native_index':0,
                              'native_done':False,'native_removed_tags':[]}


def _transport(ledger: Mapping[str, Any], mission_id: int) -> dict:
    t=_get(ledger,mission_id).get('auto_transport')
    if not isinstance(t,dict):
        raise ValueError('Uninitialized Crew automatic transport')
    return t


def propose(ledger: Mapping[str,Any], mission_id: int, catalog: Iterable[Mapping[str,Any]],
            *, bank: CrewBankStatus, observations: Iterable[CrewUnitObservation],
            base_established: bool, home_tag: int,
            available_prerequisites: Iterable[str] = (),
            in_progress_prerequisites: Iterable[str] = ()) -> tuple[dict,str | None]:
    """Stage and emit at most one command; caller persists result BEFORE sending.

    Proposals are idempotent across reboots. A lost chat message can be retried
    with exactly the same sequence and copy ID. The SC2 handler rejects a
    duplicate request after creating its one unit and writes only one receipt.
    """
    updated=copy.deepcopy(ledger)
    t=_transport(updated, mission_id)
    token=t['token']
    if t['ended']:
        return updated,None
    # A sent chat message is not evidence that Galaxy processed it. Only its
    # token-qualified SC2-bank Ended field releases the victory settlement
    # barrier. Repeated End commands are harmless when an ACK was lost.
    if t.get('end_requested',False):
        if bank.ended:
            if t['pending'] is not None or not t.get('native_done',False):
                raise RuntimeError('Crew Ended receipt with unresolved deployment')
            t['ended']=True
            return updated,None
        return updated,f'?SlayCrewEnd {token}'
    if bank.ended:
        raise RuntimeError('Unsolicited Crew Ended receipt')
    if not bank.ready:
        return updated,f'?SlayCrewSession {token}' if base_established else None
    if not base_established:
        return updated,None
    # Starting structures must be explicitly retained or removed before a
    # single purchased copy may be spawned. Native and spawn sequences are
    # separate; durable native receipts are handled by accept_native().
    if not t.get('native_done',False):
        updated, native_command=propose_native(updated,mission_id,bank=bank,observations=observations)
        if native_command is not None or not t['native_done']:
            return updated,native_command
    pending=t['pending']
    if pending is not None:
        if pending['stage']=='await-ack':
            if pending['sequence'] in bank.acknowledged:
                t['pending']=None
            else:
                return updated,pending['ack']
        else:
            return updated,f"?SlayCrewSpawn {token} {pending['sequence']} {pending['native_type']}"
    rows=automatic_plan(manifest(updated,mission_id,catalog),NATIVE_TYPES)
    if not rows:
        # Empty pending means all supported copies are deployed. Unsupported
        # catalog variants remain reserved and are never silently fabricated.
        t['end_requested']=True
        return updated,f'?SlayCrewEnd {token}'
    already=set(t['settled_ids']) | set(t.get('skipped_ids',()))
    # A deployment receipt proves ownership, NOT that the producer is still
    # present or finished. Only the bot's current, completed, player-owned
    # prerequisite observations may authorize new unit deployment. Otherwise
    # a destroyed paid Barracks could spawn free Marines later in the mission.
    ready=set(available_prerequisites)
    candidates=[r for r in rows if r['copy_id'] not in already and
                (not r['requires'] or r['requires'] in ready)]
    if not candidates and any(r['requires'] in set(in_progress_prerequisites)
                              for r in rows if r['copy_id'] not in already):
        # A newly deployed structure may need several game frames to finish.
        # Do not irrevocably End the session while its prerequisite exists but
        # is unfinished. If it dies/disappears, the next snapshot can End.
        return updated,None
    if not candidates:
        # A unit may be owned without its required production infrastructure.
        # It remains pending/undeployed and must not block victory forever.
        # SC2 will only receive commands for satisfied prerequisites.
        t['end_requested']=True
        return updated,f'?SlayCrewEnd {token}'
    if type(home_tag) is not int or home_tag <= 0:
        raise ValueError('Live SC2 home anchor tag is required')
    obs=tuple(observations)
    if any(not isinstance(x,CrewUnitObservation) for x in obs):
        raise ValueError('Only verified SC2 unit observations are accepted')
    r=candidates[0]
    sequence=t['sequence']+1
    t['pending']={'copy_id':r['copy_id'],'native_type':r['native_type'],
                  'name':r['name'],'sequence':sequence,'home_tag':home_tag,
                  'baseline_tags':[x.tag for x in obs],'stage':'spawn'}
    return updated,f'?SlayCrewSpawn {token} {sequence} {r["native_type"]}'


def accept(ledger: Mapping[str,Any], mission_id:int, *,
           receipt:CrewAutoBankReceipt, observations:Iterable[CrewUnitObservation]) -> tuple[dict,str]:
    """Atomically bind an actual tag to a copy; persist before sending ACK.

    Refuses same-type campaign freebies, wrong owner, mismatched anchor, stale
    bank tokens, or multiple indistinguishable newly created candidates.
    """
    updated=copy.deepcopy(ledger)
    t=_transport(updated,mission_id)
    pending=t['pending']
    if pending is None or pending['stage']!='spawn':
        raise RuntimeError('No outstanding Crew spawn to match')
    if receipt.sequence != pending['sequence']:
        raise ValueError('Wrong Crew sequence')
    obs=tuple(observations)
    # The bank's committed tag is the identity, not a count of new units.
    # Other legitimate campaign units of the same type may appear while SC2
    # is saving its bank. Do not reject that situation or claim the bystander.
    candidates=matching_full_tags(receipt.tag,(u.tag for u in obs
                                               if u.owner==t['player_id']))
    if not candidates:
        raise CrewObservationPending('Banked Crew spawn tag is not in the latest '
                                     'SC2 observation; waiting for visibility')
    if len(candidates)!=1:
        raise RuntimeError(f'Crew spawn receipt tag ambiguous: wire={receipt.tag}, '
                           f'full={candidates}')
    resolved=candidates[0]
    if resolved in set(pending['baseline_tags']) or str(resolved) in t.get('native_starting', {}):
        raise RuntimeError('Crew receipt attempts to claim a native starting unit')
    new=[u for u in obs if u.tag == resolved and u.owner==t['player_id']]
    if len(new)!=1:
        raise RuntimeError('Crew receipt observation duplicated or missing')
    if new[0].native_type != pending['native_type']:
        raise ValueError('Crew banked unit has incorrect observed CUnit type: '
                         f'expected={pending["native_type"]}, '
                         f'observed={new[0].native_type}, tag={resolved}')
    if (resolved & 0xffffffff) == receipt.producer_tag:
        raise RuntimeError('Crew receipt cannot claim its own spawn anchor')
    # The Galaxy home selector may choose a different hall once a new owned
    # town hall is deployed. Prove the bank anchor is an actual player-owned
    # observed structure; do not assume it equals the earlier chosen hall.
    anchors=[o for o in obs if (o.tag & 0xffffffff) == receipt.producer_tag and
             o.owner==t['player_id'] and (o.is_structure or o.native_type in
             {'CommandCenter','OrbitalCommand','PlanetaryFortress','Hatchery','Lair','Hive','Nexus'})]
    if len(anchors)!=1:
        # The only permitted absent anchor is a previously observed native
        # structure removed by the acknowledged pre-deployment phase. Galaxy
        # keeps its original tag and position after that building disappears.
        removed=set(t.get('native_removed_tags',()))
        removed_matches=matching_full_tags(receipt.producer_tag,removed)
        baseline_tag=removed_matches[0] if len(removed_matches)==1 else None
        baseline=t.get('native_starting',{}).get(str(baseline_tag))
        if not (t.get('native_done') and len(removed_matches)==1 and
                baseline is not None and baseline['owner']==t['player_id']):
            raise ValueError('Bank placement anchor is not a verified owned structure')
        from .crew_sc2_adapter import CrewUnitObservation
        anchors=[CrewUnitObservation(baseline_tag,baseline['type'],
                     t['player_id'],0.0,0.0,True)]
    # Validate with full observed tags, but acknowledge the original 32-bit
    # Galaxy receipt. Never send a 64-bit SC2 tag through StringToInt().
    resolved_receipt=replace(receipt,tag=resolved,producer_tag=anchors[0].tag)
    validate_observed_receipt(resolved_receipt,token=t['token'],sequence=pending['sequence'],
                    expected_native_type=pending['native_type'],player_id=t['player_id'],
                    expected_producer_tag=anchors[0].tag, observed_tag=new[0].tag,
                    observed_native_type=new[0].native_type,observed_owner=new[0].owner)
    ack=f'?SlayCrewAck {t["token"]} {receipt.sequence} {receipt.tag}'
    observe_receipt(updated,mission_id,copy_id=pending['copy_id'],tag=resolved,
                    observed_name=pending['name'],observed_owner=new[0].owner,
                    player_id=t['player_id'],provenance='crew-created')
    t['settled_ids'].append(pending['copy_id'])
    t['sequence']=pending['sequence']
    pending['stage']='await-ack'
    pending['ack']=ack
    return updated,ack


def accept_skip(ledger: Mapping[str,Any], mission_id: int, *,
                sequence: int, bank: CrewBankStatus) -> tuple[dict,str]:
    """Accept a banked unsuccessful SC2 placement without consuming a copy.

    A skip is not a deployment receipt. The paid copy stays in the zone, and
    the sequence is acknowledged to free Galaxy for the next copy. A second
    attempt can occur on a later mission, never silently during this session.
    """
    updated=copy.deepcopy(ledger)
    t=_transport(updated,mission_id)
    p=t['pending']
    if p is None or p.get('stage')!='spawn' or sequence!=p['sequence']:
        raise RuntimeError('No matching Crew placement failure in flight')
    if sequence not in bank.skipped or any(r.sequence==sequence for r in bank.receipts):
        raise ValueError('Crew placement failure lacks an exclusive SC2 bank proof')
    if p['copy_id'] in t['settled_ids'] or p['copy_id'] in t.get('skipped_ids',[]):
        raise RuntimeError('Crew placement failure would duplicate a resolved copy')
    t.setdefault('skipped_ids',[]).append(p['copy_id'])
    t['sequence']=sequence
    p['stage']='await-ack'
    p['ack']=f'?SlayCrewAck {t["token"]} {sequence} 0'
    return updated,p['ack']


def ensure_no_pending_settlement(ledger:Mapping[str,Any],mission_id:int) -> None:
    """Disallow victory while any SC2 command or acknowledgment is in flight."""
    t=_transport(ledger,mission_id)
    if not t.get('native_done') or t.get('native_pending') is not None or t['pending'] is not None or not t['ended']:
        raise RuntimeError('Crew automatic deployment not yet completed')


def native_reconciliation_preview(ledger:Mapping[str,Any], mission_id:int,
                                  observations:Iterable[CrewUnitObservation]) -> tuple[dict,...]:
    """Pure read-only copy of the *actual* native building selection policy.

    Use the same plan for the probe-only preview and for later reconciliation.
    The preview must not change roster copies, pending state or SC2 buildings.
    """
    t=_transport(ledger,mission_id)
    current=tuple(observations)
    if any(not isinstance(o,CrewUnitObservation) for o in current):
        raise ValueError('Invalid native pre-deployment observation')
    starters=sorted((o for o in current if o.owner==t['player_id'] and
                    (o.is_structure or o.native_type in {'SCV','Drone','Probe'})),
                   key=lambda o:o.tag)
    # Mission-scripted actors without verified catalog identity are never
    # destroyed. Starting workers use the same per-copy bank-acknowledged
    # protocol as native structures; free extra workers are removed.
    protected=[o for o in starters if o.native_type.startswith('unmapped:')]
    starters=[o for o in starters if o not in protected]
    active=_get(ledger,mission_id)
    pending=set(active.get('pending',()))
    available={}
    for c in ledger['copies']:
        if (c.get('status')=='zone' and c['id'] in pending and
                (c.get('kind')=='structure' or c.get('name') in {'SCV','Drone','Probe'})):
            native=NATIVE_TYPES.get(c['name'])
            if native:available.setdefault(native,[]).append(c['id'])
    for ids in available.values():ids.sort()
    plan=[]
    for item in starters:
        ids=available.get(item.native_type,[])
        copy_id=ids.pop(0) if ids else None
        plan.append({'tag':item.tag,'native_type':item.native_type,
                     'is_structure':item.is_structure,
                     'action':1 if copy_id else 2,'copy_id':copy_id})
    return tuple(sorted(plan,key=lambda x:(x['action']!=1,x['tag'])))


def propose_native(ledger:dict, mission_id:int, *, bank:CrewBankStatus,
                   observations:Iterable[CrewUnitObservation]) -> tuple[dict,str|None]:
    """Reconcile ONLY the immutable initial player-building snapshot.

    One matching zone structure is consumed by each kept native building.
    All others are removed, one per bank-acknowledged operation. No unit may
    spawn while any operation is unconfirmed. Unrecognized native buildings
    are eligible for *removal*, never for opportunistic ownership claiming.
    """
    t=_transport(ledger,mission_id)
    if t.get('native_done'):return ledger,None
    if not bank.ready:return ledger,None
    if t['native_plan'] is None:
        # Freeze the actual completed-base state here, not during the first
        # readable loading frame. No Crew spawn has occurred at this point.
        current=tuple(observations)
        plan=native_reconciliation_preview(ledger,mission_id,current)
        starters=sorted((o for o in current if o.owner==t['player_id'] and o.is_structure),
                        key=lambda o:o.tag)
        t['native_structures']=[{'tag':o.tag,'native_type':o.native_type} for o in starters]
        t['native_starting']={str(o.tag):{'type':o.native_type,'owner':o.owner}
                              for o in current if o.owner==t['player_id']}
        # The read-only test preview and the real transaction are identical.
        t['native_plan']=[dict(item) for item in plan]
    pending=t['native_pending']
    if pending is not None:
        if pending['stage']=='await-ack':
            if pending['sequence'] in bank.native_acknowledged:
                t['native_index']+=1
                t['native_pending']=None
            else:return ledger,pending['ack']
        else:
            return ledger,pending['command']
    if t['native_index']>=len(t['native_plan']):
        if bank.native_done:
            t['native_done']=True
            return ledger,None
        return ledger,f'?SlayCrewNativeEnd {t["token"]}'
    item=t['native_plan'][t['native_index']]
    # The map can destroy or replace an original building while earlier
    # reconciliation commands are in flight. If an intended KEEP no longer
    # exists with the same player/type, it must NOT consume its purchased
    # roster copy. Instead turn that step into an acknowledged REMOVE. The
    # unchanged purchased copy remains in the zone and may deploy normally.
    # Once a native command is outstanding, never rewrite its intent.
    current=[o for o in observations if o.tag==item['tag']]
    if item['action']==1 and not any(
            o.owner==t['player_id'] and o.is_structure and
            o.native_type==item['native_type'] for o in current):
        item['action']=2
        item['copy_id']=None
    sequence=t['native_index']+1
    command=f'?SlayCrewNative {t["token"]} {sequence} {wire_tag(item["tag"])} {item["action"]}'
    t['native_pending']={**item,'sequence':sequence,'stage':'execute','command':command}
    return ledger,command


def accept_native(ledger:Mapping[str,Any],mission_id:int,*,receipt,
                  observations:Iterable[CrewUnitObservation]) -> tuple[dict,str]:
    """Require a Galaxy bank receipt plus independent live actor evidence."""
    from .crew_bridge import observe_receipt
    updated=copy.deepcopy(ledger)
    t=_transport(updated,mission_id)
    p=t.get('native_pending')
    if p is None or p['stage']!='execute':
        raise RuntimeError('No outstanding native Crew reconciliation')
    if (receipt.token!=t['token'] or receipt.sequence!=p['sequence'] or
        receipt.tag!=wire_tag(p['tag']) or receipt.action!=p['action'] or
        receipt.owner!=t['player_id']):
        raise ValueError('Native Crew bank receipt does not match intent')
    obs=list(observations)
    matches=[o for o in obs if o.tag==p['tag']]
    if p['action']==1:
        if (len(matches)!=1 or not matches[0].is_structure or
            matches[0].native_type!=p['native_type'] or
            matches[0].owner!=t['player_id'] or not p['copy_id']):
            raise RuntimeError('Native Crew claimed structure is not present and owned')
        name=next(c['name'] for c in updated['copies'] if c['id']==p['copy_id'])
        observe_receipt(updated,mission_id,copy_id=p['copy_id'],tag=p['tag'],
                        observed_name=name,observed_owner=t['player_id'],
                        player_id=t['player_id'],provenance='crew-claimed-starting')
        t['settled_ids'].append(p['copy_id'])
    else:
        if matches:
            raise RuntimeError('Native structure removal is not confirmed by SC2')
        t['native_removed_tags'].append(p['tag'])
    ack=f'?SlayCrewNativeAck {t["token"]} {p["sequence"]} {receipt.tag}'
    p['stage']='await-ack'
    p['ack']=ack
    return updated,ack
