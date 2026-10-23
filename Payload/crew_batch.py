"""Crew-only, bank-verified three-pass deployment.

Legacy serial sessions remain supported. New sessions use one native snapshot,
chunked native removal/retention (one BankSave per chunk), and chunked roster
creation (one BankSave per chunk). Every created copy is still identified by
an independent SC2 observation matching an exact Galaxy bank tag.
"""
from __future__ import annotations
import copy
import time
from collections.abc import Iterable, Mapping
from .crew_runtime import (CrewBankStatus, CrewObservationPending,
    native_reconciliation_preview, accept)
from .crew_sc2_adapter import CrewUnitObservation
from .crew_tags import wire_tag, matching_full_tags
from .crew_bridge import observe_receipt

NATIVE_CHUNK=8
SPAWN_CHUNK=10


def _transport(ledger: dict, mission_id: int) -> dict:
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        raise ValueError('Crew mission mismatch')
    t=active.get('auto_transport')
    if not isinstance(t,dict):raise ValueError('Crew session not started')
    return t


def _native_command(token:int, first:int, items:list[dict], last:bool)->str:
    arguments=[]
    for item in items:
        arguments.extend((str(item['action']),str(wire_tag(item['tag']))))
    return ' '.join(['?SlayCrewFastNative',str(token),str(first),str(len(items)),str(int(last)),*arguments])


def _spawn_command(token:int, first:int, items:list[dict])->str:
    return ' '.join(['?SlayCrewFastSpawn',str(token),str(first),str(len(items)),
                     *(r['native_type'] for r in items)])


def _native_batch_fully_banked(pending:dict, bank:CrewBankStatus, token:int)->bool:
    """Only a matching, independently committed Galaxy receipt qualifies for recovery."""
    by_sequence={r.sequence:r for r in bank.native_receipts}
    for index,item in enumerate(pending['rows']):
        seq=pending['first']+index
        r=by_sequence.get(seq)
        if (r is None or seq not in bank.native_acknowledged or
            r.token!=token or r.action!=item['action'] or
            r.owner!=pending.get('player_id',r.owner) or
            r.tag!=wire_tag(item['tag'])):
            return False
    # The last chunk must also have Galaxy's explicit terminal commitment.
    return not pending.get('last') or bank.native_done


def _validate_native_group(ledger:dict, mission_id:int, pending:dict,
                           bank:CrewBankStatus, observed:tuple[CrewUnitObservation,...],
                           *, allow_delayed_observation:bool=False):
    """Keep ownership verification strict; recover missing/stale BotAI snapshots.

    Galaxy's native action receipt is proof that it executed the requested
    command, not proof that a now-missing actor should cost a purchased copy.
    Never bind an absent or mismatched actor. Never invent permanent deaths.
    """
    t=_transport(ledger,mission_id)
    by_seq={r.sequence:r for r in bank.native_receipts}
    unresolved_keeps=[]
    unconfirmed_removes=[]
    for index,item in enumerate(pending['rows']):
        seq=pending['first']+index
        r=by_seq.get(seq)
        if (r is None or r.token!=t['token'] or r.action!=item['action'] or
            r.owner!=t['player_id'] or r.tag!=wire_tag(item['tag']) or
            seq not in bank.native_acknowledged):
            raise CrewObservationPending('Native batch is not completely bank-committed')
        matches=[o for o in observed if o.tag==item['tag']]
        if item['action']==1:
            if (len(matches)==1 and item['copy_id'] and
                matches[0].native_type==item['native_type'] and
                matches[0].owner==t['player_id'] and
                matches[0].is_structure==item.get('is_structure',True)):
                continue
            if allow_delayed_observation and not matches and item['copy_id']:
                unresolved_keeps.append(item['copy_id'])
            else:
                raise CrewObservationPending('Native KEEP not independently observable: '
                                             +item['native_type']+':'+str(item['tag']))
        elif matches:
            # Galaxy banked UnitRemove, but BotAI may keep a stale unit snapshot
            # or a mission may have recreated it. Neither proves permanent
            # removal. Record uncertainty without minting a Crew entitlement.
            if allow_delayed_observation:
                unconfirmed_removes.append(item['tag'])
            else:
                raise CrewObservationPending('Native REMOVE still observed: '+str(item['tag']))
    for item in pending['rows']:
        if item['action']==1:
            if item['copy_id'] in unresolved_keeps:
                # Still in Reserves: bank execution alone does not bind it.
                t.setdefault('unconfirmed_native_keep_ids',[]).append(item['copy_id'])
                continue
            name=next(c['name'] for c in ledger['copies'] if c['id']==item['copy_id'])
            observe_receipt(ledger, mission_id, copy_id=item['copy_id'],tag=item['tag'],
                observed_name=name,observed_owner=t['player_id'],
                player_id=t['player_id'],provenance='crew-claimed-starting')
            t['settled_ids'].append(item['copy_id'])
        elif item['tag'] in unconfirmed_removes:
            t.setdefault('unconfirmed_removed_tags',[]).append(item['tag'])
        else:
            t['native_removed_tags'].append(item['tag'])
    t['native_index']+=len(pending['rows'])
    if pending['last']:
        if not bank.native_done:raise CrewObservationPending('NativeDone not banked')
        t['native_done']=True


def _validate_spawn_group(ledger:dict, mission_id:int, pending:dict,
                          bank:CrewBankStatus, observed:tuple[CrewUnitObservation,...]):
    """SC2 owns the tag; Python verifies each purchase before binding it."""
    t=_transport(ledger,mission_id)
    by_seq={r.sequence:r for r in bank.receipts}
    for i,row in enumerate(pending['rows']):
        seq=pending['first']+i
        success=by_seq.get(seq)
        skipped=seq in bank.skipped
        if success is not None and skipped:raise ValueError('Conflicting Crew batch receipt and skip')
        if not success and not skipped:raise CrewObservationPending('Spawn batch bank receipt missing')
        if seq not in bank.acknowledged:raise CrewObservationPending('Spawn batch commit acknowledgment missing')
        if success:
            if success.native_type!=row['native_type'] or success.owner!=t['player_id'] or success.token!=t['token']:
                raise ValueError('Spawn batch bank type/owner/token mismatch')
            unique=matching_full_tags(success.tag,(o.tag for o in observed if o.owner==t['player_id']))
            if len(unique)!=1:raise CrewObservationPending('Spawn batch tag not uniquely observable yet')
    # Reuse the verified legacy receipt binder for anchor/type/owner checks;
    # it does not send commands. All writes occur in this local cloned ledger.
    for i,row in enumerate(pending['rows']):
        seq=pending['first']+i
        receipt=by_seq.get(seq)
        if receipt is None:
            t['skipped_ids'].append(row['copy_id'])
            t['sequence']=seq
            continue
        t['pending']={'stage':'spawn','copy_id':row['copy_id'],
                      'name':row['name'],'native_type':row['native_type'],
                      'sequence':seq,'home_tag':pending['home_tag'],
                      'baseline_tags':pending['baseline_tags']}
        updated,_=accept(ledger,mission_id,receipt=receipt,observations=observed)
        ledger.clear();ledger.update(updated)
        t=_transport(ledger,mission_id)
        t['pending']=None
    t['sequence']=pending['first']+len(pending['rows'])-1


def step(ledger:Mapping,mission_id:int,*,bank:CrewBankStatus,
         observations:Iterable[CrewUnitObservation], catalog_rows:Iterable[Mapping],
         ready_prerequisites:Iterable[str]=())->tuple[dict,str|None]:
    updated=copy.deepcopy(ledger)
    t=_transport(updated,mission_id)
    token=t['token']
    observed=tuple(observations)
    if any(not isinstance(o,CrewUnitObservation) for o in observed):
        raise ValueError('Verified Crew observations required')
    if not bank.ready:return updated,None
    b=t.get('batch')
    if b is None:
        if t['native_plan'] is not None or t.get('pending') or t.get('native_pending'):
            raise RuntimeError('Cannot switch a serial Crew session into bulk mode')
        plan=native_reconciliation_preview(updated,mission_id,observed)
        halls=[x for x in plan if x['action']==1 and x['native_type'] in
               {'CommandCenter','Hatchery','Nexus'}]
        if not halls:raise RuntimeError('Batch Crew requires an owned, retained starting town hall')
        t['native_plan']=[dict(x) for x in plan]
        b={'phase':'native','index':0,'pending':None,'spawn_rows':None}
        t['batch']=b
    pending=b['pending']
    if pending is not None:
        candidate=copy.deepcopy(updated)
        try:
            if b['phase']=='native':
                if _native_batch_fully_banked(pending,bank,t['token']):
                    pending.setdefault('fully_banked_since',time.monotonic())
                # Give SC2's observer four seconds to catch up to an entirely
                # committed Galaxy batch; do not stall the rest of the mission
                # indefinitely because an independently observed tag vanished.
                waited=time.monotonic()-pending.get('fully_banked_since',time.monotonic())
                _validate_native_group(candidate,mission_id,pending,bank,observed,
                    allow_delayed_observation=(waited>=4.0 and
                        _native_batch_fully_banked(pending,bank,t['token'])))
            elif b['phase']=='spawn':
                _validate_spawn_group(candidate,mission_id,pending,bank,observed)
            else:raise RuntimeError('Unexpected pending Crew batch phase')
        except CrewObservationPending as exc:
            if b['phase']=='native':
                pending['last_validation_issue']=str(exc)
                arrived=any(r.sequence==pending['first'] for r in bank.native_receipts)
            else:
                arrived=(any(r.sequence==pending['first'] for r in bank.receipts) or
                         pending['first'] in bank.skipped)
            return updated,None if arrived else pending['command']
        updated=candidate
        t=_transport(updated,mission_id)
        b=t['batch']
        b['index']+=len(pending['rows'])
        b['pending']=None
    if b['phase']=='native':
        plan=t['native_plan']
        if b['index']>=len(plan):
            if not bank.native_done:raise CrewObservationPending('Native batch End not yet verified')
            t['native_done']=True
            # Manual Deployment Zone: the player's Build/Train orders consume
            # individual paid copies. Skip FastSpawn for *new* sessions.
            # Legacy sessions already in the spawn phase can still finish
            # their saved pending chunk safely on the branch below.
            b['phase']='end';b['end_requested']=True
        else:
            chunk=plan[b['index']:b['index']+NATIVE_CHUNK]
            last=(b['index']+len(chunk)==len(plan))
            command=_native_command(token,b['index']+1,chunk,last)
            b['pending']={'command':command,'first':b['index']+1,'rows':chunk,'last':last}
            return updated,command
    if b['phase']=='spawn':
        if b['spawn_rows'] is None:
            already=set(t['settled_ids'])|set(t.get('skipped_ids',()))
            rows=[dict(r) for r in catalog_rows if r['copy_id'] not in already
                  and r['native_type'] not in {'TechLab','PlanetaryFortress'}]
            available={o.native_type for o in observed if o.owner==t['player_id'] and o.is_structure}
            available.update(r['native_type'] for r in rows if r.get('kind')=='structure')
            available.update(ready_prerequisites)
            b['spawn_rows']=[r for r in rows if not r.get('requires') or r['requires'] in available]
        rows=b['spawn_rows']
        if b['index']>=len(rows):
            b['phase']='end';b['end_requested']=True
        else:
            chunk=rows[b['index']:b['index']+SPAWN_CHUNK]
            command=_spawn_command(token,t['sequence']+1,chunk)
            # Skip only from SC2's own bank, never just because of an absence.
            b['pending']={'command':command,'first':t['sequence']+1,'rows':chunk,
                'baseline_tags':[int(tag) for tag in t['native_starting']],
                'home_tag':t['native_structures'][0]['tag'] if t['native_structures'] else 0}
            return updated,command
    if b['phase']=='end':
        if bank.ended:
            t['ended']=True;b['phase']='done'
            return updated,None
        return updated,f'?SlayCrewEnd {token}'
    return updated,None
