"""Staged Crew Challenge SC2 transport and candidate-observation logic.

The live SC2 bot is not wired yet. Automatically issue one roster copy
at a time once the base exists. The strict boundary here is intentional:
seeing a new unit of the expected type NEVER by itself creates a Crew roster
receipt. Authoritative confirmation of its SC2 tag from the Galaxy handler
must also be supplied by a future trusted channel.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

# Capturable Terran mercenaries are battlefield prizes, not shop/AP unlocks.
# Only an exact SC2 engine CUnit identity and owned unit tag can be adopted.
CREW_MERCENARY_NATIVE = {
    'WarPig': ('War Pigs', 1),
    'DevilDog': ('Devil Dogs', 2),
    'HammerSecurity': ('Hammer Securities', 2),
    'HammerSecurities': ('Hammer Securities', 2),
    'SpartanCompany': ('Spartan Company', 2),
    'SiegeBreaker': ('Siege Breakers', 3),
    'HelsAngel': ("Hel's Angels", 2),
    'DuskWing': ('Dusk Wings', 3),
    'JacksonsRevenge': ("Jackson's Revenge", 6),
    'JacksonRevenge': ("Jackson's Revenge", 6),
    'HelsAngelFighter': ("Hel's Angels", 2),
    'DukesRevenge': ("Jackson's Revenge", 6),
    'SkibisAngel': ("Skibi's Angels", 3),
    'DeathHead': ('Death Heads', 2),
    'WingedNightmare': ('Winged Nightmares', 3),
    'MidnightRider': ('Midnight Riders', 2),
    'Brynhild': ('Brynhild', 6),
    'Jotun': ('Jotun', 6),
}

# Display name -> exact native SC2 CUnit catalog ID. Unmapped catalog entries
# cannot be used by the prototype spawner. No AP variant is guessed from a name.
NATIVE_TYPES = {
    'SCV':'SCV', 'Marine':'Marine', 'Dominion Trooper':'Trooper', 'Marauder':'Marauder',
    'Reaper':'Reaper', 'Firebat':'Firebat', 'Hellion':'Hellion', 'Vulture':'Vulture',
    'Siege Tank':'SiegeTank', 'Viking':'VikingFighter',
    'Medic':'Medic','Ghost':'Ghost','Spectre':'Spectre','HERC':'HERC',
    'Goliath':'Goliath','Diamondback':'Diamondback','Widow Mine':'WidowMine',
    'Cyclone':'Cyclone','Thor':'Thor','Warhound':'Warhound',
    'Wraith':'Wraith','Raven':'Raven','Science Vessel':'ScienceVessel',
    'Valkyrie':'Valkyrie','Liberator':'Liberator',
    'Medivac':'Medivac', 'Banshee':'Banshee', 'Battlecruiser':'Battlecruiser',
    'Command Center':'CommandCenter', 'Supply Depot':'SupplyDepot',
    'Barracks':'Barracks', 'Factory':'Factory', 'Starport':'Starport',
    'Drone':'Drone', 'Hatchery':'Hatchery', 'Spawning Pool':'SpawningPool',
    'Overlord':'Overlord', 'Zergling':'Zergling', 'Roach':'Roach',
    'Baneling':'Baneling','Hydralisk':'Hydralisk','Queen':'Queen',
    'Mutalisk':'Mutalisk','Corruptor':'Corruptor','Ultralisk':'Ultralisk',
    'Probe':'Probe', 'Nexus':'Nexus', 'Pylon':'Pylon',
    'Gateway':'Gateway', 'Zealot':'Zealot', 'Stalker':'Stalker',
    'Sentry':'Sentry','Adept':'Adept','Immortal':'Immortal',
    'Observer':'Observer','Warp Prism':'WarpPrism','Colossus':'Colossus',
    'Void Ray':'VoidRay','Carrier':'Carrier',
    'Roach Warren':'RoachWarren',
    'Refinery':'Refinery', 'Engineering Bay':'EngineeringBay',
    'Armory':'Armory', 'Bunker':'Bunker', 'Missile Turret':'MissileTurret',
    'Sensor Tower':'SensorTower',
    'Extractor':'Extractor', 'Evolution Chamber':'EvolutionChamber',
    'Baneling Nest':'BanelingNest', 'Hydralisk Den':'HydraliskDen',
    'Infestation Pit':'InfestationPit', 'Spire':'Spire',
    'Ultralisk Cavern':'UltraliskCavern',
    'Spine Crawler':'SpineCrawler', 'Spore Crawler':'SporeCrawler',
    'Assimilator':'Assimilator', 'Cybernetics Core':'CyberneticsCore',
    'Forge':'Forge', 'Robotics Facility':'RoboticsFacility',
    'Stargate':'Stargate', 'Twilight Council':'TwilightCouncil',
    'Robotics Bay':'RoboticsBay', 'Templar Archives':'TemplarArchives',
    'Fleet Beacon':'FleetBeacon', 'Photon Cannon':'PhotonCannon',
    'Tech Lab':'TechLab', 'Planetary Fortress':'PlanetaryFortress',
    'Devastator Turret':'DevastatorTurret', 'Perdition Turret':'PerditionTurret',
    'Aegis Guard':'AegisGuard',
    "Emperor's Shadow":'EmperorsShadow',
    'Field Response Theta':'FieldResponseTheta',
    'Son of Korhal':'SonOfKorhal',
    'Blackhammer':'Blackhammer',
    'Bulwark Company':'BulwarkCompany',
    'Shock Division':'ShockDivision',
    'Blood Hunter':'BloodHunter',
    'Havoc':'Havoc',
    'Sentinel':'Sentinel',
    'Signifier':'Signifier',
    'Supplicant':'Supplicant',
    'Caladrius':'Caladrius',
    'Dawnbringer':'Dawnbringer',
    'Destroyer':'Destroyer',
    'Mist Wing':'MistWing',
    'Oppressor':'Oppressor',
    'Pulsar':'Pulsar',
    'Skirmisher':'Skirmisher',
    'Skylord':'Skylord',
    'Trireme':'Trireme',

    'Predator':'Predator',
    'Hercules':'Hercules',
    'Bullfrog':'Bullfrog',
    'Tauren Marine':'TaurenMarine',
    'Lurker':'Lurker',
    'Impaler':'Impaler',
    'Viper':'Viper',
    'Swarm Host':'SwarmHost',
    'Infestor':'Infestor',
    'Overseer':'Overseer',
    'Brood Lord':'BroodLord',
    'Guardian':'Guardian',
    'Devourer':'Devourer',
    'Scourge':'Scourge',
    'Ravager':'Ravager',
    'Defiler':'Defiler',
    'Aberration':'Aberration',
    'Dragoon':'Dragoon',
    'High Templar':'HighTemplar',
    'Dark Templar':'DarkTemplar',
    'Archon':'Archon',
    'Dark Archon':'DarkArchon',
    'Phoenix':'Phoenix',
    'Scout':'Scout',
    'Oracle':'Oracle',
    'Disruptor':'Disruptor',
    'Reaver':'Reaver',
    'Arbiter':'Arbiter',
    'Corsair':'Corsair',
    'Tempest':'Tempest',
    'Mothership':'Mothership',
    'Mirage':'Mirage',
    'Centurion':'Centurion',
    'Instigator':'Instigator',
    'Avenger':'Avenger',
    'Slicer':'Slicer',
    'Vanguard':'Vanguard',
    'Wrathwalker':'Wrathwalker',
    'Ascendant':'Ascendant',
    'Slayer':'Slayer',
    'Annihilator':'Annihilator',
    'Energizer':'Energizer',

}

# CUnit identity, independent of localized display names and unsupported enums.
# Existing AP_ variants must be normalized to these stable receipt names.
STRUCTURE_TYPES=frozenset({
    'CommandCenter','SupplyDepot','Barracks','Factory','Starport','Hatchery',
    'SpawningPool','RoachWarren','Nexus','Pylon','Gateway','Refinery',
    'EngineeringBay','Armory','Bunker','MissileTurret','SensorTower',
    'Extractor','EvolutionChamber','BanelingNest','HydraliskDen',
    'InfestationPit','Spire','UltraliskCavern','SpineCrawler','SporeCrawler',
    'Assimilator','CyberneticsCore','Forge','RoboticsFacility','Stargate',
    'TwilightCouncil','RoboticsBay','TemplarArchives','FleetBeacon',
    'PhotonCannon','TechLab','PlanetaryFortress','DevastatorTurret',
    'PerditionTurret',
})


@dataclass(frozen=True)
class CrewUnitObservation:
    tag: int
    native_type: str
    owner: int
    x: float
    y: float
    is_structure: bool = False

    @classmethod
    def parse(cls, row: Mapping[str, Any]) -> 'CrewUnitObservation':
        # Do not accept bools as integer tags, or non-positive/unowned actors.
        if type(row.get('tag')) is not int or row['tag'] <= 0:
            raise ValueError('SC2 observations require a positive integer unit tag')
        if type(row.get('owner')) is not int or row['owner'] <= 0:
            raise ValueError('SC2 observations require an explicit player owner')
        native_type = row.get('native_type')
        if not isinstance(native_type, str) or not native_type:
            raise ValueError('Missing native CUnit type')
        structure=row.get('is_structure', False)
        if type(structure) is not bool:
            raise ValueError('SC2 structure observation flag must be boolean')
        return cls(row['tag'], native_type, row['owner'],float(row['x']),float(row['y']),structure)

class CrewSpawnSession:
    """Single outstanding spawn. Retries reuse sequence, never grant two copies."""
    def __init__(self, mission_id: int, token: int, player_id: int,
                 manifest: Iterable[Mapping[str, Any]]):
        if any(type(v) is not int or v <= 0 or v >= 2**31
               for v in (mission_id,token,player_id)):
            raise ValueError('Invalid mission, session token, or SC2 player ID')
        self.mission_id, self.token, self.player_id = mission_id, token, player_id
        rows = [dict(m) for m in manifest]
        self.manifest = {str(m['copy_id']):m for m in rows}
        if len(self.manifest) != len(rows):
            raise ValueError('Duplicate Crew IDs')
        self.index = 0
        self.pending: tuple[int,str,str,set[int]] | None = None
        self.finished: dict[str,int] = {}

    def start_message(self) -> str:
        return f'?SlayCrewSession {self.token}'

    def end_message(self) -> str:
        if self.pending is not None:
            raise RuntimeError('Cannot end Crew spawn session during unconfirmed spawn')
        return f'?SlayCrewEnd {self.token}'

    def issue(self, copy_id: str, *, preexisting: Iterable[CrewUnitObservation],
              base_established: bool, prerequisite_ready: bool) -> str:
        if not base_established or not prerequisite_ready:
            raise RuntimeError('Crew cannot deploy before base and production prerequisite')
        if self.pending is not None:
            if self.pending[1] == copy_id:
                return f'?SlayCrewSpawn {self.token} {self.pending[0]} {self.pending[2]}'
            raise RuntimeError('Only one outstanding Crew spawn command is safe')
        if copy_id in self.finished or copy_id not in self.manifest:
            raise ValueError('Copy not available for deployment')
        m = self.manifest[copy_id]
        native_type = NATIVE_TYPES.get(str(m['name']))
        if native_type is None:
            raise ValueError('Crew type has no verified prototype SC2 unit mapping')
        if m.get('status') != 'pending':
            raise ValueError('Only pending Crew manifest copies may spawn')
        existing = tuple(preexisting)
        if any(type(obs.tag) is not int or obs.tag <= 0 for obs in existing):
            raise ValueError('Invalid baseline observation')
        self.pending = (self.index + 1, copy_id, native_type, {o.tag for o in existing})
        n,_,unit_type,_ = self.pending
        return f'?SlayCrewSpawn {self.token} {n} {unit_type}'

    def candidates(self, observations: Iterable[CrewUnitObservation]) -> tuple[int,...]:
        """Diagnostic candidates only. Never turn this result into a receipt."""
        if self.pending is None:
            return ()
        _,_,native_type,old = self.pending
        return tuple(sorted(o.tag for o in observations if o.tag not in old
                            and o.owner == self.player_id and o.native_type == native_type))

    def confirm(self, copy_id: str, *, verified_galaxy_tag: int,
                observations: Iterable[CrewUnitObservation]) -> tuple[str,int]:
        """Require an authenticated engine tag plus observed identity.

        A future trusted SC2 adapter must provide verified_galaxy_tag via an
        actual Galaxy-to-bot reply channel. An observation-only guess is not
        authorized to call this function or the persistent crew_bridge.
        """
        if self.pending is None or self.pending[1] != copy_id:
            raise ValueError('No matching outstanding Crew request')
        if type(verified_galaxy_tag) is not int or verified_galaxy_tag <= 0:
            raise ValueError('Missing trusted Galaxy unit tag')
        possible = self.candidates(observations)
        if possible != (verified_galaxy_tag,):
            raise RuntimeError('Ambiguous or mismatched SC2 spawn evidence; leave roster unmodified')
        _,_,native_type,_ = self.pending
        self.index += 1
        self.finished[copy_id] = verified_galaxy_tag
        self.pending = None
        return native_type,verified_galaxy_tag


