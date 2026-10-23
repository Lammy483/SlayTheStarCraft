"""Crew-only Archipelago SC2 BotAI bridge for purchased production.

Runs only when a Crew mission was explicitly staged in its persistent ledger.
The bot samples actual unit tags, owner IDs and native types; the SC2-written
bank must independently name the same unit before its roster copy is bound.
Standard/Campaign bot control flow is untouched. Crew is enabled in dev builds.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from .crew_bank_receipts import read_bank_status
from .crew_sc2_adapter import CrewUnitObservation, NATIVE_TYPES, STRUCTURE_TYPES
from .crew_tags import matching_full_tags

# `unit.name` may be localized/display-spaced, while `type_id.name` is an enum.
# Accept only an explicitly mapped native CUnit ID. Unknown AP variants are
# preserved in the baseline snapshot, but never mistaken for eligible copies.
_NORMALIZE = re.compile(r'[^A-Za-z0-9]')
from .crew_sc2_adapter import CREW_MERCENARY_NATIVE
_EXACT_NATIVE_CUNITS = frozenset(NATIVE_TYPES.values()) | frozenset(CREW_MERCENARY_NATIVE)
_LOOKUP = {_NORMALIZE.sub('', k).casefold():k for k in _EXACT_NATIVE_CUNITS}
_KNOWN_BUILDINGS = STRUCTURE_TYPES
# Verified in the Dev30 live SC2 observations: Archipelago structures use
# custom CUnit IDs that python-sc2's UnitTypeId enum does not contain.
# Pair BOTH the exact game-data catalog name and the observed raw SC2 unit id.
# AP_MercCompound is not a purchasable Crew building, so preserve its own
# identifier rather than incorrectly treating it as a Barracks or other offer.
_AP_WORKER_VARIANTS = {'AP_SCV':'SCV', 'AP_Drone':'Drone', 'AP_Probe':'Probe'}
# Domination may create Mengsk/Trooper weapon-configured native units rather
# than the simple Trooper CUnit used by the Crew production bridge. Exact,
# nonlocalized SC2 catalog identities only; never fuzzy display-name matching.
_TROOPER_CUNIT_ALIASES = frozenset({
    'Trooper','AP_Trooper','TrooperMengsk','AP_TrooperMengsk',
    'TrooperRifle','AP_TrooperRifle','TrooperFlamethrower',
    'AP_TrooperFlamethrower','TrooperMissileLauncher',
    'AP_TrooperMissileLauncher',
})
_AP_CUNIT_BY_RAW_ID = {
    2099: ('AP_CommandCenter', 'CommandCenter'),
    2058: ('AP_SupplyDepot', 'SupplyDepot'),
    2082: ('AP_Barracks', 'Barracks'),
    2300: ('AP_MercCompound', 'AP_MercCompound'),
}


def probe_note(ctx, phase: str, detail: str) -> None:
    """Persist Crew-only preflight breadcrumbs even when client stdout is hidden.

    Never alter normal game modes. This is diagnostic output, not proof of an
    SC2 receipt; only a verified ReadyAnchor produces a PASS result.
    """
    if os.environ.get('SLAY_CREW_TEST_MODE') != 'probe':
        return
    key=str(phase)
    seen=getattr(ctx,'_slay_crew_probe_phases',None)
    if seen is None:
        seen=set()
        ctx._slay_crew_probe_phases=seen
    if key in seen:
        return
    seen.add(key)
    message=f'Crew probe [{key}]: {detail}'
    print(message,flush=True)
    root=os.environ.get('SLAY_PORTABLE_ROOT','').strip()
    if not root:
        return  # No surprise writes outside the portable game directory.
    try:
        target=Path(root)/'Runtime'/'Logs'/'CrewProbe.log'
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('a',encoding='utf-8') as log:
            log.write(message+'\n')
    except OSError:
        pass  # A logging failure must not interfere with the SC2 handshake.


def live_test_authorized(ctx) -> bool:
    """Normal Crew missions run live, without developer environment flags.

    Probe mode is an explicit non-destructive diagnostic override. Actual
    transport and settlement remain gated independently by the matching staged
    mission, readable SC2 controller and confirmed native receipts.
    """
    config = getattr(ctx, 'slay_config', {}) or {}
    return (config.get('game_mode') == 'crew' and
            os.environ.get('SLAY_CREW_TEST_MODE') != 'probe')


def crew_live_note(ctx, phase: str, detail: str) -> None:
    """Durable diagnostic trail for the separately authorized live test."""
    if not live_test_authorized(ctx):
        return
    message=f'Crew live [{phase}]: {detail}'
    print(message,flush=True)
    root=os.environ.get('SLAY_PORTABLE_ROOT','').strip()
    if root:
        try:
            target=Path(root)/'Runtime'/'Logs'/'CrewLive.log'
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('a',encoding='utf-8') as log:
                log.write(message+'\n')
        except OSError:
            pass

# Terran lift-off changes the CUnit ID without changing the physical actor.
# This normalization is ONLY for roster/debit accounting, not production abilities.
_FLYING_TO_GROUNDED = {
    'CommandCenterFlying':'CommandCenter',
    'OrbitalCommand':'CommandCenter',
    'OrbitalCommandFlying':'CommandCenter',
    'BarracksFlying':'Barracks',
    'FactoryFlying':'Factory',
    'StarportFlying':'Starport',
}


def accounted_native_type(unit) -> str:
    """Canonical physical structure across lift-off for per-actor debit checks."""
    raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
    name=getattr(getattr(unit,'_type_data',None),'name',None)
    if type(raw) is int and raw>0 and isinstance(name,str):
        native=name[3:] if name.startswith('AP_') else name
        if native in _FLYING_TO_GROUNDED:
            return _FLYING_TO_GROUNDED[native]
    return native_type(unit)


def accounted_structure(unit) -> bool:
    raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
    name=getattr(getattr(unit,'_type_data',None),'name',None)
    if type(raw) is int and raw>0 and isinstance(name,str):
        native=name[3:] if name.startswith('AP_') else name
        if native in _FLYING_TO_GROUNDED:
            return True
    return bool(getattr(unit,'is_structure',False))


def native_type(unit) -> str:
    # Native Terran add-ons are distinct SC2 CUnits but use a single Crew
    # purchased Tech Lab entitlement. Never infer them from translated names.
    raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
    catalog_name=getattr(getattr(unit,'_type_data',None),'name',None)
    if (bool(getattr(unit,'is_structure',False)) and type(raw) is int and raw>0
            and catalog_name in {'BarracksTechLab','FactoryTechLab','StarportTechLab',
                                 'AP_BarracksTechLab','AP_FactoryTechLab',
                                 'AP_StarportTechLab','TechLab','AP_TechLab'}):
        return 'TechLab'
    # An enum member is an exact SC2 type identity, not a localized display
    # name. AP custom units may have no UnitTypeId enum member at all.
    enum_name=getattr(getattr(unit,'type_id',None),'name',None)
    if not bool(getattr(unit,'is_structure',False)) and type(raw) is int and raw>0:
        # The raw CUnit catalog is more accurate than python-sc2 enum names for
        # Dominion variants. Each accepted name is explicitly whitelisted.
        if catalog_name in _TROOPER_CUNIT_ALIASES:
            return 'Trooper'
    if isinstance(enum_name,str) and enum_name:
        native=_LOOKUP.get(_NORMALIZE.sub('',enum_name).casefold())
        if native is not None:
            # An API enum that describes a unit cannot identify an observed
            # structure; reject contradictory SC2 metadata fail-closed.
            if bool(getattr(unit,'is_structure',False)) and native not in _KNOWN_BUILDINGS:
                return 'unmapped:enum-inconsistent-structure'
            return native
        if enum_name.startswith('AP_'):
            base=_LOOKUP.get(_NORMALIZE.sub('',enum_name[3:]).casefold())
            if (base is not None and
                    bool(getattr(unit,'is_structure',False)) == (base in _KNOWN_BUILDINGS)):
                return base
        if not bool(getattr(unit,'is_structure',False)) and enum_name in _AP_WORKER_VARIANTS:
            raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
            catalog_name=getattr(getattr(unit,'_type_data',None),'name',None)
            if type(raw) is int and raw>0 and catalog_name == enum_name:
                return _AP_WORKER_VARIANTS[enum_name]
        return 'unmapped:' + enum_name

    # For AP custom structures absent from the enum, use the **raw catalog
    # identity**, never Unit.name (which can be translated/display-specific).
    # A name alone is insufficient: the numeric raw ID must also match a
    # catalog entry verified against live SC2 observations.
    raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
    catalog_name=getattr(getattr(unit,'_type_data',None),'name',None)
    if bool(getattr(unit,'is_structure',False)):
        match=_AP_CUNIT_BY_RAW_ID.get(raw) if type(raw) is int else None
        if match is not None:
            return match[1] if catalog_name == match[0] else 'unmapped:no-native-enum'
        # Archipelago generates catalog variants with IDs that differ by
        # mission and dependency set. The nonlocalized engine CUnit entry is
        # authoritative; keep unknown variants distinct and fail closed.
        if (type(raw) is int and raw > 0 and isinstance(catalog_name,str)
                and catalog_name.startswith('AP_')):
            suffix=catalog_name[3:]
            if suffix in _EXACT_NATIVE_CUNITS and suffix in _KNOWN_BUILDINGS:
                return suffix
            if suffix in ('MercCompound','MercenaryCompound','PredatorNest',
                          'ZergMercenaryCompound','ZergPredatorNest'):
                return catalog_name
    else:
        # AP workers have no python-sc2 UnitTypeId enum. Match the exact
        # nonlocalized CUnit ID, not Unit.name / a translated UI label.
        if type(raw) is int and raw>0 and catalog_name in _AP_WORKER_VARIANTS:
            return _AP_WORKER_VARIANTS[catalog_name]
        # AP campaign combat units often have no python-sc2 UnitTypeId enum.
        # Require an engine catalog identity, raw numeric type and an exact
        # allowed CUnit suffix; a UI/display name alone never authorizes one.
        if (type(raw) is int and raw>0 and isinstance(catalog_name,str)
                and catalog_name.startswith('AP_') and
                catalog_name[3:] in _EXACT_NATIVE_CUNITS and
                catalog_name[3:] not in _KNOWN_BUILDINGS):
            return catalog_name[3:]

    # Ordinary UnitCreate("Barracks"), UnitCreate("SCV"), and
    # UnitCreate("Marine") also commonly return Unit.type_id=None in the
    # Archipelago modded catalog (live Dev34: raw id=21, catalog="Barracks").
    # These are native canonical CUnit IDs already allowed by the Galaxy
    # whitelist. Trust the *engine catalog name* only when accompanied by
    # a real numeric SC2 unit type and consistent structure classification.
    # Identity/ownership still requires the separate SC2 banked unit tag.
    if (type(raw) is int and raw > 0 and
            isinstance(catalog_name, str) and
            catalog_name in _EXACT_NATIVE_CUNITS and
            bool(getattr(unit,'is_structure',False)) == (catalog_name in _KNOWN_BUILDINGS)):
        return catalog_name
    return 'unmapped:no-native-enum'


def unknown_structure_diagnostics(bot, unresolved_tags) -> str:
    """Record native SC2 fields, not unverified display-name substitutions.

    This allows diagnosing AP/custom unit IDs without ever identifying a
    building from a localized name for destructive reconciliation.
    """
    tags=set(unresolved_tags)
    result=[]
    for unit in getattr(bot,'structures',()):
        if getattr(unit,'tag',None) not in tags:continue
        tid=getattr(unit,'type_id',None)
        raw=getattr(getattr(unit,'_proto',None),'unit_type',None)
        display=str(getattr(unit,'name',''))[:70].replace('\n',' ')
        data_name=str(getattr(getattr(unit,'_type_data',None),'name',''))[:70].replace('\n',' ')
        result.append(f'tag={unit.tag}, type_id={str(tid)[:70]}, '
                      f'enum_name={getattr(tid,"name",None)}, raw_id={raw}, '
                      f'name={display!r}, type_data_name={data_name!r}')
    return '; '.join(result[:16])


def observations(bot) -> tuple[CrewUnitObservation,...]:
    """Take one snapshot, including both player mobile units and structures.

    Never silently assign player ID 1, since campaign missions can use other
    owners. A reported unit with no proven owner must not enter the snapshot.
    """
    result={}

    def add(unit, *, carrier_position=None):
        tag=getattr(unit,'tag',None)
        owner=getattr(unit,'owner_id',None)
        pos=getattr(unit,'position',None)
        # A loaded passenger can lack an independent world position, but the
        # visible transport supplies one. NEVER infer its owner or native type
        # from the carrier: those are required from the passenger itself.
        if pos is None:
            pos=carrier_position
        if type(tag) is not int or tag<=0 or type(owner) is not int or owner<=0:
            return
        if pos is None:
            return
        observed=CrewUnitObservation.parse({
            'tag':tag,'native_type':accounted_native_type(unit),'owner':owner,
            'x':pos.x,'y':pos.y,'is_structure':accounted_structure(unit)})
        old=result.get(tag)
        if old is not None and (old.native_type,old.owner,old.is_structure) != (observed.native_type,observed.owner,observed.is_structure):
            raise ValueError('Conflicting Crew live observations for one SC2 unit tag')
        # Prefer a map position if a tag appears both in the world snapshot and
        # a transport manifest; either position is irrelevant to ownership.
        if old is None:
            result[tag]=observed

    groups=[getattr(bot,'units',()),getattr(bot,'structures',())]
    # Campaign variants do not always include workers or newly created mobile
    # actors in BotAI.units on the same frame. Other BotAI collections provide
    # an independently tagged observation of that *same actor*; the bank tag,
    # player owner and CUnit identity must still pass strict validation.
    for attribute in ('workers','townhalls','all_units'):
        extra=getattr(bot,attribute,None)
        if extra is not None:
            groups.append(extra)
    for group in groups:
        for unit in group:
            add(unit)
            # python-sc2 excludes loaded units from BotAI.units/structures,
            # but exposes their real tags/types/owners as Unit.passengers for
            # Medivacs, Bunkers, Overlords, Warp Prisms, Nydus, etc. Without
            # this, surviving loaded units would be permanently lost at victory.
            for passenger in getattr(unit,'passengers',()) or ():
                add(passenger,carrier_position=getattr(unit,'position',None))
    return tuple(result[tag] for tag in sorted(result))


def banks() -> tuple[Path,...]:
    """Find SC2 banks below the actual StarCraft II Documents root.

    SC2 uses several layouts, notably Documents/StarCraft II/Banks/<author>
    and Documents/StarCraft II/Accounts/<account>/<profile>/Banks/<author>.
    Restrict file search to the exact Crew bank basename. Do not treat an
    absent file as a successful handshake and never mutate player banks.
    """
    override=os.environ.get('SLAY_CREW_BANK_ROOTS','').strip()
    if override:
        return tuple(dict.fromkeys(Path(v) for v in override.split(os.pathsep)
                                   if v.strip()))
    home=Path.home()
    document_folders=[home/'Documents', home/'OneDrive'/'Documents']
    onedrive=os.environ.get('OneDrive','')
    if onedrive:
        document_folders.append(Path(onedrive)/'Documents')
    # Windows can redirect Documents to a different volume or OneDrive.
    # Avoid importing winreg on non-Windows platforms and test runners.
    if os.name=='nt':
        try:
            import winreg
            key=r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as handle:
                value,_=winreg.QueryValueEx(handle,'Personal')
                document_folders.append(Path(os.path.expandvars(value)))
        except (OSError,ImportError):
            pass
    roots=[]
    for doc in document_folders:
        folder=doc/'StarCraft II'
        if folder.is_dir():
            roots.append(folder)
    return tuple(dict.fromkeys(roots))


def bank_files(roots) -> tuple[Path,...]:
    """Enumerate candidate files for diagnosis, with no reads or writes."""
    files=set()
    for root in roots:
        try:
            if Path(root).is_dir():
                files.update(Path(root).rglob('SlayTheStarCraftCrew.SC2Bank'))
        except OSError:
            continue
    return tuple(sorted(files))


def cached_bank_paths(ctx, roots) -> tuple[Path,...]:
    """Reuse already-discovered exact SC2 bank paths during fast deployment.

    Bank XML is still reread and token-validated on EVERY poll. Only the
    expensive recursive filesystem discovery is cached. A missing bank is
    rescanned frequently while waiting for base established; existing bank
    files are re-discovered periodically for profile/account changes.
    """
    roots=tuple(Path(p) for p in roots)
    now=time.monotonic()
    record=getattr(ctx,'_slay_crew_bank_path_cache',None)
    if (record is None or record[0]!=roots or now>=record[2] or
        any(not p.is_file() for p in record[1])):
        found=bank_files(roots)
        record=(roots,found,now+(4.0 if found else 0.25))
        ctx._slay_crew_bank_path_cache=record
    return record[1] or roots


def deployment_anchor(snapshot, bot) -> tuple[bool,int]:
    """Require a completed observed player structure. Galaxy checks macro base."""
    player=getattr(bot,'player_id',None)
    if type(player) is not int or not 0<player<=16:return False,0
    live=[]
    for item in bot.structures:
        if (getattr(item,'owner_id',None)==player and getattr(item,'is_ready',False)
                and type(getattr(item,'tag',None)) is int):
            live.append(item)
    if not live:return False,0
    townhalls={'CommandCenter','Hatchery','Nexus'}
    live.sort(key=lambda u:(native_type(u) not in townhalls, int(u.tag)))
    return True,int(live[0].tag)


def ready_prerequisites(bot, *, include_unfinished: bool = False) -> tuple[str, ...]:
    """Actual player-owned, completed structures can satisfy Crew prerequisites.

    A map-native Barracks can physically support a Marine deployment without
    making the Barracks an owned Crew roster copy. Do not count unfinished,
    allied, enemy, unmapped or unobserved buildings, and do not infer that
    their attached units or upgrades also belong to the Crew.
    """
    from .crew_catalog import preview_catalog
    player=getattr(bot,'player_id',None)
    if type(player) is not int or not 0<player<=16:
        return ()
    allowed={str(e['requires']) for e in preview_catalog(('terran','zerg','protoss'))
             if e.get('requires')}
    name_for_native={NATIVE_TYPES.get(name,name):name for name in allowed}
    result=set()
    for unit in bot.structures:
        if getattr(unit,'owner_id',None)!=player:
            continue
        if bool(getattr(unit,'is_ready',False)) == include_unfinished:
            continue
        name=name_for_native.get(native_type(unit))
        if name is not None:
            result.add(name)
    return tuple(sorted(result))


async def field_build_step(bot, status, observed, player: int) -> str | None:
    """Synchronize paid field-build charges only after verified deployment End.

    Neither a stock chat message nor a bank receipt by itself claims an actor.
    The spawned building must be uniquely present and fully completed in the
    independent SC2 controller view before one permanent copy is consumed.
    """
    from . import slay_the_starcraft as slay
    from .crew_field_build import stock_commands
    ctx=bot.ctx
    active=slay.crew_roster(ctx).get('active_mission') or {}
    auto=active.get('auto_transport') or {}
    if not auto.get('ended') or active.get('terminal_snapshot') is not None:
        return None
    slay.crew_record_live_claims(ctx,bot.mission_id,status.production_claims)
    receipts=status.build_receipts
    if receipts:
        ready_tags=frozenset(int(unit.tag) for unit in bot.structures
                              if getattr(unit,'owner_id',None)==player
                              and getattr(unit,'is_ready',False))
        try:
            slay.crew_accept_field_builds(ctx,bot.mission_id,
                receipts=receipts,observations=observed,
                ready_tags=ready_tags,player_id=player,
                death_tags=status.death_tags)
        except (ValueError,RuntimeError) as exc:
            # A bank receipt may arrive before BotAI has observed its actor.
            # Await the matching full tag instead of consuming a purchased
            # copy, inventing one, or flooding the live diagnostics.
            now=time.monotonic()
            sign=(type(exc).__name__,str(exc))
            if (sign!=getattr(ctx,'_slay_field_error',None) or
                now-getattr(ctx,'_slay_field_error_at',0)>6.0):
                crew_live_note(ctx,'field-build-waiting',repr(sign))
                ctx._slay_field_error=sign
                ctx._slay_field_error_at=now
    if getattr(status,'train_receipts',()):
        try:
            from .crew_native_train import accept_native_trains
            accept_native_trains(ctx,bot.mission_id,status.train_receipts,observed,player,
                                 death_tags=status.death_tags,
                                 authorized=status.build_authorized)
        except (ValueError,RuntimeError) as exc:
            now=time.monotonic()
            signature=(type(exc).__name__,str(exc))
            if (signature!=getattr(ctx,'_slay_train_error',None) or
                now-getattr(ctx,'_slay_train_error_at',0.0)>6.0):
                crew_live_note(ctx,'native-train-waiting',repr(signature))
                ctx._slay_train_error=signature
                ctx._slay_train_error_at=now
    diagnostic=getattr(status,'production_debug',())
    if diagnostic != getattr(ctx,'_slay_crew_prod_diag_seen',()):
        crew_live_note(ctx,'production-diag',' '.join(f'{k}={v}' for k,v in diagnostic))
        ctx._slay_crew_prod_diag_seen=diagnostic
    # Acknowledgments are independent of the chat-send log. Log a change once
    # per bank snapshot to distinguish "Marine not yet advertised" from
    # "Marine authorized but native training did not finish" in live tests.
    current_auth=frozenset(status.build_authorized)
    if current_auth != getattr(ctx,'_slay_crew_stock_ack_seen',frozenset()):
        crew_live_note(ctx,'native-stock-ack',
            f'authorized_count={len(current_auth)} newly_acknowledged='
            f'{sorted(current_auth-getattr(ctx,"_slay_crew_stock_ack_seen",frozenset()))[:24]}')
        ctx._slay_crew_stock_ack_seen=current_auth
    remaining=stock_commands(slay.crew_roster(ctx),bot.mission_id,
                              status.build_authorized)
    if not remaining:return None
    command=remaining[0]
    now=time.monotonic()
    last=getattr(ctx,'_slay_field_stock_command',None)
    last_at=getattr(ctx,'_slay_field_stock_at',0.0)
    if command==last and now-last_at<1.0:return None
    ctx._slay_field_stock_command=command
    ctx._slay_field_stock_at=now
    if command!=last:
        crew_live_note(ctx,'field-build-stock',
            f'Crew Build/Train stock advertised: {command[:230]}')
    await bot.chat_send(command)
    return command


def discover_controllable_units(bot, observed, player: int, *,
                                exclude_wire_tags=frozenset()):
    """Scan every player-owned CUnit, including loaded campaign reinforcements.

    Actor identity is an observed SC2 tag + owner + canonical catalog type.
    Some AP units do not implement python-sc2's is_mine/is_commandable
    properties even though they are owned; explicit False still vetoes a unit.
    No hero, temporary timed-life, hallucination or unpurchasable class enters
    the roster (the catalog/AP item allowlist checks that separately).
    """
    from .crew_tags import wire_tag
    by_tag={r.tag:r for r in observed if not r.is_structure and r.owner==player}
    found={}
    collections=[]
    for name in ('units','workers','all_units'):
        group=getattr(bot,name,None)
        if group is not None:collections.append(group)
    for collection in collections:
        for unit in collection:
            # Passengers are usually absent from BotAI.units; they have exact
            # native owner/type/tag and can be adopted while in transports.
            for actor in (unit,*(getattr(unit,'passengers',()) or ())):
                tag=getattr(actor,'tag',None)
                if type(tag) is not int or tag not in by_tag:continue
                # Building Turrets draws a nonselectable Battlecruiser proxy
                # per building. SC2's Python Unit.is_selectable can still be
                # True for these. Its native max life is explicitly 1, unlike
                # a genuine BC; don't persist or double it in Crew.
                if (native_type(actor)=='Battlecruiser' and
                        getattr(actor,'health_max',float('inf'))<=1):
                    continue
                if (getattr(actor,'owner_id',None)!=player or
                    accounted_structure(actor) or
                    getattr(actor,'is_ready',True) is False or
                    getattr(actor,'is_visible',True) is False or
                    getattr(actor,'is_hallucination',False) or
                    getattr(actor,'is_blip',False) or
                    getattr(actor,'is_snapshot',False) or
                    getattr(actor,'is_selectable',True) is False or
                    getattr(actor,'is_commandable',True) is False or
                    getattr(actor,'is_temporary',False) or
                    getattr(actor,'is_timed_life',False)):
                    continue
                try: short=wire_tag(tag)
                except ValueError:
                    # An unrepresentable signed Galaxy chat tag cannot be
                    # acknowledged/doubled safely. Skip only this one actor.
                    continue
                if short in exclude_wire_tags:continue
                found[tag]=by_tag[tag]
    return tuple(found[tag] for tag in sorted(found))


async def auto_step(bot, *, bank_roots=None) -> str | None:
    """Crew v62: activate production without deleting or deploying map units.

    The sole handshake is a mission-scoped Galaxy bank token. Normal starting
    units and buildings remain in place and remain temporary/unowned Crew
    assets. A uniquely banked paid TRAIN/BUILD receipt is still required to
    bind anything to the persistent Crew roster.
    """
    from . import slay_the_starcraft as slay
    ctx=bot.ctx
    if not slay.crew_mode(ctx) or not slay.state_ready(ctx):
        return None
    if not getattr(bot,'can_read_game',False) or not getattr(bot,'game_running',False):
        return None
    if os.environ.get('SLAY_CREW_TEST_MODE')=='probe':
        # Probe is read-only: never send production or delete anything.
        probe_note(ctx,'direct-session','Crew direct mode: startup cleanup disabled')
        return None
    if not live_test_authorized(ctx):
        return None
    player=getattr(bot,'player_id',None)
    mission_id=getattr(bot,'mission_id',None)
    if type(player) is not int or not 0<player<=16 or type(mission_id) is not int:
        return None
    active=slay.crew_roster(ctx).get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        crew_live_note(ctx,'waiting-stage',f'Mission={mission_id} roster not staged')
        return None

    # A new SC2 BotAI instance is a NEW mission attempt, even if it shares a
    # long-lived Slay process. Return surviving roster copies to Reserves and
    # retain only already-confirmed deaths from the prior attempt.
    if not getattr(bot,'_slay_crew_new_game_checked',False):
        bot._slay_crew_new_game_checked=True
        if active.get('auto_transport') is not None:
            result=slay.crew_abandon_interrupted_session(ctx)
            slay.crew_ensure_mission_staged(ctx,mission_id)
            crew_live_note(ctx,'new-game-reset',
                f'Returned {result["returned"]} deployed copies; '
                f'preserved {result["lost"]} confirmed losses')

    now=time.monotonic()
    if now-getattr(ctx,'_slay_last_item_grants_sync',0.0)>=2.0:
        slay.crew_sync_item_grants(ctx)
        ctx._slay_last_item_grants_sync=now

    observed=observations(bot)
    slay.crew_record_live_snapshot(ctx,mission_id,
                                   observations=observed,player_id=player)
    # The original map-owned actors are recorded ONLY to distinguish them from
    # paid completions. They are NEVER removed, spawned or auto-purchased.
    token=slay.crew_initialize_auto_transport(ctx,mission_id,player,
                                               starting_observations=observed)
    roots=banks() if bank_roots is None else tuple(bank_roots)
    if getattr(ctx,'_slay_crew_logged_token',None)!=token:
        ctx._slay_crew_logged_token=token
        ctx._slay_crew_stock_ack_seen=frozenset()
        ctx._slay_crew_unlock_announced=set()
        ctx._slay_crew_prod_diag_seen=()
        ctx._slay_crew_seen_free_buildings={}
        ctx._slay_crew_seen_ready_buildings={}
        ctx._slay_field_stock_command=None
        ctx._slay_field_stock_at=0.0
        ctx._slay_crew_session_retry_at=0.0
        crew_live_note(ctx,'direct-start',f'Mission={mission_id} player={player} '
            f'token={token}; no starting-unit deletion or auto deployment')
    # Track every actually observed free building by its *bank wire tag*.
    # Store type and owner as well as the tag: a bank-only death could
    # otherwise charge a structure 200 times in a misconfigured mission.
    observed_buildings=getattr(ctx,'_slay_crew_seen_free_buildings',{})
    ready_buildings=getattr(ctx,'_slay_crew_seen_ready_buildings',{})
    ready_tags=set()
    for collection in ('structures','townhalls','all_units'):
        for u in getattr(bot,collection,()) or ():
            if (getattr(u,'owner_id',None)!=player or
                not accounted_structure(u) or
                type(getattr(u,'tag',None)) is not int):
                continue
            if getattr(u,'is_ready',False) or getattr(u,'build_progress',0.0)>=0.999:
                ready_tags.add(u.tag)
    for unit in observed:
        # Do not let a malformed/partial observer row interrupt Crew startup.
        if (getattr(unit,'owner',None)==player and
            getattr(unit,'is_structure',False) and
            getattr(unit,'native_type',None) in _KNOWN_BUILDINGS and
            type(getattr(unit,'tag',None)) is int):
            observed_buildings[int(unit.tag)&0xffffffff]=unit.native_type
            if unit.tag in ready_tags:
                ready_buildings[int(unit.tag)&0xffffffff]=unit.native_type
    ctx._slay_crew_seen_free_buildings=observed_buildings
    ctx._slay_crew_seen_ready_buildings=ready_buildings
    status=read_bank_status(token,cached_bank_paths(ctx,roots))
    if status.death_tags:
        slay.crew_record_live_deaths(ctx,mission_id,status.death_tags)
    if status.free_building_deaths:
        slay.crew_charge_free_building_deaths(ctx,mission_id,status.free_building_deaths,
                                            verified_tags=ready_buildings)
    for notice in slay.crew_take_loss_notifications(ctx):
        # Print through the Galaxy Slay chat UI, not an ArchipelagoBot player
        # chat bubble that can be hidden by its AP overlay.
        match=re.fullmatch(r'(.+) destroyed, subtracting ([0-9]+) credits',notice)
        if match:
            cost=int(match.group(2));display=match.group(1).replace(' ','_')
            if 1<=cost<=1000 and re.fullmatch(r'[A-Za-z0-9_]+',display):
                await bot.chat_send(f'?SlayCrewLoss {token} {cost} {display}')
        else:
            crew_live_note(ctx,'loss-notice-skipped',repr(notice))

    if not status.ready:
        # Galaxy uses the matching token to initialize the production/death
        # bank. It no longer waits for macro-base establishment or native
        # reconciliation. Retry idempotently if the chat precedes the mod load.
        if now-getattr(ctx,'_slay_crew_session_retry_at',0.0)<1.0:
            return None
        ctx._slay_crew_session_retry_at=now
        command=f'?SlayCrewSession {token}'
        await bot.chat_send(command)
        return command

    # A bank-ready direct session has NO further setup phases. The durable
    # ended flag is a Python permission to synchronize purchased stock; it is
    # not a claim that the original map-owned units have been removed.
    if slay.crew_activate_direct_session(ctx,mission_id,token,player):
        crew_live_note(ctx,'direct-ready',
            f'Galaxy bank acknowledged token={token}; Reserves enabled; '
            f'free map units remain temporary')
    result=await field_build_step(bot,status,observed,player)
    if (slay.crew_roster(ctx).get('active_mission') or {}).get('auto_transport',{}).get('ended'):
        # Wait for paid train receipts to arrive before adopting campaign
        # rewards. Polling observations are not automatically a native receipt.
        reserved=frozenset(int(r.tag) for r in getattr(status,'train_receipts',()))
        eligible=discover_controllable_units(bot,observed,player,exclude_wire_tags=reserved)
        first_seen=getattr(bot,'_slay_crew_discovery_first_seen',{})
        new_seen={u.tag:first_seen.get(u.tag,now) for u in eligible}
        bot._slay_crew_discovery_first_seen=new_seen
        mature=[u for u in eligible if now-new_seen[u.tag]>=3.0]
        adopted=slay.crew_adopt_live_units(ctx,mission_id,player_id=player,
                                          candidates=mature,reserved_wire_tags=reserved)
        # Keep a focused diagnosis for a mission-specific CUnit not yet mapped.
        # No speculative roster copies from localized display names.
        reported=getattr(ctx,'_slay_crew_unmapped_trooper_tags',set())
        if len(reported)<24:
            for actor in getattr(bot,'units',()):
                raw_name=str(getattr(getattr(actor,'_type_data',None),'name',''))
                raw_tag=getattr(actor,'tag',None)
                if (getattr(actor,'owner_id',None)==player and
                        ('trooper' in raw_name.casefold()) and
                        raw_tag not in reported and
                        native_type(actor)!='Trooper'):
                    crew_live_note(ctx,'trooper-unmapped',
                        f'tag={raw_tag} native={native_type(actor)} raw_name={raw_name} '
                        f'raw_id={getattr(getattr(actor,"_proto",None),"unit_type",None)} '
                        f'enum={getattr(getattr(actor,"type_id",None),"name",None)}')
                    reported.add(raw_tag)
            ctx._slay_crew_unmapped_trooper_tags=reported
        if adopted:
            crew_live_note(ctx,'unit-discovery',f'Mission={mission_id} adopted={adopted} on-field=updated')
    # Apply the normal Crew durability/deployed flag to adopted battlefield
    # actors, with the same native tag as their persistent roster binding.
    # The SC2 bank acknowledges the exact actor; missed chat commands retry.
    from .crew_tags import wire_tag
    from .crew_bank_receipts import WIRE_TYPES
    from .crew_sc2_adapter import NATIVE_TYPES
    active=slay.crew_roster(ctx).get('active_mission') or {}
    receipts=dict(getattr(status,'adopted_tags',()))
    by_tag={u.tag:u for u in observed if getattr(u,'owner',None)==player and
            not getattr(u,'is_structure',True) and type(getattr(u,'tag',None)) is int}
    reported=getattr(ctx,'_slay_crew_adopt_last_sent',{})
    for raw in active.get('adopted_tags',()):
        full=int(raw)
        unit=by_tag.get(full)
        if unit is None:continue
        try:short=wire_tag(full)
        except ValueError:continue
        expected=WIRE_TYPES.index(unit.native_type)+1 if unit.native_type in WIRE_TYPES else 0
        if not expected or receipts.get(short)==expected:continue
        if now-reported.get(full,0.0)<2.0:continue
        reported[full]=now
        ctx._slay_crew_adopt_last_sent=reported
        await bot.chat_send(f'?SlayCrewAdopt {token} {short} {unit.native_type}')
        return result
    # A purchased, awarded or adopted AP unit can unlock after mission start.
    # Native tech-tree allow is idempotent and strictly limited to cataloged
    # unit types. Actual production still requires a separate paid stock copy.
    from .crew_sc2_adapter import NATIVE_TYPES
    from .crew_catalog import preview_catalog
    available={row['name'] for row in preview_catalog(tuple(ctx.slay_config.get('races',['terran'])))
               if row['category']=='unit'}
    roster=slay.crew_roster(ctx)
    unlocked=set(roster.get('discovered_unit_unlocks',()))
    unlocked.update(c['name'] for c in roster['copies']
                    if c.get('kind')=='unit' and c.get('status')!='lost')
    sent=getattr(ctx,'_slay_crew_unlock_announced',set())
    from .crew_bank_receipts import WIRE_TYPES
    native_allowed=set(WIRE_TYPES)
    # Planetary Fortress is a purchased AP Building morph unlock, not a
    # normal unit and not a permanent type discovery. It must be advertised
    # whenever a live Crew session actually owns a usable PF stock copy.
    if ('Planetary Fortress' not in sent and
        any(c.get('name')=='Planetary Fortress' and
            c.get('status') in ('zone','reserve','deployed')
            for c in roster.get('copies',()))):
        sent.add('Planetary Fortress')
        ctx._slay_crew_unlock_announced=sent
        await bot.chat_send(f'?SlayCrewUnlock {token} PlanetaryFortress')
        return result
    for name in sorted((unlocked & available)-sent):
        native=NATIVE_TYPES.get(name)
        sent.add(name)
        if native in native_allowed:
            await bot.chat_send(f'?SlayCrewUnlock {token} {native}')
            ctx._slay_crew_unlock_announced=sent
            return result
    ctx._slay_crew_unlock_announced=sent
    return result


async def crew_game_ended(bot, result) -> None:
    """Reset On Field at SC2 game exit, without treating a quit as victory.

    Normal victory is settled earlier from Archipelago's own victory bit.
    Some map scripts instead trigger an SC2 Victory result before emitting that
    bit (observed on Cutthroat). A real SC2 Victory is authoritative too.
    """
    from . import slay_the_starcraft as slay
    ctx=bot.ctx
    if not slay.crew_mode(ctx) or not slay.state_ready(ctx):return
    result_name=str(getattr(result,'name',result)).casefold()
    won=result_name=='victory'
    mission_id=getattr(bot,'mission_id',None)
    if won and not bot.mission_completed:
        # An SC2 Victory result is a completed mission, NOT a disconnected or
        # cancelled session. Send the regular AP victory cache checks once.
        from .client import get_location_id, VICTORY_CACHE_OFFSET, VICTORY_MODULO
        ids=[get_location_id(mission_id,0)]
        for local in getattr(ctx,'mission_id_to_location_ids',{}).get(mission_id,()):
            if local % VICTORY_MODULO>=VICTORY_CACHE_OFFSET:
                ids.append(get_location_id(mission_id,local))
        await ctx.send_msgs([{'cmd':'LocationChecks','locations':sorted(set(ids))}])
        bot.mission_completed=True
        crew_live_note(ctx,'sc2-victory-fallback',f'Mission={mission_id} SC2 Victory; AP checks delivered')
    active=slay.crew_roster(ctx).get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:return
    if won:
        try:
            await victory_step(bot)
        except Exception as exc:
            crew_live_note(ctx,'game-end-settlement-deferred',f'{type(exc).__name__}: {exc}')
    if isinstance(slay.crew_roster(ctx).get('active_mission'),dict):
        # Only this actual on_end callback authorizes clearing the active
        # session. Confirmed live deaths and complete terminal snapshots are
        # honored; all unconfirmed surviving field copies return to Reserves.
        outcome=slay.crew_abandon_interrupted_session(ctx,verified_game_closed=True)
        crew_live_note(ctx,'game-end-reserves',f'Mission={mission_id} returned={outcome["returned"]} lost={outcome["lost"]}')


async def victory_step(bot) -> dict[str, int]:
    """Settle Crew from the authoritative Archipelago `game_state` victory bit.

    Normally invoked by ArchipelagoBot.on_step before it sends LocationChecks.
    It can also run on an independently confirmed SC2 Result.Victory at on_end
    when the mission never emitted the AP victory bit. A quit is not a win.

    Self-owned BotAI.units and BotAI.structures together provide the complete
    owned-unit view; a disconnected/uninitialized bot must never claim this
    view is complete. If the process exits between settlement and LocationChecks,
    the persistent `settled_missions` record lets the callback replay harmlessly.
    """
    from . import slay_the_starcraft as slay
    ctx = bot.ctx
    if not slay.crew_mode(ctx):
        return {}
    if os.environ.get('SLAY_CREW_TEST_MODE') == 'probe':
        raise RuntimeError('Crew probe-only run: victory settlement is intentionally disabled')
    if not live_test_authorized(ctx):
        raise RuntimeError('Crew victory settlement requires a staged live Crew run')
    if not slay.state_ready(ctx) or not getattr(bot, 'can_read_game', False):
        raise RuntimeError('Crew cannot settle without a connected game controller')
    mission_id = getattr(bot, 'mission_id', None)
    if type(mission_id) is not int:
        raise RuntimeError('Missing Crew victory mission identity')
    player=getattr(bot,'player_id',None)
    if type(player) is not int or not 0<player<=16:
        raise RuntimeError('No verified Crew player owner at victory')
    # The regular discovery loop waits 3 seconds for native paid-training
    # receipts. At a confirmed victory this delay would lose late-spawned
    # Domination reinforcements, so adopt once from the complete terminal view
    # after excluding explicit paid receipts (the bank's real producer tags).
    live_now=observations(bot)
    possible=discover_controllable_units(bot,live_now,player)
    death_bank=None
    initial=slay.crew_roster(ctx).get('active_mission') or {}
    token=(initial.get('auto_transport') or {}).get('token')
    if type(token) is int:
        death_bank=read_bank_status(token,cached_bank_paths(ctx,banks()))
    reserved={int(r.tag) for r in getattr(death_bank,'train_receipts',())} if death_bank is not None else set()
    if possible:
        adopted=slay.crew_adopt_live_units(ctx,mission_id,player_id=player,
            candidates=possible,reserved_wire_tags=reserved)
        if adopted:crew_live_note(ctx,'victory-final-adoption',f'Mission={mission_id} adopted={adopted}')
    ledger = slay.crew_roster(ctx)
    active = ledger.get('active_mission')
    if active is None:
        confirmed = ledger.get('settled_missions', {}).get(str(mission_id))
        if confirmed is None:
            raise RuntimeError('Unstaged Crew mission cannot be settled')
        return dict(confirmed)
    if active.get('mission_id') != mission_id:
        raise RuntimeError('Victory belongs to a different Crew mission')
    player = getattr(bot, 'player_id', None)
    if type(player) is not int or not 0 < player <= 16:
        raise RuntimeError('No verified Crew player owner for victory snapshot')
    # Preserve separately committed terminal evidence if the client crashed
    # after Bank receipt validation and the snapshot but before settlement.
    if active.get('terminal_snapshot') is None:
        auto=active.get('auto_transport') or {}
        token=auto.get('token')
        # Older source-only fixtures and pre-death-ledger sessions can still
        # use their verified end-of-mission snapshot. New live Crew sessions
        # additionally cross-check the positive Galaxy death receipts.
        death_tags=frozenset()
        if type(token) is int:
            death_bank=read_bank_status(token,cached_bank_paths(ctx,banks()))
            death_tags=death_bank.death_tags
            crew_live_note(ctx,'death-receipts',
                f'Mission={mission_id} confirmed-death-wire-tags={sorted(death_tags)}')
        slay.crew_record_terminal_snapshot(ctx, mission_id,
            observations=observations(bot), player_id=player,
            victory_confirmed=True, complete=True,
            death_wire_tags=death_tags)
    settled=slay.crew_settle_tracked_victory(ctx, mission_id,
        victory_confirmed=True, terminal_snapshot_complete=True)
    crew_live_note(ctx,'victory-settlement',f'Mission={mission_id}: {settled}')
    return settled


# Preserve the original BotAI entry points and make persistence of errors
# transparent to call sites. Source checks still inspect the actual handlers.
_auto_step_raw=auto_step
_victory_step_raw=victory_step

async def _auto_step_reported(bot, *, bank_roots=None) -> str | None:
    try:
        return await _auto_step_raw(bot, bank_roots=bank_roots)
    except Exception as exc:
        message=f'{type(exc).__name__}: {exc}'
        ctx=bot.ctx
        if getattr(ctx,'_slay_crew_logged_error',None)!=message:
            try:setattr(ctx,'_slay_crew_logged_error',message)
            except (AttributeError,TypeError):pass
            crew_live_note(ctx,'transport-error',message)
            probe_note(ctx,'transport-error',message)
        # No input freeze exists. Leave the Crew transport failure recorded;
        # do not send an obsolete unlock command or fabricate a completed run.
        raise

async def _victory_step_reported(bot) -> dict[str,int]:
    try:
        result=await _victory_step_raw(bot)
        crew_live_note(bot.ctx,'victory-settled',str(result))
        return result
    except Exception as exc:
        message=f'{type(exc).__name__}: {exc}'
        ctx=bot.ctx
        if getattr(ctx,'_slay_crew_logged_victory_error',None)!=message:
            try:setattr(ctx,'_slay_crew_logged_victory_error',message)
            except (AttributeError,TypeError):pass
            crew_live_note(ctx,'victory-blocked',message)
        raise

auto_step=_auto_step_reported
victory_step=_victory_step_reported
