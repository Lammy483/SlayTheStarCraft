"""Provisional core-unit/structure cost catalog for Crew UI development.

NOT the complete AP unit/structure catalog. Unsupported production variants
are excluded from purchasable Crew offers.
"""
from __future__ import annotations

# Reactor permits simultaneous queues but Crew intentionally authorizes only
# one active purchase per producer. Never sell these addons in Crew mode.
# Royal Guard, non-playable novelty/story units and Dominion Elite actors are
# not ordinary purchasable Standard unlocks. Exclude from ALL Crew catalog
# consumers (including unit reward pools), not only the shop rendering.
CREW_NOT_STANDARD_UNITS = frozenset({
    'Pride of Augustgrad','Sky Fury','Shock Division','Blackhammer',
    'Aegis Guard',"Emperor's Shadow",'Son of Korhal','Bulwark Company',
    'Field Response Theta',"Emperor's Guardian",'Night Hawk','Night Wolf',
    'Tauren Marine',
    'Bullfrog',  # Crew-only exclusion; AP/Standard catalog remains unchanged.
})

CREW_BLOCKED_REACTOR_ITEMS = frozenset({
    'Reactor', 'Barracks Reactor', 'Factory Reactor', 'Starport Reactor',
    'Tech Reactor (Terran)', 'Tech Reactor',
})

# Tuple: (name, minerals, gas, supply, required production building)
_CORE={
 'terran':{
  'structure':[
   ('Command Center',400,0,0,''),('Supply Depot',100,0,0,''),
   ('Refinery',75,0,0,''),('Barracks',150,0,0,''),
   ('Factory',150,100,0,''),('Starport',150,100,0,''),
   ('Engineering Bay',125,0,0,''),('Armory',150,100,0,''),
   ('Tech Lab',50,25,0,''),('Planetary Fortress',150,150,0,''),
   ('Bunker',100,0,0,''),('Devastator Turret',150,100,0,''),
   ('Perdition Turret',100,50,0,''),
   ('Missile Turret',100,0,0,''),('Sensor Tower',125,100,0,''),
   ('SCV',50,0,1,'Command Center')],
  'unit':[
   ('Marine',50,0,1,'Barracks'),('Dominion Trooper',40,0,1,'Barracks'),('Marauder',100,25,2,'Barracks'),
   ('Reaper',50,50,1,'Barracks'),('Firebat',100,25,2,'Barracks'),
   ('Hellion',100,0,2,'Factory'),('Vulture',75,0,2,'Factory'),('Siege Tank',150,125,3,'Factory'),
   ('Viking',150,75,2,'Starport'),('Medivac',100,100,2,'Starport'),
   ('Banshee',150,100,3,'Starport'),('Battlecruiser',400,300,6,'Starport'),
   ('Medic',50,25,1,'Barracks'),('Ghost',150,125,2,'Barracks'),
   ('Spectre',150,150,2,'Barracks'),('HERC',100,50,2,'Barracks'),
   ('Goliath',150,50,2,'Factory'),('Diamondback',150,150,3,'Factory'),
   ('Widow Mine',75,25,2,'Factory'),('Cyclone',150,100,3,'Factory'),
   ('Thor',300,200,6,'Factory'),('Warhound',150,75,2,'Factory'),
   ('Wraith',150,100,2,'Starport'),('Raven',100,200,2,'Starport'),
   ('Science Vessel',100,200,2,'Starport'),('Valkyrie',250,125,3,'Starport'),
   ('Liberator',150,150,3,'Starport')],
 },
 'zerg':{
  'structure':[
   ('Hatchery',300,0,0,''),('Lair',150,100,0,''),('Hive',200,150,0,''),
   ('Overlord',100,0,0,''),('Extractor',25,0,0,''),
   ('Spawning Pool',200,0,0,''),('Evolution Chamber',75,0,0,''),
   ('Roach Warren',150,0,0,''),('Baneling Nest',100,50,0,''),
   ('Hydralisk Den',100,100,0,''),('Infestation Pit',100,100,0,''),
   ('Spire',200,200,0,''),('Ultralisk Cavern',150,200,0,''),
   ('Spine Crawler',100,0,0,''),('Spore Crawler',75,0,0,''),
   ('Drone',50,0,1,'Hatchery')],
  'unit':[
   ('Zergling',25,0,.5,'Spawning Pool'),('Baneling',50,25,.5,'Spawning Pool'),
   ('Roach',75,25,2,'Roach Warren'),('Hydralisk',100,50,2,'Hydralisk Den'),
   ('Queen',150,0,2,'Hatchery'),('Mutalisk',100,100,2,'Spire'),
   ('Corruptor',150,100,2,'Spire'),('Ultralisk',300,200,6,'Ultralisk Cavern')],
 },
 'protoss':{
  'structure':[
   ('Nexus',400,0,0,''),('Pylon',100,0,0,''),('Assimilator',75,0,0,''),
   ('Gateway',150,0,0,''),('Cybernetics Core',150,0,0,''),
   ('Forge',150,0,0,''),('Robotics Facility',200,100,0,''),
   ('Stargate',150,150,0,''),('Twilight Council',150,100,0,''),
   ('Robotics Bay',150,150,0,''),('Templar Archives',150,200,0,''),
   ('Fleet Beacon',300,200,0,''),('Photon Cannon',150,0,0,''),
   ('Probe',50,0,1,'Nexus')],
  'unit':[
   ('Zealot',100,0,2,'Gateway'),('Stalker',125,50,2,'Gateway'),
   ('Sentry',50,100,2,'Gateway'),('Adept',100,25,2,'Gateway'),
   ('Immortal',250,100,4,'Robotics Facility'),
   ('Observer',25,75,1,'Robotics Facility'),
   ('Warp Prism',200,0,2,'Robotics Facility'),
   ('Colossus',300,200,6,'Robotics Facility'),
   ('Void Ray',250,150,4,'Stargate'),('Carrier',350,250,6,'Stargate')],
 },
}

# AP-native additional units; costs are Crew pricing inputs and should be
# reconciled against individual Standard campaign variant recipes in SC2.
_ADDITIONAL={
 'terran':[
  ('Shock Division',200,125,3,'Factory'),
  ('Bulwark Company',150,150,3,'Factory'),
  ('Blackhammer',250,150,4,'Factory'),
  ('Son of Korhal',100,50,2,'Barracks'),
  ('Field Response Theta',50,75,2,'Barracks'),
  ("Emperor's Shadow",150,150,2,'Barracks'),
  ('Aegis Guard',100,50,2,'Barracks'),
  ('Predator',100,100,2,'Factory'),
  ('Hercules',300,200,4,'Starport'),
  ('Bullfrog',150,100,2,'Factory'),
  ('Tauren Marine',100,50,2,'Barracks'),
 ],
 'zerg':[
  ('Lurker',150,150,2,'Hydralisk Den'),
  ('Impaler',150,150,2,'Hydralisk Den'),
  ('Viper',100,200,3,'Hive'),
  ('Swarm Host',100,75,3,'Infestation Pit'),
  ('Infestor',100,150,2,'Infestation Pit'),
  ('Overseer',150,50,0,'Hatchery'),
  ('Brood Lord',300,250,4,'Spire'),
  ('Guardian',300,200,3,'Spire'),
  ('Devourer',300,200,3,'Spire'),
  ('Scourge',25,75,0.5,'Spire'),
  ('Ravager',100,100,3,'Roach Warren'),
  ('Defiler',50,150,2,'Infestation Pit'),
  ('Aberration',150,150,4,'Hatchery'),
 ],
 'protoss':[
  ('Trireme',350,250,6,'Stargate'),
  ('Skylord',350,250,6,'Stargate'),
  ('Skirmisher',150,100,2,'Stargate'),
  ('Pulsar',150,100,2,'Stargate'),
  ('Oppressor',250,150,3,'Stargate'),
  ('Mist Wing',150,100,2,'Stargate'),
  ('Destroyer',250,150,4,'Stargate'),
  ('Dawnbringer',250,175,4,'Stargate'),
  ('Caladrius',150,100,2,'Stargate'),
  ('Supplicant',50,0,1,'Gateway'),
  ('Signifier',50,150,2,'Gateway'),
  ('Sentinel',100,0,2,'Gateway'),
  ('Havoc',50,100,2,'Gateway'),
  ('Blood Hunter',125,125,2,'Gateway'),
  ('Dragoon',125,50,2,'Gateway'),
  ('High Templar',50,150,2,'Gateway'),
  ('Dark Templar',125,125,2,'Gateway'),
  ('Archon',100,300,4,'Gateway'),
  ('Dark Archon',250,250,4,'Gateway'),
  ('Phoenix',150,100,2,'Stargate'),
  ('Scout',275,125,3,'Stargate'),
  ('Oracle',150,150,3,'Stargate'),
  ('Disruptor',150,150,3,'Robotics Facility'),
  ('Reaver',200,100,4,'Robotics Facility'),
  ('Arbiter',100,350,4,'Stargate'),
  ('Corsair',150,100,2,'Stargate'),
  ('Tempest',250,175,4,'Stargate'),
  ('Mothership',400,400,8,'Stargate'),
  ('Mirage',150,100,2,'Stargate'),
  ('Centurion',100,0,2,'Gateway'),
  ('Instigator',125,50,2,'Gateway'),
  ('Avenger',125,125,2,'Gateway'),
  ('Slicer',100,50,2,'Gateway'),
  ('Vanguard',125,100,3,'Robotics Facility'),
  ('Wrathwalker',200,150,4,'Robotics Facility'),
  ('Ascendant',50,150,2,'Gateway'),
  ('Slayer',125,50,2,'Gateway'),
  ('Annihilator',250,100,4,'Robotics Facility'),
  ('Energizer',50,100,2,'Gateway'),
 ],
}


def preview_catalog(races=('terran',)):
    """Verified *core* choices only. An AP-complete catalog remains a blocker."""
    result=[]
    for race in races:
        if race not in _CORE:raise ValueError('Invalid Crew race')
        for category,entries in _CORE[race].items():
            if category=='unit':entries=list(entries)+_ADDITIONAL.get(race,[])
            for name,m,g,supply,required in entries:
                if name in CREW_BLOCKED_REACTOR_ITEMS or name in CREW_NOT_STANDARD_UNITS:
                    continue
                result.append(dict(name=name,race=race,category=category,
                    minerals=m,gas=g,supply=supply,requires=required))
    producers={entry['requires'] for entry in result if entry['category']=='unit' and entry['requires']}
    for entry in result:
        entry['enables_units']=entry['category']=='structure' and entry['name'] in producers
    return result


def catalog_entry_for_standard_unit(name: str, race: str):
    """Return priced, verified catalog entries for Standard AP unit types.

    The Standard item table determines which campaign unit unlocks are real;
    this conversion refuses entries without a Crew cost/producer mapping.
    """
    return next((dict(row) for row in preview_catalog((race,))
                 if row['category']=='unit' and row['name']==name),None)
