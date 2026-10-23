"""Crew Challenge's isolated, serializable campaign roster and eligibility logic.

This module intentionally has no StarCraft II, Archipelago, or Kivy imports. Actual
unit tags must be bound to copy IDs by the SC2 deployment bridge; without that
bridge, a mission is not considered safely completed by this ledger.
"""
from __future__ import annotations

import copy
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

MODES = {'adventure', 'campaign', 'crew'}
DEFAULT_CREW_RACES = ('terran',)
WORKER_BY_RACE = {'terran': 'SCV', 'zerg': 'Drone', 'protoss': 'Probe'}
TOWNHALL_BY_RACE = {'terran': 'Command Center', 'zerg': 'Hatchery', 'protoss': 'Nexus'}
PRODUCTION_BY_RACE = {'terran': 'Barracks', 'zerg': 'Spawning Pool', 'protoss': 'Gateway'}
SUPPLY_STRUCTURES = {'Supply Depot':8, 'Pylon':8, 'Overlord':8,
                     'Command Center':10, 'Orbital Command':10, 'Planetary Fortress':10,
                     'Hatchery':6, 'Lair':6, 'Hive':6, 'Nexus':10}
WORKER_NAMES = frozenset(WORKER_BY_RACE.values())
SPECIAL_STRUCTURE_NAMES = frozenset({'Supply Depot','Pylon','Overlord','Tech Lab',
                                     'Barracks Tech Lab','Factory Tech Lab','Starport Tech Lab'})
DEFAULT_MAX_SUPPLY = 200


def _rules() -> dict[str, Any]:
    return json.loads(Path(__file__).with_name('crew_rules.json').read_text('utf-8'))


def eligible_effect(effect_id: str, kind: str) -> bool:
    if kind not in {'mutation', 'blessing'}:
        return False
    return _rules()[kind].get(effect_id, False) is True


def eligible_boon(title: str) -> bool:
    return _rules()['boon'].get(title, '').strip().casefold().startswith('yes')


# Crew-only balance overrides. Never alter Standard/AP resource costs.
# This is the single source of truth for shop purchases, revives, free-building
# destruction debits and any other transaction priced through credit_cost.
CREW_FIXED_CREDIT_PRICES = {
    'Wraith': 30,
    'Hercules': 80,
    'HERC': 20,
    'Firebat': 20,
    'Predator': 25,
    'Diamondback': 40,
    'Perdition Turret': 25,
    'Sensor Tower': 20,
    'Spectre': 50,
    'Widow Mine': 15,
}


def credit_cost(minerals: int, gas: int, *, unit_name: str = '') -> int:
    """Crew credits: explicit balance prices, otherwise (minerals+gas)/5."""
    if minerals < 0 or gas < 0:
        raise ValueError('resource costs must be nonnegative')
    if unit_name in CREW_FIXED_CREDIT_PRICES:
        return CREW_FIXED_CREDIT_PRICES[unit_name]
    if unit_name == 'Drone':
        return 2
    return max(0, int(math.floor((minerals + gas) / 5 + 0.5)))


def available_unit_fraction(completed_layers: int, total_layers: int) -> float:
    """From cheapest 35% of unit types to 100% at 75% completed layers."""
    if total_layers < 1:
        raise ValueError('total_layers must be positive')
    progress = min(1.0, max(0.0, completed_layers / (total_layers * 0.75)))
    return 0.35 + 0.65 * progress


def eligible_unit_pool(units: Sequence[Mapping[str, Any]], completed_layers: int,
                       total_layers: int) -> list[dict[str, Any]]:
    ordered = sorted((dict(u) for u in units),
                     key=lambda u: (credit_cost(int(u['minerals']), int(u['gas']),
                               unit_name=str(u['name'])), str(u['name']).casefold()))
    count = min(len(ordered), max(4,int(math.ceil(len(ordered)*available_unit_fraction(completed_layers,total_layers)))))
    return ordered[:count]


def default_roster(races: Sequence[str] = DEFAULT_CREW_RACES) -> dict[str, Any]:
    if not races or any(race not in WORKER_BY_RACE for race in races):
        raise ValueError('at least one valid race is required')
    # Crew starts with exactly one purchased supply structure, never a free
    # worker or production/town-hall copy. Map-provided actors are temporary.
    copies=[]
    for race in races[:1]:
        for name, kind, supply in (({'terran':'Supply Depot','zerg':'Overlord','protoss':'Pylon'}[race],'structure',0),):
            copies.append({'id':f'crew_{len(copies)+1}','name':name,'race':race,
                           'kind':kind,'supply':supply,'kills':0,'status':'zone'})
    return {'version':1,'copies':copies,'next_id':len(copies)+1,
            'active_mission':None,'owned_purchases':{}}


def _copies(ledger: Mapping[str, Any]) -> list[dict[str, Any]]:
    return list(ledger.get('copies', []))


def supply_capacity(ledger: Mapping[str, Any], *, zone_only: bool=False) -> int:
    return min(DEFAULT_MAX_SUPPLY, sum(
        SUPPLY_STRUCTURES.get(c['name'],0)
        for c in _copies(ledger) if c['status']=='zone' or (not zone_only and c['status']=='deployed')))


def supply_reserved(ledger: Mapping[str, Any], *, include_deployed: bool=True) -> int:
    return sum(float(c.get('supply',0)) for c in _copies(ledger)
               if c['status']=='zone' or (include_deployed and c['status']=='deployed'))


def supply_remaining(ledger: Mapping[str, Any]) -> int:
    return max(0,supply_capacity(ledger)-supply_reserved(ledger))


def counts_by_status(ledger: Mapping[str, Any]) -> dict[str, Counter]:
    out={key:Counter() for key in ('zone','reserve','deployed','lost')}
    for c in _copies(ledger):
        out[c['status']][str(c['name'])]+=1
    return out


def acquire(ledger: dict[str, Any], *, name: str, race: str, kind: str,
            supply: int, quantity: int=1, purchases: bool=False) -> list[str]:
    if kind not in {'unit','structure'} or race not in WORKER_BY_RACE or not name.strip():
        raise ValueError('invalid Crew roster item')
    if float(supply)<0 or int(quantity)<1:
        raise ValueError('supply and quantity must be nonnegative and positive')
    result=[]
    active=ledger.get('active_mission')
    for _ in range(quantity):
        identifier=f"crew_{int(ledger['next_id'])}"
        ledger['next_id']=int(ledger['next_id'])+1
        copy_id={'id':identifier,'name':name,'race':race,'kind':kind,
                 'supply':float(supply),'kills':0,'status':'zone'}
        # Supply is an in-mission deployment constraint only. Never prevent
        # purchased or awarded roster copies entering the deployment zone.
        ledger['copies'].append(copy_id)
        if purchases and active is not None:
            # Existing live deployment manifests stay immutable. New purchases
            # are eligible for later missions or authorized field construction.
            active.setdefault('purchased_during_mission',[]).append(identifier)
        elif active is not None:
            active['pending'].append(identifier)
        result.append(identifier)
    if purchases:
        ledger.setdefault('owned_purchases',{})[name]=int(ledger.get('owned_purchases',{}).get(name,0))+quantity
    return result


def select_zone(ledger:dict[str,Any], copy_id:str, active:bool)->bool:
    matches=[c for c in _copies(ledger) if c['id']==copy_id]
    if len(matches)!=1 or matches[0]['status'] not in {'reserve','zone'}:
        return False
    item=matches[0]
    if active:
        if item['status']=='zone':return True
        item['status']='zone'
        if (ledger.get('active_mission') is not None and
                copy_id not in ledger['active_mission'].get('purchased_during_mission',()) and
                copy_id not in ledger['active_mission']['pending']):
            ledger['active_mission']['pending'].append(copy_id)
    else:
        item['status']='reserve'
        if ledger.get('active_mission') is not None and copy_id in ledger['active_mission']['pending']:
            ledger['active_mission']['pending'].remove(copy_id)
    return True


def deployment_zone_rows(ledger: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One inventory record per name/race/kind, keeping all copies individually tracked."""
    groups: dict[tuple[str,str,str], dict[str, Any]] = {}
    for entry in _copies(ledger):
        key=(entry['name'], entry['race'], entry['kind'])
        group=groups.setdefault(key, {'name':entry['name'],'race':entry['race'],
            'kind':entry['kind'],'supply':float(entry.get('supply',0)),
            'zone':0,'reserve':0,'deployed':0,'lost':0,'kills':0,'total':0})
        if entry['status']!='lost':group['total']+=1
        group['kills']+=int(entry.get('kills',0))
        group[entry['status']]+=1
    # SC2 confirms live death tags before end-of-mission settlement. They are
    # reported separately from permanently lost copies until victory is proven.
    active=ledger.get('active_mission') or {}
    death_tags={str(tag) for tag in active.get('live_dead_tags',())}
    for tag,copy_id in active.get('tags',{}).items():
        if str(tag) not in death_tags:continue
        copy_row=next((c for c in _copies(ledger) if c['id']==copy_id),None)
        if copy_row is None:continue
        key=(copy_row['name'],copy_row['race'],copy_row['kind'])
        if key in groups:groups[key]['killed_in_mission']=groups[key].get('killed_in_mission',0)+1
    # A verified SC2 death is reflected immediately, before the terminal
    # victory settlement changes the stored status to permanent ``lost``.
    claimed=set(active.get('live_claimed_copy_ids',()))
    unbound_dead=set(active.get('unbound_dead_ids',()))
    for entry in _copies(ledger):
        if entry['id'] not in claimed or entry['status'] not in ('zone','reserve'):
            continue
        key=(entry['name'],entry['race'],entry['kind'])
        if key in groups:groups[key]['claimed']=groups[key].get('claimed',0)+1
    for group in groups.values():
        killed=group.setdefault('killed_in_mission',0)
        pending=group.setdefault('claimed',0)
        group['on_field']=max(0,group['deployed']-killed)
        group['ready']=max(0,group['zone']+group['reserve']-pending)
        group['destroyed']=group['lost']+killed
        group['available_total']=max(0,group['total']-killed)
    return sorted(groups.values(),key=lambda row:(row['kind']!='structure',row['race'],row['name'].casefold()))


def set_zone_quantity(ledger:dict[str,Any],name:str,quantity:int,*,race:str|None=None) -> tuple[int,int]:
    """Move idle copies into/out of the zone; active mission copies stay deployed.

    Return the actual counts selected/reserved. Never evict deployed copies,
    and never allow removing supply providers to overbook existing units.
    """
    selected=[c for c in _copies(ledger) if c['name']==name and
              (race is None or c['race']==race) and c['status']!='lost']
    if not selected:
        raise ValueError('Crew unit or structure is not owned')
    fixed=sum(c['status']=='deployed' for c in selected)
    if quantity<fixed or quantity>len(selected):
        raise ValueError('Crew deployment quantity outside owned range')
    zone=[c for c in selected if c['status']=='zone']
    reserved=[c for c in selected if c['status']=='reserve']
    desired=max(0,quantity-fixed)
    if desired<len(zone):
        # Zone selection is independent of supply. Mission deployment is not.
        for c in reversed(zone[desired:]):
            select_zone(ledger,c['id'],False)
    elif desired>len(zone):
        for c in reserved[:desired-len(zone)]:
            if not select_zone(ledger,c['id'],True):
                raise ValueError('Unable to place purchased copy into the deployment zone')
    return (sum(c['status']=='zone' for c in selected),
            sum(c['status']=='reserve' for c in selected))


def purchase_copy(ledger:dict[str,Any], *, name:str, race:str, kind:str,
                  supply:int, minerals:int, gas:int, credits_available:int,
                  quantity:int=1) -> tuple[int,list[str]]:
    """Atomic credit-priced purchase; supply is checked inside the SC2 mission."""
    cost=credit_cost(minerals,gas,unit_name=name)*quantity
    if credits_available<cost:
        raise ValueError('Not enough credits')
    # Validate *before* mutating IDs or copies.
    if kind not in {'unit','structure'} or race not in WORKER_BY_RACE or not name.strip():
        raise ValueError('Invalid Crew purchase')
    if (type(quantity) is not int or quantity < 1 or quantity > 5 or
            not math.isfinite(float(supply)) or supply < 0 or
            minerals < 0 or gas < 0):
        raise ValueError('Invalid Crew purchase quantities or resource costs')
    ids=acquire(ledger,name=name,race=race,kind=kind,supply=supply,quantity=quantity,purchases=True)
    return cost,ids


def begin_mission(ledger:dict[str,Any],mission_id:int)->list[dict[str,Any]]:
    """Prepare pending copies, but do NOT expend any until SC2 binds a real tag.

    Structures that are never built and units whose prerequisite structure is
    absent must remain available for future missions. This is intentionally
    separate from physical deployment, which the SC2 bridge must acknowledge.
    """
    if ledger.get('active_mission') is not None:
        raise ValueError('Crew mission already active: resolve it before launching another')
    if str(int(mission_id)) in ledger.get('settled_missions', {}):
        raise ValueError('Crew mission was already settled; refusing to redeploy copies')
    # Every surviving unused Crew copy is deployable from Reserves; no toggles.
    for entry in _copies(ledger):
        if entry.get('status')=='reserve':entry['status']='zone'
    manifest=[copy.deepcopy(entry) for entry in _copies(ledger) if entry['status']=='zone']
    ledger['active_mission']={'mission_id':int(mission_id),'tags':{},
                              'pending':sorted(entry['id'] for entry in manifest),
                              'deployed':[]}
    return manifest


def bind_unit_tag(ledger:dict[str,Any],copy_id:str,sc2_tag:int)->None:
    """Claim one real SC2 unit for one roster copy; free scripted units are ignored."""
    mission=ledger.get('active_mission')
    if mission is None or copy_id not in mission['pending']:
        raise ValueError('Unit was not pending Crew deployment')
    if sc2_tag<=0 or str(sc2_tag) in mission['tags']:
        raise ValueError('Unit tag must be unique and positive')
    entry=next((c for c in _copies(ledger) if c['id']==copy_id),None)
    if entry is None or entry['status']!='zone':
        raise ValueError('Roster copy is no longer available to deploy')
    # Binding by SC2 tag is the only way to consume a zone unit.
    entry['status']='deployed'
    mission['pending'].remove(copy_id)
    mission['deployed'].append(copy_id)
    mission['tags'][str(sc2_tag)]=copy_id


def complete_mission(ledger:dict[str,Any],mission_id:int,
                     survivors:Mapping[int,int])->dict[str,int]:
    """Return surviving, bound copies; untouched pending entries stay in zone."""
    mission=ledger.get('active_mission')
    if mission is None or mission['mission_id']!=int(mission_id):
        raise ValueError('No matching Crew mission')
    survived={}
    for tag,copy_id in mission['tags'].items():
        if int(tag) in survivors:
            survived[copy_id]=max(0,int(survivors[int(tag)]))
    outcome={'returned':0,'lost':0,'unused':len(mission['pending'])}
    for entry in _copies(ledger):
        if entry['id'] not in mission['deployed']:
            continue
        if entry['id'] in survived:
            entry['status']='zone'
            entry['kills']=int(entry.get('kills',0))+survived[entry['id']]
            outcome['returned']+=1
        else:
            entry['status']='lost'
            outcome['lost']+=1
    ledger['active_mission']=None
    return outcome

def abandon_interrupted_mission(ledger:dict[str,Any], *, verified_game_closed:bool=False) -> dict[str,int]:
    """Close a non-victory SC2 session without carrying its unit tags into a new game.

    A bank-confirmed death remains permanent. Unconfirmed absence is NOT death.
    This is deliberately different from AP-confirmed victory settlement.
    Never reuse the old transport token or starting-unit snapshot.
    """
    active=ledger.get('active_mission')
    if not isinstance(active,dict):return {'returned':0,'lost':0}
    if active.get('terminal_snapshot') is not None and not verified_game_closed:
        raise RuntimeError('Crew terminal snapshot must be settled, not abandoned')
    assigned={str(tag):str(identifier) for tag,identifier in active.get('tags',{}).items()}
    confirmed_dead={str(tag) for tag in active.get('live_dead_tags',())}
    dead_ids={assigned[tag] for tag in confirmed_dead if tag in assigned}
    terminal=active.get('terminal_snapshot')
    if isinstance(terminal,dict) and verified_game_closed:
        # A verified complete terminal snapshot is authoritative evidence that
        # any absent bound tag died, even if victory settlement itself failed.
        alive={str(tag) for tag in terminal.get('alive_tags',())}
        dead_ids.update(identifier for tag,identifier in assigned.items() if tag not in alive)
    dead_ids.update(str(x) for x in active.get('unbound_dead_ids',()))
    outcome={'returned':0,'lost':0}
    for entry in _copies(ledger):
        if entry.get('status')=='lost':continue
        if entry['id'] in dead_ids:
            entry['status']='lost'
            outcome['lost']+=1
        elif entry.get('status') in {'zone','reserve','deployed'}:
            if entry.get('status')=='deployed':outcome['returned']+=1
            entry['status']='zone'
    # Reset pending transactions, completed receipt IDs and the SC2-bank token
    # together. They describe the old game, not persistent purchased copies.
    ledger['active_mission']=None
    return outcome


def fail_mission(ledger:dict[str,Any])->None:
    """Do not silently erase untracked survivors on an interrupted mission."""
    if ledger.get('active_mission') is None:return
    # The client cannot infer deaths after an interrupted session. Hold the
    # mission open for recovery, rather than assuming everyone is alive/dead.
    raise RuntimeError('Crew mission interrupted: require an explicit recovery decision')


def normalized_ledger(value:Any,races:Sequence[str]=DEFAULT_CREW_RACES)->dict[str,Any]:
    if not isinstance(value,dict):return default_roster(races)
    result=copy.deepcopy(value)
    if not isinstance(result.get('copies'),list) or not isinstance(result.get('next_id'),int):
        raise ValueError('invalid Crew roster: refusing to discard saved copies')
    if len({c.get('id') for c in result['copies']})!=len(result['copies']):
        raise ValueError('duplicate Crew copy IDs')
    converted=[]
    for copy_row in result['copies']:
        if copy_row.get('status')=='reserve':
            copy_row['status']='zone'
            converted.append(copy_row['id'])
    active=result.get('active_mission')
    if isinstance(active,dict):
        pending=active.setdefault('pending',[])
        for identifier in converted:
            if identifier not in pending:
                pending.append(identifier)
    return result


def shop_categories(catalog: Sequence[Mapping[str,Any]], races:Sequence[str],
                    *, completed_layers:int, total_layers:int,
                    owned_units:Sequence[str] = (), seed:int=0,
                    frozen_offer:str="", expansion:int=0) -> dict[str,list[dict[str,Any]]]:
    """Build Crew-only shop inventory from a validated, costed game-data catalog.

    Entries must include name/race/category/minerals/gas. A unit upgrade may
    specify its required parent via `parent` (name). This is a pure shop-pool
    calculation, not a purchase, so it does not change the roster or credits.
    """
    active_races=set(races)
    if not active_races or not active_races<=set(WORKER_BY_RACE):
        raise ValueError('Crew shop requires at least one valid race')
    from .crew_catalog import CREW_BLOCKED_REACTOR_ITEMS
    entries=[dict(x) for x in catalog if x.get('race') in active_races
             and x.get('name') not in CREW_BLOCKED_REACTOR_ITEMS]
    for e in entries:
        if not {'name','race','category','minerals','gas'} <= e.keys():
            raise ValueError(f'Crew shop entry missing essential fields: {e}')
        if int(e['minerals'])<0 or int(e['gas'])<0:
            raise ValueError('Crew shop costs must be nonnegative')
        e['credits']=credit_cost(int(e['minerals']),int(e['gas']),unit_name=str(e['name']))
    structures=sorted((e for e in entries if e['category']=='structure'),
                      key=lambda e:(e['race'],str(e['name']).lower()))
    # The three mandatory supply providers and workers are fixed offers, but
    # production variants stay race-specific and ALL structures remain offered.
    units=[e for e in entries if e['category']=='unit' and e['name'] not in WORKER_NAMES]
    cheap=eligible_unit_pool(units,completed_layers,total_layers)
    rng=random.Random(seed)
    # A purchased Shop Expansion grants additional *Crew* unit offers,
    # not just slots in Standard's independently rolled AP shop.
    expansion=max(0,min(3,int(expansion)))
    unit_roll=rng.sample(cheap,min(3+expansion,len(cheap)))
    frozen=next((u for u in units if u['name']==frozen_offer),None)
    if frozen is not None and all(u['name']!=frozen_offer for u in unit_roll):
        if len(unit_roll)==3+expansion:unit_roll[-1]=frozen
        else:unit_roll.append(frozen)
    present={e['name'] for e in unit_roll}|set(owned_units)
    upgrades=[e for e in entries if e['category']=='upgrade' and
              e['name']!='Tech Reactor (Terran)' and
              (not e.get('parent') or e['parent'] in present)]
    upgrade_roll=rng.sample(upgrades,min(3+expansion,len(upgrades)))
    return {'Structures':structures,'Units':unit_roll,'Unit Upgrades':upgrade_roll}


def revive_destroyed(ledger:dict[str,Any], *, name:str, race:str, kind:str,
                     quantity:int, supply:float) -> list[str]:
    """Restore destroyed copies using NEW identifiers; old bank tags stay dead.

    This avoids old death/claim events prematurely killing the revived unit.
    Callers must independently validate current catalog pricing and credits.
    """
    if kind!='unit' or quantity not in (1,5):
        raise ValueError('Only unit copies support Revive 1 or Revive 5')
    active=ledger.get('active_mission')
    # A bank-confirmed unit death is already shown as Destroyed in the
    # inventory before the mission is settled. Such a paid copy is revivable;
    # a merely missing unit, pending purchase or free mission unit is not.
    confirmed_dead=set()
    if isinstance(active,dict):
        dead_tags={str(t) for t in active.get('live_dead_tags',())}
        confirmed_dead={str(ident) for tag,ident in active.get('tags',{}).items()
                        if str(tag) in dead_tags}
    matches=[c for c in ledger['copies'] if c['name']==name and c['race']==race
             and c['kind']==kind and (c['status']=='lost' or
               (c['status']=='deployed' and c['id'] in confirmed_dead))]
    if len(matches)<quantity:
        raise ValueError('Not enough destroyed copies to revive')
    removed={c['id'] for c in matches[:quantity]}
    active=ledger.get('active_mission')
    if isinstance(active,dict):
        old_tags={tag for tag,ident in active.get('tags',{}).items() if ident in removed}
        active['tags']={tag:ident for tag,ident in active.get('tags',{}).items() if ident not in removed}
        active['live_dead_tags']=[x for x in active.get('live_dead_tags',()) if str(x) not in old_tags]
        active['unbound_dead_ids']=[x for x in active.get('unbound_dead_ids',()) if x not in removed]
        active['live_claimed_copy_ids']=[x for x in active.get('live_claimed_copy_ids',()) if x not in removed]
        for key in ('pending','deployed','purchased_during_mission'):
            if key in active:active[key]=[x for x in active[key] if x not in removed]
    ledger['copies']=[c for c in ledger['copies'] if c['id'] not in removed]
    return acquire(ledger,name=name,race=race,kind=kind,supply=supply,
                   quantity=quantity,purchases=False)
