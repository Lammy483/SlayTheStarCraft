"""Independently verified Crew native-unit training receipts."""
from __future__ import annotations
import copy
from .crew_sc2_adapter import NATIVE_TYPES
from .crew_tags import require_unique_tag
from .crew_bridge import observe_receipt

def accept_native_trains(ctx, mission_id, receipts, observations, player_id, *,
                         death_tags=frozenset(), authorized=frozenset()):
    """Reconcile each independently paid native train without head-of-line stalls.

    Already-bound receipts are idempotent even if the actor later died.
    Deaths that occur between SC2 ticks can be resolved by the completed
    Galaxy receipt plus the separate Galaxy death event and verified producer.
    Missing but not confirmed-dead actors are retried, never guessed lost.
    """
    from . import slay_the_starcraft as slay
    from .crew_tags import wire_tag, matching_full_tags
    original=slay.crew_roster(ctx)
    active=original.get('active_mission') or {}
    auto=active.get('auto_transport') or {}
    if active.get('mission_id')!=mission_id or not auto.get('ended'):
        raise ValueError('Native training outside confirmed Crew deployment')
    updated=copy.deepcopy(original)
    actors={o.tag:o for o in observations}
    valid_zone=set(active.get('pending',()))|set(active.get('purchased_during_mission',()))
    bound_tags=active.get('tags',{})
    starting_tags=auto.get('native_starting',{})
    accepted=0
    for receipt in receipts:
        if receipt.token != auto.get('token') or receipt.owner != player_id:
            raise ValueError('Incorrect Crew train receipt identity')
        copy_id=f'crew_{receipt.copy_number}'
        bought=next((c for c in updated['copies'] if c['id']==copy_id),None)
        if bought is None or bought.get('kind')!='unit' or NATIVE_TYPES.get(bought['name'])!=receipt.native_type:
            raise ValueError('Trained unit does not match paid Crew copy')
        if receipt.copy_number not in authorized:
            raise ValueError('Train receipt is missing an acknowledged purchase')
        if copy_id in updated['active_mission'].get('confirmed_training_losses',()):
            continue
        # A death does not remove an accepted completion receipt from the
        # SC2 bank. Resolve prior bindings first, before requiring visibility.
        already=[tag for tag,member in bound_tags.items() if member==copy_id]
        if already:
            if len(already)!=1 or wire_tag(int(already[0]))!=receipt.tag or bought['status']!='deployed':
                raise ValueError('Crew train receipt conflicts with bound roster copy')
            continue
        if bought['status']!='zone' or copy_id not in valid_zone:
            raise ValueError('Crew training copy not available in this mission')
        matching=matching_full_tags(receipt.tag,actors)
        if len(matching)>1:
            raise ValueError('Ambiguous trained actor wire tag')
        full=matching[0] if matching else None
        if full is not None:
            actor=actors[full]
            if actor.owner!=player_id or actor.is_structure or actor.native_type!=receipt.native_type:
                raise ValueError('Crew trained actor SC2 identity mismatch')
            if str(full) in starting_tags:
                raise ValueError('Trained unit is a native starting actor')
        producers=matching_full_tags(receipt.producer_tag,
            tuple(actors)+tuple(int(x) for x in bound_tags)+
            tuple(int(x) for x in starting_tags))
        if len(producers)!=1:
            # A producer may be temporarily unobservable. Leave the record
            # for the next poll; don't block later Marines behind it.
            continue
        producer=producers[0]
        host=actors.get(producer)
        if host is not None and (host.owner!=player_id or not host.is_structure):
            raise ValueError('Native train producer is not a player structure')
        if (str(producer) not in bound_tags and str(producer) not in starting_tags
                and host is None):
            # A mission script may provide another free, temporary Barracks
            # after the initial observation. Its live owner/structure proof
            # and Galaxy producer tag are sufficient to TRAIN an individually
            # purchased unit; the producer itself never becomes permanent.
            raise ValueError('Native producer was not a verified player structure')
        if full is not None:
            if copy_id not in updated['active_mission']['pending']:
                updated['active_mission']['pending'].append(copy_id)
            observe_receipt(updated,mission_id,copy_id=copy_id,tag=full,
                            observed_name=bought['name'],observed_owner=player_id,
                            player_id=player_id,provenance='crew-created')
            updated['active_mission'].setdefault('field_train_completed_ids',[]).append(copy_id)
            accepted+=1
        elif receipt.tag in death_tags:
            # Positive construction-complete AND death events in the bank,
            # with a valid paid copy and independently observed producer.
            # No live full unit tag survives to bind: record the explicit
            # loss without guessing a 64-bit tag or claiming a survivor.
            bought['status']='lost'
            mission=updated['active_mission']
            for name in ('pending','purchased_during_mission'):
                if copy_id in mission.get(name,()):mission[name].remove(copy_id)
            mission.setdefault('confirmed_training_losses',[]).append(copy_id)
            accepted+=1
        # Else: it may be hidden or in transit; retry this receipt next poll.
    if updated!=original:
        slay.state(ctx)['crew_roster']=updated
        slay._persist_state(ctx)
    return accepted
