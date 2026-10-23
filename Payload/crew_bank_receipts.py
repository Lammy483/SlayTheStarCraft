"""Crew-only SC2 BankSave automatic deployment receipt decoder.

Bank contents are candidates, not authenticated receipts on their own. The
caller must match token/sequence/tag/type/owner/producer against a current SC2
observation AND atomically bind the matching pending copy before sending ACK.
Standard and Campaign neither open nor consume this Crew bank.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

WIRE_TYPES = (
    'SCV',
    'Marine',
    'Marauder',
    'Reaper',
    'Firebat',
    'Hellion',
    'SiegeTank',
    'VikingFighter',
    'Medivac',
    'Banshee',
    'Battlecruiser',
    'Drone',
    'Zergling',
    'Roach',
    'Probe',
    'Zealot',
    'Stalker',
    'CommandCenter',
    'SupplyDepot',
    'Barracks',
    'Factory',
    'Starport',
    'Hatchery',
    'SpawningPool',
    'Overlord',
    'Nexus',
    'Pylon',
    'Gateway',
    'RoachWarren',
    'Trooper',
    'Refinery',
    'EngineeringBay',
    'Armory',
    'Bunker',
    'MissileTurret',
    'SensorTower',
    'Extractor',
    'EvolutionChamber',
    'BanelingNest',
    'HydraliskDen',
    'InfestationPit',
    'Spire',
    'UltraliskCavern',
    'SpineCrawler',
    'SporeCrawler',
    'Assimilator',
    'CyberneticsCore',
    'Forge',
    'RoboticsFacility',
    'Stargate',
    'TwilightCouncil',
    'RoboticsBay',
    'TemplarArchives',
    'FleetBeacon',
    'PhotonCannon',
    'TechLab',
    'PlanetaryFortress',
    'DevastatorTurret',
    'PerditionTurret',
    'Vulture',
    'Medic',
    'Ghost',
    'Spectre',
    'HERC',
    'Goliath',
    'Diamondback',
    'WidowMine',
    'Cyclone',
    'Thor',
    'Warhound',
    'Wraith',
    'Raven',
    'ScienceVessel',
    'Valkyrie',
    'Liberator',
    'Baneling',
    'Hydralisk',
    'Queen',
    'Mutalisk',
    'Corruptor',
    'Ultralisk',
    'Sentry',
    'Adept',
    'Immortal',
    'Observer',
    'WarpPrism',
    'Colossus',
    'VoidRay',
    'Carrier',
    'Predator',
    'Hercules',
    'Bullfrog',
    'TaurenMarine',
    'Lurker',
    'Impaler',
    'Viper',
    'SwarmHost',
    'Infestor',
    'Overseer',
    'BroodLord',
    'Guardian',
    'Devourer',
    'Scourge',
    'Ravager',
    'Defiler',
    'Aberration',
    'Dragoon',
    'HighTemplar',
    'DarkTemplar',
    'Archon',
    'DarkArchon',
    'Phoenix',
    'Scout',
    'Oracle',
    'Disruptor',
    'Reaver',
    'Arbiter',
    'Corsair',
    'Tempest',
    'Mothership',
    'Mirage',
    'Centurion',
    'Instigator',
    'Avenger',
    'Slicer',
    'Vanguard',
    'Wrathwalker',
    'Ascendant',
    'Slayer',
    'Annihilator',
    'Energizer',
    'AegisGuard',
    'EmperorsShadow',
    'FieldResponseTheta',
    'SonOfKorhal',
    'Blackhammer',
    'BulwarkCompany',
    'ShockDivision',
    'BloodHunter',
    'Havoc',
    'Sentinel',
    'Signifier',
    'Supplicant',
    'Caladrius',
    'Dawnbringer',
    'Destroyer',
    'MistWing',
    'Oppressor',
    'Pulsar',
    'Skirmisher',
    'Skylord',
    'Trireme',
    'WarPig',
    'DevilDog',
    'HammerSecurity',
    'HammerSecurities',
    'SpartanCompany',
    'SiegeBreaker',
    'HelsAngel',
    'DuskWing',
    'JacksonsRevenge',
    'JacksonRevenge',
    'HelsAngelFighter',
    'DukesRevenge',
    'SkibisAngel',
    'DeathHead',
    'WingedNightmare',
    'MidnightRider',
    'Brynhild',
    'Jotun',
)
_TYPE_BY_CODE = {i + 1: name for i, name in enumerate(WIRE_TYPES)}
_KEY = re.compile(r'^Click([1-9][0-9]*)(Tag|Producer|Type|Owner|Commit)$')
_MAX_TAG = 2**32 - 1
_NATIVE_KEY = re.compile(r'^Native([1-9][0-9]*)(Tag|Action|Owner|Commit)$')


@dataclass(frozen=True)
class CrewAutoBankReceipt:
    token: int
    sequence: int
    tag: int
    producer_tag: int
    native_type: str
    owner: int


@dataclass(frozen=True)
class CrewNativeBankReceipt:
    token: int
    sequence: int
    tag: int
    action: int  # 1 keep / 2 remove
    owner: int


_BUILD_KEY = re.compile(r'^Build([1-9][0-9]*)(Tag|Worker|Type|Owner|Complete)$')
_BUILD_AUTH_KEY = re.compile(r'^BuildAuth([1-9][0-9]*)$')

_TRAIN_KEY = re.compile(r'^Train([1-9][0-9]*)(Tag|Worker|Type|Owner|Complete)$')

@dataclass(frozen=True)
class CrewFieldTrainReceipt:
    token: int
    copy_number: int
    tag: int
    producer_tag: int
    native_type: str
    owner: int

def decode_field_train_bank(xml: str | bytes, token: int) -> tuple[CrewFieldTrainReceipt,...]:
    root=ET.fromstring(xml)
    sections=root.findall(f".//Section[@name='Session{token}']")
    if len(sections)>1:raise ValueError('Duplicate Crew native train session')
    if not sections:return ()
    rows={}
    for key in sections[0].findall('Key'):
        m=_TRAIN_KEY.fullmatch(key.get('name',''))
        if not m:continue
        ident=_int(m.group(1),100000)
        value=key.find('Value')
        number=_int(value.get('int') if value is not None else None,_MAX_TAG)
        row=rows.setdefault(ident,{})
        if m.group(2) in row:raise ValueError('Duplicate Crew train field')
        row[m.group(2)]=number
    out=[]
    for ident,row in sorted(rows.items()):
        if (set(row)!={'Tag','Worker','Type','Owner','Complete'} or row['Complete']!=token
                or row['Owner']>16 or row['Type'] not in _TYPE_BY_CODE):
            raise ValueError('Invalid Crew train receipt')
        out.append(CrewFieldTrainReceipt(token,ident,row['Tag'],row['Worker'],
                                        _TYPE_BY_CODE[row['Type']],row['Owner']))
    return tuple(out)



@dataclass(frozen=True)
class CrewFieldBuildReceipt:
    token: int
    copy_number: int
    tag: int
    worker_tag: int
    native_type: str
    owner: int


def decode_field_build_bank(xml: str | bytes, token: int) -> tuple[tuple[CrewFieldBuildReceipt,...],frozenset[int]]:
    """A banked build is not enough; bot must also validate its exact actor."""
    root=ET.fromstring(xml)
    sections=root.findall(f".//Section[@name='Session{token}']")
    if len(sections)>1:raise ValueError('Duplicate Crew field-build session')
    if not sections:return (),frozenset()
    records={}
    authorizations=set()
    for key in sections[0].findall('Key'):
        name=key.get('name','')
        m=_BUILD_KEY.fullmatch(name)
        auth=_BUILD_AUTH_KEY.fullmatch(name)
        if not m and not auth:continue
        value=key.find('Value')
        number=_int(value.get('int') if value is not None else None,_MAX_TAG)
        if auth:
            if number!=token:raise ValueError('Crew building authorization token mismatch')
            identifier=_int(auth.group(1),100000)
            if identifier in authorizations:raise ValueError('Duplicate Crew building authorization')
            authorizations.add(identifier)
            continue
        identifier=_int(m.group(1),100000)
        row=records.setdefault(identifier,{})
        if m.group(2) in row:raise ValueError('Duplicate Crew building receipt field')
        row[m.group(2)]=number
    result=[]
    for identifier,row in sorted(records.items()):
        if (set(row)!={'Tag','Worker','Type','Owner','Complete'} or
            row['Complete']!=token or row['Owner']>16 or
            row['Type'] not in _TYPE_BY_CODE):
            raise ValueError('Incomplete or incorrect Crew building receipt')
        result.append(CrewFieldBuildReceipt(token,identifier,row['Tag'],row['Worker'],
                                           _TYPE_BY_CODE[row['Type']],row['Owner']))
    return tuple(result),frozenset(authorizations)


def _int(value: str | None, upper: int) -> int:
    if not isinstance(value, str) or not value.isdecimal() or len(value) > 15:
        raise ValueError('Invalid Crew bank integer')
    number = int(value)
    if not 0 < number <= upper:
        raise ValueError('Out-of-range Crew bank integer')
    return number


def decode_bank(xml: str | bytes, token: int) -> tuple[CrewAutoBankReceipt, ...]:
    """Reject incomplete/malformed receipt tuples; never accept old tokens."""
    if type(token) is not int or not 0 < token < 2**31:
        raise ValueError('Invalid Crew mission token')
    root = ET.fromstring(xml)
    matches = root.findall(f".//Section[@name='Session{token}']")
    if len(matches) > 1:
        raise ValueError('Duplicate Crew session sections')
    if not matches:
        return ()
    rows: dict[int, dict[str,int]] = {}
    for key in matches[0].findall('Key'):
        match = _KEY.fullmatch(key.get('name', ''))
        if not match:
            continue  # keys for other protocols or future versions
        seq = _int(match.group(1),2**31-1)
        field = match.group(2)
        value = key.find('Value')
        if value is None or value.get('int') is None:
            raise ValueError('Missing Crew bank integer value')
        number = _int(value.get('int'), _MAX_TAG)
        current=rows.setdefault(seq,{})
        if field in current:
            raise ValueError('Duplicate Crew bank receipt field')
        current[field]=number
    out=[]
    for seq, row in sorted(rows.items()):
        if set(row) != {'Tag','Producer','Type','Owner','Commit'}:
            raise ValueError('Incomplete Crew bank click record')
        if row['Commit'] != token or row['Type'] not in _TYPE_BY_CODE or row['Owner'] > 16:
            raise ValueError('Crew bank receipt token, type or owner mismatch')
        out.append(CrewAutoBankReceipt(token,seq,row['Tag'],row['Producer'],
                                         _TYPE_BY_CODE[row['Type']],row['Owner']))
    return tuple(out)


def decode_native_bank(xml: str | bytes, token: int) -> tuple[CrewNativeBankReceipt,...]:
    root=ET.fromstring(xml)
    sections=root.findall(f".//Section[@name='Session{token}']")
    if len(sections)>1:raise ValueError('Duplicate Crew bank session')
    if not sections:return ()
    rows={}
    for key in sections[0].findall('Key'):
        m=_NATIVE_KEY.fullmatch(key.get('name',''))
        if not m:continue
        seq=_int(m.group(1),2**31-1)
        value=key.find('Value')
        number=_int(value.get('int') if value is not None else None,_MAX_TAG)
        row=rows.setdefault(seq,{})
        if m.group(2) in row:raise ValueError('Duplicate native receipt field')
        row[m.group(2)]=number
    out=[]
    for seq,row in sorted(rows.items()):
        if (set(row)!={'Tag','Action','Owner','Commit'} or
            row['Action'] not in (1,2) or row['Owner']>16 or row['Commit']!=token):
            raise ValueError('Invalid native reconciliation receipt')
        out.append(CrewNativeBankReceipt(token,seq,row['Tag'],row['Action'],row['Owner']))
    return tuple(out)


def read_banks(token: int, roots: Iterable[Path]) -> tuple[CrewAutoBankReceipt, ...]:
    """Read SC2-written banks only. Missing/partial banks never infer a receipt.

    A collision between documents profiles for the same token is an error; we
    do not pick whichever file was encountered first.
    """
    if type(token) is not int or not 0 < token < 2**31:
        raise ValueError('Invalid Crew mission token')
    collected: dict[int,CrewAutoBankReceipt] = {}
    scanned=set()
    for root in roots:
        root=Path(root)
        if not root.is_dir():
            continue
        for path in root.rglob('SlayTheStarCraftCrew.SC2Bank'):
            resolved=path.resolve()
            if resolved in scanned:
                continue
            scanned.add(resolved)
            try:
                if path.stat().st_size > 1024 * 1024:
                    raise ValueError('Oversized Crew receipt bank')
                contents=path.read_bytes()
                receipts=decode_bank(contents,token)
            except (OSError, ET.ParseError):
                continue  # transient game-written XML; retry later
            for item in receipts:
                previous=collected.get(item.sequence)
                if previous is not None and previous != item:
                    raise ValueError('Conflicting Crew receipt banks')
                collected[item.sequence]=item
    return tuple(collected[k] for k in sorted(collected))


def validate_observed_receipt(receipt: CrewAutoBankReceipt, *, token: int,
                              sequence: int, expected_native_type: str,
                              player_id: int, expected_producer_tag: int,
                              observed_tag: int, observed_native_type: str,
                              observed_owner: int) -> str:
    """Return ACK only for a verified SC2-created tag and home anchor."""
    if (receipt.token != token or receipt.sequence != sequence or
        receipt.native_type != expected_native_type or receipt.owner != player_id or
        receipt.producer_tag != expected_producer_tag or
        receipt.tag != observed_tag or
        observed_native_type != expected_native_type or
        observed_owner != player_id):
        raise ValueError('SC2 observation does not match Crew bank receipt')
    return f'?SlayCrewAck {token} {sequence} {receipt.tag}'


def decode_bank_status(xml: str | bytes, token: int):
    """Session readiness and SC2 ACKs, read from the same bank as receipts.

    An old bank with a coincidentally named section can never advance without
    matching the fresh random token in each ready/ack field.
    """
    from .crew_runtime import CrewBankStatus
    receipts=decode_bank(xml,token)
    native_receipts=decode_native_bank(xml,token)
    root=ET.fromstring(xml)
    sections=root.findall(f".//Section[@name='Session{token}']")
    if not sections:
        return CrewBankStatus(False,frozenset(),receipts,native_receipts)
    ready=False
    ack=set()
    native_ack=set()
    native_done=False
    ended=False
    skipped=set()
    origin_tag=None
    dead_tags=set()
    build_receipts,build_authorized=decode_field_build_bank(xml,token)
    train_receipts=decode_field_train_bank(xml,token)
    seen=set()
    production_debug={}
    production_claims=set()
    free_building_deaths={}
    adopted_tags={}
    for key in sections[0].findall('Key'):
        name=key.get('name','')
        adopt_match=re.fullmatch(r'AdoptTag([1-9][0-9]*)',name)
        if adopt_match:
            tag=_int(adopt_match.group(1),2**31-1)
            value=key.find('Value')
            code=_int(value.get('int') if value is not None else None,10000)
            if tag in adopted_tags or code not in _TYPE_BY_CODE:
                raise ValueError('Invalid or duplicate Crew adopted actor')
            adopted_tags[tag]=code
            continue
        free_match=re.fullmatch(r'FreeBuildDeath([1-9][0-9]*)',name)
        if free_match:
            tag=_int(free_match.group(1),2**31-1)
            value=key.find('Value')
            code=_int(value.get('int') if value is not None else None,10000)
            if tag in free_building_deaths:raise ValueError('Duplicate free building death')
            free_building_deaths[tag]=code
            continue
        claim_match=re.fullmatch(r'Claim([1-9][0-9]*)',name)
        if claim_match:
            ident=_int(claim_match.group(1),100000)
            value=key.find('Value')
            raw=value.get('int') if value is not None else None
            if raw not in ('0',str(token)):
                raise ValueError('Invalid Crew production claim token')
            if raw==str(token):production_claims.add(ident)
            continue
        if name.startswith(('ProdDiag','ProdLast')):
            # Bank-sourced diagnostics are observations, never authorization.
            if not re.fullmatch(r'Prod(Diag|Last)(StockAccepted|TrainStart|TrainClaim|TrainAdvance|TrainComplete|BuildStart|BuildClaim|BuildAdvance|BuildComplete|BuildPercentBefore|BuildPercentAfter|FoundationFound|BuilderFound|BuildResetSeen|BuildReplicaFailed|BuildReplicaComplete|BuildCompleteRecovered|SpecialStart|SpecialClaim|SpecialAdvance|SpecialComplete|SpecialOrderClaim)',name):
                continue
            if name in production_debug:raise ValueError('Duplicate Crew production diagnostic')
            value=key.find('Value')
            production_debug[name]=_int(value.get('int') if value is not None else None,2**31-1)
            continue
        if name not in ('Ready','ReadyAnchor','NativeDone','Ended') and not re.fullmatch(r'(Ack|NativeAck|Skip|DeathTag)[1-9][0-9]*',name):
            continue
        if name in seen:raise ValueError('Duplicate Crew bank status field')
        seen.add(name)
        value=key.find('Value')
        if name=='ReadyAnchor':
            try:
                origin_tag=_int(value.get('int') if value is not None else None,_MAX_TAG)
            except ValueError as exc:
                raise ValueError('Invalid Crew Galaxy origin tag; verify Galaxy/SC2 tag representation') from exc
            continue
        number=_int(value.get('int') if value is not None else None,2**31-1)
        if number != token:raise ValueError('Wrong token in Crew bank status')
        if name=='Ready':ready=True
        elif name.startswith('DeathTag'):
            dead_tags.add(_int(name[8:],2**31-1))
        elif name=='NativeDone':native_done=True
        elif name=='Ended':ended=True
        elif name.startswith('NativeAck'):native_ack.add(_int(name[9:],2**31-1))
        elif name.startswith('Skip'):skipped.add(_int(name[4:],2**31-1))
        else:ack.add(_int(name[3:],2**31-1))
    if any(r.sequence in skipped for r in receipts):
        raise ValueError('Crew sequence has both successful and skipped receipts')
    return CrewBankStatus(ready,frozenset(ack),receipts,native_receipts,
                          frozenset(native_ack),native_done,ended,frozenset(skipped),
                          origin_tag,frozenset(dead_tags),build_receipts,build_authorized,train_receipts,
                          tuple(sorted(production_debug.items())),
                          frozenset(production_claims),
                          tuple(sorted(free_building_deaths.items())),
                          tuple(sorted(adopted_tags.items())))


def read_bank_status(token: int, roots: Iterable[Path]):
    """Read all valid bank files, rejecting conflicting copies of one receipt.

    Files actively being saved are retried later. This must not treat absence
    of a receipt as success or settle an in-flight deployment.
    """
    from .crew_runtime import CrewBankStatus
    ready=False
    ack=set()
    receipts={}
    native_receipts={}
    native_ack=set()
    native_done=False
    ended=False
    skipped=set()
    origin_tag=None
    dead_tags=set()
    build_receipts={}
    build_authorized=set()
    train_receipts={}
    production_debug={}
    production_claims=set()
    free_building_deaths={}
    adopted_tags={}
    seen=set()
    for root in roots:
        root=Path(root)
        # The Crew bot caches the exact bank paths after discovery. Accept
        # exact files here so every fast poll does NOT recursively enumerate
        # the player's entire SC2 Documents/account tree.
        if root.is_file() and root.name == 'SlayTheStarCraftCrew.SC2Bank':
            candidates=(root,)
        elif root.is_dir():
            candidates=root.rglob('SlayTheStarCraftCrew.SC2Bank')
        else:
            continue
        for path in candidates:
            resolved=path.resolve()
            if resolved in seen:continue
            seen.add(resolved)
            try:
                if path.stat().st_size>1024*1024:
                    raise ValueError('Oversized Crew receipt bank')
                status=decode_bank_status(path.read_bytes(),token)
            except (OSError,ET.ParseError):
                continue
            ready|=status.ready
            ack.update(status.acknowledged)
            native_ack.update(status.native_acknowledged)
            native_done|=status.native_done
            ended|=status.ended
            skipped.update(status.skipped)
            dead_tags.update(status.death_tags)
            for tag,code in status.adopted_tags:
                if tag in adopted_tags and adopted_tags[tag]!=code:
                    raise ValueError('Conflicting Crew adopted unit identity')
                adopted_tags[tag]=code
            for tag,code in status.free_building_deaths:
                if tag in free_building_deaths and free_building_deaths[tag]!=code:
                    raise ValueError('Conflicting free structure death type')
                free_building_deaths[tag]=code
            build_authorized.update(status.build_authorized)
            production_claims.update(status.production_claims)
            for name,value in status.production_debug:
                production_debug[name]=max(production_debug.get(name,0),value)
            for train in status.train_receipts:
                old=train_receipts.get(train.copy_number)
                if old is not None and old!=train:raise ValueError('Conflicting Crew native-train receipts')
                train_receipts[train.copy_number]=train
            for build in status.build_receipts:
                old=build_receipts.get(build.copy_number)
                if old is not None and old!=build:
                    raise ValueError('Conflicting Crew field-build receipts')
                build_receipts[build.copy_number]=build
            if status.origin_tag is not None:
                if origin_tag is not None and origin_tag!=status.origin_tag:
                    raise ValueError('Conflicting Galaxy origin tag probes across Crew banks')
                origin_tag=status.origin_tag
            for nr in status.native_receipts:
                old=native_receipts.get(nr.sequence)
                if old is not None and old!=nr:
                    raise ValueError('Conflicting native reconciliation receipts')
                native_receipts[nr.sequence]=nr
            for receipt in status.receipts:
                previous=receipts.get(receipt.sequence)
                if previous is not None and previous!=receipt:
                    raise ValueError('Conflicting Crew bank receipts')
                receipts[receipt.sequence]=receipt
    if skipped.intersection(receipts):
        raise ValueError('Conflicting Crew successes and placement failures across banks')
    return CrewBankStatus(ready,frozenset(ack),tuple(receipts[k] for k in sorted(receipts)),
                          tuple(native_receipts[k] for k in sorted(native_receipts)),
                          frozenset(native_ack),native_done,ended,frozenset(skipped),
                          origin_tag,frozenset(dead_tags),
                          tuple(build_receipts[k] for k in sorted(build_receipts)),
                          frozenset(build_authorized),
                          tuple(train_receipts[k] for k in sorted(train_receipts)),
                          tuple(sorted(production_debug.items())),
                          frozenset(production_claims),
                          tuple(sorted(free_building_deaths.items())),
                          tuple(sorted(adopted_tags.items())))
