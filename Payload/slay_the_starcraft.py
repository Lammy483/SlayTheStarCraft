

















from __future__ import annotations

PACKAGE_VERSION = "1.2.2"



import copy

import csv

import hashlib

import importlib.util

import json

import logging

import math

import os

import random

import re

from collections import Counter

from pathlib import Path

from typing import Any, Iterable, Mapping, Sequence



from BaseClasses import ItemClassification

from NetUtils import NetworkItem

from Utils import async_start



from .item.item_tables import get_full_item_list

try:

    from .item import item_parents as _AP_ITEM_PARENTS

except Exception:

    _AP_ITEM_PARENTS = None

try:

    from .item.item_groups import item_name_groups as _AP_ITEM_NAME_GROUPS

except Exception:





    _AP_ITEM_NAME_GROUPS = {}



logger = logging.getLogger("Starcraft2")



AP_ITEM_DOCS_FILE = "slay_ap_item_docs.json"



def _load_ap_item_docs() -> dict[str, dict[str, str]]:

    try:

        data = json.loads((Path(__file__).resolve().parent / AP_ITEM_DOCS_FILE).read_text(encoding="utf-8"))

        if isinstance(data, dict):

            return {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}

    except Exception:

        pass

    return {}



_AP_ITEM_DOCS = _load_ap_item_docs()



POTION_ICONS = {
    1: 'icon-mineral-nobg.png',
    2: 'icon-gas-terran-nobg.png',
    3: 'btn-unit-terran-odin.png',
    4: 'btn-unit-zerg-leviathan.png',
    5: 'btn-unit-terran-battlecruiser.png',
    6: 'talent-raynor-level08-orbitaldroppods.png',
    7: 'btn-ability-terran-emp-color.png',
    8: 'btn-ability-terran-armnuke.png',
    9: 'btn-building-nova-orbitalcommand.png',
    10: 'btn-ability-terran-cloak-color.png',
    11: 'btn-ability-terran-stimpack-color.png',
    12: 'btn-ability-spearofadun-chronosurge.png',
    13: 'btn-commander-kerrigan.png',
    14: 'btn-tips-mercenary.png',
    15: 'btn-upgrade-swann-defensivematrix.png',
    16: 'btn-ability-zerg-corruption-color.png',
    17: 'btn-unit-terran-marine.png',
    18: 'btn-unit-protoss-hightemplar.png',
    19: 'btn-unit-terran-marine.png',

}
POTION_VARIANT_ICONS = {
    1: 'btn-unit-terran-marine.png',
    2: 'btn-unit-terran-marauder.png',
    3: 'btn-unit-terran-reaper.png',
    4: 'btn-unit-terran-hellion.png',
    5: 'btn-unit-terran-siegetank.png',
    6: 'btn-unit-terran-viking.png',
    7: 'btn-unit-terran-banshee.png',
    8: 'btn-unit-terran-thor.png',
    9: 'btn-unit-zerg-roach.png',
    10: 'btn-unit-zerg-hydralisk.png',
    11: 'btn-unit-zerg-mutalisk.png',
    12: 'btn-unit-zerg-ultralisk.png',
    13: 'btn-unit-protoss-zealot.png',
    14: 'btn-unit-protoss-stalker.png',
    15: 'btn-unit-protoss-immortal.png',
    16: 'btn-unit-protoss-voidray-purifier.png',
    17: 'btn-unit-protoss-colossus.png',
    18: 'btn-unit-protoss-hightemplar.png',

}

def shop_entry_icon(item_name: str) -> str:
    if item_name in POTION_CATALOG:
        index = int(POTION_CATALOG[item_name]["index"])
        if 1901 <= index <= 1918:
            return POTION_VARIANT_ICONS[index - 1900]
        return POTION_ICONS.get(index, "btn-unit-terran-marine.png")



    if item_name.startswith(BOON_PREFIX):

        return ""

    return str(_AP_ITEM_DOCS.get(str(item_name), {}).get("icon", "") or "")



COMMANDER_HERO_NAMES: dict[int, str] = {

    0: "Raynor", 2: "Tychus", 5: "Swann", 7: "Zeratul", 9: "Artanis",

    10: "Alarak", 13: "Mohandar", 14: "Selendis", 15: "Karax", 18: "Zagara",

    19: "Dehaka", 20: "Nova", 23: "Tosh", 24: "Stukov", 27: "Fenix",

    30: "Vorazun", 31: "Stukov", 32: "Urun", 33: "Niadra", 34: "Karass",

}





COMMANDER_GENERATED_INDICES: tuple[int, ...] = (

    0, 5, 7, 9, 10, 13, 14, 15, 18, 19, 20, 23, 24, 27, 30, 32, 33, 34,

)



RUN_FILE_NAME = "slay_the_starcraft_run.json"

STATE_FILE_PREFIX = "slay_the_starcraft_state_"



RACE_WEAPON_ARMOR_UPGRADE_ITEMS = {

    "Progressive Terran Weapon/Armor Upgrade",

    "Progressive Zerg Weapon/Armor Upgrade",

    "Progressive Protoss Weapon/Armor Upgrade",

}









RACE_GLOBAL_UPGRADE_ITEMS = {

    "terran": {

        "Progressive Terran Weapon/Armor Upgrade",







        "Progressive Fire-Suppression System (Terran)",

        "Progressive Regenerative Bio-Steel (Terran)",

        "Cellular Reactor (Terran)", "Automated Refinery (Terran)",

        "Tech Reactor (Terran)", "Ultra-Capacitors (Terran)",

        "Vanadium Plating (Terran)", "Advanced Optics (Terran)",

        "Structure Armor (Terran)", "Hi-Sec Auto Tracking (Terran)",

        "Orbital Depots (Terran)", "Micro-Filtering (Terran)",

        "Advanced Construction (SCV)", "Dual-Fusion Welders (SCV)",

        "Construction Jump Jets (SCV)",

        "Command Center Reactor (Command Center)",

        "Mechanical Know-how (Terran)", "Mercenary Munitions (Terran)",



        "Extra Supplies (Command Center)", "MULE (Command Center)",

        "Scanner Sweep (Command Center)", "Orbital Module (Planetary Fortress)",

    },

    "zerg": {

        "Progressive Zerg Weapon/Armor Upgrade",



        "Automated Extractors (Zerg)", "Improved Overlords (Overlord)",

        "Malignant Creep (Zerg)", "Twin Drones (Zerg)",

        "Vespene Efficiency (Zerg)", "Zergling Reconstitution (Zerg)",

        "Excavating Claws (Zerg)", "Creep Stomach (Zerg)",

        "Hive Cluster Maturation (Zerg)", "Macroscopic Recuperation (Zerg)",

        "Broodling Spore Saturation (Zerg)",

    },

    "protoss": {

        "Progressive Protoss Weapon/Armor Upgrade",

        "Amplified Assimilators (Protoss)", "Elder Probes (Protoss)",

        "Khalai Ingenuity (Protoss)",

        "Matrix Overload (Protoss)", "Nexus Overcharge (Protoss)",

        "Optimized Ordnance (Protoss)", "Orbital Assimilators (Protoss)",

        "Warp Harmonization (Protoss)", "Superior Warp Gates (Protoss)",

        "Progressive Warp Relocate (Protoss)", "Probe Warp-In (Protoss)",

        "Quatro (Protoss)",

    },

}





REDUNDANT_BASIC_STAT_UPGRADE_ITEMS = {

    "Progressive Terran Armor Upgrade", "Progressive Terran Infantry Armor",

    "Progressive Terran Infantry Upgrade", "Progressive Terran Infantry Weapon",

    "Progressive Terran Ship Armor", "Progressive Terran Ship Upgrade",

    "Progressive Terran Ship Weapon", "Progressive Terran Vehicle Armor",

    "Progressive Terran Vehicle Upgrade", "Progressive Terran Vehicle Weapon",

    "Progressive Terran Weapon Upgrade",

    "Progressive Zerg Armor Upgrade", "Progressive Zerg Flyer Attack",

    "Progressive Zerg Flyer Carapace", "Progressive Zerg Flyer Upgrade",

    "Progressive Zerg Ground Carapace", "Progressive Zerg Ground Upgrade",

    "Progressive Zerg Melee Attack", "Progressive Zerg Missile Attack",

    "Progressive Zerg Weapon Upgrade",

    "Progressive Protoss Air Armor", "Progressive Protoss Air Upgrade",

    "Progressive Protoss Air Weapon", "Progressive Protoss Armor Upgrade",

    "Progressive Protoss Ground Armor", "Progressive Protoss Ground Upgrade",

    "Progressive Protoss Ground Weapon", "Progressive Protoss Shields",

    "Progressive Protoss Weapon Upgrade",

}









REDUNDANT_WAR_COUNCIL_UPGRADE_ITEMS = {"Enhanced Targeting (Protoss)"}



RESEARCH_SPEED_ITEM = "Increased Upgrade Research Speed"

GENERIC_OTHER_UPGRADE_ITEMS = {

    "Increased Building Construction Speed",

    "Increased Shield Regeneration",

    "Increased Upgrade Research Speed",

    "Reduced Upgrade Research Cost",

}









LEGACY_35_CREDIT_GENERIC_ITEMS = {

    "Additional Starting Minerals",

    "Additional Starting Vespene",

    "Additional Starting Supply",

    "Additional Maximum Supply",

    "Increased Shield Regeneration",

    "Increased Building Construction Speed",

    "Reduced Upgrade Research Cost",

}



DEFENSIVE_STRUCTURE_ITEMS = {

    "Bunker", "Missile Turret", "Devastator Turret", "Planetary Fortress",

    "Perdition Turret", "Sensor Tower", "Psi Disrupter", "Hive Mind Emulator",
    "Sonic Disrupter (Psi Disrupter)", "Psi Screen (Psi Disrupter)",

    "Argus Amplifier (Hive Mind Emulator)", "Psi Indoctrinator (Hive Mind Emulator)",

    "Spine Crawler", "Spore Crawler", "Bile Launcher", "Infested Bunker",

    "Infested Missile Turret", "Photon Cannon", "Khaydarin Monolith", "Shield Battery",

}









PROGRESSION_PREFIX = "PROGRESSION::"

TERRAN_CONTRACTS = PROGRESSION_PREFIX + "terran_contracts"

ZERG_CONTRACTS = PROGRESSION_PREFIX + "zerg_contracts"

KERRIGAN_UNLOCK = PROGRESSION_PREFIX + "kerrigan_unlock"

SPEAR_UNLOCK = PROGRESSION_PREFIX + "spear_unlock"

SPEAR_ENERGY_REGEN = PROGRESSION_PREFIX + "spear_energy_regen"

SPEAR_COOLDOWN_REDUCTION = PROGRESSION_PREFIX + "spear_cooldown_reduction"

SPEAR_PRICE_DISCOUNT = PROGRESSION_PREFIX + "spear_price_discount"

KERRIGAN_PRICE_DISCOUNT = PROGRESSION_PREFIX + "kerrigan_price_discount"

KERRIGAN_RECKLESS_POWER = PROGRESSION_PREFIX + "kerrigan_reckless_power"

KERRIGAN_RECKLESS_SPEED = PROGRESSION_PREFIX + "kerrigan_reckless_speed"

KERRIGAN_CUSTOM_ITEMS = (KERRIGAN_PRICE_DISCOUNT, KERRIGAN_RECKLESS_POWER, KERRIGAN_RECKLESS_SPEED)

SPEAR_CUSTOM_ITEMS = (SPEAR_ENERGY_REGEN, SPEAR_COOLDOWN_REDUCTION, SPEAR_PRICE_DISCOUNT)

MERCENARY_UPGRADE_PREFIX = PROGRESSION_PREFIX + "mercenary_upgrade::"

MERC_ELITE = MERCENARY_UPGRADE_PREFIX + "elite_mercenaries"

MERC_ARMORED = MERCENARY_UPGRADE_PREFIX + "armored_mercenaries"

MERC_REGENERATIVE = MERCENARY_UPGRADE_PREFIX + "regenerative_mercenaries"

MERC_SNIPER = MERCENARY_UPGRADE_PREFIX + "sniper_mercenaries"

MERC_AFFORDABLE = MERCENARY_UPGRADE_PREFIX + "affordable_mercenaries"

MERC_REPEAT_CONTRACTOR = MERCENARY_UPGRADE_PREFIX + "repeat_contractor"

MERC_SPOTTERS = MERCENARY_UPGRADE_PREFIX + "spotters"

MERC_SUPPORT_CREW = MERCENARY_UPGRADE_PREFIX + "support_crew"

MERCENARY_CUSTOM_UPGRADE_ITEMS = (

    MERC_ELITE, MERC_ARMORED, MERC_REGENERATIVE,

    MERC_SNIPER, MERC_AFFORDABLE, MERC_REPEAT_CONTRACTOR,

    MERC_SPOTTERS, MERC_SUPPORT_CREW,

)

MERCENARY_CUSTOM_UPGRADE_TITLES = {

    MERC_ELITE: "Elite Mercenaries",

    MERC_ARMORED: "Armored Mercenaries",

    MERC_REGENERATIVE: "Regenerative Mercenaries",

    MERC_SNIPER: "Sniper Mercenaries",

    MERC_AFFORDABLE: "Affordable Mercenaries",

    MERC_REPEAT_CONTRACTOR: "Repeat Contractor",

    MERC_SPOTTERS: "Spotters",

    MERC_SUPPORT_CREW: "Support Crew",

}

SLAYER_PHASE_BLINK = "Phase Blink (Slayer)"



PROGRESSION_DISPLAY_NAMES = {

    TERRAN_CONTRACTS: "Terran Contracts",

    ZERG_CONTRACTS: "Zerg Contracts",

    KERRIGAN_UNLOCK: "Unlock Kerrigan",

    SPEAR_UNLOCK: "Unlock Spear of Adun",

    SPEAR_ENERGY_REGEN: "Increase Spear of Adun Energy Recharge Rate",

    SPEAR_COOLDOWN_REDUCTION: "Reduce Spear of Adun Cooldowns",

    SPEAR_PRICE_DISCOUNT: "Reduced Spear of Adun Shop Prices by 50%",

    KERRIGAN_PRICE_DISCOUNT: "Reduced Kerrigan Shop Prices by 50%",

    KERRIGAN_RECKLESS_POWER: "Reckless Power",

    KERRIGAN_RECKLESS_SPEED: "Reckless Speed",

}

PROGRESSION_DESCRIPTIONS = {

    TERRAN_CONTRACTS: "Unlock the Terran Mercenary Compound in every mission.",

    ZERG_CONTRACTS: "Unlock the Zerg Predator Nest in every mission.",

    KERRIGAN_UNLOCK: "Kerrigan joins every mission and appears at your established base.",

    SPEAR_UNLOCK: "",

    SPEAR_ENERGY_REGEN: "",

    SPEAR_COOLDOWN_REDUCTION: "",

    SPEAR_PRICE_DISCOUNT: "",

    KERRIGAN_PRICE_DISCOUNT: "",

    KERRIGAN_RECKLESS_POWER: "Kerrigan gains 50% damage and maximum energy but takes twice as long to respawn after death",

    KERRIGAN_RECKLESS_SPEED: "Kerrigan gains 50% speed and attack speed but takes twice as long to respawn",

}









def _ap_group_items(group_name: str) -> set[str]:

    try:

        return {str(x) for x in _AP_ITEM_NAME_GROUPS.get(group_name, ())}

    except Exception:

        return set()



TERRAN_MERCENARY_ITEMS = _ap_group_items("Terran Mercenaries")

ZERG_MERCENARY_ITEMS = _ap_group_items("Zerg Mercenaries")

KERRIGAN_ABILITY_ITEMS = _ap_group_items("Kerrigan Abilities")

SPEAR_OF_ADUN_ITEMS = _ap_group_items("SOA")









PROTOSS_WAR_COUNCIL_ITEMS = _ap_group_items("Protoss War Council Upgrades")

MERCENARY_GENERAL_UPGRADE_ITEMS = {







    "Rogue Forces (Terran)", "Progressive Fast Delivery (Terran)",

    "Rapid Reinforcement (Terran)", "Signal Beacon (Terran)",

    "Cell Division (Zerg)", "Self-Sufficient (Zerg)",

    "Unrestricted Mutation (Zerg)", "Evolutionary Leap (Zerg)",

}





def _load_mercenary_shop_catalog_rows() -> dict[str, dict[str, str]]:



    try:

        path = Path(__file__).resolve().parent / "MERCENARY_SHOP_CATALOG.csv"

        with path.open(encoding="utf-8-sig", newline="") as handle:

            rows: dict[str, dict[str, str]] = {}

            for row in csv.DictReader(handle):

                title = str(row.get("Item Title", "")).strip()

                if title:

                    rows[title] = row

            return rows

    except Exception:

        return {}



_MERCENARY_SHOP_CATALOG_ROWS = _load_mercenary_shop_catalog_rows()



def _load_unit_shop_price_overrides() -> dict[str, int]:



    result: dict[str, int] = {}

    try:

        path = Path(__file__).resolve().parent / "UNIT_SHOP_CATALOG.csv"

        with path.open(encoding="utf-8-sig", newline="") as handle:

            for row in csv.DictReader(handle):

                name = str(row.get("Unit", "")).strip()

                if not name:

                    continue

                try:

                    result[name] = max(0, int(str(row.get("Price", "")).strip()))

                except (TypeError, ValueError):

                    continue

    except Exception:

        return {}

    return result



UNIT_SHOP_PRICE_OVERRIDES = _load_unit_shop_price_overrides()



def _variant_family_unit_price(item_name: str) -> int | None:















    folded = str(item_name or "").strip().casefold()

    if "scout" in folded and folded != "scout":

        return UNIT_SHOP_PRICE_OVERRIDES.get("archipelago scout variants")

    if "void ray" in folded and folded != "void ray":

        return UNIT_SHOP_PRICE_OVERRIDES.get("archipelago void ray variants")

    return None



MERCENARY_SHOP_PRICE_OVERRIDES: dict[str, int] = {}

for _merc_title, _merc_row in _MERCENARY_SHOP_CATALOG_ROWS.items():

    try:

        MERCENARY_SHOP_PRICE_OVERRIDES[_merc_title] = max(0, int(str(_merc_row.get("Cost", "")).strip()))

    except (TypeError, ValueError):

        pass



PROGRESSION_DISPLAY_NAMES.update(MERCENARY_CUSTOM_UPGRADE_TITLES)

for _merc_key, _merc_title in MERCENARY_CUSTOM_UPGRADE_TITLES.items():

    _merc_row = _MERCENARY_SHOP_CATALOG_ROWS.get(_merc_title, {})

    PROGRESSION_DESCRIPTIONS[_merc_key] = str(

        _merc_row.get("Description", "")

    ).strip()

KERRIGAN_PRIMAL_FORM_ITEM = "Primal Form (Kerrigan)"



SHOP_CATALOG_DESCRIPTION_COLUMN = "Description"



def _load_progression_shop_catalog_rows(filename: str) -> dict[str, dict[str, str]]:



    try:

        path = Path(__file__).resolve().parent / filename

        with path.open(encoding="utf-8-sig", newline="") as handle:

            rows: dict[str, dict[str, str]] = {}

            for row in csv.DictReader(handle):

                title = str(row.get("Item Title", "")).strip()

                if title:

                    rows[title] = row

            return rows

    except Exception:

        return {}



def _catalog_int_prices(rows: Mapping[str, Mapping[str, str]]) -> dict[str, int]:

    result: dict[str, int] = {}

    for title, row in rows.items():

        try:

            result[str(title)] = max(0, int(str(row.get("Cost", "")).strip()))

        except (TypeError, ValueError):

            pass

    return result



_KERRIGAN_SHOP_CATALOG_ROWS = _load_progression_shop_catalog_rows("KERRIGAN_SHOP_CATALOG.csv")

_SPEAR_SHOP_CATALOG_ROWS = _load_progression_shop_catalog_rows("SPEAR_OF_ADUN_SHOP_CATALOG.csv")

KERRIGAN_SHOP_PRICE_OVERRIDES = _catalog_int_prices(_KERRIGAN_SHOP_CATALOG_ROWS)

SPEAR_SHOP_PRICE_OVERRIDES = _catalog_int_prices(_SPEAR_SHOP_CATALOG_ROWS)







for _pseudo, _title in {

    KERRIGAN_PRICE_DISCOUNT: "Reduced Kerrigan Shop Prices by 50%",

    KERRIGAN_RECKLESS_POWER: "Reckless Power",

    KERRIGAN_RECKLESS_SPEED: "Reckless Speed",

}.items():

    PROGRESSION_DESCRIPTIONS[_pseudo] = str(_KERRIGAN_SHOP_CATALOG_ROWS.get(_title, {}).get(SHOP_CATALOG_DESCRIPTION_COLUMN, "")).strip()

for _pseudo, _title in {

    SPEAR_ENERGY_REGEN: "Increase Spear of Adun Energy Recharge Rate",

    SPEAR_COOLDOWN_REDUCTION: "Reduce Spear of Adun Cooldowns",

    SPEAR_PRICE_DISCOUNT: "Reduced Spear of Adun Shop Prices by 50%",

}.items():

    PROGRESSION_DESCRIPTIONS[_pseudo] = str(_SPEAR_SHOP_CATALOG_ROWS.get(_title, {}).get(SHOP_CATALOG_DESCRIPTION_COLUMN, "")).strip()



PROGRESSION_DESCRIPTIONS[SPEAR_UNLOCK] = str(_SPEAR_SHOP_CATALOG_ROWS.get("Unlock Spear of Adun", {}).get(SHOP_CATALOG_DESCRIPTION_COLUMN, "")).strip()













MERCENARY_BASE_UNIT_EQUIVALENTS: dict[str, set[str]] = {





    "Marine": {"War Pigs"},

    "Firebat": {"Devil Dogs"},

    "Marauder": {"Hammer Securities"},

    "Goliath": {"Spartan Company"},

    "Siege Tank": {"Siege Breakers"},

    "Viking": {"Hel's Angels"},

    "Banshee": {"Dusk Wings"},

    "Battlecruiser": {"Jackson's Revenge"},

    "Medic": {"Skibi's Angels", "Infested Medics"},

    "Reaper": {"Death Heads"},

    "Wraith": {"Winged Nightmares"},

    "Liberator": {"Midnight Riders"},

    "Valkyrie": {"Brynhilds"},

    "Thor": {"Jotun"},



    "Zergling": {"Devouring Ones"},

    "Hydralisk": {"Hunter Killers"},

    "Ultralisk": {"Wise Old Torrasque"},

    "Roach": {"Caustic Horrors"},

    "Overlord": {"Yggdrasil"},





    "Infested Siege Tank": {"Infested Siege Breakers"},

    "Infested Banshee": {"Infested Dusk Wings"},

}



# The Spear's initial Deploy Pylon tier is granted for free on unlock.
SPEAR_BASE_PYLON_ITEM = "Progressive Proxy Pylon (Spear of Adun)"

SPEAR_FALLBACK_ITEMS = {

    "Chrono Surge (Spear of Adun)", "Progressive Proxy Pylon (Spear of Adun)",

    "Pylon Overcharge (Spear of Adun)", "Orbital Strike (Spear of Adun)",

    "Temporal Field (Spear of Adun)", "Solar Lance (Spear of Adun)",

    "Mass Recall (Spear of Adun)", "Shield Overcharge (Spear of Adun)",

    "Deploy Fenix (Spear of Adun)", "Purifier Beam (Spear of Adun)",

    "Time Stop (Spear of Adun)", "Solar Bombardment (Spear of Adun)",

    "Guardian Shell (Spear of Adun)", "Reconstruction Beam (Spear of Adun)",

    "Overwatch (Spear of Adun)",

}

SPEAR_OF_ADUN_ITEMS.update(SPEAR_FALLBACK_ITEMS)

SPEAR_CHEAP_BASE_NAMES = {"Pylon Overcharge", "Temporal Field", "Mass Recall", "Recall", "Orbital Strike", "Progressive Proxy Pylon"}





EFFECT_BANK_BITS: dict[str, tuple[int, int]] = {'low_quality_minerals': (0, 1), 'conga_line': (0, 2), 'ten_minutes_until_destruction': (0, 4), 'golden_armada': (0, 8), 'siege_mode': (0, 16), 'drakken_laser_drill_enemy': (0, 32), 'dark_archons': (0, 64), 'drop_pods': (0, 128), 'dark_templar': (0, 256), 'fragile_workers': (0, 512), 'decay': (0, 1024), 'zombies_mutation': (0, 2048), 'limited_bank': (0, 4096), 'leviathan_in_orbit': (0, 8192), 'heroes_of_the_storm': (0, 16384), 'too_many_wraiths': (0, 32768), 'void_thrashers': (0, 65536), 'not_enough_energy': (0, 131072), 'viking_raids': (0, 262144), 'nuclear_annihilation': (0, 524288), 'squishy': (0, 1048576), 'picky_eaters': (0, 2097152), 'darkness': (0, 4194304), 'adrenaline': (0, 8388608), 'arms_race': (0, 16777216), 'rising_gas_prices': (0, 33554432), 'forced_variety': (0, 67108864), 'occasional_thor_mutation': (0, 134217728), 'occasional_ultralisk_mutation': (0, 268435456), 'occasional_colossus_mutation': (0, 536870912), 'enemy_regeneration': (0, 1073741824), 'investors': (1, 1), 'multi_class': (1, 2), 'speedy': (1, 4), 'general': (1, 8), 'farseers': (1, 16), 'air_support': (1, 32), 'fire_squad': (1, 64), 'fuel_pipeline': (1, 128), 'rapid_evolution': (1, 256), 'zombies_blessing': (1, 512), 'compounding_interest': (1, 1024), 'transports': (1, 2048), 'lost_vikings': (1, 4096), 'warfields_reinforcements': (1, 8192), 'energy_overload': (1, 16384), 'explosive_armor': (1, 32768), 'instant_workers': (1, 65536), 'juggernaut': (1, 131072), 'assembly_line': (1, 262144), 'elite_soldiers': (1, 524288), 'blinding_light': (1, 1048576), 'specialists': (1, 2097152), 'fortifications': (1, 4194304), 'baneling_stream': (1, 8388608), 'tychus': (1, 16777216), 'zagaras_aid': (1, 33554432), 'logistics': (1, 67108864), 'occasional_thor_blessing': (2, 1), 'occasional_ultralisk_blessing': (2, 2), 'occasional_colossus_blessing': (2, 4), 'unexpected_evolution': (2, 8), 'another_gorgon_blessing': (2, 16), 'another_gorgon_mutation': (2, 32), 'burrowed_zerglings': (2, 64), 'sniper_thor': (2, 128), 'horde_mode': (2, 256), 'tower_defense': (2, 512), 'cloaked_nightmare': (2, 1024), 'rapid_repair': (2, 2048), 'blink_blessing': (2, 4096), 'boon_viking_anchors': (2, 8192), 'power_overwhelming': (2, 16384), 'drakken_laser_drill_blessing': (2, 32768), 'jetpacks': (2, 65536), 'stealth_tunnels': (2, 131072), 'lurker_defense': (2, 262144), 'combat_workers': (2, 524288), 'rapid_evolution_mutation': (2, 1048576), 'no_deaths_allowed': (2, 2097152), 'glass_cannons': (2, 4194304), 'victory_is_temporary': (2, 8388608), 'odin': (2, 16777216), 'nuclear_workers': (2, 33554432), 'bounty_kills': (2, 67108864), 'tactical_binoculars': (2, 134217728), 'building_overcharge': (2, 268435456), 'ghost_reporting': (2, 536870912), 'taldarim_reinforcements': (2, 1073741824), 'miras_mercenaries': (3, 1), 'glorious_martyrs': (3, 2), 'inflatable_soldiers': (3, 4), 'double_time': (3, 8), 'shrinkage': (3, 16), 'mineral_thieves': (3, 32), 'active_enemies': (3, 64), 'infinite_larva': (3, 128), 'zagaras_banelings': (3, 256), 'reflective_armor': (3, 512), 'buddy_system': (3, 1024), 'torrasque': (3, 2048), 'nexus_shield': (3, 4096), 'gargantuan_enemies': (3, 8192), 'boon_deadly_weapons': (3, 16384), 'boon_auto_repair': (3, 32768), 'boon_rapid_fire': (3, 65536), 'boon_shields_for_all': (3, 131072), 'boon_heavy_armor': (3, 262144), 'boon_unlimited_blink': (3, 524288), 'boon_interplanetary_fortress': (3, 1048576), 'boon_roach_infestation': (3, 2097152), 'boon_chain_reaction': (3, 4194304), 'boon_aiur_recruitment': (3, 8388608), 'boon_toxic_observation': (3, 16777216), 'boon_cloning_technology': (3, 33554432), 'raynors_raiders': (3, 67108864), 'boon_defender': (3, 134217728), 'boon_fire_power': (3, 268435456), 'boon_roachling_mines': (3, 536870912), 'boon_broodling_evolution': (3, 1073741824), 'boon_adamantium_blades': (1, 134217728), 'boon_enhanced_control': (1, 268435456), 'boon_banshee_swarm': (1, 536870912), 'boon_enlarged_banelings': (1, 1073741824), 'boon_corrosive_claws': (4, 2), 'boon_unlimited_power': (4, 4), 'boon_unstable_colossi': (4, 8), 'boon_archon_cannons': (4, 16), 'boon_hyrda_storms': (4, 32), 'boon_mobile_siege': (4, 64), 'boon_maddening_shades': (4, 128), 'boon_concussed_shells': (4, 256), 'purifier': (4, 512), 'spear_of_adun_blessing': (4, 1024), 'spear_of_adun_overcharge': (4, 2048), 'dehakas_pack': (4, 4096), 'zombie_apocalypse': (4, 8192), 'arguments': (4, 16384), 'combat_pay': (4, 32768), 'nuclear_structures': (4, 65536), 'resource_swap': (4, 131072), 'rich_vespene': (4, 262144), 'rich_minerals': (4, 524288), 'boon_missile_defense': (4, 1048576), 'boon_stretchy_spines': (4, 2097152), 'boon_gargantuan_units': (4, 4194304), 'boon_chaos_blessings': (4, 8388608)}

EFFECT_DISPLAY_NAMES: dict[str, str] = {'golden_armada': 'Golden Armada', 'low_quality_minerals': 'Low-Quality Minerals', 'conga_line': 'Meat Grinder', 'ten_minutes_until_destruction': '10 Minutes Until Destruction', 'siege_mode': 'Siege Mode', 'drakken_laser_drill_enemy': 'Drakken Laser Drill', 'dark_archons': 'Archons', 'drop_pods': 'Drop Pods', 'dark_templar': 'Dark Templar', 'fragile_workers': 'Fragile Workers', 'decay': 'Decay', 'zombies_mutation': 'Zombies', 'limited_bank': 'Limited Bank', 'leviathan_in_orbit': 'Leviathan In Orbit', 'heroes_of_the_storm': 'Heroes of the Storm', 'too_many_wraiths': 'Too many Wraiths', 'void_thrashers': 'Void Thrashers', 'not_enough_energy': 'Energy Leak', 'viking_raids': 'Viking Raids', 'nuclear_annihilation': 'Nuclear Annihilation', 'darkness': 'Darkness', 'adrenaline': 'Adrenaline', 'picky_eaters': 'Picky Eaters', 'arms_race': 'Arms Race', 'rising_gas_prices': 'Rising Gas Prices', 'squishy': 'Squishy', 'forced_variety': 'Forced Variety', 'occasional_thor_mutation': 'Occasional Thor', 'occasional_ultralisk_mutation': 'Occasional Ultralisk', 'occasional_colossus_mutation': 'Occasional Colossus', 'enemy_regeneration': 'Enemy Regeneration', 'investors': 'Investors', 'multi_class': 'Multi-Class', 'speedy': 'Speedy', 'general': 'Commander', 'farseers': 'Farseers', 'air_support': 'Air Support', 'fire_squad': 'Fire Squad', 'fuel_pipeline': 'Fuel Pipeline', 'rapid_evolution': 'Constant Evolution', 'zombies_blessing': 'Zombies', 'compounding_interest': 'Compound Interest', 'transports': 'Transports', 'lost_vikings': 'Lost Vikings', 'warfields_reinforcements': "Warfield's Reinforcements", 'energy_overload': 'Energy Overload', 'explosive_armor': 'Explosive Armor', 'instant_workers': 'Instant workers', 'juggernaut': 'Juggernaut', 'assembly_line': 'Assembly Line', 'elite_soldiers': 'Elite Soldiers', 'blinding_light': 'Blinding Light', 'specialists': 'Specialists', 'fortifications': 'Fortifications', 'baneling_stream': 'Baneling Stream', 'tychus': 'Tychus', 'zagaras_aid': "Zagara's Aid", 'logistics': 'Logistics', 'occasional_thor_blessing': 'Occasional Thor', 'occasional_ultralisk_blessing': 'Occasional Ultralisk', 'occasional_colossus_blessing': 'Occasional Colossus', 'unexpected_evolution': 'Unexpected Evolution', 'another_gorgon_blessing': 'ANOTHER GORGON', 'another_gorgon_mutation': 'ANOTHER GORGON', 'burrowed_zerglings': 'Burrowed Zerglings', 'sniper_thor': 'Sniper Thor', 'horde_mode': 'Horde Mode', 'tower_defense': 'Tower Defense', 'cloaked_nightmare': 'Cloaked Nightmare', 'rapid_repair': 'Rapid Repair', 'blink_blessing': 'Blink', 'boon_viking_anchors': 'Viking Anchors', 'power_overwhelming': 'Power Overwhelming', 'drakken_laser_drill_blessing': 'Drakken Laser Drill', 'jetpacks': 'Jetpacks', 'stealth_tunnels': 'Stealth Tunnels', 'lurker_defense': 'Lurker Defense', 'combat_workers': 'Combat Workers', 'rapid_evolution_mutation': 'Rapid Evolution', 'no_deaths_allowed': 'No Deaths Allowed', 'glass_cannons': 'Glass Cannons', 'victory_is_temporary': 'Victory is Temporary', 'odin': 'Odin', 'nuclear_workers': 'Nuclear Workers', 'bounty_kills': 'Bounty Kills', 'tactical_binoculars': 'Tactical Binoculars', 'building_overcharge': 'Building Turrets', 'ghost_reporting': 'Ghost Reporting', 'taldarim_reinforcements': "Tal'darim Reinforcements", 'miras_mercenaries': "Mira's Mercenaries", 'glorious_martyrs': 'Glorious Martyrs', 'inflatable_soldiers': 'Inflatable Soldiers', 'double_time': 'Double Time', 'shrinkage': 'Shrinkage', 'mineral_thieves': 'Mineral Thieves', 'active_enemies': 'Active enemies', 'infinite_larva': 'Infinite Larva', 'zagaras_banelings': "Zagara's Banelings", 'reflective_armor': 'Reflective Armor', 'buddy_system': 'Buddy System', 'torrasque': 'Torrasque', 'nexus_shield': 'Nexus Shield', 'gargantuan_enemies': 'Gargantuan Enemies', 'boon_deadly_weapons': 'Deadly Weapons', 'boon_auto_repair': 'Auto-repair', 'boon_rapid_fire': 'Rapid-Fire', 'boon_shields_for_all': 'Shields for all', 'boon_heavy_armor': 'Heavy Armor', 'boon_unlimited_blink': 'Unlimited Blink', 'boon_interplanetary_fortress': 'Interplanetary Fortress', 'boon_roach_infestation': 'Roach Infestation', 'boon_chain_reaction': 'Chain Reaction', 'boon_aiur_recruitment': 'For Aiur!', 'boon_toxic_observation': 'Toxic Gaze', 'boon_cloning_technology': 'Cloning Technology', 'raynors_raiders': "Raynor's Raiders", 'boon_defender': 'Defender', 'boon_fire_power': 'Fire Power', 'boon_roachling_mines': 'Roachling Mines', 'boon_broodling_evolution': 'Broodling evolution', 'boon_adamantium_blades': 'Adamantium Blades', 'boon_enhanced_control': 'Enhanced Control', 'boon_banshee_swarm': 'Banshee Swarm', 'boon_enlarged_banelings': 'Enlarged Banelings', 'boon_corrosive_claws': 'Corrosive Claws', 'boon_unlimited_power': 'Unlimited Power', 'boon_unstable_colossi': 'Unstable Colossi', 'boon_archon_cannons': 'Archon Cannons', 'boon_hyrda_storms': 'Hyrda Storms', 'boon_mobile_siege': 'Mobile Siege', 'boon_maddening_shades': 'Maddening Shades', 'boon_concussed_shells': 'Concussed Shells', 'purifier': 'Purifier', 'spear_of_adun_blessing': 'Spear of Adun', 'spear_of_adun_overcharge': 'Spear of Adun Overcharge', 'dehakas_pack': "Dehaka's Pack", 'zombie_apocalypse': 'Zombie Apocalypse', 'arguments': 'Arguments', 'combat_pay': 'Combat Pay', 'nuclear_structures': 'Nuclear Structures', 'resource_swap': 'Resource Swap', 'rich_vespene': 'Rich Vespene', 'rich_minerals': 'Rich Minerals', 'boon_missile_defense': 'Missile Defense System', 'boon_stretchy_spines': 'Stretchy Spines', 'boon_gargantuan_units': 'Gargantuan Units', 'boon_chaos_blessings': 'Chaos Blessings', 'resource_pickups': 'Resource Pickups', 'marauder_kill_teams': 'Marauder Kill Teams', 'dark_archons_x5': 'Archons x5', 'siege_mode_x5': 'Siege Mode x5'}







EFFECT_DESCRIPTIONS: dict[str, str] = {'golden_armada': 'The Golden Armada patrols the map', 'low_quality_minerals': 'Mineral resource patches have fewer minerals', 'conga_line': 'Zerglings, marines, and/or zealots constantly spawn from 3 randomly-selected enemy buildings and attack your base', 'ten_minutes_until_destruction': 'After 10 minutes all enemies will attack your base', 'siege_mode': 'The enemy has sieged tanks scattered around the map', 'drakken_laser_drill_enemy': 'The enemy has a Drakken Laser Drill', 'dark_archons': 'Archons patrol the map', 'drop_pods': 'Drop pods filled with terran infantry randomly drop around the map', 'dark_templar': 'Dark Templar attack your base', 'fragile_workers': 'Your workers have 1 hit point', 'decay': 'Each of your units gain one stack of decay every minute. For each stack of decay, a unit takes 1 damage every 10 seconds.', 'zombies_mutation': 'Whenever any unit dies, they spawn a hostile infested terran', 'limited_bank': 'You cannot store more than 1700 total resources at a time', 'leviathan_in_orbit': 'Many zerg drop pods constantly rain down', 'heroes_of_the_storm': 'Enemy heroes wander the map (Warning: some may be cloaked)', 'too_many_wraiths': 'Independent enemy wraiths attack from all sides', 'void_thrashers': 'Void Thrashers spawn to siege your base', 'not_enough_energy': 'Your units and structures all lose 1 energy every 3 seconds', 'viking_raids': 'Vikings periodically try to land in your mineral lines', 'nuclear_annihilation': 'Every 30 seconds, a nuke can land ANYWHERE', 'darkness': 'Reduce the the vision range of all of your units by 3', 'adrenaline': 'Enemies move and attack 30% faster', 'picky_eaters': 'Supply structures and bases provide far less supply', 'arms_race': 'Enemy damage is increased by 10% every 2 minutes', 'rising_gas_prices': 'Units cost 50% more vespene gas', 'squishy': 'Your units have all 0 armor, even with upgrades', 'forced_variety': 'Building a unit increases its cost for the rest of the mission', 'occasional_thor_mutation': 'Some enemy units are actually Thors', 'occasional_ultralisk_mutation': 'Some enemy units are actually Ultralisks', 'occasional_colossus_mutation': 'Some enemy units are actually Colossi', 'enemy_regeneration': 'Enemy units and structures all recover 5 life and shield per second', 'investors': 'You start with 1000 additional minerals', 'multi_class': 'You start with an additional scv, drone, and probe', 'speedy': 'Your units move at 2x speed', 'general': 'you gain (hero). They respawn 60 seconds after dying.', 'farseers': 'You gain full map vision', 'air_support': 'Allied aircraft attack the enemies, but you cannot control them', 'fire_squad': 'Start with a squad of fiery units', 'fuel_pipeline': 'Gain 3 vespene gas every second', 'rapid_evolution': 'Your units gain 1 maximum HP every 5 seconds', 'zombies_blessing': 'Whenever any unit dies, they spawn an allied infested terran', 'compounding_interest': 'Increase your mineral supply by 10% every 30 seconds.', 'transports': 'Start with durable transports', 'lost_vikings': 'Every 60 seconds, gain a viking in a random location', 'warfields_reinforcements': 'Warfield sends many allied drop pods to aid you in random locations', 'energy_overload': 'Your units produce energy 3x faster', 'explosive_armor': 'Your units explode on death, dealing damage to enemies proportional to their supply cost', 'instant_workers': 'Your workers build instantly', 'juggernaut': 'Your units gain armor equal to their supply cost but move 15% slower', 'assembly_line': 'Produce every thing 2x faster', 'elite_soldiers': 'Your units and structures have a 15% increase to all of their stats', 'blinding_light': 'Reduce the vision range of enemies by 4', 'specialists': 'Start with a wide variety of spellcasters', 'fortifications': 'Your buildings all have +5 armor', 'baneling_stream': 'Your main bases all spawn banelings that automatically attack the enemy base', 'tychus': 'You can technically control tychus, but he is automatically issued an attack move order towards the enemy every 10-25 seconds.', 'zagaras_aid': 'Every 10 minutes Zagara sends 100 banelings to aid you.', 'logistics': 'Your maximum supply is 400', 'occasional_thor_blessing': 'Whenever you train a unit, you have a 4% chance of training a Thor instead', 'occasional_ultralisk_blessing': 'Whenever you train a unit, you have a 4% chance of training an Ultralisk instead', 'occasional_colossus_blessing': 'Whenever you train a unit, you have a 4% chance of training a Colossus instead', 'unexpected_evolution': 'When you train a unit, there is a chance to actually train a more expensive unit.', 'another_gorgon_blessing': 'Warfield is sending gorgon after gorgon to assist you, but they are quite fragile', 'another_gorgon_mutation': 'The enemy sends many gorgons at you, but they are quite fragile', 'burrowed_zerglings': 'There are 150 burrowed zerglings scattered throughout the map', 'sniper_thor': 'A thor with enhanced health, range, and damage is somewhere on the map', 'horde_mode': 'Your units cost half as much, build twice as fast, and have 25% fewer hit points', 'tower_defense': 'Hostile probes continually build photon cannons, shield batteries, and pylons around the map', 'cloaked_nightmare': 'All enemies are cloaked', 'rapid_repair': 'Your SCVs repair 5x as fast', 'blink_blessing': 'All of your units have the blink ability', 'power_overwhelming': 'Your workers can merge into archons', 'drakken_laser_drill_blessing': 'Workers can construct a Drakken Laser Drill for 800 minerals and gas', 'jetpacks': 'All enemy marines, zealots, and zerglings can fly and sometimes attack your base', 'stealth_tunnels': 'All of your units can move while burrowed', 'lurker_defense': 'You start with 4 lurkers and 4 impalers to protect your base, but they move slowly', 'combat_workers': 'Your workers have triple health, damage, speed, and attack speed', 'rapid_evolution_mutation': 'Enemy units gain 1 maximum HP every 5 seconds', 'no_deaths_allowed': 'Whenever one of your units die, spawn an enemy ultralisk with timed life in its place', 'glass_cannons': 'Your units deal double damage but have 35% less health', 'victory_is_temporary': 'Enemy units have a 50% chance of respawning 1 minute after they die', 'odin': 'You start with the odin', 'nuclear_workers': 'Your workers set off a nuclear explosion when they die', 'bounty_kills': 'You gain 4 minerals and 2 gas every time you kill an enemy unit', 'tactical_binoculars': 'Enemies have double range', 'building_overcharge': 'All of your buildings shoot lasers', 'ghost_reporting': 'You start with 3 ghosts and a ghost academy with unlimited nukes', 'taldarim_reinforcements': "Absurdly Deadly Tal'darim armies repeatedly attack after the 20 minute mark", 'miras_mercenaries': 'Mira Han has mercenaries on the map on the enemy team. If you have 6000 minerals you purchase them for yourself', 'glorious_martyrs': 'whenever one of your units die, all nearby units gain a permanent speed and attack speed bonus', 'inflatable_soldiers': 'Your non-worker units continually grow in all ways but become become slower over time', 'double_time': 'All units move and attack twice as fast.', 'shrinkage': 'Your units continually shrink over time', 'mineral_thieves': 'The enemy repeatedly calls down MULEs to steal your mineral fields', 'active_enemies': 'Enemies move around independently a lot more', 'infinite_larva': 'Your bases produce nearly unlimited larva', 'zagaras_banelings': 'Every 10 minutes, zagara sends 100 banelings towards your base', 'reflective_armor': 'Your units reflect 50% of incoming damage back to attackers', 'buddy_system': 'Your units rapidly take damage when not near an ally', 'torrasque': 'The Torrasque attacks your base. Every time you kill him he gets stronger', 'nexus_shield': 'The enemy has a special nexus somewhere. All enemy units have 300 shields until it is destroyed.', 'gargantuan_enemies': 'Enemy units are gargantuan and have 50% more health, damage, size, and range', 'raynors_raiders': "The Hyperion regularly flies by your base along with many of Raynor's reinforcements", 'boon_defender': 'Your defensive structures gain 50% range and damage', 'boon_fire_power': 'Every time your fiery units kill an enemy, increase the attack speed of all fiery units by 2% until the end of the level.', 'boon_roachling_mines': 'Your spider mines spawn 5 roachlings when they are destroyed', 'boon_broodling_evolution': 'your broodlings continually evolve and become permanent every time they get kills', 'boon_adamantium_blades': "All of your units' melee attacks deal double damage", 'boon_enhanced_control': 'When you mind-control a unit, triple its health and attack speed', 'boon_banshee_swarm': 'Whenever you train a banshee, train 6 mini banshees instead', 'boon_enlarged_banelings': 'Your banelings have triple the explosion radius', 'boon_unlimited_power': 'Halve all cooldowns and energy requirements for all abilities', 'boon_unstable_colossi': 'Your colossi attack faster the lower their hp is', 'boon_archon_cannons': 'Your Photon Cannons and Dragoons shoot mini-archons with timed life', 'boon_hyrda_storms': 'Your hydralisk attack projectiles cause psionic storms when they land', 'boon_mobile_siege': 'Siege tanks can still move while sieged', 'boon_maddening_shades': 'When an adept shade successfully completes, spawn a random temporary unit at the destination', 'boon_concussed_shells': 'Marauder missiles move 99% slower but deal 10x damage.', 'purifier': 'The purifier with a golden armada escort slowly approaches your base', 'spear_of_adun_blessing': 'You have access to Spear of Adun abilities', 'spear_of_adun_overcharge': 'The spear of adun recharges energy and abilities twice as fast', 'dehakas_pack': 'Dehaka and swarms of primal zerg constantly attack your base', 'zombie_apocalypse': 'Every unit that dies spawns multiple infested terran that attack your base', 'arguments': 'Your units occasionally get in arguments and fight each other', 'combat_pay': 'You lose 4 minerals every time you kill an enemy unit', 'nuclear_structures': 'Enemy structures detonate in a nuclear explosion on death', 'resource_swap': 'When you obtain vespene gas, obtain minerals instead. when you obtain minerals, obtain vespene gas instead.', 'rich_vespene': 'All vespene geysers are replaced with rich vespene geysers', 'rich_minerals': 'All mineral fields are replaced with rich mineral fields', 'boon_missile_defense': 'Your missile turrets gain +50% damage, range, hp, and attack speed', 'boon_stretchy_spines': 'When a spine crawler kills a unit, permanently increase its range by 10%', 'boon_gargantuan_units': 'When you train a unit, it gains 50% health, damage, size, and range', 'boon_chaos_blessings': 'Randomly gain more blessings each mission', 'resource_pickups': 'mineral and gas resource pickups scattered around the map', 'marauder_kill_teams': 'After 5 minutes, 2 Marauder Kill Teams begin patrolling the map', 'dark_archons_x5': '50 enemy Archons are scattered around the map', 'siege_mode_x5': '50 enemy Siege Tanks are scattered around the map'}





_NEW_BOON_BANK_F: dict[str, int] = {

    "boon_energized_queens": 1,

    "boon_goliaths_online": 2,

    "boon_regenerative_aberrations": 4,

    "boon_infantry_reinforcements": 8,

    "boon_acidic_landing_markers": 16,

    "boon_permanent_stimpack": 32,

    "boon_recycled_armor": 64,

    "boon_invasion_fleet": 128,

    "boon_dead_man_switch": 256,

    "boon_reflective_carapace": 512,

    "boon_cell_division": 1024,

    "boon_spine_rifling": 2048,

    "boon_guided_shells": 4096,

    "boon_zergling_infestation": 8192,

    "boon_hyperion": 16384,

    "boon_leviathan": 32768,

    "boon_true_scouts": 65536,

    "boon_true_carriers": 131072,

    "boon_deadly_vultures": 262144,

    "boon_immortal_immortals": 524288,

    "boon_kill_streak": 1048576,

    "boon_hit_and_run": 2097152,

    "boon_meat_grinder": 4194304,

    "boon_reaper_blitz": 8388608,

    "boon_purifier_alliance": 16777216,

    "resource_pickups": 33554432,

    "marauder_kill_teams": 67108864,

    "dark_archons_x5": 134217728,

    "siege_mode_x5": 268435456,
    "boon_single_use_tools": 536870912,

}

EFFECT_BANK_BITS.update({effect: (5, bit) for effect, bit in _NEW_BOON_BANK_F.items()})

# Nydus Worms occupies unused bank-E bit 1; no new protocol or dependency.
EFFECT_BANK_BITS["nydus_worms"] = (4, 1)
EFFECT_DISPLAY_NAMES["nydus_worms"] = "Nydus Worms"
EFFECT_DESCRIPTIONS["nydus_worms"] = "Nydus worms periodically spawn to send units towards your base"

# Dev41: unused E-bank bits for three new mutations and Covert Assistance.
_DEV41_EFFECTS = {
    "point_defense_drones": ((4, 16777216), "Point Defense Drones", "Enemy structures each have a point defense drone deployed near them to stop your projectiles"),
    "heavily_defended_drakken_laser_drill": ((4, 33554432), "Heavily-Defended Drakken Laser Drill", "The enemy has a Heavily-Defended Drakken Laser Drill"),
    "multiple_air_bogies": ((4, 67108864), "Multiple Air Bogies", "Zerg air units occasionally attack your base"),
    "covert_assistance": ((4, 134217728), "Covert Assistance", "Tosh works independently to assist you. He does not respawn."),
}
for _effect_key, (_bank_bit, _title, _description) in _DEV41_EFFECTS.items():
    EFFECT_BANK_BITS[_effect_key] = _bank_bit
    EFFECT_DISPLAY_NAMES[_effect_key] = _title
    EFFECT_DESCRIPTIONS[_effect_key] = _description

# Dev42: mutation death event, using a free E-bank bit.
EFFECT_BANK_BITS["hybrid_research"] = (4, 268435456)
EFFECT_DISPLAY_NAMES["hybrid_research"] = "Hybrid Research"
EFFECT_DESCRIPTIONS["hybrid_research"] = "Each enemy structure releases a random hybrid when destroyed"

# Dev43: same hostile roaming patrol logic as Archons, 30 units.
EFFECT_BANK_BITS["fifty_immortals"] = (4, 536870912)
EFFECT_BANK_BITS["armored_enemies"] = (4, 1073741824)
EFFECT_DISPLAY_NAMES["armored_enemies"] = "Armored Enemies"
EFFECT_DESCRIPTIONS["armored_enemies"] = "All enemies gain +5 armor"
EFFECT_DISPLAY_NAMES["fifty_immortals"] = "Immortals"
EFFECT_DESCRIPTIONS["fifty_immortals"] = "There are 30 immortals patrolling around the map"

# v1.0.2.17 mutations are transported in mission_flags because banks A-F are full.
_V1024_MUTATIONS: dict[str, tuple[str, str, int]] = {'hellion_run_by': ('Hellion Run-by', 'Hellions try to run into your mineral lines', 2), 'diamondback_wanderers': ('Diamondbacks', '50 diamondbacks wander all over the place', 3), 'leviathan_outside_base': ('Leviathan Approaching', 'The Leviathan floats outside your base spawning mutalisks and brood lords', 5), 'odin_delayed_assault': ('Odin', 'The enemy base has an odin in it. After 13 minutes it attacks your base.', 3), 'combined_raids': ('Ultimate Harassment', 'The enemy sends many wraiths, vikings, and hellions bother you', 5), 'brakk_primal_army': ("Brakk's Pack", 'Brakk and a massive primal army awaits on the map. It attacks after 10 minutes.', 5), 'orlan_fortress': ("Orlan's Planetary Fortress", 'Colonel Orlan has a well-defended Planetary Fortress on the map that gains 1 range every 30 seconds.', 4), 'enemy_spear_of_adun': ('Enemy Spear of Adun', "The enemy has the Spear of Adun. Let's see how YOU like it", 7), 'true_golden_armada': ('True Golden Armada', 'A massive golden armada patrols the map', 6), 'immortal_zergling': ('Immortal Zergling', 'A single immortal zergling attacks you constantly', 1), 'tosh_and_his_boys': ('Tosh and his Boys', 'Tosh is somewhere on the map. While he lives, cloaked spectres periodically try to nuke your base.', 3)}
EFFECT_BANK_BITS.update({effect_id: (5, 0) for effect_id in _V1024_MUTATIONS})
EFFECT_DISPLAY_NAMES.update({effect_id: values[0] for effect_id, values in _V1024_MUTATIONS.items()})
EFFECT_DESCRIPTIONS.update({effect_id: values[1] for effect_id, values in _V1024_MUTATIONS.items()})



# New v1.2.1 boons use their own trailing launch mask, not occupied A-F bits.
_NEW_DEV5_BOON_KEYS: dict[str, int] = {
    "boon_eternal_perdition": 1,
    "boon_speedy_buildings": 2,
    "boon_enhanced_allies": 4,
    "boon_explosive_predators": 8,
    "boon_harvesting_equipment": 16,
    "boon_refective_diamondbacks": 32,
    "boon_psionic_guardians": 64,
    "boon_improved_morphs": 128,
    "boon_psionic_lords": 256,
    "boon_unlimited_scarabs": 512,
    "boon_armor_disintegration": 1024,
}
EFFECT_BANK_BITS.update({name: (6, bit) for name, bit in _NEW_DEV5_BOON_KEYS.items()})


_NEW_BOON_TITLES: dict[str, str] = {

    "energized_queens": "Energized Queens",

    "goliaths_online": "Goliaths Online",

    "regenerative_aberrations": "Regenerative Abberations",

    "infantry_reinforcements": "Infantry Reinforcements",

    "acidic_landing_markers": "Acidic Landing Markers",

    "permanent_stimpack": "Permanent Stimpack",

    "recycled_armor": "Recycled Armor Suits",

    "invasion_fleet": "Invasion Fleet",

    "dead_man_switch": "Dead Man Switch",

    "reflective_carapace": "Reflective Carapace",

    "cell_division": "Cell Division (Ultralisk)",

    "spine_rifling": "Spine Rifling",

    "guided_shells": "Guided Shells",

    "zergling_infestation": "Zergling Infestation",

    "hyperion": "Hyperion",

    "leviathan": "Leviathan",

    "true_scouts": "True Scouts",

    "true_carriers": "True Carriers",

    "deadly_vultures": "Deadly Vultures",

    "immortal_immortals": "Immortal immortals",

    "kill_streak": "Kill Streak",

    "hit_and_run": "Hit and Run!",

    "meat_grinder": "Meat Grinder",

    "reaper_blitz": "Reaper Blitz",

    "purifier_alliance": "Purifier Alliance",
    "single_use_tools": "Single-Use Tools",
    "eternal_perdition": "Eternal Perdition",
    "speedy_buildings": "Speedy Buildings",
    "enhanced_allies": "Enhanced Allies",
    "explosive_predators": "Explosive Predators",
    "harvesting_equipment": "Harvesting Equipment",
    "refective_diamondbacks": "Refective Diamondbacks",
    "psionic_guardians": "Psionic Guardians",
    "improved_morphs": "Improved morphs",
    "psionic_lords": "Psionic Lords",
    "unlimited_scarabs": "Unlimited Scarabs",
    "armor_disintegration": "Armor Disintegration",

}

_NEW_BOON_EFFECT_BY_KIND: dict[str, str] = {kind: "boon_" + kind for kind in _NEW_BOON_TITLES}

for _kind, _title in _NEW_BOON_TITLES.items():

    EFFECT_DISPLAY_NAMES[_NEW_BOON_EFFECT_BY_KIND[_kind]] = _title







def _load_boon_catalog_rows() -> dict[str, dict[str, str]]:

    try:

        with (Path(__file__).resolve().parent / "BOON_CATALOG.csv").open(encoding="utf-8-sig", newline="") as handle:

            return {str(row.get("Boon Title", "")).strip(): row for row in csv.DictReader(handle) if str(row.get("Boon Title", "")).strip()}

    except Exception:

        return {}



_BOON_CATALOG_ROWS = _load_boon_catalog_rows()

for _kind, _title in _NEW_BOON_TITLES.items():

    _row = _BOON_CATALOG_ROWS.get(_title, {})

    EFFECT_DESCRIPTIONS[_NEW_BOON_EFFECT_BY_KIND[_kind]] = str(_row.get("Description", "")).strip()





for _effect_id, _csv_title in {

    "boon_aiur_recruitment": "For Aiur!",

    "boon_roachling_mines": "Roachling Mines",

    "boon_toxic_observation": "Toxic Gaze",

}.items():

    _row = _BOON_CATALOG_ROWS.get(_csv_title, {})

    _description = str(_row.get("Description", "")).strip()

    if _description:

        EFFECT_DESCRIPTIONS[_effect_id] = _description



REPEATABLE_BOON_KINDS = {"auto_repair", "deadly_weapons"}



DEFAULT_STATE: dict[str, Any] = {

    "chosen": [],
    "crew_roster": None,

    "purchases": {},

    # Display-only inventory safety net for transient AP reconnect states.
    "inventory_received_snapshot": [],

    "spent": 0,





    "test_credit_bonus": 0,

    "shop_cycle": -1,

    "shop_stock": [],
    "shop_frozen_item": "",
    "potion_inventory": [],
    "potion_serial": 0,
    "shop_potions_bought": [],

    "shop_stock_logic_version": 0,

    "shop_sale_items": [],

    "shop_visit_nonce": 0,

    "shop_cycle_purchases": {},

    "shop_cycle_purchase_victory_count": -1,

    "shop_rerolls_this_cycle": 0,

    "shop_reroll_purchase_victory_count": -1,

    "boon_purchases": {},

    "permanent_blessings": [],

    "permanent_boons": [],

    "permanent_mutations": [],

    "shop_expansion": 0,
    "single_use_tools_last_victory": -1,

    "shop_reroll_nonce": 0,

    "risky_investment_charges": 0,

    "golden_goose_bonus_per_mission": 0,

    "golden_goose_credit_offset": 0,

    "saving_grace_charges": 0,
    "saving_grace_pending": [],

    "temporary_blessings": {},

    "node_effect_overrides": {},

    "test_mission_overrides": {},

    "duplicate_replacements": {},

    "duplicate_announced": [],

    "test_effects_next": [],

    "test_clear_next": False,

    "auto_victory_next": False,

    "godmode_next": False,

    "godmode_mission_id": -1,







    "route_layout_x_fractions": {},

}



# Potion inventory and eligibility are independent of the Archipelago item pool.
# IDs are a stable wire format shared with APRogue.galaxy: do not reorder.
POTION_PREFIX = "slay_potion::"
POTION_DEFINITIONS = (
    ("Mineral Reserves", 1, 'Gain 1500 minerals', "instant"),
    ("Gas Reserves", 1, 'Gain 1500 vespene gas', "instant"),
    ("Odin in a Bottle", 2, 'Spawn the Odin, but you cannot control it', "point"),
    ("Leviathan in a Bottle", 3, 'Spawn the WoL leviathan, but you cannot control it', "point"),
    ("Hyperion in a Bottle", 4, 'Spawn the WoL hyperion, but you cannot control it', "point"),
    ("Drop Pod Wave", 2, 'Call down 10 terran drop pods on target area.', "point"),
    ("Mass EMP", 1, 'Reduce all shields and energy of all units to 0 and remove all cloaked for 60 seconds', "instant"),
    ("Tactical Nuke", 1, 'Immediately detonate a single tactical nuke at target location', "point"),
    ("Tosh's Miners", 1, 'Drop down a flying command center with 5 scvs at target location', "point"),
    ("Stealth Protocol", 2, 'All of your units and structures become stealthed for 1 minute', "instant"),
    ("Mass Stimpack", 2, 'All of your units gain 50% movement and attack speed for 1 minute, but they all lose 1 hp per second during this time.', "instant"),
    ("Spear of Adun Recharge", 1, "Set the Spear of Adun's energy to maximum.", "instant"),
    ("Second Kerrigan", 2, 'Spawn a second kerrigan that does not respawn on death', "instant"),
    ("Mercenary Favor", 2, 'Instantly call down all units unlocked in the predator nest and merc compound for free regardless of cooldown and charges', "instant"),
    ("Guardian Matrix", 1, 'Target unit gains 2000 shields until the shields are completely depleted', "friendly"),
    ("Corruption Spores", 1, 'Target unit or structure takes double damage until death', "unit"),
    ("Mass Marines", 1, 'Instantly lose up to 5000 minerals. For every 10 minerals lost, spawn a marine at your base that automatically attacks the enemy.', "instant"),
    ("Mass Spellcasters", 1, 'Instantly lose up to 5000 gas. For every 20 gas spent, spawn a random spellcaster at your base. The spellcasters automatically attack the enemy and use their abilities.', "instant"),
    ("Spawn [amount] [unit]", 1, 'Spawn [amount] [unit] at target location that automatically attacks the enemy.', "point"),
)
POTION_CATALOG = {
    POTION_PREFIX + str(index): dict(index=index, name=name, severity=severity,
        rarity=severity,  # Older inventory/tests still use the rarity alias.
        price=severity * 125, description=description, target=target)
    for index, (name, severity, description, target) in enumerate(POTION_DEFINITIONS, 1)
}
# These are native campaign combat units with conventional unmodified build costs.
# Fix the roll when a shop is generated, not when a potion is consumed.
# (display singular, display plural, native SC2 catalog ID, mineral cost, gas cost)
POTION_RANDOM_UNITS = (
    ("Marine", "Marines", "Marine", 50, 0),
    ("Marauder", "Marauders", "Marauder", 100, 25),
    ("Reaper", "Reapers", "Reaper", 50, 50),
    ("Hellion", "Hellions", "Hellion", 100, 0),
    ("Siege Tank", "Siege Tanks", "SiegeTank", 150, 125),
    ("Viking", "Vikings", "VikingFighter", 150, 75),
    ("Banshee", "Banshees", "Banshee", 150, 100),
    ("Thor", "Thors", "Thor", 300, 200),
    ("Roach", "Roaches", "Roach", 75, 25),
    ("Hydralisk", "Hydralisks", "Hydralisk", 100, 50),
    ("Mutalisk", "Mutalisks", "Mutalisk", 100, 100),
    ("Ultralisk", "Ultralisks", "Ultralisk", 300, 200),
    ("Zealot", "Zealots", "Zealot", 100, 0),
    ("Stalker", "Stalkers", "Stalker", 125, 50),
    ("Immortal", "Immortals", "Immortal", 275, 100),
    ("Void Ray", "Void Rays", "VoidRay", 250, 150),
    ("Colossus", "Colossi", "Colossus", 300, 200),
    ("High Templar", "High Templar", "HighTemplar", 50, 150),
)
POTION_VARIANT_PREFIX = POTION_PREFIX + "19::"
# Store each random roll as an immutable variant ID. Type 1901..1918 is the
# serialized Galaxy wire value, while the canonical type 19 remains a shop roll.
POTION_CATALOG.update({
    POTION_VARIANT_PREFIX + str(i): dict(
        index=1900+i, name=f"Spawn {2000 // (mineral + gas)} {plural}",
        severity=1, rarity=1, price=125,
        description=f"Spawn {2000 // (mineral + gas)} {plural} at target location that automatically attacks the enemy.",
        target="point", unit=unit_type, amount=2000 // (mineral + gas))
    for i, (_singular, plural, unit_type, mineral, gas) in enumerate(POTION_RANDOM_UNITS, 1)
})
POTION_CAPACITY = 2


POTION_MERC_NAMES = (
    "War Pigs", "Devil Dogs", "Hammer Securities", "Spartan Company",
    "Siege Breakers", "Hel's Angels", "Dusk Wings", "Jackson's Revenge",
    "Skibi's Angels", "Death Heads", "Winged Nightmares", "Midnight Riders",
    "Brynhilds", "Jotun", "Devouring Ones", "Hunter Killers",
    "Wise Old Torrasque", "Caustic Horrors", "Yggdrasil",
    "Infested Siege Breakers", "Infested Dusk Wings",
)


def potion_mercenary_mask(ctx: Any) -> int:
    return sum(1 << i for i, name in enumerate(POTION_MERC_NAMES)
               if _progression_owned(ctx, name))


def _spear_unlocked_active_ability_count(ctx: Any) -> int:
    """Distinct purchased castable Spear abilities; excludes passive spear upgrades."""
    if not _progression_owned(ctx, SPEAR_UNLOCK):
        return 0
    passive = {"Guardian Shell (Spear of Adun)", "Reconstruction Beam (Spear of Adun)",
               "Overwatch (Spear of Adun)"}
    return sum(1 for item in SPEAR_FALLBACK_ITEMS
               if item not in passive and _purchased_count(ctx, item) > 0)


def _potion_unlock_eligible(ctx: Any, name: str) -> bool:
    info = POTION_CATALOG.get(name)
    if info is None or info["index"] == 14:
        return False  # Mercenary Favor is disabled across all modes.
    if info["index"] == 12:
        return _spear_unlocked_active_ability_count(ctx) >= 2
    if info["index"] == 13:
        return _progression_owned(ctx, KERRIGAN_UNLOCK)
    if info["index"] == 14:
        try:
            return potion_mercenary_mask(ctx).bit_count() >= 3
        except Exception:
            return False
    return True


_POTION_BANK_USE_CACHE: dict[int, tuple[float, set[int]]] = {}


def _potion_bank_uses(ctx: Any) -> set[int]:
    """SC2 BankSave is the authoritative acknowledgement of use. Never write banks from Python.

    Read only our signed-by-game bank XML; the serial key is namespaced by the run
    token, so old runs cannot consume the new run's purchases. Missing banks mean
    no confirmed consumption, NOT an empty/full reset.
    """
    import os
    import time
    import xml.etree.ElementTree as ET
    token = test_potion_run_token(ctx)
    cached = _POTION_BANK_USE_CACHE.get(token)
    now = time.monotonic()
    # The Kivy shop queries inventory for many rows. Avoid repeatedly scanning
    # the StarCraft II Documents directory, while polling recent consumption.
    if cached is not None and now - cached[0] < 0.75:
        return set(cached[1])
    roots = [Path.home() / "Documents" / "StarCraft II"]
    for env in ("USERPROFILE", "OneDrive", "OneDriveConsumer"):
        base = os.environ.get(env, "")
        if base:
            roots.append(Path(base) / "Documents" / "StarCraft II")
    used: set[int] = set()
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        try:
            candidates = root.rglob("SlayTheStarCraftPotions.SC2Bank")
            for bank_path in candidates:
                if bank_path in seen:
                    continue
                seen.add(bank_path)
                try:
                    tree = ET.parse(bank_path)
                    for key in tree.findall(".//Section[@name='PotionUses']/Key"):
                        serial = str(key.attrib.get("name", ""))
                        value = key.find("Value")
                        if serial.startswith("Serial") and value is not None and int(value.attrib.get("int", "0")) == token:
                            used.add(int(serial[6:]))
                except (OSError, ValueError, ET.ParseError):
                    continue
        except OSError:
            pass
    _POTION_BANK_USE_CACHE[token] = (now, set(used))
    return used


def refresh_consumable_slots(ctx: Any) -> list[dict[str, int | str]]:
    """Refresh consumed serials before rendering an initial shop/inventory modal."""
    _POTION_BANK_USE_CACHE.pop(test_potion_run_token(ctx), None)
    return potion_inventory(ctx)


def _single_use_tools_grant(ctx: Any, slots: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
    """Award at most one eligible shop consumable per completed mission.

    Called after bank acknowledgements have removed consumed entries. The durable
    mission-count cursor guarantees reconnects and UI refreshes cannot duplicate
    a reward. Skipped rewards when full never queue up for later collection.
    """
    s = state(ctx)
    if "boon_single_use_tools" not in s.get("permanent_boons", []):
        return slots
    count = victory_count(ctx)
    last = int(s.get("single_use_tools_last_victory", count))
    if last < 0:  # A legacy state that obtained the boon before this feature existed.
        s["single_use_tools_last_victory"] = count
        _persist_state(ctx)
        return slots
    if count <= last:
        return slots
    for completed_index in range(last + 1, count + 1):
        if len(slots) >= POTION_CAPACITY:
            continue
        candidates = [name for name in POTION_CATALOG
                      if not name.startswith(POTION_VARIANT_PREFIX)
                      and _potion_unlock_eligible(ctx, name)]
        if not candidates:
            continue
        digest = hashlib.sha256(f"{ctx.slay_config.get('run_seed', 0)}:single-use-tools:{completed_index}".encode()).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        chosen = rng.choice(candidates)
        if chosen == POTION_PREFIX + "19":
            chosen = POTION_VARIANT_PREFIX + str(rng.randint(1, len(POTION_RANDOM_UNITS)))
        serial = max(int(s.get("potion_serial", 0)),
                     *(int(x.get("serial", 0)) for x in s.get("potion_inventory", []) if isinstance(x, dict)), 0) + 1
        s["potion_serial"] = serial
        slots.append({"id": chosen, "serial": serial})
    s["potion_inventory"] = slots
    s["single_use_tools_last_victory"] = count
    _persist_state(ctx)
    return slots


def potion_inventory(ctx: Any) -> list[dict[str, int | str]]:
    if not enabled(ctx) or not state_ready(ctx):
        return []
    saved = state(ctx).get("potion_inventory", [])
    consumed = _potion_bank_uses(ctx)
    slots = [dict(row) for row in saved if isinstance(row, dict)
            and str(row.get("id", "")) in POTION_CATALOG
            and str(row.get("id", "")) != POTION_PREFIX + "14"  # disabled Mercenary Favor
            and int(row.get("serial", 0)) > 0 and int(row.get("serial", 0)) not in consumed][:POTION_CAPACITY]
    if "boon_single_use_tools" not in state(ctx).get("permanent_boons", []):
        return slots
    return _single_use_tools_grant(ctx, slots)


def potion_handshake_slots(ctx: Any) -> tuple[int, int, int, int]:
    slots = potion_inventory(ctx)
    values: list[int] = []
    for i in range(POTION_CAPACITY):
        row = slots[i] if i < len(slots) else {}
        values.extend((int(POTION_CATALOG.get(str(row.get("id", "")), {}).get("index", 0)), int(row.get("serial", 0))))
    return tuple(values)  # type: ignore[return-value]

SHOP_CATEGORY_ORDER = (

    "Terran Units", "Terran Upgrades",

    "Zerg Units", "Zerg Upgrades",

    "Protoss Units", "Protoss Upgrades",

    "Defensive Structures & Detectors", "General Upgrades",

    "Mercenary Contracts", "Mercenaries", "Kerrigan", "Spear of Adun", "Boons", "Consumables",

)

SHOP_ITEMS_PER_CATEGORY = 2

SHOP_STOCK_LOGIC_VERSION = 114
SHOP_EXPANSION_MAX = 3

SHOP_SALE_COUNT = 4

NOVA_CAMPAIGN_ITEM_SUFFIXES = (

    "(Nova Equipment)", "(Nova Ability)", "(Nova Suit Module)",

    "(Nova Weapon)", "(Nova Gadget)",

)











ROYAL_GUARD_UNIT_ITEMS = {

    "Pride of Augustgrad", "Sky Fury", "Shock Division", "Blackhammer",

    "Aegis Guard", "Emperor's Shadow", "Son of Korhal", "Bulwark Company",

    "Field Response Theta", "Emperor's Guardian", "Night Hawk", "Night Wolf",

}



def _is_nova_campaign_item(item_name: str, data: Any | None = None) -> bool:

    clean = str(item_name).strip()

    type_name = ""

    if data is not None:

        type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    normalized_type = type_name.replace("_", " ").strip().casefold()

    return any(clean.endswith(suffix) for suffix in NOVA_CAMPAIGN_ITEM_SUFFIXES) or normalized_type.startswith("nova ")





def _is_deprecated_item(item_name: str, data: Any | None = None) -> bool:

















    clean = str(item_name).replace("_", " ").strip().casefold()

    type_name = ""

    if data is not None:

        type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    normalized_type = type_name.replace("_", " ").strip().casefold()

    return "deprecated" in clean or "deprecated" in normalized_type

DETECTOR_ITEMS = {"Missile Turret", "Raven", "Science Vessel", "Spore Crawler", "Overseer", "Photon Cannon", "Observer"}

BLESSING_SEVERITY = {'investors': 1, 'multi_class': 1, 'speedy': 3, 'general': 2, 'farseers': 1, 'air_support': 2, 'fire_squad': 1, 'fuel_pipeline': 2, 'rapid_evolution': 2, 'zombies_blessing': 4, 'compounding_interest': 2, 'transports': 1, 'lost_vikings': 1, 'warfields_reinforcements': 4, 'energy_overload': 1, 'explosive_armor': 3, 'instant_workers': 2, 'juggernaut': 1, 'assembly_line': 2, 'elite_soldiers': 2, 'blinding_light': 2, 'specialists': 1, 'fortifications': 1, 'baneling_stream': 4, 'tychus': 1, 'zagaras_aid': 2, 'logistics': 1, 'occasional_thor_blessing': 1, 'occasional_ultralisk_blessing': 1, 'occasional_colossus_blessing': 1, 'horde_mode': 3, 'unexpected_evolution': 2, 'another_gorgon_blessing': 2, 'rapid_repair': 1, 'blink_blessing': 2, 'power_overwhelming': 2, 'drakken_laser_drill_blessing': 4, 'lurker_defense': 1, 'combat_workers': 2, 'glass_cannons': 2, 'odin': 4, 'bounty_kills': 1, 'building_overcharge': 3, 'ghost_reporting': 1, 'glorious_martyrs': 4, 'infinite_larva': 2, 'reflective_armor': 2, 'rich_minerals': 1, 'resource_pickups': 1}

BOON_PREFIX = "BOON::"















SWARM_DEPENDENCY_MUTATIONS = {"dehakas_pack", "another_gorgon_mutation", "brakk_primal_army"}

SWARM_DEPENDENCY_BLESSINGS = {"another_gorgon_blessing", "lurker_defense", "specialists", "fire_squad"}

VOID_DEPENDENCY_MUTATIONS = {"void_thrashers", "taldarim_reinforcements", "heroes_of_the_storm", "enemy_spear_of_adun", "true_golden_armada"}

# Disabled mechanics remain in the catalog for old-run compatibility but are never active or purchasable.
DISABLED_MUTATIONS = {"enemy_spear_of_adun"}

DEPENDENCY_SENSITIVE_MISSIONS = {"safe haven", "haven's fall"}

VOID_NATIVE_CAMPAIGNS = {

    "Legacy of the Void",

    "Whispers of Oblivion (Legacy of the Void: Prologue)",

    "Into the Void (Legacy of the Void: Epilogue)",

}

DEPENDENCY_VARIANT_DIR_NAME = "SlayDependencyVariants"



GOLDEN_GOOSE_MUTATIONS: dict[str, int] = {'golden_armada': 2, 'true_golden_armada': 6, 'low_quality_minerals': 2, 'conga_line': 3, 'ten_minutes_until_destruction': 4, 'siege_mode': 1, 'drakken_laser_drill_enemy': 4, 'dark_archons': 1, 'drop_pods': 3, 'dark_templar': 3, 'fragile_workers': 1, 'decay': 3, 'zombies_mutation': 3, 'limited_bank': 1, 'leviathan_in_orbit': 5, 'heroes_of_the_storm': 3, 'too_many_wraiths': 2, 'void_thrashers': 4, 'not_enough_energy': 1, 'viking_raids': 2, 'nuclear_annihilation': 3, 'darkness': 2, 'adrenaline': 3, 'picky_eaters': 2, 'arms_race': 3, 'rising_gas_prices': 2, 'squishy': 2, 'forced_variety': 2, 'occasional_thor_mutation': 1, 'occasional_ultralisk_mutation': 1, 'occasional_colossus_mutation': 1, 'enemy_regeneration': 3, 'sniper_thor': 1, 'another_gorgon_mutation': 2, 'burrowed_zerglings': 1, 'tower_defense': 2, 'cloaked_nightmare': 5, 'jetpacks': 2, 'tactical_binoculars': 4, 'no_deaths_allowed': 7, 'victory_is_temporary': 5, 'nuclear_workers': 1, 'taldarim_reinforcements': 4, 'miras_mercenaries': 2, 'double_time': 1, 'shrinkage': 3, 'mineral_thieves': 1, 'active_enemies': 2, 'zagaras_banelings': 3, 'buddy_system': 3, 'torrasque': 3, 'nexus_shield': 4, 'gargantuan_enemies': 5, 'raynors_raiders': 6, 'purifier': 4, 'dehakas_pack': 5, 'zombie_apocalypse': 5, 'arguments': 2, 'combat_pay': 2, 'marauder_kill_teams': 2, 'dark_archons_x5': 4, 'siege_mode_x5': 4, 'nuclear_structures': 1, 'hellion_run_by': 2, 'diamondback_wanderers': 3, 'leviathan_outside_base': 5, 'odin_delayed_assault': 3, 'combined_raids': 5, 'brakk_primal_army': 5, 'orlan_fortress': 4, 'enemy_spear_of_adun': 7, 'immortal_zergling': 1, 'tosh_and_his_boys': 3}
GOLDEN_GOOSE_MUTATIONS["nydus_worms"] = 3
GOLDEN_GOOSE_MUTATIONS.update({
    "point_defense_drones": 1,
    "heavily_defended_drakken_laser_drill": 6,
    "multiple_air_bogies": 1,
    "hybrid_research": 4,
    "fifty_immortals": 3,
})
GOLDEN_GOOSE_MUTATIONS["dehakas_pack"] = 6
GOLDEN_GOOSE_MUTATIONS["armored_enemies"] = 3
BLESSING_SEVERITY["covert_assistance"] = 1













def _load_effect_catalog_rows() -> dict[tuple[str, str], dict[str, str]]:

    try:

        with (Path(__file__).resolve().parent / "EFFECT_CATALOG.csv").open(encoding="utf-8-sig", newline="") as handle:

            rows = {}

            for row in csv.DictReader(handle):

                title = str(row.get("Title", "")).strip()

                kind = str(row.get("Mutation or Blessing", "")).strip().casefold()

                if title and kind in {"mutation", "blessing"}:

                    rows[(title, kind)] = row

            return rows

    except Exception:

        return {}



_EFFECT_CATALOG_ROWS = _load_effect_catalog_rows()

_EFFECT_CATALOG_TITLE_ALIASES = {"general": "(hero) Commander", "building_overcharge": "Building Turrets"}

for _effect_id, _kind in [

    *((effect_id, "mutation") for effect_id in GOLDEN_GOOSE_MUTATIONS),

    *((effect_id, "blessing") for effect_id in BLESSING_SEVERITY),

]:

    _title = _EFFECT_CATALOG_TITLE_ALIASES.get(_effect_id, EFFECT_DISPLAY_NAMES.get(_effect_id, ""))

    _row = _EFFECT_CATALOG_ROWS.get((_title, _kind))

    if _row is not None:

        _description = str(_row.get("Description", "")).strip()

        if _description:

            EFFECT_DESCRIPTIONS[_effect_id] = _description



def _archipelago_root() -> Path:



    return Path(__file__).resolve().parents[2]





def _launcher_run_dir() -> Path | None:

    raw = os.environ.get("SLAY_RUN_DIR", "").strip()

    if not raw:

        return None

    try:

        return Path(raw).expanduser().resolve()

    except Exception:

        return None





def _run_file() -> Path:

    launcher_dir = _launcher_run_dir()

    if launcher_dir is not None:

        return launcher_dir / "run.json"

    return _archipelago_root() / RUN_FILE_NAME





def enabled(ctx: Any) -> bool:

    cfg = getattr(ctx, "slay_config", None)

    return isinstance(cfg, Mapping) and bool(cfg.get("enabled", False))





def _normalize_config(raw: Any) -> dict[str, Any]:

    if not isinstance(raw, Mapping):

        return {}

    cfg = copy.deepcopy(dict(raw))

    raw_nodes = cfg.get("nodes", {})

    nodes: dict[str, dict[str, Any]] = {}

    if isinstance(raw_nodes, Mapping):

        for key, value in raw_nodes.items():

            if not isinstance(value, Mapping):

                continue

            node = dict(value)

            try:

                mission_id = int(node.get("mission_id", key))

                layer = int(node.get("layer", 0))

                lane = int(node.get("lane", 0))

            except (TypeError, ValueError):

                continue

            node["mission_id"] = mission_id

            node["layer"] = layer

            node["lane"] = lane

            node["next"] = [int(x) for x in node.get("next", [])]

            node["mutators"] = [str(x) for x in node.get("mutators", []) if str(x) in EFFECT_BANK_BITS]

            node["blessings"] = [str(x) for x in node.get("blessings", []) if str(x) in EFFECT_BANK_BITS]

            node["credit_reward"] = max(0, int(node.get("credit_reward", 0)))

            node["mission_name"] = str(node.get("mission_name", ""))

            nodes[str(mission_id)] = node

    cfg["nodes"] = nodes

    cfg["shop_pool"] = [str(x) for x in cfg.get("shop_pool", [])]

    cfg["starting_shop"] = [str(x) for x in cfg.get("starting_shop", [])]

    cfg["starting_credits"] = max(0, int(cfg.get("starting_credits", 0)))

    def _config_frequency_multiplier(raw: Any) -> float:
        legacy = {"less": 0.5, "normal": 1.0, "more": 1.5}
        if isinstance(raw, str) and raw.strip().casefold() in legacy:
            return legacy[raw.strip().casefold()]
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return 1.0
        return value if math.isfinite(value) and value >= 0.0 else 1.0

    cfg["mutation_frequency"] = _config_frequency_multiplier(cfg.get("mutation_frequency", 1.0))
    cfg["blessing_frequency"] = _config_frequency_multiplier(cfg.get("blessing_frequency", 1.0))
    try:
        cfg["campaign_length"] = max(2, int(cfg.get("campaign_length", int(cfg.get("choice_layers", 11)) + 1)))
    except (TypeError, ValueError):
        cfg["campaign_length"] = max(2, int(cfg.get("choice_layers", 11)) + 1)
    try:
        cfg["extra_shop_slots"] = max(0, min(3, int(cfg.get("extra_shop_slots", 0))))
    except (TypeError, ValueError):
        cfg["extra_shop_slots"] = 0
    cfg["start_with_spear"] = bool(cfg.get("start_with_spear", False))
    cfg["start_with_kerrigan"] = bool(cfg.get("start_with_kerrigan", False))

    try:

        cfg["victory_credit_reward_multiplier"] = max(0.0, float(cfg.get("victory_credit_reward_multiplier", 1.0)))

    except (TypeError, ValueError):

        cfg["victory_credit_reward_multiplier"] = 1.0

    cfg["item_credit_reward"] = max(0, int(cfg.get("item_credit_reward", 60)))

    cfg["game_speed"] = str(cfg.get("game_speed", "default"))

    cfg["run_seed"] = int(cfg.get("run_seed", 0))

    cfg["run_id"] = str(cfg.get("run_id", f"seed_{cfg['run_seed']}"))

    cfg["player_name"] = str(cfg.get("player_name", ""))

    cfg["enabled"] = bool(cfg.get("enabled", False))

    return cfg





def _load_local_config(ctx: Any) -> dict[str, Any]:

    path = _run_file()

    if not path.is_file():

        return {}

    try:

        raw = json.loads(path.read_text(encoding="utf-8"))

    except Exception as exc:

        logger.error("Slay the StarCraft: could not read %s: %s", path, exc)

        return {}

    cfg = _normalize_config(raw)

    if not cfg.get("enabled"):

        return {}



    expected_name = cfg.get("player_name", "").casefold().strip()

    actual_name = str(getattr(ctx, "auth", "") or "").casefold().strip()

    if expected_name and actual_name and expected_name != actual_name:

        logger.warning(

            "Slay the StarCraft run file is for player %r, but connected slot is %r; disabling Slay mode.",

            cfg.get("player_name"), getattr(ctx, "auth", ""),

        )

        return {}







    expected_ids = {int(k) for k in cfg.get("nodes", {})}





    actual_ids = {

        int(mission_id)

        for mission_id in getattr(ctx, "mission_id_to_location_ids", {}).keys()

        if int(mission_id) >= 0

    }

    if expected_ids and actual_ids and expected_ids != actual_ids:

        logger.warning(

            "Slay the StarCraft run file mission set does not match this seed "

            "(%d expected, %d actual). Missing: %s; Extra: %s; disabling Slay mode.",

            len(expected_ids),

            len(actual_ids),

            sorted(expected_ids - actual_ids),

            sorted(actual_ids - expected_ids),

        )

        return {}

    return cfg





def _state_file(ctx: Any) -> Path:

    launcher_dir = _launcher_run_dir()

    if launcher_dir is not None:

        launcher_dir.mkdir(parents=True, exist_ok=True)

        return launcher_dir / "slay_state.json"

    cfg = getattr(ctx, "slay_config", {})

    run_id = str(cfg.get("run_id", f"seed_{cfg.get('run_seed', 0)}"))

    safe = "".join(ch for ch in run_id if ch.isalnum() or ch in "-_" )[:80] or "unknown"

    return _archipelago_root() / f"{STATE_FILE_PREFIX}{safe}.json"





def _legacy_node_credit(node: Mapping[str, Any]) -> int:



    layer_number = max(1, int(node.get("layer", 0)) + 1)

    mission_tier = max(1, int(node.get("mission_pool", 0)) + 1)

    expected_tier = (layer_number + 2) // 3

    mutation_value = int(node.get("mutation_value", 0))

    blessing_value = int(node.get("blessing_value", 0))

    old_reward = (

        400

        + 300 * (mission_tier - expected_tier)

        + 125 * mutation_value

        - 100 * blessing_value

        + 100 * layer_number

    )

    reward = max(150, old_reward - (100 * layer_number))

    mission_name = str(node.get("mission_name", node.get("name", ""))).strip().casefold()

    if mission_name == "lab rat":

        reward -= 100

    # Match credit_reward() when loading legacy nodes without stored payouts.
    layer = int(node.get("layer", 0))
    if layer == 0:
        reward += 50
    elif layer == 1:
        reward += 25

    return reward





def _neutralize_legacy_kerrigan_adjustment(node: Mapping[str, Any]) -> dict[str, Any] | None:



















    adjustment = str(node.get("kerrigan_adjustment", "none"))

    if adjustment not in {"extra_mutation", "removed_blessing", "credit_penalty"}:

        return None



    fixed = copy.deepcopy(dict(node))

    fixed.pop("kerrigan_adjustment", None)

    mutators = [str(x) for x in fixed.get("mutators", [])]

    mutation_value = max(0, int(fixed.get("mutation_value", 0)))



    if adjustment == "extra_mutation":







        for index in range(len(mutators) - 1, -1, -1):

            if int(GOLDEN_GOOSE_MUTATIONS.get(mutators[index], 0)) == 1:

                mutators.pop(index)

                mutation_value = max(0, mutation_value - 1)

                break

    elif adjustment == "removed_blessing":







        candidates = [

            (int(GOLDEN_GOOSE_MUTATIONS.get(name, 999)), index)

            for index, name in enumerate(mutators)

            if int(GOLDEN_GOOSE_MUTATIONS.get(name, 0)) > 0

        ]

        if candidates:

            severity, index = min(candidates)

            mutators.pop(index)

            mutation_value = max(0, mutation_value - severity)



    fixed["mutators"] = mutators

    fixed["mutation_value"] = mutation_value

    fixed["credit_reward"] = _legacy_node_credit(fixed)

    return fixed





def _migrate_legacy_kerrigan_adjustments(ctx: Any) -> int:



    cfg_nodes = getattr(ctx, "slay_config", {}).get("nodes", {})

    if not isinstance(cfg_nodes, Mapping):

        return 0

    s = state(ctx)

    raw_overrides = s.get("node_effect_overrides", {})

    overrides = copy.deepcopy(dict(raw_overrides)) if isinstance(raw_overrides, Mapping) else {}

    changed = 0

    for raw_mid, base in cfg_nodes.items():

        if not isinstance(base, Mapping):

            continue

        try:

            mid = int(raw_mid)

        except (TypeError, ValueError):

            continue







        try:

            if ctx.is_mission_completed(mid):

                continue

        except Exception:

            pass

        override = overrides.get(str(mid), overrides.get(mid))

        merged = copy.deepcopy(dict(base))

        if isinstance(override, Mapping):

            merged.update(copy.deepcopy(dict(override)))

        fixed = _neutralize_legacy_kerrigan_adjustment(merged)

        if fixed is None:

            continue

        overrides[str(mid)] = {

            "mutators": list(fixed.get("mutators", [])),

            "blessings": list(fixed.get("blessings", [])),

            "mutation_value": int(fixed.get("mutation_value", 0)),

            "blessing_value": int(fixed.get("blessing_value", 0)),

            "credit_reward": int(fixed.get("credit_reward", 0)),

        }

        overrides.pop(mid, None)

        changed += 1

    if changed:

        s["node_effect_overrides"] = overrides

        _persist_state(ctx)

    return changed





def _fresh_state_from_config(ctx: Any) -> dict[str, Any]:
    fresh = copy.deepcopy(DEFAULT_STATE)
    cfg = getattr(ctx, "slay_config", {})
    try:
        extra_slots = max(0, min(3, int(cfg.get("extra_shop_slots", 0))))
    except (TypeError, ValueError):
        extra_slots = 0
    fresh["shop_expansion"] = extra_slots
    if extra_slots:
        fresh["boon_purchases"] = {BOON_PREFIX + "shop_expansion": extra_slots}
    purchases = dict(fresh.get("purchases", {}))
    if bool(cfg.get("start_with_spear", False)):
        purchases[SPEAR_UNLOCK] = 1
        purchases[SPEAR_BASE_PYLON_ITEM] = max(1,purchases.get(SPEAR_BASE_PYLON_ITEM,0))
    if bool(cfg.get("start_with_kerrigan", False)):
        purchases[KERRIGAN_UNLOCK] = 1
    fresh["purchases"] = purchases
    if str(cfg.get("game_mode", "adventure")) == "crew":
        from .crew_challenge import default_roster
        fresh["crew_roster"] = default_roster(cfg.get("races", ["terran"]))
    return fresh


def _load_local_state(ctx: Any) -> dict[str, Any]:

    path = _state_file(ctx)

    if not path.is_file():

        return _fresh_state_from_config(ctx)

    try:

        return _sanitize_state(json.loads(path.read_text(encoding="utf-8")))

    except Exception as exc:

        logger.error("Slay the StarCraft: could not read state %s: %s; using fresh state.", path, exc)

        return copy.deepcopy(DEFAULT_STATE)





def initialize_context(ctx: Any) -> None:



    ctx.slay_config = _load_local_config(ctx)

    ctx.slay_state = copy.deepcopy(DEFAULT_STATE)

    ctx.slay_state_loaded = False

    if not enabled(ctx):

        return



    ctx.slay_state = _load_local_state(ctx)

    ctx.slay_state_loaded = True
    if endless_mode(ctx):
        ctx.missions_unlocked = True
        if not isinstance(state(ctx).get("endless"), dict):
            progress = {"floor": 0, "choices": [], "history": [], "offers": [], "selected": None}
            _new_endless_floor(ctx, progress)
            state(ctx)["endless"] = progress
            _persist_state(ctx)










    if hasattr(ctx, "kerrigan_total_level_cap"):

        try:

            ctx.kerrigan_total_level_cap = -1

        except Exception:

            pass







    if hasattr(ctx, "kerrigan_max_active_abilities"):

        try:

            ctx.kerrigan_max_active_abilities = 12

        except Exception:

            pass

    if hasattr(ctx, "kerrigan_max_passive_abilities"):

        try:

            ctx.kerrigan_max_passive_abilities = 5

        except Exception:

            pass

    _normalize_kerrigan_context(ctx)

    migrated_kerrigan_nodes = _migrate_legacy_kerrigan_adjustments(ctx)

    if migrated_kerrigan_nodes:

        logger.info(

            "Slay the StarCraft: neutralized legacy Kerrigan difficulty adjustments on %d uncompleted node(s).",

            migrated_kerrigan_nodes,

        )







    locations = sorted(int(x) for x in getattr(ctx, "server_locations", set()))

    if locations:

        async_start(ctx.send_msgs([{

            "cmd": "LocationScouts",

            "locations": locations,

            "create_as_hint": 0,

        }]), name="SC2 Slay location scouting")

    logger.info(

        "Slay the StarCraft active: run %s (seed %s), %d mission nodes.",

        ctx.slay_config.get("run_id"), ctx.slay_config.get("run_seed"), len(ctx.slay_config.get("nodes", {})),

    )





def _sanitize_state(value: Any) -> dict[str, Any]:

    state = copy.deepcopy(DEFAULT_STATE)

    if not isinstance(value, Mapping):

        return state



    chosen: list[int] = []

    for raw in value.get("chosen", []):

        try:

            mission_id = int(raw)

        except (TypeError, ValueError):

            continue

        if mission_id not in chosen:

            chosen.append(mission_id)

    state["chosen"] = chosen



    purchases: dict[str, int] = {}

    raw_purchases = value.get("purchases", {})

    if isinstance(raw_purchases, Mapping):

        for name, count in raw_purchases.items():

            try:

                count_i = max(0, int(count))

            except (TypeError, ValueError):

                continue

            if count_i:

                purchases[str(name)] = count_i

    if purchases.get(SPEAR_UNLOCK,0)>0:
        purchases[SPEAR_BASE_PYLON_ITEM] = max(1,purchases.get(SPEAR_BASE_PYLON_ITEM,0))
    state["purchases"] = purchases

    raw_inventory_snapshot = value.get("inventory_received_snapshot", [])
    inventory_snapshot: list[list[int]] = []
    if isinstance(raw_inventory_snapshot, Sequence) and not isinstance(raw_inventory_snapshot, (str, bytes)):
        for raw_record in raw_inventory_snapshot:
            if not isinstance(raw_record, Sequence) or isinstance(raw_record, (str, bytes)) or len(raw_record) < 3:
                continue
            try:
                inventory_snapshot.append([int(raw_record[0]), int(raw_record[1]), int(raw_record[2])])
            except (TypeError, ValueError):
                continue
    state["inventory_received_snapshot"] = inventory_snapshot

    cycle_purchases: dict[str, int] = {}

    raw_cycle_purchases = value.get("shop_cycle_purchases", {})

    if isinstance(raw_cycle_purchases, Mapping):

        for name, count in raw_cycle_purchases.items():

            try:

                count_i = max(0, int(count))

            except (TypeError, ValueError):

                continue

            if count_i:

                cycle_purchases[str(name)] = count_i

    state["shop_cycle_purchases"] = cycle_purchases



    try:

        state["spent"] = max(0, int(value.get("spent", 0)))

        state["test_credit_bonus"] = int(value.get("test_credit_bonus", 0))

        state["shop_cycle"] = int(value.get("shop_cycle", -1))

    except (TypeError, ValueError):

        state["spent"] = 0

        state["test_credit_bonus"] = 0

        state["shop_cycle"] = -1



    raw_potions = value.get("potion_inventory", [])
    if isinstance(raw_potions, list):
        state["potion_inventory"] = [dict(row) for row in raw_potions
            if isinstance(row, Mapping) and str(row.get("id", "")) in POTION_CATALOG
            and str(row.get("serial", "0")).isdigit()][:POTION_CAPACITY]
    try:
        state["potion_serial"] = max(0, int(value.get("potion_serial", 0)))
    except (TypeError, ValueError):
        state["potion_serial"] = 0
    raw_potion_purchases = value.get("shop_potions_bought", [])
    if isinstance(raw_potion_purchases, (list, tuple)):
        state["shop_potions_bought"] = list(dict.fromkeys(
            str(name) for name in raw_potion_purchases if str(name) in POTION_CATALOG
        ))
    state["shop_frozen_item"] = str(value.get("shop_frozen_item", "") or "")
    raw_stock = value.get("shop_stock", [])

    if isinstance(raw_stock, Sequence) and not isinstance(raw_stock, (str, bytes)):

        stock: list[str] = []

        for raw in raw_stock:

            name = str(raw)

            if name and name not in stock:

                stock.append(name)

        state["shop_stock"] = stock

    raw_sales = value.get("shop_sale_items", [])

    if isinstance(raw_sales, Sequence) and not isinstance(raw_sales, (str, bytes)):

        state["shop_sale_items"] = list(dict.fromkeys(str(x) for x in raw_sales if str(x)))

    for key in ("shop_stock_logic_version", "shop_visit_nonce"):

        try:

            state[key] = max(0, int(value.get(key, 0)))

        except (TypeError, ValueError):

            state[key] = 0



    for mapping_key in ("boon_purchases", "temporary_blessings", "node_effect_overrides", "duplicate_replacements"):

        raw_map = value.get(mapping_key, {})

        if isinstance(raw_map, Mapping):

            state[mapping_key] = copy.deepcopy(dict(raw_map))
            if mapping_key == "boon_purchases":
                expansion_id = _boon_id("shop_expansion")
                if expansion_id in state[mapping_key]:
                    try:
                        state[mapping_key][expansion_id] = min(SHOP_EXPANSION_MAX, max(0, int(state[mapping_key][expansion_id])))
                    except (TypeError, ValueError):
                        state[mapping_key][expansion_id] = state["shop_expansion"]

    raw_test_missions = value.get("test_mission_overrides", {})

    if isinstance(raw_test_missions, Mapping):

        test_missions: dict[str, dict[str, Any]] = {}

        for raw_mid, raw_override in raw_test_missions.items():

            if not isinstance(raw_override, Mapping):

                continue

            try:

                mid_key = str(int(raw_mid))

            except (TypeError, ValueError):

                continue

            raw_effects = raw_override.get("effects", [])

            effects: list[str] = []

            if isinstance(raw_effects, Sequence) and not isinstance(raw_effects, (str, bytes)):

                effects = list(dict.fromkeys(str(x) for x in raw_effects if str(x) in EFFECT_BANK_BITS))

            test_missions[mid_key] = {

                "clear": bool(raw_override.get("clear", False)),

                "effects": effects,

            }

        state["test_mission_overrides"] = test_missions

    state["permanent_blessings"] = [

        str(x) for x in value.get("permanent_blessings", []) if str(x) in BLESSING_SEVERITY

    ]

    state["permanent_boons"] = [str(x) for x in value.get("permanent_boons", []) if str(x) in EFFECT_BANK_BITS and str(x).startswith("boon_")]

    state["permanent_mutations"] = [str(x) for x in value.get("permanent_mutations", []) if str(x) in GOLDEN_GOOSE_MUTATIONS and str(x) in EFFECT_BANK_BITS]

    for int_key in ("shop_expansion", "shop_reroll_nonce", "shop_cycle_purchase_victory_count", "shop_rerolls_this_cycle", "shop_reroll_purchase_victory_count", "risky_investment_charges", "golden_goose_bonus_per_mission", "golden_goose_credit_offset", "single_use_tools_last_victory"):

        try: state[int_key] = max(0, int(value.get(int_key, 0)))

        except (TypeError, ValueError): state[int_key] = 0

    # Old saves may exceed the new three-expansion cap. Normalize on load.
    state["shop_expansion"] = min(SHOP_EXPANSION_MAX, state["shop_expansion"])

    try:

        state["saving_grace_charges"] = max(0, int(value.get("saving_grace_charges", 0)))

    except (TypeError, ValueError):

        state["saving_grace_charges"] = 0

    raw_grace = value.get("saving_grace_pending", [])
    if isinstance(raw_grace, list):
        state["saving_grace_pending"] = [
            [str(e) for e in package if str(e) in BLESSING_SEVERITY]
            for package in raw_grace if isinstance(package, list)
        ]

    announced = value.get("duplicate_announced", [])

    if isinstance(announced, Sequence) and not isinstance(announced, (str, bytes)):

        state["duplicate_announced"] = [str(x) for x in announced]

    raw_test = value.get("test_effects_next", [])

    if isinstance(raw_test, Sequence) and not isinstance(raw_test, (str, bytes)):

        state["test_effects_next"] = list(dict.fromkeys(str(x) for x in raw_test if str(x) in EFFECT_BANK_BITS))

    state["test_clear_next"] = bool(value.get("test_clear_next", False))

    state["auto_victory_next"] = bool(value.get("auto_victory_next", False))

    state["godmode_next"] = bool(value.get("godmode_next", False))

    try:

        state["godmode_mission_id"] = int(value.get("godmode_mission_id", -1))

    except (TypeError, ValueError):

        state["godmode_mission_id"] = -1



    raw_route_layout = value.get("route_layout_x_fractions", {})

    if isinstance(raw_route_layout, Mapping):

        route_layout: dict[str, float] = {}

        for raw_mid, raw_fraction in raw_route_layout.items():

            try:

                mid_key = str(int(raw_mid))

                fraction = float(raw_fraction)

            except (TypeError, ValueError):

                continue

            if math.isfinite(fraction) and 0.0 <= fraction <= 1.0:

                route_layout[mid_key] = fraction

        state["route_layout_x_fractions"] = route_layout

    progress = value.get("endless")
    if isinstance(progress, Mapping):
        history = progress.get("history", [])
        choices = progress.get("choices", [])
        floor = int(progress.get("floor", 0))
        if floor != len(history) or not 2 <= len(choices) <= 4:
            raise ValueError("Invalid endless floor history or candidate count")
        state["endless"] = copy.deepcopy(dict(progress))

    # Crew state is durable. Dropping these extension fields during an
    # unrelated save used to erase the rolled upgrade offers and the replay
    # guard for free-building deaths. The latter repeatedly charged the same
    # SC2 bank receipt on EVERY live poll (reported as thousands of credits).
    raw_upgrade_cycle = value.get('crew_upgrade_shop_cycle')
    if isinstance(raw_upgrade_cycle, Mapping):
        cycle = raw_upgrade_cycle.get('cycle')
        rows = raw_upgrade_cycle.get('rows')
        if isinstance(cycle, str) and len(cycle) <= 256 and isinstance(rows, list):
            valid_rows = []
            for raw in rows[:12]:
                if (not isinstance(raw, Mapping) or
                    not isinstance(raw.get('id'), str) or
                    len(raw['id']) > 200):
                    continue
                valid_rows.append(copy.deepcopy(dict(raw)))
            state['crew_upgrade_shop_cycle'] = {'cycle': cycle,
                'rows': valid_rows, 'ids': [r['id'] for r in valid_rows]}
    charged = value.get('crew_charged_free_structure_deaths', [])
    if isinstance(charged, list):
        state['crew_charged_free_structure_deaths'] = list(dict.fromkeys(
            x for x in charged if isinstance(x, str) and len(x) <= 120))
    notifications = value.get('crew_loss_notifications', [])
    if isinstance(notifications, list):
        state['crew_loss_notifications'] = [str(x)[:256] for x in notifications[-100:]]

    # Crew's individual roster copies belong to saved state, not the AP
    # inventory. Never coerce a malformed roster into an empty one.
    if value.get("crew_roster") is not None:
        from .crew_challenge import normalized_ledger
        state["crew_roster"] = normalized_ledger(value["crew_roster"])
    return state





def state_ready(ctx: Any) -> bool:

    if not enabled(ctx):

        return True

    return bool(getattr(ctx, "slay_state_loaded", False))





def state(ctx: Any) -> dict[str, Any]:

    if not enabled(ctx):

        return copy.deepcopy(DEFAULT_STATE)

    if not hasattr(ctx, "slay_state"):

        ctx.slay_state = copy.deepcopy(DEFAULT_STATE)

    return ctx.slay_state





def _persist_state(ctx: Any) -> None:

    if not enabled(ctx):

        return

    payload = _sanitize_state(state(ctx))

    ctx.slay_state = payload

    ctx.slay_state_loaded = True

    path = _state_file(ctx)

    tmp = path.with_suffix(path.suffix + ".tmp")

    try:

        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        tmp.replace(path)

    except Exception as exc:

        logger.error("Slay the StarCraft: failed to persist run state to %s: %s", path, exc)

        try:

            if tmp.exists():

                tmp.unlink()

        except OSError:

            pass





DANGER_OUTLIER_MARGIN = 450
DEV86_12_MISSION_DANGER_MARGIN = 250

DANGER_CREDIT_BONUS = 100







_EXPECTED_MUTATION_SEVERITY_PROFILE = (

    2.42, 2.83, 3.92, 4.59, 5.73, 6.81, 7.66, 8.85, 10.24, 11.51, 12.97, 15.36,

)

_EXPECTED_BLESSING_SEVERITY_PROFILE = (

    8.01, 6.39, 6.11, 5.71, 5.07, 4.67, 3.99, 3.66, 3.42, 2.14, 1.79, 1.80,

)

_BRUTAL_POOL_TARGET_PROFILE = (0.0, 1.316, 1.575, 1.959, 2.388, 2.684, 2.558, 3.056, 3.526, 3.545, 4.0)

_DIFFICULTY_POOL_OFFSETS = {"easy": -0.75, "medium": 0.0, "hard": 0.75, "brutal": 1.25}

_EFFECT_FREQUENCY_FACTORS = {"less": 0.5, "normal": 1.0, "more": 1.5}
_DEFAULT_CAMPAIGN_LENGTH = 12







_EXPECTED_OPENING_CREDIT_AVERAGE = {

    ("easy", "less", "less"): 391.0, ("easy", "less", "normal"): 278.0,

    ("easy", "less", "more"): 258.0, ("easy", "normal", "less"): 441.0,

    ("easy", "normal", "normal"): 297.0, ("easy", "normal", "more"): 263.0,

    ("easy", "more", "less"): 510.0, ("easy", "more", "normal"): 335.0,

    ("easy", "more", "more"): 281.0, ("medium", "less", "less"): 407.0,

    ("medium", "less", "normal"): 287.0, ("medium", "less", "more"): 259.0,

    ("medium", "normal", "less"): 469.0, ("medium", "normal", "normal"): 317.0,

    ("medium", "normal", "more"): 267.0, ("medium", "more", "less"): 555.0,

    ("medium", "more", "normal"): 372.0, ("medium", "more", "more"): 294.0,

    ("hard", "less", "less"): 428.0, ("hard", "less", "normal"): 291.0,

    ("hard", "less", "more"): 260.0, ("hard", "normal", "less"): 498.0,

    ("hard", "normal", "normal"): 331.0, ("hard", "normal", "more"): 271.0,

    ("hard", "more", "less"): 594.0, ("hard", "more", "normal"): 407.0,

    ("hard", "more", "more"): 311.0, ("brutal", "less", "less"): 435.0,

    ("brutal", "less", "normal"): 300.0, ("brutal", "less", "more"): 262.0,

    ("brutal", "normal", "less"): 528.0, ("brutal", "normal", "normal"): 342.0,

    ("brutal", "normal", "more"): 280.0, ("brutal", "more", "less"): 644.0,

    ("brutal", "more", "normal"): 443.0, ("brutal", "more", "more"): 319.0,

}



def _expected_opening_credit_average(config: Mapping[str, Any]) -> float:

    try:

        stored = float(config.get("expected_opening_credit_average", 0.0))

    except (TypeError, ValueError):

        stored = 0.0

    if stored > 0.0:

        return stored

    difficulty = str(config.get("difficulty", "brutal")).strip().casefold()
    if difficulty not in {"easy", "medium", "hard", "brutal"}:
        difficulty = "brutal"
    mf = _effect_frequency_factor(config.get("mutation_frequency", 1.0))
    bf = _effect_frequency_factor(config.get("blessing_frequency", 1.0))
    labels = ((0.5, "less"), (1.0, "normal"), (1.5, "more"))
    def interp(points: Sequence[tuple[float, float]], x: float) -> float:
        pts = sorted((float(px), float(py)) for px, py in points)
        if x <= pts[0][0]: left, right = pts[0], pts[1]
        elif x >= pts[-1][0]: left, right = pts[-2], pts[-1]
        else:
            left, right = pts[0], pts[-1]
            for a, b in zip(pts, pts[1:]):
                if a[0] <= x <= b[0]: left, right = a, b; break
        t = 0.0 if abs(right[0] - left[0]) < 1e-9 else (x - left[0]) / (right[0] - left[0])
        return left[1] + ((right[1] - left[1]) * t)
    def at_bless(mut_label: str) -> float:
        return interp([(x, _EXPECTED_OPENING_CREDIT_AVERAGE[(difficulty, mut_label, lab)]) for x, lab in labels], bf)
    base = interp([(x, at_bless(lab)) for x, lab in labels], mf)

    try:

        multiplier = max(0.0, float(config.get("victory_credit_reward_multiplier", 1.0)))

    except (TypeError, ValueError):

        multiplier = 1.0

    return float(base - 50.0 + 125.0 * mf) * multiplier





def _curve_value(profile: Sequence[float], frac: float) -> float:

    if not profile:

        return 0.0

    if len(profile) == 1:

        return float(profile[0])

    x = max(0.0, min(1.0, float(frac))) * (len(profile) - 1)

    lo = int(x)

    hi = min(len(profile) - 1, lo + 1)

    t = x - lo

    return float(profile[lo]) * (1.0 - t) + float(profile[hi]) * t





def _effect_frequency_factor(raw: Any) -> float:
    if isinstance(raw, str):
        key = raw.strip().casefold()
        if key in _EFFECT_FREQUENCY_FACTORS:
            return _EFFECT_FREQUENCY_FACTORS[key]
        raw = key
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0
    return value if math.isfinite(value) and value >= 0.0 else 1.0


def _runtime_effect_means(layer: int, choice_layers: int, final: bool) -> tuple[float, float]:
    total_missions = max(1, int(choice_layers) + 1)
    mission_number = max(1, int(layer) + 1)
    frac = 1.0 if final else (0.0 if choice_layers <= 0 else layer / max(1, choice_layers))
    if total_missions == _DEFAULT_CAMPAIGN_LENGTH:
        return (
            _curve_value(_EXPECTED_MUTATION_SEVERITY_PROFILE, frac) + 1.0 + 0.25 * mission_number,
            _curve_value(_EXPECTED_BLESSING_SEVERITY_PROFILE, frac),
        )
    mut_mean = float(mission_number + 2) + (2.0 if final else 0.0)
    third_last = max(1, total_missions - 2)
    if mission_number >= third_last or third_last <= 1:
        bless_mean = 1.0
    else:
        bless_mean = 7.0 - (6.0 * ((mission_number - 1) / max(1, third_last - 1)))
    return mut_mean + 1.0 + 0.25 * mission_number, bless_mean


def _fallback_expected_danger_score(config: Mapping[str, Any], data: Mapping[str, Any]) -> int:



    try:

        layer = max(0, int(data.get("layer", 0)))

    except (TypeError, ValueError):

        layer = 0

    try:

        choice_layers = max(1, int(config.get("choice_layers", 11)))

    except (TypeError, ValueError):

        choice_layers = 11

    difficulty = str(config.get("difficulty", "brutal")).strip().casefold()

    if difficulty not in _DIFFICULTY_POOL_OFFSETS:

        difficulty = "brutal"

    mutation_frequency = config.get("mutation_frequency", 1.0)
    blessing_frequency = config.get("blessing_frequency", 1.0)
    mut_factor = _effect_frequency_factor(mutation_frequency)
    bless_factor = _effect_frequency_factor(blessing_frequency)
    final = layer >= choice_layers
    mutation_mean, blessing_mean = _runtime_effect_means(layer, choice_layers, final)
    mutation_mean = max(0.0, mutation_mean + {
        "easy": -1.25, "medium": -0.75, "hard": -0.30, "brutal": 0.0,
    }[difficulty]) * mut_factor
    blessing_mean = max(0.0, blessing_mean) * bless_factor
    expected_pool = 4.0 if final else (1.0 + 3.0 * (layer / max(1, choice_layers)))

    layer_number = layer + 1

    expected_tier_zero_based = ((layer_number + 2) // 3) - 1

    return int(round(

        300.0 * (expected_pool - expected_tier_zero_based)

        + 150.0 * mutation_mean

        - 100.0 * blessing_mean

    ))





def _merged_nodes(ctx: Any) -> dict[int, dict[str, Any]]:



    if not enabled(ctx):

        return {}

    raw = ctx.slay_config.get("nodes", {})
    if endless_mode(ctx) and state_ready(ctx):
        progress = state(ctx).get("endless")
        if isinstance(progress, dict):
            raw = {str(int(n["mission_id"])): n for n in progress["choices"]}
            raw.update({str(-(index+1)): dict(n, mission_id=-(index+1), next=[], _display_status="completed")
                        for index, n in enumerate(progress["history"])})

    overrides = state(ctx).get("node_effect_overrides", {}) if state_ready(ctx) else {}

    result: dict[int, dict[str, Any]] = {}

    for key, value in raw.items():

        mid = int(key)

        merged = dict(value)

        override = overrides.get(str(mid), overrides.get(mid)) if isinstance(overrides, Mapping) else None

        if isinstance(override, Mapping):

            merged.update(copy.deepcopy(dict(override)))

            if "kerrigan_adjustment" not in override:

                merged.pop("kerrigan_adjustment", None)

        result[mid] = merged

    return result





def nodes(ctx: Any) -> dict[int, dict[str, Any]]:



    result = _merged_nodes(ctx)

    config = getattr(ctx, "slay_config", {})

    for mid, data in result.items():

        if endless_mode(ctx):
            data["danger_credit_bonus"] = 0
            data["_endless_floor"] = True
            continue
        if _mission_is_difficulty_outlier_in_nodes(result, mid, config):







            bonus = 0 if int(data.get("layer", -1)) == 0 else DANGER_CREDIT_BONUS
            if campaign_mode(ctx):
                bonus = int((bonus / 4.0) + 0.5)

            data["danger_credit_bonus"] = bonus

            data["credit_reward"] = int(data.get("credit_reward", 0)) + bonus

        else:

            data["danger_credit_bonus"] = 0

    return result





def node(ctx: Any, mission_id: int) -> dict[str, Any] | None:

    return nodes(ctx).get(int(mission_id))





def mission_layer_for_mission(ctx: Any, mission_id: int) -> int:

    data = node(ctx, int(mission_id)) or {}

    try:

        return max(1, int(data.get("layer", 0)) + 1)

    except (TypeError, ValueError):

        return 1





def _mission_danger_score(data: Mapping[str, Any]) -> int:



    try:

        mission_pool = int(data.get("mission_pool", 0))

    except (TypeError, ValueError):

        mission_pool = 0

    try:

        layer = int(data.get("layer", 0))

    except (TypeError, ValueError):

        layer = 0

    try:

        mutation_value = int(data.get("mutation_value", 0))

    except (TypeError, ValueError):

        mutation_value = 0

    try:

        blessing_value = int(data.get("blessing_value", 0))

    except (TypeError, ValueError):

        blessing_value = 0

    layer_number = max(1, layer + 1)

    mission_tier = max(1, mission_pool + 1)

    expected_tier = (layer_number + 2) // 3

    return (300 * (mission_tier - expected_tier)) + (150 * mutation_value) - (100 * blessing_value)





def _mission_expected_danger_score(config: Mapping[str, Any], data: Mapping[str, Any]) -> int:

    try:

        return int(data["expected_danger_score"])

    except (KeyError, TypeError, ValueError):

        return _fallback_expected_danger_score(config, data)





def _mission_is_difficulty_outlier_in_nodes(

    all_nodes: Mapping[int, Mapping[str, Any]], mission_id: int,

    config: Mapping[str, Any] | None = None,

) -> bool:















    data = all_nodes.get(int(mission_id))

    if data is None:

        return False

    config = config or {}

    try:

        layer = int(data.get("layer", -1))

        choice_layers = int(config.get("choice_layers", 11))

    except (TypeError, ValueError):

        return False

    if layer < 0:
        return False
    if str(config.get("game_mode", "")).casefold() == "campaign" and layer >= choice_layers:
        return bool(data.get("high_risk", False))
    if layer >= choice_layers:
        return False

    if layer == 0:









        try:

            expected_average = float(data.get("expected_opening_credit_average", 0.0))

        except (TypeError, ValueError):

            expected_average = 0.0

        if expected_average <= 0.0:

            expected_average = _expected_opening_credit_average(config)

        # 900+ credit first-layer missions are elite visually, with no +100 bonus.
        return float(data.get("credit_reward", 0)) >= 900.0 or float(data.get("credit_reward", 0)) > (2.5 * expected_average)

    score = _mission_danger_score(data)

    baseline = _mission_expected_danger_score(config, data)

    # Dev86's 12-mission classification must agree with the generator's
    # assignment guard/hardening steps, not only the UI badge.
    margin = (DEV86_12_MISSION_DANGER_MARGIN if choice_layers + 1 == _DEFAULT_CAMPAIGN_LENGTH
              else DANGER_OUTLIER_MARGIN)
    return score >= baseline + margin





def mission_is_difficulty_outlier(ctx: Any, mission_id: int) -> bool:
    if endless_mode(ctx):
        return bool((node(ctx, mission_id) or {}).get("high_risk"))

    return _mission_is_difficulty_outlier_in_nodes(

        _merged_nodes(ctx), int(mission_id), getattr(ctx, "slay_config", {})

    )





MISSION_FLAG_UNRESTRICTED_GROUND_SPAWNS = 1

MISSION_FLAG_PHANTOMS_AIR_EXCLUSION = 2

MISSION_FLAG_TIMED_DEFENSE = 4
# Mission flag bit 8 is retired. Keep other flag values stable.
MISSION_FLAG_HELLION_RUN_BY = 16
MISSION_FLAG_DIAMONDBACK_WANDERERS = 32
MISSION_FLAG_LEVIATHAN_OUTSIDE_BASE = 64
MISSION_FLAG_ODIN_DELAYED_ASSAULT = 128
MISSION_FLAG_COMBINED_RAIDS = 256
MISSION_FLAG_BRAKK_PRIMAL_ARMY = 512
MISSION_FLAG_ORLAN_FORTRESS = 1024
MISSION_FLAG_ENEMY_SPEAR_OF_ADUN = 2048
MISSION_FLAG_TRUE_GOLDEN_ARMADA = 4096
MISSION_FLAG_LAB_RAT_OPENING = 8192
MISSION_FLAG_IMMORTAL_ZERGLING = 16384
MISSION_FLAG_TOSH_AND_HIS_BOYS = 32768
MISSION_FLAG_DOMINATION_ANY_PICKER = 65536
MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI = 131072
MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS = 262144
MISSION_FLAG_DEVILS_PLAYGROUND_ZERG_ELIMINATION = 524288
MISSION_FLAG_EPILOGUE_KERRIGAN = 1048576
MISSION_FLAG_CREW_CHALLENGE = 2097152

GORGON_MISSION_EXCLUSIONS = {"fire in the sky"}

ISLAND_MISSION_NAMES = {

    "maw of the void",

    "the moebius factor",

    "the mobius factor",

    "templar's charge",

}





def mission_flags_for_mission(ctx: Any, mission_id: int) -> int:



    data = node(ctx, int(mission_id)) or {}

    mission_name = _mission_base_name(str(data.get("mission_name", "")))

    flags = 0
    if crew_mode(ctx):
        flags |= MISSION_FLAG_CREW_CHALLENGE







    if mission_name.casefold() in ISLAND_MISSION_NAMES:

        flags |= MISSION_FLAG_UNRESTRICTED_GROUND_SPAWNS

    if mission_name.casefold() == "phantoms of the void":

        flags |= MISSION_FLAG_PHANTOMS_AIR_EXCLUSION

    if bool(data.get("timed_defense", False)):

        flags |= MISSION_FLAG_TIMED_DEFENSE

    if mission_name.casefold() == "lab rat":

        flags |= MISSION_FLAG_LAB_RAT_OPENING
    if mission_name.casefold() == "domination":
        flags |= MISSION_FLAG_DOMINATION_ANY_PICKER
    if mission_name.casefold() == "engine of destruction":
        flags |= MISSION_FLAG_ENGINE_OF_DESTRUCTION_LOKI
    if mission_name.casefold() == "smash and grab" and not crew_mode(ctx):
        flags |= MISSION_FLAG_SMASH_AND_GRAB_EXTRA_WORKERS
    if mission_name.casefold() in {"the essence of eternity", "essence of eternity", "amon's fall"}:
        flags |= MISSION_FLAG_EPILOGUE_KERRIGAN

    mutation_flag_bits = {
        "hellion_run_by": MISSION_FLAG_HELLION_RUN_BY,
        "diamondback_wanderers": MISSION_FLAG_DIAMONDBACK_WANDERERS,
        "leviathan_outside_base": MISSION_FLAG_LEVIATHAN_OUTSIDE_BASE,
        "odin_delayed_assault": MISSION_FLAG_ODIN_DELAYED_ASSAULT,
        "combined_raids": MISSION_FLAG_COMBINED_RAIDS,
        "brakk_primal_army": MISSION_FLAG_BRAKK_PRIMAL_ARMY,
        "orlan_fortress": MISSION_FLAG_ORLAN_FORTRESS,
        "enemy_spear_of_adun": MISSION_FLAG_ENEMY_SPEAR_OF_ADUN,
        "true_golden_armada": MISSION_FLAG_TRUE_GOLDEN_ARMADA,
        "immortal_zergling": MISSION_FLAG_IMMORTAL_ZERGLING,
        "tosh_and_his_boys": MISSION_FLAG_TOSH_AND_HIS_BOYS,
    }
    for effect in _effective_mutations(ctx, int(mission_id)):
        flags |= int(mutation_flag_bits.get(str(effect), 0))

    return flags





def test_potion_run_token(ctx: Any) -> int:
    """Stable positive 31-bit token used by the experimental one-use potion UI."""
    run_seed = int(getattr(ctx, "slay_config", {}).get("run_seed", 0))
    digest = hashlib.sha256(f"SlayTestPotion:{run_seed}".encode("utf-8")).digest()
    token = int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
    return token or 1


def crew_mode(ctx: Any) -> bool:
    return enabled(ctx) and str(getattr(ctx,"slay_config",{}).get("game_mode","adventure")) == "crew"


def crew_roster(ctx: Any) -> dict[str, Any]:
    if not crew_mode(ctx):
        raise ValueError("Crew roster is only accessible in Crew")
    if not state_ready(ctx):
        raise RuntimeError("Slay state has not been loaded")
    roster = state(ctx).get("crew_roster")
    if roster is None:
        from .crew_challenge import default_roster
        roster = default_roster(getattr(ctx,"slay_config",{}).get("races",["terran"]))
        state(ctx)["crew_roster"] = roster
        _persist_state(ctx)
    # Dev51: legacy ``zone`` remains the transport state; the player's entire
    # unspent roster is now a single Reserves pool. Migrate older inactive
    # Reserve toggles instead of hiding otherwise purchased copies forever.
    from .crew_challenge import normalized_ledger
    migrated=normalized_ledger(roster,getattr(ctx,"slay_config",{}).get("races",["terran"]))
    # A newly opened Slay client is NOT in its previous SC2 mission. Never
    # carry old field tags, production claims or a bank token into the GUI.
    # The in-process guard means normal in-game inventory refreshes cannot
    # abandon the current mission. Confirmed deaths remain permanent.
    if not getattr(ctx,"_slay_crew_client_roster_opened",False):
        ctx._slay_crew_client_roster_opened=True
        previous=migrated.get('active_mission')
        if isinstance(previous,dict) and previous.get('terminal_snapshot') is None:
            from .crew_challenge import abandon_interrupted_mission
            abandon_interrupted_mission(migrated)
    # AP has acknowledged this mission's victory. A missed SC2 on_end callback
    # must not leave its actors On Field indefinitely. This fallback is only
    # authorized by the *actual* AP completion location, never by a disconnect,
    # selected node or a mere mission-window close. Preserve recorded deaths.
    active=migrated.get('active_mission')
    if isinstance(active,dict) and type(active.get('mission_id')) is int:
        mid=active['mission_id']
        try:
            confirmed=bool(ctx.is_mission_completed(mid))
        except (AttributeError, KeyError, TypeError, ValueError):
            confirmed=False
        if confirmed:
            from .crew_challenge import abandon_interrupted_mission
            outcome=abandon_interrupted_mission(migrated,verified_game_closed=True)
            migrated.setdefault('settled_missions',{}).setdefault(str(mid),{
                'returned':outcome['returned'],'lost':outcome['lost'],
                'recovered_after_ap_completion':True})
    if migrated!=roster:
        roster=migrated
        state(ctx)["crew_roster"]=roster
        _persist_state(ctx)
    return roster


def crew_supply_summary(ctx: Any) -> tuple[int,int,int]:
    from .crew_challenge import supply_capacity, supply_reserved, supply_remaining
    roster = crew_roster(ctx)
    return (supply_reserved(roster), supply_capacity(roster), supply_remaining(roster))


def crew_catalog_offers(ctx: Any) -> dict[str, list[dict[str, Any]]]:
    """Development preview only: core-unit catalog; not the complete AP catalog."""
    from .crew_catalog import preview_catalog
    from .crew_challenge import shop_categories
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    # Crew MVP is Terran-only, including on older mixed-race save files.
    races=('terran',)
    # Do not sell prototype entries which the live Crew Galaxy transport
    # cannot actually create. The source catalog contains many future shop
    # options, but a paid structure without a verified native spawn mapping
    # would stay in the roster forever with no usable deployment. Keep those
    # proposals in the development catalog until their transport is ready.
    from .crew_sc2_adapter import NATIVE_TYPES
    from .crew_catalog import CREW_BLOCKED_REACTOR_ITEMS
    item_table=_item_table()
    # Standard's actual buyable AP unit pool is the source of truth. Merely
    # adding Standard entries to a Crew-only prototype list left illegal
    # Royal Guard, Tauren Marine and story actors in the shop.
    def is_standard_unit(name):
        data=item_table.get(name)
        if data is None or getattr(data,'code',None) is None:return False
        typ=str(getattr(getattr(data,'type',None),'display_name',''))
        return (_is_unit_or_morph_unlock_type(typ)
                and not _is_mercenary_unit(name,data)
                and not _is_deprecated_item(name,data)
                and not _is_nova_campaign_item(name,data)
                and not _is_royal_guard_item(name,data,item_table)
                and str(name).casefold()!='tauren marine')
    from .crew_catalog import CREW_NOT_STANDARD_UNITS
    catalog=[entry for entry in preview_catalog(races)
             if entry['name'] not in CREW_NOT_STANDARD_UNITS and
             entry['name'] in NATIVE_TYPES and
             entry['name'] not in CREW_BLOCKED_REACTOR_ITEMS and
             (entry['category']!='unit' or is_standard_unit(entry['name']))]
    # Use Standard's actual Archipelago unit-item table as the authority for
    # purchasable campaign units. Include every verified native-mapped type,
    # not only those in the old little Crew table. Absent CUnit mappings are
    # tracked separately instead of offering undeliverable purchases.
    from .crew_catalog import catalog_entry_for_standard_unit
    included={(e['race'],e['name']) for e in catalog}
    for name,data in item_table.items():
        typ=str(getattr(getattr(data,'type',None),'display_name',''))
        if not is_standard_unit(name):continue
        race=_item_race_key(name,data)
        if race not in races or (race,name) in included:continue
        if name not in NATIVE_TYPES:continue
        entry=catalog_entry_for_standard_unit(name,race)
        if entry is not None:
            catalog.append(entry);included.add((race,name))
    roster=crew_roster(ctx)
    owned={c['name'] for c in roster['copies'] if c['status']!='lost'}
    owned.update(roster.get('discovered_unit_unlocks',()))
    layers=max(1,int(ctx.slay_config.get('layers',10)))
    graph=nodes(ctx)
    completed=completed_mission_ids(ctx) & set(graph) if graph else set()
    completed_layers=len({int(graph[mid]['layer']) for mid in completed if mid in graph}) if graph else 0
    seed=int(ctx.slay_config.get('run_seed',0)) + 997*victory_count(ctx) + 31*int(state(ctx).get('shop_reroll_nonce',0))
    offers=shop_categories(catalog,races,completed_layers=completed_layers,
                           total_layers=layers,owned_units=sorted(owned),seed=seed,
                           frozen_offer=str(state(ctx).get('shop_frozen_item','')),
                           expansion=int(state(ctx).get('shop_expansion',0)))
    offers['Unit Upgrades']=crew_upgrade_offers(ctx, unit_offers=offers['Units']+offers.get('Structures',[]))
    return offers



def crew_shop_description(entry: Mapping[str,Any]) -> str:
    """Use only the existing Archipelago item documentation for Crew cards.

    The roster and purchase rules are shown in their own UI; card text must
    not invent building effects, prerequisites or persistence claims.
    """
    name=str(entry['name'])
    return str(_AP_ITEM_DOCS.get(name, {}).get('description', '') or '').strip()



def crew_excluded_economy_item(name: str, description: str = '') -> bool:
    """Reject items whose benefit is bypassed by Crew's free/instant orders.

    Do not reject faster combat cooldowns, movement or transformation speed.
    """
    title=str(name).casefold()
    desc=' '.join(str(description).casefold().split())
    if title in {'tech reactor (terran)', 'tech reactor', 'reactor',
                 'barracks reactor', 'factory reactor', 'starport reactor'}:
        return True
    if any(k in title for k in (
        'optimized logistics','resource efficiency',
        'increased building construction speed','increased upgrade research speed',
        'reduced upgrade research cost','khalai ingenuity',
    )):return True
    # Explicit cost-of-production discounts, not mineral-generation bonuses.
    if ('cost' in desc or 'cheaper' in desc) and any(
        k in desc for k in ('train','training','unit','build','construct','research','production','upgrade')) and any(
        k in desc for k in ('mineral','vespene','gas','resource','cheaper','less to','reduc')):
        return True
    if any(k in desc for k in (
        'training speed','train faster','unit training time','build time',
        'construction speed','construct faster','production speed',
        'production time','research time','research speed','warp-in time',
        'warping time','warps in faster')):
        return True
    return False


# These AP general Terran items are economic/mercenary, and must not appear
# in a mode that does not buy conventional resources or mercenary contracts.
CREW_TERRAN_GENERAL_BLOCKED = frozenset({
    'Automated Refinery (Terran)', 'Tech Reactor (Terran)',
    'Orbital Depots (Terran)', 'Micro-Filtering (Terran)',
    'Advanced Construction (SCV)', 'Dual-Fusion Welders (SCV)',
    'Construction Jump Jets (SCV)', 'Command Center Reactor (Command Center)',
    'Mercenary Munitions (Terran)', 'Mechanical Know-how (Terran)',
    'Extra Supplies (Command Center)',
    'MULE (Command Center)',
})


# AP's Crew YAML requests generic_upgrade_items: individual_items. Match the
# *exact* six items that this option makes available; do not offer items from
# bundle_unit_class, bundle_weapon_and_armor, or bundle_all in the Crew shop.
CREW_TERRAN_INDIVIDUAL_STAT_UPGRADES = frozenset({
    'Progressive Terran Infantry Weapon',
    'Progressive Terran Infantry Armor',
    'Progressive Terran Vehicle Weapon',
    'Progressive Terran Vehicle Armor',
    'Progressive Terran Ship Weapon',
    'Progressive Terran Ship Armor',
})
CREW_TERRAN_BUNDLED_STAT_UPGRADES = frozenset({
    'Progressive Terran Infantry Upgrade',
    'Progressive Terran Vehicle Upgrade',
    'Progressive Terran Ship Upgrade',
    'Progressive Terran Weapon Upgrade',
    'Progressive Terran Armor Upgrade',
    'Progressive Terran Weapon/Armor Upgrade',
})


def crew_progressive_generic_upgrade(name: str) -> bool:
    """Only stat upgrades selected by the Crew individual-items YAML mode."""
    return str(name) in CREW_TERRAN_INDIVIDUAL_STAT_UPGRADES


def crew_excluded_story_upgrade(name: str, data: Any | None = None,
                                table: Mapping[str, Any] | None = None) -> bool:
    """No hero campaign equipment or unsupported merc/story upgrades in Crew.

    Crew is Terran race-only, but the AP item table contains Nova, Royal
    Guard, mission story and hero modules that cannot be used as Crew units.
    """
    if table is None:table=_item_table()
    if data is None:data=table.get(name)
    text=str(name).casefold()
    type_name=str(getattr(getattr(data,'type',None),'display_name','')).casefold()
    parents=_unit_specific_parent_names(name,table)
    forbidden=('nova','kerrigan','tychus','raynor commando','royal guard',
               'mercenary','spear of adun','zagara','dehaka','primal')
    return (any(word in text or word in type_name for word in forbidden)
            or _is_nova_campaign_item(name,data)
            or _is_kerrigan_item(name,data) or _is_spear_item(name,data)
            or _is_deprecated_item(name,data)
            or _is_royal_guard_item(name,data,table)
            or any(parent in {'Nova','Tychus','Kerrigan','Raynor Commando'}
                   for parent in parents))


def crew_general_terran_upgrade(name: str, data: Any | None = None,
                                table: Mapping[str, Any] | None = None) -> bool:
    """Admit real Standard-mode AP Terran-wide upgrades, excluding eco/mercs.

    Progressive weapon/armor items are general even when the AP item type is
    categorized separately. Other upgrades are selected from Standard's
    explicit race-global catalog or Terran-wide Upgrade/Progressive Upgrade
    entries, never from a unit parent such as Marine or a mercenary contract.
    """
    if (name in CREW_TERRAN_GENERAL_BLOCKED or name in CREW_TERRAN_BUNDLED_STAT_UPGRADES
            or crew_excluded_story_upgrade(name,data,table)):
        return False
    if table is None:
        table = _item_table()
    if data is None:
        data = table.get(name)
    if data is None or _item_race_key(name, data) != 'terran':
        return False
    if _is_mercenary_general_upgrade(name, data) or _mercenary_contract_for_item(name, data):
        return False
    if _is_unit_specific_upgrade(name, table):
        return False
    if crew_excluded_economy_item(name, shop_entry_description(name)):
        return False
    if (name in RACE_GLOBAL_UPGRADE_ITEMS.get('terran', ())
            or crew_progressive_generic_upgrade(name)):
        return True
    type_name = str(getattr(getattr(data, 'type', None), 'display_name', '')).casefold()
    return (type_name in {'upgrade', 'progressive upgrade'}
            and shop_category_for_item(name) == 'Terran Upgrades')


def crew_upgrade_price(ctx: Any, name: str) -> int:
    """Unit-specific upgrades cost 100; general AP upgrades keep Standard prices.

    Preserve Crew's established 80-credit initial weapon/armor tier and
    +40 credits for each previously purchased tier. Other general upgrades
    retain the Standard AP price; no discount on unit-specific upgrades.
    """
    if crew_progressive_generic_upgrade(name):
        # Crew's weapon/armor progression uses its own 80-credit base,
        # regardless of AP Standard's current base price. Add 50% of
        # the base per purchased tier: 80, 120, 160, 200, ...
        prior = max(0, int(purchased_count(ctx, name)))
        return 80 + 40 * prior
    if _is_unit_specific_upgrade(name):
        return 100
    return price_for_item(name, ctx)


def crew_upgrade_offers(ctx: Any, *, unit_offers: Sequence[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Stable per-shop-cycle Crew upgrade offers.

    The *roll* enforces one entry per SPECIFIC unit, while generic weapon,
    armor and shield upgrades each occupy an independent category. A purchase
    updates the offered item's price/eligibility but NEVER rerolls the other
    displayed offers. Only a real shop reroll/victory/expansion rerolls them.
    """
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    if unit_offers is None:
        unit_offers=[]
    active_races={'terran'}
    owned={str(x.get('name')) for x in crew_roster(ctx)['copies'] if x.get('status')!='lost'}
    available_units=owned|{str(e.get('name')) for e in unit_offers}
    table=_item_table()
    candidates=[]
    for name,data in table.items():
        is_crew_generic=crew_general_terran_upgrade(name,data,table)
        if not (_is_unit_specific_upgrade(name,table) or is_crew_generic):
            continue
        if (crew_excluded_economy_item(name,shop_entry_description(name))
                or _is_mercenary_general_upgrade(name,data)
                or name in CREW_TERRAN_GENERAL_BLOCKED
                or crew_excluded_story_upgrade(name,data,table)):
            continue
        item_race=_item_race_key(name,data)
        if item_race not in active_races:
            continue
        if not is_crew_generic and shop_category_for_item(name) not in (
                'Terran Upgrades','Zerg Upgrades','Protoss Upgrades'):
            continue
        parents=([None] if is_crew_generic else [parent
            for parent in _unit_specific_parent_names(name,table)
            if parent in available_units])
        if not parents:
            continue
        cap=_max_owned_copies(data)
        purchased=purchased_count(ctx,name)
        available=cap is None or _effective_shop_copies(name,purchased)<cap
        candidates.append({'id':name,'name':shop_entry_display_name(name),
            'parent':parents[0],'category':'upgrade','race':item_race,
            'credits':crew_upgrade_price(ctx,name),
            'description':shop_entry_description(name),
            'show_owned_count':(cap is None or cap > 1),
            'available':available})

    state_row=state(ctx)
    cycle=':'.join((str(ctx.slay_config.get('run_seed',0)),
        str(victory_count(ctx)),str(state_row.get('shop_reroll_nonce',0)),
        str(state_row.get('shop_expansion',0)),','.join(sorted(active_races))))
    cache=state_row.get('crew_upgrade_shop_cycle')
    candidate_by_id={r['id']:r for r in candidates}
    # Existing offers are not invalidated merely because a purchase reached its
    # cap, or unit inventory changed. A fresh cycle calculates eligible offers.
    if isinstance(cache,dict) and cache.get('cycle')==cycle:
        # Existing displayed offers must not disappear when the pool changes
        # after buying a unit/upgrade, or when live AP item data is refreshed.
        # Preserve the exact roll; only explicit reroll/victory changes IDs.
        frozen_rows=cache.get('rows')
        if isinstance(frozen_rows,list) and frozen_rows:
            # Existing Dev76/77 shop snapshots may contain one of AP's bundled
            # items from a different YAML mode. Migrate just that offer out of
            # the frozen roll while preserving other visible upgrades.
            if any(row.get('id') not in table
                   or row.get('id') in CREW_TERRAN_BUNDLED_STAT_UPGRADES
                   or crew_excluded_story_upgrade(row.get('id',''),table=table)
                   for row in frozen_rows if isinstance(row,dict)):
                seed='crew-upgrade:'+cycle
                rng=random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8],'big'))
                available_pool=[e for e in candidates if e['available']]
                rng.shuffle(available_pool)
                fresh=[dict(r) for r in frozen_rows if isinstance(r,dict)
                       and r.get('id') in table
                       and r.get('id') not in CREW_TERRAN_BUNDLED_STAT_UPGRADES
                       and not crew_excluded_story_upgrade(r.get('id',''),table=table)]
                wanted=min(3+max(0,min(3,int(state_row.get('shop_expansion',0)))),len(candidates))
                used={('unit',r['parent']) if r.get('parent') is not None
                      else ('generic',r['id']) for r in fresh}
                for e in available_pool:
                    if len(fresh)>=wanted:break
                    key=('unit',e['parent']) if e['parent'] is not None else ('generic',e['id'])
                    if key in used:continue
                    fresh.append(dict(e));used.add(key)
                state_row['crew_upgrade_shop_cycle']={'cycle':cycle,
                    'ids':[r['id'] for r in fresh],'rows':[dict(r) for r in fresh]}
                _persist_state(ctx)
                frozen_rows=fresh
            result=[]
            for original in frozen_rows:
                entry=dict(original)
                name=entry['id']
                entry['credits']=crew_upgrade_price(ctx,name)
                entry['show_owned_count']=bool(candidate_by_id.get(name,{}).get('show_owned_count',True))
                cap=_max_owned_copies(table.get(name)) if name in table else None
                count=purchased_count(ctx,name)
                entry['available']=(cap is None or _effective_shop_copies(name,count)<cap)
                result.append(entry)
            return result
        return [candidate_by_id[name] for name in cache.get('ids',())
                if name in candidate_by_id]

    seed='crew-upgrade:'+cycle
    rng=random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8],'big'))
    pool=[e for e in candidates if e['available']]
    rng.shuffle(pool)
    distinct=[]
    represented=set()
    for entry in pool:
        # Each generic upgrade is its own independent category; only upgrades
        # specifically tied to a unit compete for that unit's single slot.
        key=('unit',entry['parent']) if entry['parent'] is not None else ('generic',entry['id'])
        if key in represented:
            continue
        represented.add(key)
        distinct.append(entry)
    count=min(3+max(0,min(3,int(state_row.get('shop_expansion',0)))),len(distinct))
    result=distinct[:count]
    frozen=frozen_shop_item(ctx)
    frozen_row=next((r for r in distinct if r['id']==frozen),None)
    if frozen_row is not None and all(r['id']!=frozen for r in result):
        key=('unit',frozen_row['parent']) if frozen_row['parent'] is not None else ('generic',frozen_row['id'])
        result=[r for r in result if (
            ('unit',r['parent']) if r['parent'] is not None else ('generic',r['id']))!=key]
        if len(result)>=count and result:
            result[-1]=frozen_row
        else:
            result.append(frozen_row)
    state_row['crew_upgrade_shop_cycle']={'cycle':cycle,
        'ids':[r['id'] for r in result],
        'rows':[dict(r) for r in result]}
    _persist_state(ctx)
    return result


def crew_purchase_upgrade(ctx: Any, item_name: str) -> tuple[bool, str]:
    """Grant a verified AP upgrade item, with Crew unit ownership eligibility."""
    if not crew_mode(ctx):return False,'Not in Crew'
    # Do not regenerate the entire shop when validating a purchase. It can
    # change when a previous purchase updates AP ownership/prerequisites.
    cache=state(ctx).get('crew_upgrade_shop_cycle')
    original_rows=cache.get('rows',[]) if isinstance(cache,dict) else []
    offer=next((dict(x) for x in original_rows if x.get('id')==item_name),None)
    expected_cycle=':'.join((str(ctx.slay_config.get('run_seed',0)),
        str(victory_count(ctx)),str(state(ctx).get('shop_reroll_nonce',0)),
        str(state(ctx).get('shop_expansion',0)),
        'terran'))
    if (not isinstance(cache,dict) or cache.get('cycle') != expected_cycle):
        return False,'Shop changed; reroll or reopen before buying this offer'
    if item_name in CREW_TERRAN_BUNDLED_STAT_UPGRADES:
        return False,'Bundled weapon/armor upgrades are disabled; buy individual weapon and armor items instead'
    if offer is None:return False,'That upgrade is not currently in the Crew shop'
    if not offer.get('available',True):return False,'Upgrade has reached its purchase limit'
    table=_item_table()
    data=table.get(item_name)
    is_generic = crew_general_terran_upgrade(item_name,data,table)
    if (data is None or not (_is_unit_specific_upgrade(item_name,table) or is_generic)
            or crew_excluded_economy_item(item_name,shop_entry_description(item_name))
            or _is_mercenary_general_upgrade(item_name,data)
            or item_name in CREW_TERRAN_GENERAL_BLOCKED
            or crew_excluded_story_upgrade(item_name,data,table)
            or _item_race_key(item_name,data) != 'terran'):
        return False,'Unrecognized AP upgrade'
    cap=_max_owned_copies(data)
    if cap is not None and _effective_shop_copies(item_name,purchased_count(ctx,item_name))>=cap:
        return False,'Upgrade has reached its purchase limit'
    price=crew_upgrade_price(ctx,item_name)
    if credits(ctx)<price:return False,f'Need {price} credits; only {credits(ctx)} available.'
    s=state(ctx)
    copies=dict(s.get('purchases',{}))
    copies[item_name]=int(copies.get(item_name,0))+1
    s['purchases']=copies
    s['spent']=int(s.get('spent',0))+price
    if s.get('shop_frozen_item')==item_name:s['shop_frozen_item']=''
    _persist_state(ctx)
    _request_live_item_refresh(ctx)
    return True,f'Purchased {shop_entry_display_name(item_name)} for {price} credits.'


def crew_boon_offers(ctx: Any) -> list[dict[str, Any]]:
    """Roll a durable Crew-only visible boon pool from existing boon definitions.

    The vanilla stock is preferred, but Crew owns units through its roster,
    not AP unlock items, so vanilla eligible-boon rolls can be sparse. Fill
    the remaining slots from valid vanilla boon candidates, never fabricate
    a new effect ID or a price. All purchases use _purchase_boon below.
    """
    from .crew_challenge import eligible_boon, eligible_effect
    if not crew_mode(ctx):
        raise ValueError('Crew boon shop is only available in Crew')
    stock=[name for name in shop_stock(ctx) if name.startswith(BOON_PREFIX)]
    extras=_boon_candidates(ctx)
    extras.extend(_boon_id(k) for k in ('deadly_weapons','auto_repair',
                                       'rapid_fire','shields_for_all','fire_power'))
    frozen=frozen_shop_item(ctx)
    ordered=list(dict.fromkeys(([frozen] if frozen.startswith(BOON_PREFIX) else [])
                                 +stock+extras))
    eligible=[]
    for item in ordered:
        if not item.startswith(BOON_PREFIX):
            continue
        title=boon_display_name(item)
        rule_title=('Random Permanent Blessing' if title.startswith('Random Permanent Blessing (')
                    else 'Permanent Blessing: (Blessing)' if title.startswith('Permanent Blessing: ')
                    else title)
        if not eligible_boon(rule_title) or crew_excluded_economy_item(title,shop_entry_description(item)):
            continue
        kind,payload=_parse_boon(item)
        if kind=='permanent_blessing' and not eligible_effect(payload,'blessing'):
            continue
        if kind=='random_blessing' and not any(
                eligible_effect(effect,'blessing') and severity==int(payload)
                and effect not in state(ctx).get('permanent_blessings',())
                for effect,severity in BLESSING_SEVERITY.items()):
            continue
        eligible.append(item)
    # Stable stock per floor/reroll; freeze always survives a subsequent roll.
    # Standard-style Crew boon shelf: three items, including a frozen offer.
    regular=[x for x in eligible if x!=frozen]
    keep_stock=[x for x in regular if x in stock]
    additional=[x for x in regular if x not in stock]
    seed=f"{ctx.slay_config.get('run_seed',0)}:crew-boons:{victory_count(ctx)}:{state(ctx).get('shop_reroll_nonce',0)}"
    rng=random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8],'big'))
    rng.shuffle(additional)
    reroll=_boon_id('reroll_shop')
    # Reroll Shop is an always-visible utility, not one of the shuffled boons.
    names=([frozen] if frozen in eligible and frozen!=reroll else []) + [
        x for x in keep_stock if x!=reroll]
    names=list(dict.fromkeys(names))[:2]
    names.extend(x for x in additional if x!=reroll and x not in names and len(names)<2)
    names.append(reroll)
    rows=[]
    for item in names:
        rows.append({'id':item,'name':boon_display_name(item),'category':'boon','race':'boon',
                     'credits':price_for_item(item,ctx),
                     'description':shop_entry_description(item),
                     'available':can_buy_shop_item(ctx,item),
                     'owned':purchased_count(ctx,item)})
    return rows


def crew_purchase_boon(ctx: Any, boon_id: str) -> tuple[bool, str]:
    """Use original persistent boon engine with a Crew-specific stock guard."""
    if not crew_mode(ctx):
        return False,'Not in Crew'
    offers=crew_boon_offers(ctx)
    if boon_id not in {offer['id'] for offer in offers}:
        return False,'That Crew boon is not in this shop'
    if not can_buy_shop_item(ctx,boon_id):
        return False,'That boon has reached its purchase limit'
    price=price_for_item(boon_id,ctx)
    if credits(ctx)<price:
        return False,f'Need {price} credits; only {credits(ctx)} available.'
    # Unlike purchase(), this accepts the deterministic Crew-only filler
    # offers absent from Standard stock. It still invokes the *identical*
    # atomic state/credit/effect implementation for every boon kind.
    return _purchase_boon(ctx,boon_id,price)


def crew_consumable_offers(ctx: Any) -> list[dict[str, Any]]:
    """The original Crew excludes all consumables."""
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    return []


def crew_purchase_consumable(ctx: Any, item: str) -> tuple[bool, str]:
    return False, 'Consumables are not available in Crew'


def crew_consumable_inventory(ctx: Any) -> list[str]:
    return []


def crew_owned_effects(ctx: Any) -> dict[str, list[str]]:
    """Expose permanent purchased effects without changing Standard inventory."""
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    s=state(ctx)
    return {'Boons':[EFFECT_DISPLAY_NAMES.get(str(x),str(x))
                     for x in s.get('permanent_boons',())],
            'Blessings':[EFFECT_DISPLAY_NAMES.get(str(x),str(x))
                         for x in s.get('permanent_blessings',())],
            'Mutations':[EFFECT_DISPLAY_NAMES.get(str(x),str(x))
                         for x in s.get('permanent_mutations',())]}


def crew_structure_catalog_price(name:str, race:str) -> int | None:
    """Only purchasable, costed structures can incur Crew building debt."""
    from .crew_catalog import preview_catalog
    from .crew_challenge import credit_cost
    from .crew_sc2_adapter import NATIVE_TYPES
    try: rows=preview_catalog((race,))
    except ValueError:return None
    matches=[r for r in rows if r['name']==name and r['category']=='structure'
             and name in NATIVE_TYPES]
    if len(matches)!=1:return None
    r=matches[0]
    return credit_cost(int(r['minerals']),int(r['gas']),unit_name=name)

def crew_charge_confirmed_building_losses(ctx: Any) -> list[str]:
    """Purchases already paid for their copy: never charge them again on death."""
    return []


def crew_charge_free_building_deaths(ctx: Any, mission_id: int,
                                    deaths: Any, *, verified_tags: Mapping[int,str] | None = None) -> list[str]:
    """Charge each *free* bank-confirmed purchasable structure death once.

    Galaxy emits these only for player-owned untracked structures. A session
    token + native tag is used as the durable idempotence key, because the
    same death bank entry is re-read on every live-bot poll.
    """
    if not crew_mode(ctx):return []
    s=state(ctx)
    active=(crew_roster(ctx).get('active_mission') or {})
    if active.get('mission_id') != mission_id:return []
    token=int((active.get('auto_transport') or {}).get('token',0))
    if token<=0:return []
    from .crew_bank_receipts import _TYPE_BY_CODE
    from .crew_sc2_adapter import NATIVE_TYPES
    native_to_display={v:k for k,v in NATIVE_TYPES.items()}
    # A mission-supplied building has a real cost even if that variant has no
    # separate item card. All buildings represented in Crew's cost catalog
    # qualify; unsupported/unpriced scripted props do not incur guessed debt.
    from .crew_catalog import preview_catalog
    costs={}
    for row in preview_catalog(('terran','zerg','protoss')):
        if row.get('category')!='structure':continue
        cost=crew_structure_catalog_price(row['name'],row['race'])
        if cost is not None:
            costs.setdefault(NATIVE_TYPES.get(row['name']), (row['name'],cost))
    processed=set(s.get('crew_charged_free_structure_deaths',()))
    notices=[]; debit=0
    # A bank field is not sufficient grounds for irreversible credit debt.
    # Match the tag and native CUnit against a *finished* structure previously
    # seen in THIS player's SC2 observations. An incomplete foundation is free.
    # The observer retains tags for actors
    # that have since died, and bank tokens keep old sessions separate.
    validated=verified_tags if isinstance(verified_tags,Mapping) else {}
    # Per-copy exemption, NEVER per name or per building type. This protects
    # a deployed Barracks without exempting a second starting Barracks.
    from .crew_tags import wire_tag
    paid_tags=set()
    for full_tag,copy_id in active.get('tags',{}).items():
        owned=next((c for c in crew_roster(ctx).get('copies',())
                    if c.get('id')==copy_id),None)
        if owned is not None and owned.get('kind')=='structure':
            try:paid_tags.add(wire_tag(int(full_tag)))
            except (ValueError,TypeError):pass
    for tag,type_code in deaths:
        if tag in paid_tags:continue
        key=f'{mission_id}:{token}:{int(tag)}'
        if key in processed:continue
        native=_TYPE_BY_CODE.get(int(type_code))
        name_cost=costs.get(native)
        if name_cost is None or validated.get(int(tag))!=native:continue
        processed.add(key)
        name,cost=name_cost
        # Never allow a malformed catalog or receipt to cause large charges.
        if not (1<=cost<=1000):continue
        debit+=cost
        notices.append(f'{name} destroyed, subtracting {cost} credits')
    if notices:
        s['crew_charged_free_structure_deaths']=sorted(processed)
        s['spent']=int(s.get('spent',0))+debit
        s.setdefault('crew_loss_notifications',[]).extend(notices)
        _persist_state(ctx)
    return notices


def crew_take_loss_notifications(ctx:Any) -> list[str]:
    if not crew_mode(ctx):return []
    notices=list(state(ctx).get('crew_loss_notifications',()))
    if notices:
        state(ctx)['crew_loss_notifications']=[]
        _persist_state(ctx)
    return notices

def crew_revive_unit_price(name: str, race: str) -> int | None:
    from .crew_challenge import credit_cost
    from .crew_catalog import preview_catalog, catalog_entry_for_standard_unit
    try:
        matches=[row for row in preview_catalog((race,))
                 if row['name']==name and row['category']=='unit']
    except ValueError:
        return None
    if not matches:
        entry=catalog_entry_for_standard_unit(name,race)
        if entry is not None and entry.get('category')=='unit':
            matches=[entry]
    if len(matches)!=1:
        return None
    row=matches[0]
    return credit_cost(int(row['minerals']),int(row['gas']),unit_name=name)


def crew_revive_destroyed(ctx:Any, name:str, race:str, kind:str, quantity:int) -> tuple[int,list[str]]:
    """Revive 1 / 5: same credit cost as buying the unit, fresh Crew IDs."""
    from .crew_challenge import revive_destroyed
    if not crew_mode(ctx) or kind!='unit' or quantity not in (1,5):
        raise ValueError('Invalid Crew unit revival')
    unit_price=crew_revive_unit_price(name,race)
    if unit_price is None:
        raise ValueError('Unit cannot be revived without a verified Crew catalog price')
    charge=quantity*unit_price
    if credits(ctx)<charge:raise ValueError(f'Need {charge} credits to revive')
    updated=copy.deepcopy(crew_roster(ctx))
    ids=revive_destroyed(updated,name=name,race=race,kind=kind,quantity=quantity,supply=float(next((c.get('supply',0) for c in updated['copies'] if c['name']==name and c['race']==race and c['kind']==kind),0)))
    s=state(ctx);s['crew_roster']=updated;s['spent']=int(s.get('spent',0))+charge
    _persist_state(ctx)
    _request_live_item_refresh(ctx)
    return charge,ids


def crew_record_live_deaths(ctx: Any, mission_id: int, death_tags: Any) -> bool:
    """Persist verified bank-reported Crew deaths without prematurely settling.

    Workers or campaign freebies without a purchased Crew tag never count.
    A dead copy remains deployed until the authenticated victory outcome.
    """
    if not crew_mode(ctx):return False
    current=crew_roster(ctx)
    active=current.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        return False
    from .crew_tags import wire_tag
    by_wire={}
    for tag in active.get('tags',()):
        full=str(int(tag))
        code=wire_tag(int(tag))
        if code in by_wire:raise RuntimeError('Ambiguous Crew death wire tag')
        by_wire[code]=full
    incoming={int(tag) for tag in death_tags if type(tag) is int and tag>0}
    observed={by_wire[tag] for tag in incoming if tag in by_wire}
    previous=set(active.get('live_dead_tags',()))
    if observed<=previous:return False
    updated=copy.deepcopy(current)
    updated['active_mission']['live_dead_tags']=sorted(previous|observed)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    crew_charge_confirmed_building_losses(ctx)
    return True


def crew_record_live_claims(ctx: Any, mission_id: int, claimed_numbers: Any) -> bool:
    """Show bank-confirmed paid orders as unavailable without claiming their actors."""
    if not crew_mode(ctx):return False
    current=crew_roster(ctx)
    active=current.get('active_mission') or {}
    if active.get('mission_id')!=mission_id:return False
    bought={c['id'] for c in current['copies'] if c.get('status') in ('zone','reserve')}
    claimed=sorted({f'crew_{n}' for n in claimed_numbers if type(n) is int
                   and n>0 and f'crew_{n}' in bought})
    if claimed==active.get('live_claimed_copy_ids',[]):return False
    updated=copy.deepcopy(current)
    updated['active_mission']['live_claimed_copy_ids']=claimed
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return True


def crew_accept_field_builds(ctx: Any, mission_id: int, *, receipts: Any,
                             observations: Any, ready_tags: Any,
                             player_id: int, death_tags: Any = frozenset()) -> int:
    """Commit fully verified Galaxy construction receipts atomically."""
    if not crew_mode(ctx):return 0
    from .crew_field_build import accept_galaxy_build
    original=crew_roster(ctx)
    updated=original
    for receipt in receipts:
        updated=accept_galaxy_build(updated,mission_id,receipt=receipt,
            observations=tuple(observations),ready_tags=frozenset(ready_tags),
            player_id=player_id,death_tags=frozenset(death_tags))
    if updated!=original:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    crew_charge_confirmed_building_losses(ctx)
    return len((updated.get('active_mission') or {}).get('field_build_completed_ids',()))




# Crew rewards are separate from AP unlocks. Mission checks grant one
# deterministic *combat* unit type per mission and credits, targeting a
# combined value of 150 credits per 1-indexed route layer (200 if high-risk).  Starting workers,
# structures and nondeployable pseudo-units are never awarded.
_CREW_REWARD_NONCOMBAT = frozenset({
    'SCV', 'Drone', 'Probe',
})


def _crew_mission_reward_plan(ctx: Any) -> dict[int, dict[str, Any]]:
    if not crew_mode(ctx):
        return {}
    from .crew_catalog import preview_catalog
    from .crew_challenge import credit_cost
    from .crew_sc2_adapter import NATIVE_TYPES
    # Archipelago exposes mission locations via locations_for_mission_id();
    # mission_id_to_location_ids is absent in some AP versions. Using only
    # that optional dict caused every reward preview to say 'awaiting mapping'.
    mapping = dict(getattr(ctx, 'mission_id_to_location_ids', {}) or {})
    resolve = getattr(ctx, 'locations_for_mission_id', None)
    if callable(resolve):
        for mid in nodes(ctx):
            try:
                locs=tuple(resolve(int(mid)))
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            if locs:
                mapping[int(mid)] = locs
    if not mapping:
        return {}
    config = getattr(ctx, 'slay_config', {})
    races = tuple(str(r).casefold() for r in config.get('races', ['terran']))
    available = [u for u in preview_catalog(races)
                 if u.get('category') == 'unit'
                 and u['name'] not in _CREW_REWARD_NONCOMBAT
                 and u['name'] in NATIVE_TYPES
                 and float(u.get('supply', 0)) > 0]
    if not available:
        return {}
    graph = nodes(ctx)
    seed = str(config.get('run_seed', 0))
    result: dict[int, dict[str, Any]] = {}
    for raw_mid, raw_locs in sorted(mapping.items(), key=lambda x: str(x[0])):
        try:
            mid = int(raw_mid)
        except (TypeError, ValueError):
            continue
        if mid not in graph or not raw_locs:
            continue
        try:
            locs = sorted({int(x) for x in raw_locs if int(x) > 0})
        except (TypeError, ValueError):
            continue
        if not locs:
            continue
        layer = int(graph[mid].get('layer', 0)) + 1
        target = (200 if graph[mid].get('high_risk', False) else 150) * max(1, layer)
        race = str(graph[mid].get('race', '')).casefold()
        candidates = [u for u in available if u['race'] == race] or available
        rng = random.Random(int.from_bytes(hashlib.sha256(
            f'{seed}:crew-rewards:v2:{mid}'.encode()).digest()[:8], 'big'))
        rng.shuffle(locs)
        unit_count = (len(locs) + 1) // 2
        # Spend roughly half the mission budget on units.  Limit the chosen
        # type so each unit check can award at least one affordable copy.
        unit_budget = target if unit_count == len(locs) else target // 2
        affordable = [u for u in candidates
                      if 0 < credit_cost(int(u['minerals']), int(u['gas']),
                          unit_name=str(u['name'])) <= max(1, unit_budget // unit_count)]
        if not affordable:
            affordable = sorted(candidates, key=lambda u:(
                credit_cost(int(u['minerals']), int(u['gas']), unit_name=str(u['name'])),
                str(u['name'])))[:1]
        chosen = dict(rng.choice(affordable))
        price = max(1, credit_cost(int(chosen['minerals']), int(chosen['gas']),
                                   unit_name=str(chosen['name'])))
        # Share an integer number of copies across the unit checks; the
        # remaining budget goes to credits, with no negative credit prizes.
        copies_per = max(1, unit_budget // (unit_count * price))
        while copies_per > 1 and unit_count * copies_per * price > target:
            copies_per -= 1
        total_unit_value = unit_count * copies_per * price
        credit_locs = locs[unit_count:]
        remainder = max(0, target - total_unit_value)
        # If there are no credit checks, increase copies to approach target.
        if not credit_locs:
            copies_per = max(1, target // (unit_count * price))
            total_unit_value = unit_count * copies_per * price
            remainder = max(0, target - total_unit_value)
        for loc in locs[:unit_count]:
            result[loc] = {'kind':'unit', 'mission_id':mid, 'name':chosen['name'],
                           'race':chosen['race'], 'supply':chosen['supply'],
                           'quantity':copies_per, 'value':copies_per*price}
        for i, loc in enumerate(credit_locs):
            value = (remainder*(i+1))//len(credit_locs) - (remainder*i)//len(credit_locs)
            result[loc] = {'kind':'credits', 'mission_id':mid, 'credits':value}
    return result


def _crew_received_reward_locations(ctx: Any) -> set[int]:
    plan = _crew_mission_reward_plan(ctx)
    return {int(getattr(item,'location',0)) for item in getattr(ctx,'items_received',())
            if int(getattr(item,'location',0)) in plan}

def crew_sync_item_grants(ctx: Any) -> int:
    """Credit AP mission checks as deterministic Crew unit-copy awards.

    AP's original unit/upgrade items are suppressed for Crew; reward receipt
    IDs are durable and replay-safe, and credits derive from those receipts.
    """
    if not crew_mode(ctx) or not state_ready(ctx):
        return 0
    plan = _crew_mission_reward_plan(ctx)
    if not plan:
        return 0
    from .crew_challenge import acquire
    original = crew_roster(ctx)
    known = set(str(x) for x in original.get('award_receipts',()))
    updated = copy.deepcopy(original)
    added = 0
    for item in getattr(ctx,'items_received',()):
        try:
            loc = int(item.location)
            item_code = int(item.item)
            player = int(getattr(item,'player',0))
        except (TypeError, ValueError, AttributeError):
            continue
        reward = plan.get(loc)
        if reward is None or reward['kind'] != 'unit':
            continue
        key = f'{loc}:{item_code}:{player}'
        if key in known:
            continue
        ids = acquire(updated,name=reward['name'],race=reward['race'],
                      kind='unit',supply=reward['supply'],
                      quantity=reward['quantity'],purchases=False)
        active = updated.get('active_mission')
        if isinstance(active,dict):
            for identifier in ids:
                if identifier in active.get('pending',[]):
                    active['pending'].remove(identifier)
                active.setdefault('purchased_during_mission',[]).append(identifier)
        known.add(key)
        unlocked=set(updated.get('discovered_unit_unlocks',()))
        unlocked.add(reward['name'])
        updated['discovered_unit_unlocks']=sorted(unlocked)
        added += len(ids)
    if added:
        updated['award_receipts'] = sorted(known)
        state(ctx)['crew_roster'] = updated
        _persist_state(ctx)
    return added


def crew_adopt_live_units(ctx: Any, mission_id: int, *, player_id: int,
                          candidates: Any, reserved_wire_tags: Any = ()) -> int:
    """Persist valid, individually observed player-controlled units as Crew.

    This creates a roster copy from the real SC2 unit, not a spawn receipt.
    Existing paid/deployed units and pending native train completions are never
    adopted a second time. A discovered type stays unlocked even if it dies.
    """
    if not crew_mode(ctx) or not state_ready(ctx):return 0
    from .crew_catalog import preview_catalog
    from .crew_sc2_adapter import NATIVE_TYPES, CREW_MERCENARY_NATIVE
    from .crew_challenge import acquire, bind_unit_tag
    from .crew_tags import wire_tag
    from .crew_catalog import CREW_NOT_STANDARD_UNITS
    table=_item_table()
    allowed={}
    for row in preview_catalog(tuple(getattr(ctx,'slay_config',{}).get('races', ['terran']))):
        if row['category']!='unit' or row['name'] not in NATIVE_TYPES or row['name'] in CREW_NOT_STANDARD_UNITS:
            continue
        data=table.get(row['name'])
        if data is None or getattr(data,'code',None) is None:continue
        type_name=str(getattr(getattr(data,'type',None),'display_name',''))
        if (not _is_unit_or_morph_unlock_type(type_name)
                or _is_mercenary_unit(row['name'],data)
                or _is_deprecated_item(row['name'],data)
                or _is_nova_campaign_item(row['name'],data)
                or _is_royal_guard_item(row['name'],data,table)):
            continue
        allowed[NATIVE_TYPES[row['name']]]=row
    # Cutthroat and other campaign-controlled Mercenaries are valid physical
    # Crew copies even when Archipelago does not offer their contracts in Crew.
    # They must NOT unlock the excluded mercenary purchase/production catalog.
    for native,(name,supply) in CREW_MERCENARY_NATIVE.items():
        allowed[native]={"name":name,"race":"terran","supply":supply,
                         "captured_mercenary":True}
    if not allowed:return 0
    original=crew_roster(ctx)
    mission=original.get('active_mission') or {}
    if mission.get('mission_id')!=mission_id or not (mission.get('auto_transport') or {}).get('ended'):
        return 0
    if mission.get('terminal_snapshot') is not None:return 0
    updated=copy.deepcopy(original)
    active=updated['active_mission']
    known_tags={str(tag) for tag in active.get('tags',{})}
    starting_tags={str(tag) for tag in active.get('adopted_tags',())}
    blocked={int(tag) for tag in reserved_wire_tags}
    added=0
    for observation in candidates:
        if (observation.owner!=player_id or observation.is_structure or
                type(observation.tag) is not int or observation.tag<=0 or
                str(observation.tag) in known_tags or
                str(observation.tag) in starting_tags or
                wire_tag(observation.tag) in blocked):
            continue
        row=allowed.get(observation.native_type)
        if row is None:continue
        copy_id=acquire(updated,name=row['name'],race=row['race'],kind='unit',
                        supply=row['supply'],quantity=1,purchases=False)[0]
        bind_unit_tag(updated,copy_id,observation.tag)
        active.setdefault('adopted_tags',[]).append(str(observation.tag))
        active.setdefault('adopted_ids',[]).append(copy_id)
        if row.get('captured_mercenary'):
            # Physical roster copy only: no Crew shop/production entitlement.
            next(c for c in updated['copies'] if c['id']==copy_id)['captured_mercenary']=True
        else:
            discovered=set(updated.get('discovered_unit_unlocks',()))
            discovered.add(row['name'])
            updated['discovered_unit_unlocks']=sorted(discovered)
        known_tags.add(str(observation.tag));added+=1
    if added:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return added


def crew_inventory_groups(ctx: Any) -> list[dict[str, Any]]:
    crew_sync_item_grants(ctx)
    from .crew_challenge import deployment_zone_rows
    return deployment_zone_rows(crew_roster(ctx))


def crew_adjust_zone(ctx: Any,name:str,quantity:int,race:str|None=None) -> tuple[int,int]:
    from .crew_challenge import set_zone_quantity
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    ledger=crew_roster(ctx)
    # Atomic transaction: never persist half an adjustment after a failed supply check.
    replacement=copy.deepcopy(ledger)
    result=set_zone_quantity(replacement,name,quantity,race=race)
    state(ctx)['crew_roster']=replacement
    _persist_state(ctx)
    return result


def crew_purchase_roster_copy(ctx: Any, name: str, race: str, kind: str,
                              supply: float, mineral_cost: int, gas_cost: int,
                              quantity: int = 1) -> tuple[int, list[str]]:
    """Atomically buy one or five Crew copies at full catalog price each."""
    from .crew_challenge import purchase_copy
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    if type(quantity) is not int or quantity not in (1, 5):
        raise ValueError('Crew shop supports only Buy and Buy 5')
    # Validate against known costed entries; never trust price or type from UI.
    offers=crew_catalog_offers(ctx)
    candidates=[e for cat,rows in offers.items() for e in rows
                if e['name']==name and e['race']==race and e['category'] in ('unit','structure')]
    if len(candidates)!=1:
        raise ValueError('Crew offer not currently purchasable')
    record=candidates[0]
    expected_kind='unit' if record['category']=='unit' or name in {'SCV','Drone','Probe'} else 'structure'
    if (record['minerals']!=mineral_cost or record['gas']!=gas_cost
            or record['supply']!=supply or kind!=expected_kind):
        raise ValueError('Crew cost or kind differs from the catalog')
    replacement=copy.deepcopy(crew_roster(ctx))
    cost,ids=purchase_copy(replacement,name=name,race=race,kind=kind,supply=supply,
        minerals=mineral_cost,gas=gas_cost,credits_available=credits(ctx),
        quantity=quantity)
    s=state(ctx)
    s['crew_roster']=replacement
    s['spent']=int(s.get('spent',0))+cost
    _persist_state(ctx)
    _request_live_item_refresh(ctx)
    return cost,ids



# Crew's automatic receipt bridge is dormant until the protected live SC2
# adapter is finished. The game mode is still blocked at generation/launch.
def crew_abandon_interrupted_session(ctx: Any, *, verified_game_closed: bool=False) -> dict[str, int]:
    """Return surviving Crew actors to Reserves when a *different SC2 game*
    begins. Does not forgive a bank-confirmed in-mission death.
    """
    from .crew_challenge import abandon_interrupted_mission
    if not crew_mode(ctx):raise ValueError('Crew session reset outside Crew mode')
    updated=copy.deepcopy(crew_roster(ctx))
    result=abandon_interrupted_mission(updated, verified_game_closed=verified_game_closed)
    if updated!=state(ctx)['crew_roster']:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return result


def crew_begin_tracked_mission(ctx: Any, mission_id: int) -> list[dict[str, Any]]:
    """Stage a roster manifest without physically deploying or removing units."""
    from . import crew_challenge, crew_bridge
    from .crew_catalog import preview_catalog
    if not crew_mode(ctx):
        raise ValueError('Crew bridge is only available in Crew')
    replacement=copy.deepcopy(crew_roster(ctx))
    crew_challenge.begin_mission(replacement,mission_id)
    races=tuple(str(r).casefold() for r in ctx.slay_config.get('races',['terran']))
    instructions=crew_bridge.manifest(replacement,mission_id,preview_catalog(races))
    state(ctx)['crew_roster']=replacement
    _persist_state(ctx)
    return instructions


def crew_ensure_mission_staged(ctx: Any, mission_id: int) -> None:
    """Stage only the actual Crew SC2 mission, once, before the bot sends config.

    Choosing a mission in the GUI is not mission launch: the player must still
    be able to purchase/rearrange Crew copies until the SC2 session opens.
    A reconnect to the same mission preserves its deployment transaction,
    while a different mission cannot silently replace unresolved members.
    """
    if not crew_mode(ctx):
        return
    if not state_ready(ctx):
        raise RuntimeError('Crew roster cannot launch before run state is ready')
    roster=crew_roster(ctx)
    active=roster.get('active_mission')
    if active is not None:
        if active.get('mission_id')!=int(mission_id):
            # A newly launched SC2 mission is a distinct game. Stale tags
            # from an abandoned mission cannot authorize its production.
            crew_abandon_interrupted_session(ctx)
        else:
            return
    if str(int(mission_id)) in roster.get('settled_missions',{}):
        raise RuntimeError('Crew mission was already settled')
    crew_begin_tracked_mission(ctx,int(mission_id))


def crew_receive_deployment(ctx: Any, mission_id: int, *, copy_id: str,
                            tag: int, observed_name: str, observed_owner: int,
                            player_id: int, provenance: str) -> bool:
    """The future trusted SC2 adapter must provide every receipt explicitly."""
    from .crew_bridge import copy_and_apply, observe_receipt
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    updated, accepted=copy_and_apply(crew_roster(ctx),observe_receipt,mission_id,
        copy_id=copy_id,tag=tag,observed_name=observed_name,
        observed_owner=observed_owner,player_id=player_id,provenance=provenance)
    if accepted:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return accepted


def crew_automatic_deployment_plan(ctx: Any, mission_id: int) -> list[dict[str, Any]]:
    """Auto-order zone copies: bases/supply/production before owned units.

    Actual spawning and copy consumption still require trusted bank receipts;
    this method never writes deployed tags or manufactures ownership.
    """
    from .crew_auto import automatic_plan
    from .crew_sc2_adapter import NATIVE_TYPES
    from .crew_bridge import manifest
    from .crew_catalog import preview_catalog
    if not crew_mode(ctx):
        raise ValueError('Only Crew has automatic deployments')
    races=tuple(str(x).casefold() for x in ctx.slay_config.get('races',['terran']))
    rows=manifest(crew_roster(ctx),mission_id,preview_catalog(races))
    return automatic_plan(rows, NATIVE_TYPES)


def crew_initialize_auto_transport(ctx: Any, mission_id: int, player_id: int,
                                   starting_observations: Any = None) -> int:
    """Persist one random Crew session token before any chat command is sent.

    Reopening the same active mission reuses its durable token. A new token on
    a process restart could cause the Galaxy handler to create duplicate units.
    """
    import secrets
    from .crew_runtime import initialize
    if not crew_mode(ctx):
        raise ValueError('Only Crew may initialize auto deployment')
    replacement=copy.deepcopy(crew_roster(ctx))
    mission=replacement.get('active_mission')
    if not isinstance(mission,dict) or mission.get('mission_id')!=mission_id:
        raise ValueError('Crew mission must be staged before deploying')
    previous=mission.get('auto_transport')
    token=previous['token'] if previous is not None else secrets.randbelow(2**31-1)+1
    initialize(replacement,mission_id,token=token,player_id=player_id,
               starting_observations=starting_observations)
    if previous is None:
        state(ctx)['crew_roster']=replacement
        _persist_state(ctx)
    return token


def crew_activate_direct_session(ctx: Any, mission_id: int,
                                 token: int, player_id: int) -> bool:
    """Release Reserves after a matching Galaxy Ready bank acknowledgment.

    No native KEEP/REMOVE batch, automatic unit spawning or fake ownership.
    On-field identity remains receipt-only and map-provided assets are free,
    temporary, and never placed in the permanent roster automatically.
    """
    if not crew_mode(ctx):
        raise ValueError('Crew direct session requires Crew mode')
    ledger=crew_roster(ctx)
    active=ledger.get('active_mission')
    if not isinstance(active,dict) or active.get('mission_id')!=mission_id:
        raise ValueError('Crew direct session mission mismatch')
    session=active.get('auto_transport')
    if (not isinstance(session,dict) or session.get('token')!=token or
        session.get('player_id')!=player_id):
        raise ValueError('Crew direct session bank token/owner mismatch')
    if session.get('ended'):
        return False
    updated=copy.deepcopy(ledger)
    direct=updated['active_mission']['auto_transport']
    direct['ended']=True
    direct['native_done']=True
    direct['native_plan']=[]
    direct['native_pending']=None
    direct['end_requested']=False
    direct['pending']=None
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return True


def crew_propose_auto_command(ctx: Any, mission_id: int, *,
                              bank_status: Any, observations: Any,
                              base_established: bool, home_tag: int,
                              available_prerequisites: Any = (),
                              in_progress_prerequisites: Any = ()) -> str | None:
    """Persist intent to deploy BEFORE the client sends the resulting chat.

    This intentionally takes verified observations and a parsed SC2 bank
    status, not guessed unit types from the roster.
    """
    from .crew_runtime import propose
    if not crew_mode(ctx):
        raise ValueError('Only Crew may issue auto deployments')
    from .crew_catalog import preview_catalog
    races=tuple(str(r).casefold() for r in ctx.slay_config.get('races',['terran']))
    current=crew_roster(ctx)
    updated,command=propose(current,mission_id,preview_catalog(races),
        bank=bank_status,observations=observations,base_established=base_established,
        home_tag=home_tag,available_prerequisites=available_prerequisites,
        in_progress_prerequisites=in_progress_prerequisites)
    if updated != current:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return command


def crew_accept_auto_bank_receipt(ctx: Any, mission_id: int, *,
                                  receipt: Any, observations: Any) -> str:
    """Bind a bank-verified tag durably before emitting a Galaxy ACK."""
    from .crew_runtime import accept
    if not crew_mode(ctx):
        raise ValueError('Only Crew may accept auto deployment')
    updated,ack=accept(crew_roster(ctx),mission_id,
        receipt=receipt,observations=observations)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return ack


def crew_accept_auto_skip(ctx: Any, mission_id: int, *,
                          sequence: int, bank_status: Any) -> str:
    """Durably skip an SC2-confirmed unplaceable copy without spending it."""
    from .crew_runtime import accept_skip
    if not crew_mode(ctx):
        raise ValueError('Only Crew may skip placements')
    updated,ack=accept_skip(crew_roster(ctx),mission_id,
                            sequence=sequence,bank=bank_status)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return ack


def crew_accept_native_bank_receipt(ctx: Any, mission_id: int, *,
                                    receipt: Any, observations: Any) -> str:
    """Commit the post-base native keep/removal result before native ACK."""
    from .crew_runtime import accept_native
    if not crew_mode(ctx):raise ValueError('Not in Crew')
    updated,ack=accept_native(crew_roster(ctx),mission_id,
                              receipt=receipt,observations=observations)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return ack


def crew_propose_batch_command(ctx: Any, mission_id: int, *, bank_status: Any,
                               observations: Any,
                               available_prerequisites: Any = ()) -> str | None:
    """Durably stage an entire Crew native/spawn chunk before chat dispatch."""
    if not crew_mode(ctx):raise ValueError('Only Crew can batch deploy')
    from .crew_batch import step
    current=crew_roster(ctx)
    rows=crew_automatic_deployment_plan(ctx,mission_id)
    updated,command=step(current,mission_id,bank=bank_status,
                         observations=observations,catalog_rows=rows,
                         ready_prerequisites=available_prerequisites)
    if updated!=current:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return command


def crew_receive_unit_observation(ctx: Any, mission_id: int, *, tag: int,
                                  observed_name: str, owner: int, player_id: int,
                                  alive: bool, kills: int=0) -> bool:
    from .crew_bridge import copy_and_apply, record_observation
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    updated, accepted=copy_and_apply(crew_roster(ctx),record_observation,mission_id,
        tag=tag,observed_name=observed_name,owner=owner,
        player_id=player_id,alive=alive,kills=kills)
    if accepted:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return accepted


def crew_record_live_snapshot(ctx: Any, mission_id: int, *,
                              observations: Any, player_id: int) -> int:
    """Persist verified Crew observations without treating missing tags as dead."""
    from .crew_bridge import copy_and_apply, record_live_snapshot
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    old=crew_roster(ctx)
    updated,count=copy_and_apply(old,record_live_snapshot,mission_id,
                                  observations=observations,player_id=player_id)
    if updated!=old:
        state(ctx)['crew_roster']=updated
        _persist_state(ctx)
    return count


def crew_record_terminal_snapshot(ctx: Any, mission_id: int, *,
                                  observations: Any, player_id: int,
                                  victory_confirmed: bool, complete: bool,
                                  death_wire_tags=()) -> dict[str,int]:
    """Commit victory snapshot, cross-checking Galaxy Crew death receipts."""
    from .crew_bridge import copy_and_apply, record_terminal_snapshot
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    updated,outcome=copy_and_apply(crew_roster(ctx),record_terminal_snapshot,
        mission_id, observations=observations,player_id=player_id,
        victory_confirmed=victory_confirmed,complete=complete,
        death_wire_tags=death_wire_tags)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    return outcome


def crew_settle_tracked_victory(ctx: Any, mission_id: int, *,
                               victory_confirmed: bool,
                               terminal_snapshot_complete: bool) -> dict[str,int]:
    from .crew_bridge import copy_and_apply, settle_confirmed_victory
    if not crew_mode(ctx):
        raise ValueError('Not in Crew')
    updated, outcome=copy_and_apply(crew_roster(ctx),settle_confirmed_victory,mission_id,
        victory_confirmed=victory_confirmed,
        terminal_snapshot_complete=terminal_snapshot_complete)
    state(ctx)['crew_roster']=updated
    _persist_state(ctx)
    crew_charge_confirmed_building_losses(ctx)
    return outcome


def campaign_mode(ctx: Any) -> bool:
    return enabled(ctx) and str(getattr(ctx, "slay_config", {}).get("game_mode", "adventure")) == "campaign"


def _campaign_predecessors(graph: Mapping[int, dict[str, Any]]) -> dict[int, set[int]]:
    result = {mid: set() for mid in graph}
    for source, data in graph.items():
        for dest in data.get("next", []):
            if dest in result:
                result[dest].add(source)
    # A sparse Standard-style map can have optional branches which do not
    # lead directly to the final. Campaign's final needs ALL of those missions.
    if graph:
        final = max(graph, key=lambda mid: int(graph[mid].get("layer", -1)))
        if int(graph[final].get("layer", -1)) > 0 and not graph[final].get("next", []):
            result[final] = set(graph) - {final}
    return result


def chosen_path(ctx: Any) -> list[int]:
    if endless_mode(ctx):
        selected = state(ctx).get("endless", {}).get("selected")
        return [] if selected is None else [int(selected)]

    valid = nodes(ctx)

    return [mid for mid in state(ctx).get("chosen", []) if mid in valid]





def completed_mission_ids(ctx: Any) -> set[int]:
    if endless_mode(ctx):
        return set(range(-len(state(ctx).get("endless", {}).get("history", [])), 0))







    checked = getattr(ctx, "checked_locations", ())

    missing = getattr(ctx, "missing_locations", ())









    explicit_completed = getattr(ctx, "completed", None)

    signature = (id(checked), len(checked), id(missing), len(missing))

    if isinstance(explicit_completed, (set, frozenset, list, tuple)):

        signature += (id(explicit_completed), len(explicit_completed))

    if getattr(ctx, "slay_completed_missions_signature", None) == signature:

        cached = getattr(ctx, "slay_completed_missions_cache", None)

        if cached is not None:

            return set(cached)

    result = {mid for mid in nodes(ctx) if ctx.is_mission_completed(mid)}

    ctx.slay_completed_missions_signature = signature

    ctx.slay_completed_missions_cache = frozenset(result)

    return result





def victory_count(ctx: Any) -> int:

    return len(completed_mission_ids(ctx))



def _initial_nodes(ctx: Any) -> list[int]:

    return sorted(mid for mid, data in nodes(ctx).items() if int(data.get("layer", 0)) == 0)







def _raw_frontier(ctx: Any) -> list[int]:
    if endless_mode(ctx) and state_ready(ctx):
        progress = state(ctx)["endless"]
        return [int(progress["selected"])] if progress["selected"] is not None else [int(n["mission_id"]) for n in progress["choices"]]



    if not enabled(ctx) or not state_ready(ctx):

        return []

    if campaign_mode(ctx):
        graph = nodes(ctx)
        completed = completed_mission_ids(ctx)
        predecessors = _campaign_predecessors(graph)
        return sorted(mid for mid in graph if mid not in completed and predecessors[mid] <= completed)

    path = chosen_path(ctx)

    if not path:

        return _initial_nodes(ctx)

    last = path[-1]

    if not ctx.is_mission_completed(last):

        return [last]

    data = node(ctx, last)

    if data is None:

        return []

    return [mid for mid in data.get("next", []) if mid in nodes(ctx) and not ctx.is_mission_completed(mid)]





def sync_commit_from_checks(ctx: Any) -> bool:
    if endless_mode(ctx) or campaign_mode(ctx):
        return False













    if not enabled(ctx) or not state_ready(ctx):

        return False

    path = chosen_path(ctx)



    if path and not ctx.is_mission_completed(path[-1]):

        return False



    checked = set(getattr(ctx, "checked_locations", set()))

    if not checked:

        return False

    candidates = _raw_frontier(ctx)

    touched: list[tuple[int, int]] = []

    mapping = getattr(ctx, "mission_id_to_location_ids", {})

    for mission_id in candidates:

        locs = set(mapping.get(int(mission_id), []))

        count = len(locs & checked)

        if count:

            touched.append((count, int(mission_id)))

    if not touched:

        return False







    touched.sort(key=lambda pair: (-pair[0], pair[1]))

    mission_id = touched[0][1]

    s = state(ctx)

    path = list(s.get("chosen", []))

    if not path or path[-1] != mission_id:

        path.append(mission_id)

        s["chosen"] = path

        _persist_state(ctx)

        logger.info(

            "Slay route committed to mission %s because a location in that mission was checked.",

            mission_id,

        )

        if len(touched) > 1:

            logger.warning(

                "Multiple sibling Slay missions already had checks (%s); committed to %s.",

                [mid for _, mid in touched], mission_id,

            )

        return True

    return False





def current_frontier(ctx: Any) -> list[int]:



    sync_commit_from_checks(ctx)

    return _raw_frontier(ctx)





def _reachable_from(ctx: Any, starts: Iterable[int]) -> set[int]:

    graph = nodes(ctx)

    pending = list(dict.fromkeys(int(x) for x in starts if int(x) in graph))

    seen: set[int] = set()



    max_steps = max(1, len(graph) * 4)

    steps = 0

    while pending and steps < max_steps:

        cur = pending.pop()

        steps += 1

        if cur in seen:

            continue

        seen.add(cur)

        for nxt in graph[cur].get("next", []):

            if nxt in graph and nxt not in seen:

                pending.append(nxt)

    if pending:

        logger.warning("Slay graph traversal hit safety bound; generated graph may contain a malformed cycle.")

    return seen





def _stable_commander_choice(run_seed: int, mission_id: int) -> tuple[int, str]:



    digest = hashlib.sha256(f"{int(run_seed)}:commander:{int(mission_id)}".encode("utf-8")).digest()

    index = COMMANDER_GENERATED_INDICES[

        int.from_bytes(digest[:8], "big") % len(COMMANDER_GENERATED_INDICES)

    ]

    return index, COMMANDER_HERO_NAMES[index]





def commander_hero_index(ctx: Any, mission_id: int) -> int:

    data = node(ctx, int(mission_id)) or {}

    try:

        index = int(data.get("commander_hero_index", -1))

    except Exception:

        index = -1

    if index in COMMANDER_HERO_NAMES:

        return index









    if "general" in data.get("blessings", []):

        try:

            run_seed = int(getattr(ctx, "slay_config", {}).get("run_seed", 0))

            recovered_index, _name = _stable_commander_choice(run_seed, int(mission_id))

            return recovered_index

        except Exception:

            pass

    return -1



def _mission_effect_name(ctx: Any, mission_id: int, effect_id: str) -> str:

    if effect_id == "general":

        idx = commander_hero_index(ctx, mission_id)

        if idx >= 0:

            return f"{COMMANDER_HERO_NAMES[idx]} Commander"

    return EFFECT_DISPLAY_NAMES.get(effect_id, effect_id)



def crew_effect_description(effect_id: str, kind: str | None = None) -> str | None:
    """XLSX Crew-only text, leaving Standard descriptions unchanged."""
    global _CREW_EFFECT_DESCRIPTIONS
    try:
        cache=_CREW_EFFECT_DESCRIPTIONS
    except NameError:
        try:
            _CREW_EFFECT_DESCRIPTIONS=json.loads(Path(__file__).with_name('crew_effects.json').read_text('utf8'))
        except (OSError,ValueError):
            _CREW_EFFECT_DESCRIPTIONS={}
        cache=_CREW_EFFECT_DESCRIPTIONS
    kinds=(kind,) if kind in ('mutation','blessing') else ('mutation','blessing')
    for k in kinds:
        row=cache.get(k,{}).get(effect_id)
        if isinstance(row,dict) and row.get('description'):
            return str(row['description'])
    return None


def _mission_effect_description(ctx: Any, mission_id: int, effect_id: str) -> str:

    if effect_id == "general":

        idx = commander_hero_index(ctx, mission_id)

        if idx >= 0:

            return (f"You gain {COMMANDER_HERO_NAMES[idx]}. They do not respawn." if crew_mode(ctx)
                    else f"You gain {COMMANDER_HERO_NAMES[idx]}. They respawn 60 seconds after dying.")

    original=EFFECT_DESCRIPTIONS.get(effect_id, "")
    if crew_mode(ctx):
        m=node(ctx,mission_id) or {}
        effect_kind=('blessing' if effect_id in (m.get('blessings') or ())
                     else 'mutation')
        override=crew_effect_description(effect_id,effect_kind)
        if override:return override
    if crew_mode(ctx) and effect_id=="miras_mercenaries":
        return original.rstrip(". ") + " for this mission only."
    return original





def node_status(ctx: Any, mission_id: int) -> str:
    if endless_mode(ctx) and state_ready(ctx):
        if int(mission_id) < 0: return "completed"
        progress = state(ctx)["endless"]
        if progress["selected"] == int(mission_id): return "selected"
        return "available" if int(mission_id) in current_frontier(ctx) else "abandoned"

    mission_id = int(mission_id)

    if not enabled(ctx) or mission_id not in nodes(ctx):

        return "normal"

    if not state_ready(ctx):

        return "loading"

    if ctx.is_mission_completed(mission_id):

        return "completed"

    frontier = current_frontier(ctx)
    if campaign_mode(ctx):
        if mission_id in frontier:
            selected = state(ctx).get("chosen", [])
            return "selected" if selected and int(selected[-1]) == mission_id else "available"
        return "future"

    path = chosen_path(ctx)

    if path and mission_id == path[-1] and not ctx.is_mission_completed(path[-1]):

        return "selected"

    if mission_id in frontier:

        return "available"

    if not path:

        return "future"

    last = path[-1]

    reachable_starts = [last] if not ctx.is_mission_completed(last) else nodes(ctx).get(last, {}).get("next", [])

    reachable = _reachable_from(ctx, reachable_starts)

    return "future" if mission_id in reachable else "abandoned"





def can_launch(ctx: Any, mission_id: int) -> bool:

    if not enabled(ctx):

        return True

    mission_id = int(mission_id)

    if not state_ready(ctx):

        logger.info("Slay run state is still loading from the local server; try again in a moment.")

        return False

    if mission_id not in nodes(ctx):

        return False

    if ctx.is_mission_completed(mission_id):

        logger.info("Slay rule: completed missions are permanently closed.")

        return False

    return mission_id in current_frontier(ctx)





def _normalize_test_effect_token(value: str) -> str:

    return re.sub(r"[^a-z0-9]", "", str(value).casefold())





def _test_effect_aliases() -> dict[str, list[str]]:

    aliases: dict[str, list[str]] = {}

    for effect_id in EFFECT_BANK_BITS:

        candidates = {

            _normalize_test_effect_token(effect_id),

            _normalize_test_effect_token(EFFECT_DISPLAY_NAMES.get(effect_id, effect_id)),

        }

        if effect_id.endswith("_blessing"):

            candidates.add(_normalize_test_effect_token(effect_id.removesuffix("_blessing") + "blessing"))

        if effect_id.endswith("_mutation"):

            candidates.add(_normalize_test_effect_token(effect_id.removesuffix("_mutation") + "mutation"))

        for alias in candidates:

            if alias:

                aliases.setdefault(alias, []).append(effect_id)

    return aliases





def _current_unfinished_test_mission(ctx: Any) -> int | None:

    path = chosen_path(ctx)

    if not path:

        return None

    mission_id = int(path[-1])

    if ctx.is_mission_completed(mission_id):

        return None

    return mission_id





def _test_override_for_mission(ctx: Any, mission_id: int) -> dict[str, Any]:

    if not enabled(ctx) or not state_ready(ctx):

        return {"clear": False, "effects": []}

    overrides = state(ctx).get("test_mission_overrides", {})

    if not isinstance(overrides, Mapping):

        return {"clear": False, "effects": []}

    raw = overrides.get(str(int(mission_id)), overrides.get(int(mission_id), {}))

    if not isinstance(raw, Mapping):

        return {"clear": False, "effects": []}

    raw_effects = raw.get("effects", [])

    effects = []

    if isinstance(raw_effects, Sequence) and not isinstance(raw_effects, (str, bytes)):

        effects = list(dict.fromkeys(str(x) for x in raw_effects if str(x) in EFFECT_BANK_BITS))

    return {"clear": bool(raw.get("clear", False)), "effects": effects}





def _apply_test_effect_override(ctx: Any, mission_id: int, queued: list[str], clear: bool) -> None:



    s = state(ctx)

    overrides = dict(s.get("test_mission_overrides", {}))

    key = str(int(mission_id))

    existing = overrides.get(key, {})

    existing = dict(existing) if isinstance(existing, Mapping) else {}

    effects = [] if clear else [str(x) for x in existing.get("effects", []) if str(x) in EFFECT_BANK_BITS]

    for effect_id in queued:

        if effect_id in EFFECT_BANK_BITS and effect_id not in effects:

            effects.append(effect_id)

    overrides[key] = {

        "clear": bool(clear or existing.get("clear", False)),

        "effects": effects,

    }

    s["test_mission_overrides"] = overrides





def queue_test_effect(ctx: Any, raw_name: str) -> tuple[bool, str]:



    if not enabled(ctx) or not state_ready(ctx):

        return False, "Slay test commands require an active Slay run with loaded state."

    token = _normalize_test_effect_token(raw_name)

    if not token:

        return False, "Usage: /addtest effectname (lowercase/no spaces is fine)."

    matches = list(dict.fromkeys(_test_effect_aliases().get(token, [])))

    if not matches:

        return False, "Unknown Slay effect: " + raw_name

    if len(matches) > 1:

        options = ", ".join(_normalize_test_effect_token(x) for x in matches)

        return False, "Ambiguous effect name. Use one of: " + options

    effect_id = matches[0]

    kind = "Blessing" if effect_id in BLESSING_SEVERITY else "Mutation"

    current_mission = _current_unfinished_test_mission(ctx)

    if current_mission is not None:

        _apply_test_effect_override(ctx, current_mission, [effect_id], False)

        _persist_state(ctx)

        return True, (

            f"Forced {kind} {EFFECT_DISPLAY_NAMES.get(effect_id, effect_id)} onto the currently selected mission. "

            "Relaunch/retry the mission for the change to take effect."

        )

    queued = list(state(ctx).get("test_effects_next", []))

    if effect_id not in queued:

        queued.append(effect_id)

    state(ctx)["test_effects_next"] = queued

    _persist_state(ctx)

    return True, f"Queued {kind} {EFFECT_DISPLAY_NAMES.get(effect_id, effect_id)} for the next mission you select."





def queue_test_clear(ctx: Any) -> tuple[bool, str]:



    if not enabled(ctx) or not state_ready(ctx):

        return False, "Slay test commands require an active Slay run with loaded state."

    current_mission = _current_unfinished_test_mission(ctx)

    if current_mission is not None:

        _apply_test_effect_override(ctx, current_mission, [], True)

        state(ctx)["test_effects_next"] = []

        state(ctx)["test_clear_next"] = False

        _persist_state(ctx)

        return True, "Cleared all Blessings and Mutations from the currently selected mission. Relaunch/retry it for the change to take effect."

    state(ctx)["test_clear_next"] = True

    _persist_state(ctx)

    return True, "The next mission you select will have its generated Blessings and Mutations removed. Queued /addtest effects will still be added."





def cancel_test_overrides(ctx: Any) -> tuple[bool, str]:



    if not enabled(ctx) or not state_ready(ctx):

        return False, "Slay test commands require an active Slay run with loaded state."

    state(ctx)["test_effects_next"] = []

    state(ctx)["test_clear_next"] = False

    _persist_state(ctx)

    return True, "Pending next-mission Slay test overrides cleared."





def _consume_test_overrides_for_mission(ctx: Any, mission_id: int) -> None:

    s = state(ctx)

    queued = [str(x) for x in s.get("test_effects_next", []) if str(x) in EFFECT_BANK_BITS]

    clear = bool(s.get("test_clear_next", False))

    if not queued and not clear:

        return

    _apply_test_effect_override(ctx, mission_id, queued, clear)

    s["test_effects_next"] = []

    s["test_clear_next"] = False

    _persist_state(ctx)

    forced = [EFFECT_DISPLAY_NAMES.get(x, x) for x in queued]

    if clear and forced:

        _chat(ctx, "[Slay Test] Cleared generated effects; forced: " + ", ".join(forced))

    elif clear:

        _chat(ctx, "[Slay Test] Cleared all Blessings and Mutations for this mission.")

    elif forced:

        _chat(ctx, "[Slay Test] Forced onto this mission: " + ", ".join(forced))





def queue_godmode(ctx: Any) -> tuple[bool, str]:



    if not enabled(ctx) or not state_ready(ctx):

        return False, "Slay /godmode requires an active Slay run with loaded state."

    s = state(ctx)

    s["godmode_next"] = True

    s["godmode_mission_id"] = -1

    _persist_state(ctx)

    return True, "Slay /godmode armed: the next mission you select gets effectively unlimited minerals, gas, and build/train speed."





def _arm_godmode_for_mission(ctx: Any, mission_id: int) -> None:

    s = state(ctx)

    if not bool(s.get("godmode_next", False)):

        return

    s["godmode_next"] = False

    s["godmode_mission_id"] = int(mission_id)

    _persist_state(ctx)

    _chat(ctx, f"[Slay Test] GODMODE active for {nodes(ctx).get(int(mission_id), {}).get('mission_name', mission_id)}.")





def godmode_for_mission(ctx: Any, mission_id: int) -> int:

    if not enabled(ctx) or not state_ready(ctx):

        return 0

    try:

        return 1 if int(state(ctx).get("godmode_mission_id", -1)) == int(mission_id) else 0

    except (TypeError, ValueError):

        return 0





def queue_auto_victory(ctx: Any) -> tuple[bool, str]:



    if not enabled(ctx) or not state_ready(ctx):

        return False, "Slay /victory requires an active Slay run with loaded state."

    state(ctx)["auto_victory_next"] = True

    _persist_state(ctx)

    return True, "Slay /victory armed: the next mission you select will be completed with all of its locations checked."





def _consume_auto_victory_for_mission(ctx: Any, mission_id: int) -> None:

    s = state(ctx)

    if not bool(s.get("auto_victory_next", False)):

        return

    s["auto_victory_next"] = False

    _persist_state(ctx)







    locations = [int(x) for x in ctx.locations_for_mission_id(int(mission_id))]

    if locations:

        async_start(ctx.send_msgs([{"cmd": "LocationChecks", "locations": sorted(locations)}]), name="Slay /victory location checks")

    ctx.slay_auto_victory_skip_mission = int(mission_id)

    mission_label = str(nodes(ctx).get(int(mission_id), {}).get("mission_name", f"Mission {mission_id}"))

    _chat(ctx, f"[Slay] /victory completed {mission_label} and checked all {len(locations)} mission locations.")





def consume_auto_victory_skip(ctx: Any, mission_id: int) -> bool:



    queued = getattr(ctx, "slay_auto_victory_skip_mission", None)

    if queued is None or int(queued) != int(mission_id):

        return False

    ctx.slay_auto_victory_skip_mission = None

    return True





def commit_mission(ctx: Any, mission_id: int) -> bool:
    if endless_mode(ctx):
        mission_id = int(mission_id)
        if not can_launch(ctx, mission_id): return False
        progress = state(ctx)["endless"]
        fresh = progress["selected"] is None
        progress["selected"] = mission_id
        ctx.difficulty_override = int((node(ctx, mission_id) or {}).get("difficulty_override", 0))
        _arm_godmode_for_mission(ctx, mission_id)
        if fresh:
            if int(state(ctx).get("saving_grace_charges", 0)) > 0: _assign_saving_grace(ctx, mission_id)
            if int(state(ctx).get("risky_investment_charges", 0)) > 0: _assign_risky_investment(ctx, mission_id)
            _consume_test_overrides_for_mission(ctx, mission_id)
        state(ctx)["chosen"] = [mission_id]
        _persist_state(ctx)
        _consume_auto_victory_for_mission(ctx, mission_id)
        return True



    if not enabled(ctx):

        return True

    mission_id = int(mission_id)

    if not can_launch(ctx, mission_id):

        return False

    _arm_godmode_for_mission(ctx, mission_id)
    if campaign_mode(ctx):
        s = state(ctx)
        fresh = not s.get("chosen") or int(s["chosen"][-1]) != mission_id
        if fresh:
            if int(s.get("saving_grace_charges", 0)) > 0 and str(mission_id) not in s.get("temporary_blessings", {}):
                _assign_saving_grace(ctx, mission_id)
            if int(state(ctx).get("risky_investment_charges", 0)) > 0:
                _assign_risky_investment(ctx, mission_id)
            _consume_test_overrides_for_mission(ctx, mission_id)
        state(ctx)["chosen"] = [mission_id]
        _persist_state(ctx)
        _consume_auto_victory_for_mission(ctx, mission_id)
        return True

    s = state(ctx)

    path = list(s.get("chosen", []))

    if int(s.get("saving_grace_charges", 0)) > 0 and str(mission_id) not in s.get("temporary_blessings", {}):

        _assign_saving_grace(ctx, mission_id)

        s = state(ctx)

    if int(s.get("risky_investment_charges",0)) > 0:

        _assign_risky_investment(ctx, mission_id); s=state(ctx)

    if path and path[-1] == mission_id:

        _consume_auto_victory_for_mission(ctx, mission_id)

        return True

    if mission_id in path:

        return False

    _consume_test_overrides_for_mission(ctx, mission_id)

    s = state(ctx)

    path = list(s.get("chosen", []))

    path.append(mission_id)

    s["chosen"] = path

    _persist_state(ctx)

    _consume_auto_victory_for_mission(ctx, mission_id)

    return True







def _mission_base_name(value: Any) -> str:



    name = str(value or "").strip()

    for suffix in (" (Terran)", " (Zerg)", " (Protoss)"):

        if name.endswith(suffix):

            return name[:-len(suffix)].strip()

    return name







def _blessing_allowed_for_mission(ctx: Any, mission_id: int, effect: str) -> bool:









    data = node(ctx, int(mission_id)) or {}

    effect = str(effect)

    mission_tier = max(1, int(data.get("mission_pool", 0)) + 1)

    is_lotv = bool(data.get("lotv", False))

    mission_name = _mission_base_name(data.get("mission_name", ""))

    if effect in {"spear_of_adun_blessing", "spear_of_adun_overcharge", "inflatable_soldiers"}:

        return False

    if mission_name.casefold() in DEPENDENCY_SENSITIVE_MISSIONS and effect in SWARM_DEPENDENCY_BLESSINGS:

        return False
    if mission_name.casefold() in GORGON_MISSION_EXCLUSIONS and effect == "another_gorgon_blessing":
        return False


    if effect == "rich_minerals" and mission_name == "Devil's Playground":

        return False

    if effect in {"stealth_tunnels", "infinite_larva"}:

        return str(data.get("race", "")).casefold() == "zerg"

    if effect == "rapid_repair":

        return str(data.get("race", "")).casefold() == "terran"
    if effect == "covert_assistance" and mission_name.casefold() in ISLAND_MISSION_NAMES:
        return False

    return True





CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS = frozenset({
    "conga_line", "nexus_shield", "nuclear_structures",
    "drakken_laser_drill_enemy", "heavily_defended_drakken_laser_drill", "point_defense_drones", "hybrid_research", "purifier", "golden_armada",
    "true_golden_armada", "tower_defense", "heroes_of_the_storm",
    "viking_raids", "drop_pods", "dark_templar", "another_gorgon_mutation",
    "taldarim_reinforcements", "zagaras_banelings", "dehakas_pack",
    "torrasque", "marauder_kill_teams", "tosh_and_his_boys", "jetpacks",
    "brakk_primal_army", "odin_delayed_assault", "hellion_run_by",
    "diamondback_wanderers", "raynors_raiders", "leviathan_outside_base",
    "enemy_spear_of_adun", "combined_raids",
})



def _mutation_allowed_for_mission(ctx: Any, mission_id: int, effect: str) -> bool:



    if effect in DISABLED_MUTATIONS:
        return False

    data = node(ctx, int(mission_id)) or {}

    mission_name = _mission_base_name(data.get("mission_name", ""))









    if effect == "burrowed_zerglings" and str(mission_name).startswith("Rak'Shir"):

        return False
    if mission_name.casefold() in GORGON_MISSION_EXCLUSIONS and effect == "another_gorgon_mutation":
        return False
    if mission_name.casefold().startswith("smash and grab") and effect == "nexus_shield":
        return False
    if effect == "point_defense_drones" and bool(data.get("timed_defense", False)):
        return False
    if effect == "hybrid_research" and bool(data.get("timed_defense", False)):
        return False
    if effect == "nydus_worms" and mission_name.casefold().startswith("templar's charge"):
        return False
    if mission_name.casefold().startswith("the crucible") and effect in CRUCIBLE_ENEMY_STRUCTURE_MUTATIONS:
        return False


    if mission_name.casefold() in ISLAND_MISSION_NAMES and effect in {"ten_minutes_until_destruction", "hellion_run_by", "odin_delayed_assault", "combined_raids", "brakk_primal_army", "tosh_and_his_boys"}:

        return False

    if mission_name.casefold() in DEPENDENCY_SENSITIVE_MISSIONS and effect in (SWARM_DEPENDENCY_MUTATIONS | VOID_DEPENDENCY_MUTATIONS):

        return False

    return True





def _chaos_blessings_for_mission(ctx: Any, mission_id: int, already: Sequence[str]) -> list[str]:



    if "boon_chaos_blessings" not in _permanent_boon_effects(ctx):

        return []

    data = node(ctx, int(mission_id)) or {}

    forbidden = set(str(x) for x in already)



    muts = set(str(x) for x in data.get("mutators", []))

    if "squishy" in muts:

        forbidden.update({"juggernaut", "elite_soldiers", "fortifications"})

    pool = [

        effect for effect in BLESSING_SEVERITY

        if effect not in forbidden and _blessing_allowed_for_mission(ctx, mission_id, effect)

    ]

    seed_material = f"{ctx.slay_config.get('run_seed',0)}:chaos-blessings:{int(mission_id)}".encode("utf-8")

    rng = random.Random(int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big"))

    rng.shuffle(pool)



    def rec(index: int, remain: int, chosen: list[str]) -> list[str] | None:

        if remain == 0:

            return list(chosen)

        if remain < 0:

            return None

        for j in range(index, len(pool)):

            effect = pool[j]

            sev = int(BLESSING_SEVERITY[effect])

            if sev <= remain:

                result = rec(j + 1, remain - sev, chosen + [effect])

                if result is not None:

                    return result

        return None



    return rec(0, 5, []) or []





def apply_spear_options(ctx: Any, mission_id: int, soa_options: int) -> int:















    result = int(soa_options) & ~0b111111

    if _progression_owned(ctx, SPEAR_UNLOCK):

        result |= 0b111111

    return result





def _normalize_kerrigan_context(ctx: Any) -> None:















    if not _progression_owned(ctx, KERRIGAN_UNLOCK):

        return

    if hasattr(ctx, "kerrigan_presence"):

        try:





            ctx.kerrigan_presence = 0

        except Exception:

            pass

    if hasattr(ctx, "kerrigan_primal_status"):

        try:







            ctx.kerrigan_primal_status = 1

        except Exception:

            pass

    for attr, value in (

        ("kerrigan_total_level_cap", -1),

        ("kerrigan_max_active_abilities", 12),

        ("kerrigan_max_passive_abilities", 5),

    ):

        if hasattr(ctx, attr):

            try:

                setattr(ctx, attr, value)

            except Exception:

                pass





def apply_purchased_kerrigan_tech(ctx: Any, zerg_items: Any) -> list[int]:















    try:

        result = [int(x) for x in zerg_items]

    except Exception:

        return list(zerg_items) if zerg_items is not None else []

    if len(result) < 10 or not enabled(ctx) or not state_ready(ctx):

        return result

    if not _progression_owned(ctx, KERRIGAN_UNLOCK):

        return result



    _normalize_kerrigan_context(ctx)

    table = _item_table()

    for item_name, bought_raw in state(ctx).get("purchases", {}).items():

        if int(bought_raw) <= 0:

            continue

        data = table.get(str(item_name))

        if data is None or not _is_kerrigan_item(str(item_name), data):

            continue

        type_name = str(getattr(getattr(data, "type", None), "display_name", "")).strip().casefold()

        try:

            number = int(getattr(data, "number"))

        except Exception:

            continue

        if number < 0 or number >= 63:

            continue

        if type_name in {"ability", "kerrigan ability"}:

            result[0] |= 1 << number

        elif type_name == "evolution pit":

            result[9] |= 1 << number

    return result





def prepare_kerrigan_options(ctx: Any) -> None:

    """Normalize Kerrigan state before Archipelago packs mission options.

    Archipelago calculates the Kerrigan mission option bitfield from the context's
    presence/primal-status fields. Slay must restore the purchased global Kerrigan
    state before that calculation, not only after it.
    """
    _normalize_kerrigan_context(ctx)



def apply_kerrigan_options(ctx: Any, mission_id: int, kerrigan_options: int) -> int:



    result = int(kerrigan_options)

    if _progression_owned(ctx, KERRIGAN_UNLOCK):

        _normalize_kerrigan_context(ctx)

        result |= 1 << 0

    return result





def _effective_blessings(ctx: Any, mission_id: int) -> list[str]:

    data = node(ctx, int(mission_id)) or {}

    test_override = _test_override_for_mission(ctx, mission_id)

    result = [] if test_override["clear"] else list(data.get("blessings", []))

    result.extend(x for x in test_override["effects"] if x in BLESSING_SEVERITY)

    if enabled(ctx) and state_ready(ctx):

        result.extend(str(x) for x in state(ctx).get("permanent_blessings", []) if str(x) not in {"spear_of_adun_blessing", "spear_of_adun_overcharge", "inflatable_soldiers"})

        temp = state(ctx).get("temporary_blessings", {})

        if isinstance(temp, Mapping):

            result.extend(str(x) for x in temp.get(str(int(mission_id)), temp.get(int(mission_id), [])))

    result = list(dict.fromkeys(x for x in result if x in EFFECT_BANK_BITS and _blessing_allowed_for_mission(ctx, mission_id, x)))

    result.extend(_chaos_blessings_for_mission(ctx, mission_id, result))

    return list(dict.fromkeys(result))





def _effective_mutations(ctx: Any, mission_id: int) -> list[str]:

    data = node(ctx, int(mission_id)) or {}

    test_override = _test_override_for_mission(ctx, mission_id)

    result = [] if test_override["clear"] else list(data.get("mutators", []))

    result.extend(x for x in test_override["effects"] if x not in BLESSING_SEVERITY)

    if enabled(ctx) and state_ready(ctx):

        result.extend(str(x) for x in state(ctx).get("permanent_mutations", []))

    return list(dict.fromkeys(x for x in result if x in EFFECT_BANK_BITS and _mutation_allowed_for_mission(ctx, mission_id, x)))





def dependency_variant_for_mission(ctx: Any, mission_id: int) -> str:













    if not enabled(ctx):

        return "base"

    data = node(ctx, int(mission_id)) or {}

    mission_name = _mission_base_name(data.get("mission_name", "")).casefold()

    if mission_name in DEPENDENCY_SENSITIVE_MISSIONS and not _progression_owned(ctx, KERRIGAN_UNLOCK):

        return "base"

    mutations = set(_effective_mutations(ctx, mission_id))

    blessings = set(_effective_blessings(ctx, mission_id))

    campaign = str(data.get("campaign", ""))

    need_swarm = bool(mutations & SWARM_DEPENDENCY_MUTATIONS or blessings & SWARM_DEPENDENCY_BLESSINGS)

    # K5Kerrigan needs the Swarm and SwarmStory catalogs on non-HotS campaigns
    # too. In particular Archipelago classifies A Sinister Turn under Prophecy,
    # so the old Wings-of-Liberty-only check missed it. HotS maps already load
    # Swarm natively; every other campaign gets the explicit Swarm variant while
    # Kerrigan is unlocked. This intentionally includes Safe Haven/Haven's Fall.
    if campaign != "Heart of the Swarm" and _progression_owned(ctx, KERRIGAN_UNLOCK):
        need_swarm = True

    # The General boon uses campaign hero "ZaGara" (not "Zagara").
    # Its unit catalog lives in the HotS data and must be explicitly loaded
    # when selected on a Terran, Protoss, or other non-HotS map.
    if "general" in blessings and commander_hero_index(ctx, mission_id) == 18:
        need_swarm = True













    try:

        owned_counts = _logic_owned_item_counts(ctx)

        if any(int(owned_counts.get(name, 0)) > 0 for name in ZERG_MERCENARY_ITEMS):

            need_swarm = True









        if any(int(count) > 0 and "hellbat" in str(name).casefold() for name, count in owned_counts.items()):

            need_swarm = True

    except Exception:

        pass

    need_void = bool(mutations & VOID_DEPENDENCY_MUTATIONS)

    # ArtanisVoid is the controllable ground hero in Legacy of the Void;
    # bare Artanis is the unrelated Wings of Liberty mothership. Artanis must
    # request the Void campaign catalog just like Alarak and Vorazun, otherwise
    # his catalog entry is absent on WoL/HotS maps and the Galaxy commander
    # selector used to fall through to a random hero (sometimes Urun).
    # Respect the sensitive Haven dependency restriction above.
    if "general" in blessings and commander_hero_index(ctx, mission_id) in {9, 10, 30}:
        need_void = True











    if campaign == "Heart of the Swarm" and "specialists" not in blessings:

        need_swarm = False

    if campaign in VOID_NATIVE_CAMPAIGNS:

        need_void = False

    if need_swarm and need_void:

        return "swarm_void"

    if need_swarm:

        return "swarm"

    if need_void:

        return "void"

    return "base"





def _dependency_variant_paths() -> tuple[Path, Path, Path]:

    root = _archipelago_root() / DEPENDENCY_VARIANT_DIR_NAME

    config_path = root / "config.json"

    if not config_path.is_file():

        raise RuntimeError(f"Slay dependency variant config is missing: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    info = Path(str(config.get("target_document_info", "")))

    header = Path(str(config.get("target_document_header", "")))

    if not str(info) or not str(header):

        raise RuntimeError("Slay dependency variant config has no target DocumentInfo/DocumentHeader paths")

    return root, info, header





def _atomic_replace_bytes(path: Path, payload: bytes) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    temp = path.with_name(path.name + ".slaytmp")

    temp.write_bytes(payload)

    os.replace(temp, path)





def prepare_dependency_variant(ctx: Any, mission_id: int) -> str:















    variant = dependency_variant_for_mission(ctx, mission_id)

    root, target_info, target_header = _dependency_variant_paths()

    source_info = root / f"{variant}.DocumentInfo"

    source_header = root / f"{variant}.DocumentHeader"

    if not source_info.is_file() or not source_header.is_file():

        raise RuntimeError(f"Slay dependency variant {variant!r} is not installed")

    info_bytes = source_info.read_bytes()

    header_bytes = source_header.read_bytes()

    if not target_info.is_file() or target_info.read_bytes() != info_bytes:

        _atomic_replace_bytes(target_info, info_bytes)

    if not target_header.is_file() or target_header.read_bytes() != header_bytes:

        _atomic_replace_bytes(target_header, header_bytes)

    logger.info("Slay dependency variant for mission %s: %s", mission_id, variant)

    return variant





def restore_base_dependency_variant() -> None:



    try:

        root, target_info, target_header = _dependency_variant_paths()

        info_bytes = (root / "base.DocumentInfo").read_bytes()

        header_bytes = (root / "base.DocumentHeader").read_bytes()

        if not target_info.is_file() or target_info.read_bytes() != info_bytes:

            _atomic_replace_bytes(target_info, info_bytes)

        if not target_header.is_file() or target_header.read_bytes() != header_bytes:

            _atomic_replace_bytes(target_header, header_bytes)

    except Exception as exc:

        logger.debug("Slay dependency base restore skipped: %s", exc)





def _permanent_boon_effects(ctx: Any) -> list[str]:

    if not enabled(ctx) or not state_ready(ctx): return []

    return list(dict.fromkeys(str(x) for x in state(ctx).get("permanent_boons", []) if str(x) in EFFECT_BANK_BITS))





def effect_masks_for_mission(ctx: Any, mission_id: int) -> tuple[int, int, int, int, int, int]:

    if not enabled(ctx):



        return int(getattr(ctx, "rogue_poc_mask", 0)), 0, 0, 0, 0, 0

    data = node(ctx, int(mission_id))

    if data is None:

        return 0, 0, 0, 0, 0, 0

    masks = [0, 0, 0, 0, 0, 0]

    for effect in _effective_mutations(ctx, mission_id) + _effective_blessings(ctx, mission_id) + _permanent_boon_effects(ctx):

        bank_bit = EFFECT_BANK_BITS.get(str(effect))

        if bank_bit is None: continue

        bank, bit = bank_bit

        if bank >= 6: continue  # v1.2.1 extras are carried by mask G
        masks[bank] |= bit

    return masks[0], masks[1], masks[2], masks[3], masks[4], masks[5]




def extra_boon_mask_for_mission(ctx: Any, mission_id: int) -> int:
    """Trailing ?APRogue mask G. Keeps existing six-bank wire format stable."""
    if not enabled(ctx) or node(ctx, int(mission_id)) is None:
        return 0
    mask = 0
    for effect in _effective_mutations(ctx, mission_id) + _effective_blessings(ctx, mission_id) + _permanent_boon_effects(ctx):
        bank_bit = EFFECT_BANK_BITS.get(str(effect))
        if bank_bit is not None and bank_bit[0] == 6:
            mask |= bank_bit[1]
    return mask



def auto_repair_stacks(ctx: Any) -> int:



    if not enabled(ctx) or not state_ready(ctx):

        return 0

    return max(0, int(state(ctx).get("boon_purchases", {}).get(_boon_id("auto_repair"), 0)))





def deadly_weapons_stacks(ctx: Any) -> int:



    if not enabled(ctx) or not state_ready(ctx):

        return 0

    return max(0, int(state(ctx).get("boon_purchases", {}).get(_boon_id("deadly_weapons"), 0)))





PROGRESSION_FLAG_TERRAN_CONTRACTS = 1

PROGRESSION_FLAG_ZERG_CONTRACTS = 2

PROGRESSION_FLAG_KERRIGAN = 4

PROGRESSION_FLAG_SPEAR = 8





def progression_flags(ctx: Any) -> int:

    if not enabled(ctx) or not state_ready(ctx):

        return 0

    flags = 0

    if _progression_owned(ctx, TERRAN_CONTRACTS): flags |= PROGRESSION_FLAG_TERRAN_CONTRACTS

    if _progression_owned(ctx, ZERG_CONTRACTS): flags |= PROGRESSION_FLAG_ZERG_CONTRACTS

    if _progression_owned(ctx, KERRIGAN_UNLOCK): flags |= PROGRESSION_FLAG_KERRIGAN

    if _progression_owned(ctx, SPEAR_UNLOCK): flags |= PROGRESSION_FLAG_SPEAR

    return flags





def spear_energy_regen_stacks(ctx: Any) -> int:

    if not enabled(ctx) or not state_ready(ctx):

        return 0

    return min(3, max(0, _purchased_count(ctx, SPEAR_ENERGY_REGEN)))





def spear_cooldown_reduction_stacks(ctx: Any) -> int:

    if not enabled(ctx) or not state_ready(ctx):

        return 0

    return min(3, max(0, _purchased_count(ctx, SPEAR_COOLDOWN_REDUCTION)))





KERRIGAN_UPGRADE_FLAG_RECKLESS_POWER = 1

KERRIGAN_UPGRADE_FLAG_RECKLESS_SPEED = 2



def kerrigan_upgrade_flags(ctx: Any) -> int:













    if not enabled(ctx) or not state_ready(ctx):

        return 0

    power = min(255, max(0, _purchased_count(ctx, KERRIGAN_RECKLESS_POWER)))

    speed = min(255, max(0, _purchased_count(ctx, KERRIGAN_RECKLESS_SPEED)))

    return power | (speed << 8)





def mercenary_upgrade_packed(ctx: Any) -> int:



    if not enabled(ctx) or not state_ready(ctx):

        return 0

    packed = 0

    for index, item_name in enumerate(MERCENARY_CUSTOM_UPGRADE_ITEMS[:6]):

        stacks = min(31, max(0, _purchased_count(ctx, item_name)))

        packed |= stacks << (5 * index)

    return packed





def mercenary_upgrade_packed2(ctx: Any) -> int:



    if not enabled(ctx) or not state_ready(ctx):

        return 0

    packed = 0

    for index, item_name in enumerate(MERCENARY_CUSTOM_UPGRADE_ITEMS[6:]):

        stacks = min(31, max(0, _purchased_count(ctx, item_name)))

        packed |= stacks << (5 * index)

    # Bit 10 is outside the existing two 5-bit slots (spotters/support crew).
    # Archipelago's AP_RapidReinforcement CUpgrade subtracts 60 from fourteen
    # mercenary TimeUse AND TimeStart fields unconditionally.  Underflow occurs
    # inside the SC2 upgrade engine before Galaxy's watchdog can intervene.
    # Slay suppresses only that native tech item (in augment_network_items) and
    # applies its 60s reduction through APRG_ReduceMercenaryCooldownField.
    # Inventory/shop ownership remains unchanged, including received items.
    if _logic_owned_item_counts(ctx).get("Rapid Reinforcement (Terran)", 0) > 0:
        packed |= 1 << 10

    return packed





def effect_mask_for_mission(ctx: Any, mission_id: int) -> int:



    return effect_masks_for_mission(ctx, mission_id)[0]





def mission_launch_summary(ctx: Any, mission_id: int) -> str:



    data = node(ctx, int(mission_id)) or {}

    mask_a, mask_b, mask_c, mask_d, mask_e, mask_f = effect_masks_for_mission(ctx, mission_id)

    muts = [_mission_effect_name(ctx, mission_id, x) for x in _effective_mutations(ctx, mission_id)]

    bless = [_mission_effect_name(ctx, mission_id, x) for x in _effective_blessings(ctx, mission_id)]

    return (

        f"Slay launch: {data.get('mission_name', mission_id)}; "

        f"race={data.get('race', '?')}; campaign={data.get('campaign', '?')}; "

        f"mutators={muts or ['None']}; blessings={bless or ['None']}; "

        f"boons={[EFFECT_DISPLAY_NAMES.get(x,x) for x in _permanent_boon_effects(ctx)] or ['None']}; "

        f"maskA={mask_a}; maskB={mask_b}; maskC={mask_c}; maskD={mask_d}; maskE={mask_e}; maskF={mask_f}; "

        f"autoRepairStacks={auto_repair_stacks(ctx)}; deadlyWeaponsStacks={deadly_weapons_stacks(ctx)}; progressionFlags={progression_flags(ctx)}; "

        f"spearEnergyRegenStacks={spear_energy_regen_stacks(ctx)}; "

        f"mercenaryUpgradePacked={mercenary_upgrade_packed(ctx)}; mercenaryUpgradePacked2={mercenary_upgrade_packed2(ctx)}; "

        f"spearCooldownReductionStacks={spear_cooldown_reduction_stacks(ctx)}; "

        f"kerriganUpgradeFlags={kerrigan_upgrade_flags(ctx)}; "

        f"commanderHeroIndex={commander_hero_index(ctx, mission_id)}; godmode={godmode_for_mission(ctx, mission_id)}"

    )





def announce_mission_effects(ctx: Any, mission_id: int) -> None:



    data = node(ctx, int(mission_id)) or {}

    muts = [_mission_effect_name(ctx, mission_id, x) for x in _effective_mutations(ctx, mission_id)]

    bless = [_mission_effect_name(ctx, mission_id, x) for x in _effective_blessings(ctx, mission_id)]

    message = (

        "[Slay] Mutations: " + (", ".join(muts) if muts else "None")

        + " | Blessings: " + (", ".join(bless) if bless else "None")

        + " | Boons: " + (", ".join(EFFECT_DISPLAY_NAMES.get(x,x) for x in _permanent_boon_effects(ctx)) if _permanent_boon_effects(ctx) else "None")

    )

    try:

        ctx.on_print_json({"data": [{"text": message}]})

    except Exception:

        logger.info(message)





def _ordinary_mission_location_ids(ctx: Any) -> set[int]:





















    mapping = getattr(ctx, "mission_id_to_location_ids", {})

    if not isinstance(mapping, Mapping):

        return set()



    resolver = getattr(ctx, "locations_for_mission_id", None)

    result: set[int] = set()

    for mission_id in mapping.keys():

        try:

            mission_id = int(mission_id)

        except (TypeError, ValueError):

            continue

        if mission_id < 0:

            continue



        if callable(resolver):

            try:

                locations = resolver(mission_id)

            except (KeyError, TypeError, ValueError):

                continue

        else:







            locations = mapping.get(mission_id, ())



        for location_id in locations or ():

            try:

                location_id = int(location_id)

            except (TypeError, ValueError):

                continue

            if location_id > 0:

                result.add(location_id)

    return result





def _is_credit_replacement_location(ctx: Any, location_id: int) -> bool:



    location_id = int(location_id)

    if location_id <= 0 or not enabled(ctx):

        return False





    if crew_mode(ctx):
        reward = _crew_mission_reward_plan(ctx).get(location_id)
        return reward is not None and reward['kind']=='credits'
    if location_id not in _ordinary_mission_location_ids(ctx):

        return False

    seed = str(getattr(ctx, "slay_config", {}).get("run_seed", 0))
    if campaign_mode(ctx):
        mapping = getattr(ctx, "mission_id_to_location_ids", {})
        signature = (seed, id(mapping), len(mapping), sum(len(v) for v in mapping.values()))
        if getattr(ctx, "_campaign_credit_signature", None) != signature:
            locations = _ordinary_mission_location_ids(ctx)
            ordered = sorted(locations, key=lambda loc: hashlib.sha256(
                f"{seed}:campaign-credit-location:{loc}".encode()).digest())
            ctx._campaign_credit_ids = frozenset(ordered[:(2 * len(ordered)) // 3])
            ctx._campaign_credit_signature = signature
        return location_id in ctx._campaign_credit_ids
    digest = hashlib.sha256(f"{seed}:50-credit-location:{location_id}".encode()).digest()

    return digest[0] < 128





def _received_credit_replacement_locations(ctx: Any) -> set[int]:

    return {

        int(getattr(item, "location", 0))

        for item in getattr(ctx, "items_received", [])

        if _is_credit_replacement_location(ctx, int(getattr(item, "location", 0)))

    }





def item_credit_reward(ctx: Any) -> int:

    if not enabled(ctx):

        return 50

    try:

        return max(0, int(ctx.slay_config.get("item_credit_reward", 60)))

    except (TypeError, ValueError):

        return 50





def _sync_launcher_manifest_credits(ctx: Any, balance: int) -> None:

    run_dir = _launcher_run_dir()

    if run_dir is None:

        return

    balance = max(0, int(balance))

    if getattr(ctx, "_slay_manifest_current_credits", None) == balance:

        return

    path = run_dir / "manifest.json"

    try:

        raw = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

        manifest = dict(raw) if isinstance(raw, Mapping) else {}

        if int(manifest.get("current_credits", -1)) != balance:

            manifest["current_credits"] = balance

            tmp = path.with_suffix(path.suffix + ".tmp")

            tmp.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")

            tmp.replace(path)

        ctx._slay_manifest_current_credits = balance

    except Exception as exc:

        logger.debug("Slay launcher: could not cache current credits in %s: %s", path, exc)





def crew_effective_victory_reward(ctx: Any, data: Mapping[str, Any]) -> int:
    """Credit reward after Crew-only mission balance modifiers, UI and ledger."""
    amount=max(0,int(data.get('credit_reward',0)))
    if crew_mode(ctx):
        amount //= 2  # Dev81: Crew victory credits are half the prior Crew reward.
        if _mission_base_name(str(data.get('mission_name',''))).casefold()=='domination':
            amount=max(0,amount-200)
    return amount


def credits(ctx: Any) -> int:

    if not enabled(ctx):

        return 0

    earned = int(ctx.slay_config.get("starting_credits", 0))

    completed = completed_mission_ids(ctx)

    for mission_id, data in nodes(ctx).items():

        if mission_id in completed:
            earned+=crew_effective_victory_reward(ctx,data)





    if crew_mode(ctx):
        reward_plan = _crew_mission_reward_plan(ctx)
        earned += sum(int(reward_plan[loc]['credits']) for loc in _crew_received_reward_locations(ctx)
                      if reward_plan[loc]['kind']=='credits')
    else:
        earned += item_credit_reward(ctx) * len(_received_credit_replacement_locations(ctx))

    if state_ready(ctx): earned += max(0, victory_count(ctx) * int(state(ctx).get("golden_goose_bonus_per_mission", 0)) - int(state(ctx).get("golden_goose_credit_offset", 0)))





    test_bonus = int(state(ctx).get("test_credit_bonus", 0)) if state_ready(ctx) else 0

    raw_balance = earned + test_bonus - int(state(ctx).get("spent", 0))
    # Developer /credits deductions may intentionally put any mode into debt.
    balance = raw_balance if crew_mode(ctx) or test_bonus < 0 else max(0, raw_balance)

    _sync_launcher_manifest_credits(ctx, balance)

    return balance





_ITEM_TABLE_CACHE: Mapping[str, Any] | None = None

_ITEM_TABLE_PROVIDER: Any | None = None



def _item_table() -> Mapping[str, Any]:









    global _ITEM_TABLE_CACHE, _ITEM_TABLE_PROVIDER

    if _ITEM_TABLE_CACHE is None or _ITEM_TABLE_PROVIDER is not get_full_item_list:

        _ITEM_TABLE_CACHE = get_full_item_list()

        _ITEM_TABLE_PROVIDER = get_full_item_list

    return _ITEM_TABLE_CACHE





def _actual_item_counts(ctx: Any) -> Counter[str]:
    """Inventory-only AP counts that survive transient items_received empties."""
    table = _item_table()
    by_code = {data.code: name for name, data in table.items() if data.code is not None}
    replacements = state(ctx).get("duplicate_replacements", {}) if enabled(ctx) and state_ready(ctx) else {}

    live_records: list[list[int]] = []
    for item in getattr(ctx, "items_received", []):
        try:
            live_records.append([
                int(getattr(item, "item", 0)),
                int(getattr(item, "location", 0)),
                int(getattr(item, "player", 0)),
            ])
        except (TypeError, ValueError):
            continue

    snapshot: list[list[int]] = []
    if enabled(ctx) and state_ready(ctx):
        raw_snapshot = state(ctx).get("inventory_received_snapshot", [])
        if isinstance(raw_snapshot, Sequence) and not isinstance(raw_snapshot, (str, bytes)):
            for raw_record in raw_snapshot:
                if not isinstance(raw_record, Sequence) or isinstance(raw_record, (str, bytes)) or len(raw_record) < 3:
                    continue
                try:
                    snapshot.append([int(raw_record[0]), int(raw_record[1]), int(raw_record[2])])
                except (TypeError, ValueError):
                    continue

        # AP items are append-only within a run. A shorter live list means the
        # client is between synchronization states; do not make Inventory appear
        # to erase everything. The snapshot stores raw item/location records so
        # duplicate replacements can still be resolved using current state.
        if len(live_records) >= len(snapshot) and live_records != snapshot:
            state(ctx)["inventory_received_snapshot"] = copy.deepcopy(live_records)
            snapshot = live_records
            _persist_state(ctx)

    records = live_records if len(live_records) >= len(snapshot) else snapshot
    counts: Counter[str] = Counter()
    for item_code, location, _player in records:
        if location == -2 or _is_credit_replacement_location(ctx, location):
            continue
        name = by_code.get(item_code)
        replacement = replacements.get(str(location)) if isinstance(replacements, Mapping) else None
        if replacement in table:
            name = str(replacement)
        if name is not None:
            counts[name] += 1
    return counts



def _raw_logic_owned_item_counts(ctx: Any) -> Counter[str]:



    table = _item_table()

    received = getattr(ctx, "items_received", [])

    replacements = state(ctx).get("duplicate_replacements", {}) if enabled(ctx) and state_ready(ctx) else {}

    replacement_sig = tuple(sorted((str(k), str(v)) for k, v in replacements.items())) if isinstance(replacements, Mapping) else ()

    signature = (id(received), len(received), replacement_sig)

    if getattr(ctx, "slay_raw_logic_counts_signature", None) == signature:

        cached = getattr(ctx, "slay_raw_logic_counts_cache", None)

        if cached is not None:

            return Counter(cached)



    by_code = {data.code: name for name, data in table.items() if data.code is not None}

    counts: Counter[str] = Counter()

    for item in received:

        location = int(getattr(item, "location", 0))

        if location != -2 and _is_credit_replacement_location(ctx, location):

            continue

        name = by_code.get(getattr(item, "item", None))

        if location != -2:

            replacement = replacements.get(str(location)) if isinstance(replacements, Mapping) else None

            if replacement in table:

                name = str(replacement)

        if name is not None:

            counts[name] += 1

    ctx.slay_raw_logic_counts_signature = signature

    ctx.slay_raw_logic_counts_cache = Counter(counts)

    return counts





def _logic_owned_item_counts(ctx: Any) -> Counter[str]:



    table = _item_table()

    counts = _raw_logic_owned_item_counts(ctx)

    for name, count in state(ctx).get("purchases", {}).items():

        if int(count) > 0 and name in table:

            counts[str(name)] += _effective_shop_copies(str(name), int(count))

    return counts



def _owned_unlock_names(ctx: Any, counts: Mapping[str, int] | None = None) -> set[str]:



    table = _item_table()

    if counts is None:

        counts = _logic_owned_item_counts(ctx)

    result: set[str] = set()

    for name, count in counts.items():

        if int(count) <= 0:

            continue

        data = table.get(name)

        if data is None:

            continue

        type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

        if _is_unit_unlock_type(type_name) or type_name in {"Building", "Morph"}:

            result.add(str(name))

    return result





def _owned_unlock_name_contains(owned_unlocks: set[str], terms: Sequence[str]) -> bool:

    folded = tuple(str(term).casefold() for term in terms)

    return any(any(term in name.casefold() for term in folded) for name in owned_unlocks)





_UNIT_UNLOCK_TYPES = {"Unit", "Building", "Mercenary"}



def _is_unit_unlock_type(type_name: str) -> bool:



    normalized = str(type_name).replace("_", " ").strip().casefold()

    return normalized == "mercenary" or normalized.startswith("unit")





def _is_morph_unlock_type(type_name: str) -> bool:



    return str(type_name).replace("_", " ").strip().casefold() == "morph"





def _is_unit_or_morph_unlock_type(type_name: str) -> bool:



    return _is_morph_unlock_type(type_name) or _is_unit_unlock_type(type_name)





def _is_specific_upgrade_parent_type(type_name: str) -> bool:



    normalized = str(type_name).replace("_", " ").strip().casefold()





    return normalized in {"building", "morph"} or _is_unit_unlock_type(type_name)

_ECONOMY_TYPES = {

    "Minerals", "Vespene", "Supply", "Max Supply", "Building Speed",

    "Research Speed", "Research Cost",

}





def inventory_rows(ctx: Any) -> list[dict[str, Any]]:



    table = _item_table()

    ap_counts = _actual_item_counts(ctx)

    shop_counts = Counter({

        str(name): max(0, int(count))

        for name, count in state(ctx).get("purchases", {}).items()

    })



    rows: list[dict[str, Any]] = []

    for item_name in sorted(set(ap_counts) | set(shop_counts), key=str.casefold):

        ap_count = int(ap_counts.get(item_name, 0))

        shop_count = int(shop_counts.get(item_name, 0))

        if ap_count <= 0 and shop_count <= 0:

            continue

        data = table.get(item_name)

        is_progression = _is_progression_item(item_name)

        type_name = "Global Progression" if is_progression else (str(getattr(getattr(data, "type", None), "display_name", "Other")) if data is not None else "Other")

        race_obj = getattr(data, "race", None) if data is not None else None

        if race_obj is not None and hasattr(race_obj, "get_title"):

            try:

                race_name = str(race_obj.get_title())

            except Exception:

                race_name = "Other"

        else:

            race_name = "Other"



        if is_progression:

            category = "Global Progression"

        elif _is_unit_unlock_type(type_name) or type_name == "Building":

            category = "Unit Unlocks"

        elif type_name in _ECONOMY_TYPES:

            category = "Economy & Other"

        else:

            category = "Upgrades & Abilities"



        section = shop_category_for_item(item_name, ctx)

        if section == "Other":

            section = "General Upgrades"

        rows.append({

            "canonical_name": item_name,
            "name": PROGRESSION_DISPLAY_NAMES.get(item_name, item_name),

            "race": race_name,

            "category": category,

            "section": section,

            "type": type_name,

            "ap_count": ap_count,

            "shop_count": shop_count,

            "total": ap_count + shop_count,

            "description": shop_entry_description(item_name),

            "icon": shop_entry_icon(item_name),

        })











    # Slay-only consumables do not exist in Archipelago's item table, but must
    # be visible alongside the rest of the current inventory until consumed.
    for slot in potion_inventory(ctx):
        potion = POTION_CATALOG[str(slot["id"])]
        rows.append({
            "canonical_name": str(slot["id"]),
            "name": str(potion["name"]), "race": "Other",
            "category": "Consumables", "section": "Consumables", "type": "Consumable",
            "ap_count": 0, "shop_count": 1, "total": 1,
            "description": str(potion["description"]),
            "icon": shop_entry_icon(str(slot["id"])),
        })

    for effect_id in dict.fromkeys(str(x) for x in state(ctx).get("permanent_blessings", [])):

        if effect_id not in BLESSING_SEVERITY:

            continue

        rows.append({

            "canonical_name": effect_id,
            "name": EFFECT_DISPLAY_NAMES.get(effect_id, effect_id),

            "race": "Other",

            "category": "Permanent Blessings",

            "section": "Blessings",

            "type": "Blessing",

            "ap_count": 0,

            "shop_count": 1,

            "total": 1,

            "description": EFFECT_DESCRIPTIONS.get(effect_id, ""),

            "icon": "",

        })



    for effect_id in dict.fromkeys(str(x) for x in state(ctx).get("permanent_boons", [])):

        display = EFFECT_DISPLAY_NAMES.get(effect_id, effect_id)

        # All repeatable boons use the same boon_<kind> effect ID convention.
        # Look up the purchase counter directly; the previous partial reverse map
        # omitted Deadly Weapons and incorrectly displayed x1 for every stack.
        kind = effect_id.removeprefix("boon_")

        count = int(state(ctx).get("boon_purchases", {}).get(_boon_id(kind), 0)) if kind in REPEATABLE_BOON_KINDS else 1

        count = max(1, count)

        rows.append({

            "canonical_name": effect_id,
            "name": display, "race": "Other",

            "category": "Permanent Boons", "section": "Boons", "type": "Boon", "ap_count": 0, "shop_count": count, "total": count,

            "description": EFFECT_DESCRIPTIONS.get(effect_id, ""), "icon": "",

        })

    for effect_id in dict.fromkeys(str(x) for x in state(ctx).get("permanent_mutations", [])):

        rows.append({

            "canonical_name": effect_id,
            "name": EFFECT_DISPLAY_NAMES.get(effect_id, effect_id), "race": "Other",

            "category": "Permanent Mutations", "section": "Mutations", "type": "Mutation", "ap_count": 0, "shop_count": 1, "total": 1,

            "description": EFFECT_DESCRIPTIONS.get(effect_id, ""), "icon": "",

        })



    section_order = {name: index for index, name in enumerate((

        "Terran Units", "Terran Upgrades", "Defensive Structures & Detectors",

        "Zerg Units", "Zerg Upgrades", "General Upgrades",

        "Protoss Units", "Protoss Upgrades", "Boons", "Blessings", "Mutations",

        "Mercenary Contracts", "Mercenaries", "Kerrigan", "Spear of Adun", "Consumables",

    ))}

    rows.sort(key=lambda row: (

        section_order.get(str(row.get("section", "")), 99),

        str(row["name"]).casefold(),

    ))

    return rows





def _max_owned_copies(item_data: Any) -> int | None:

    quantity = int(getattr(item_data, "quantity", 0))

    return quantity if quantity > 0 else None





def _duplicate_owned_cap(item_name: str, item_data: Any) -> int | None:















    if _is_stackable_progressive_item(item_name):

        return _max_owned_copies(item_data)

    type_name = str(getattr(getattr(item_data, "type", None), "display_name", ""))

    normalized = type_name.replace("_", " ").strip().casefold()

    if _is_unit_unlock_type(type_name) or normalized in {"building", "morph", "mercenary"}:

        return 1

    return _max_owned_copies(item_data)





def _purchased_count(ctx: Any, item_name: str) -> int:

    return int(state(ctx).get("purchases", {}).get(item_name, 0))





def _shop_cycle_purchase_count(ctx: Any, item_name: str) -> int:

    s = state(ctx)

    if int(s.get("shop_cycle_purchase_victory_count", -1)) != victory_count(ctx):

        return 0

    return int(s.get("shop_cycle_purchases", {}).get(item_name, 0))





def _shop_reroll_purchase_count(ctx: Any) -> int:

    s = state(ctx)

    if int(s.get("shop_reroll_purchase_victory_count", -1)) != victory_count(ctx):

        return 0

    return int(s.get("shop_rerolls_this_cycle", 0))





def _same_shop_50_percent_price(base_price: int, cycle_buys: int) -> int:

    return int(round(int(base_price) * (1.50 ** max(0, int(cycle_buys)))))





def _is_legacy_35_credit_generic(item_name: str) -> bool:



    return item_name in LEGACY_35_CREDIT_GENERIC_ITEMS













FIVE_X_GENERIC_UPGRADE_ITEMS = set(LEGACY_35_CREDIT_GENERIC_ITEMS) | {RESEARCH_SPEED_ITEM}

STACKABLE_GENERAL_UPGRADE_ITEMS = set(FIVE_X_GENERIC_UPGRADE_ITEMS)





def _effective_shop_copies(item_name: str, purchased: int) -> int:





    if item_name in FIVE_X_GENERIC_UPGRADE_ITEMS:

        return purchased * 5

    if _is_legacy_35_credit_generic(item_name):

        return purchased * 2

    return purchased





def _effective_actual_item_count(ctx: Any, item_name: str) -> int:





    raw = int(_logic_owned_item_counts(ctx).get(item_name, 0))





    purchased = _effective_shop_copies(item_name, _purchased_count(ctx, item_name))

    raw = max(0, raw - purchased)

    if item_name in FIVE_X_GENERIC_UPGRADE_ITEMS:

        return raw * 5

    return raw





def _eligible_to_buy(ctx: Any, item_name: str) -> bool:

    data = _item_table().get(item_name)

    if data is None or data.code is None or _is_deprecated_item(item_name, data):

        return False

    cap = _max_owned_copies(data)

    if cap is None:

        return True

    effective_bought = _effective_shop_copies(item_name, _purchased_count(ctx, item_name))

    return _effective_actual_item_count(ctx, item_name) + effective_bought < cap





def _salvage_item_names(ctx: Any) -> list[str]:



    if not enabled(ctx) or getattr(ctx, "slot", None) is None:

        return []

    completed = completed_mission_ids(ctx)

    if not completed:

        return []

    graph = nodes(ctx)

    code_to_name = {data.code: name for name, data in _item_table().items() if data.code is not None}

    results: list[str] = []

    seen: set[str] = set()







    for mission_id, data in graph.items():

        if node_status(ctx, mission_id) not in {"completed", "abandoned"}:

            continue

        for location_id in ctx.locations_for_mission_id(mission_id):

            if location_id not in getattr(ctx, "missing_locations", set()):

                continue

            info = getattr(ctx, "locations_info", {}).get(location_id)

            if info is None:

                continue





            if int(info.player) != int(ctx.slot):

                continue

            item_name = code_to_name.get(info.item)

            if item_name is not None and item_name not in seen:

                seen.add(item_name)

                results.append(item_name)

    return results





def _effective_owned_item_count(ctx: Any, item_name: str) -> int:

    return _effective_actual_item_count(ctx, item_name) + _effective_shop_copies(

        item_name, _purchased_count(ctx, item_name)

    )





def _parent_item_name(data: Any) -> str | None:

    parent = getattr(data, "parent", None)

    if parent is None:

        parent = getattr(data, "parent_item", None)

    if isinstance(parent, str) and parent:

        return parent

    if parent is not None:

        for attr in ("name", "item_name"):

            value = getattr(parent, attr, None)

            if isinstance(value, str) and value:

                return value

    return None





def _is_progression_item(item_name: str) -> bool:

    return str(item_name).startswith(PROGRESSION_PREFIX)





def _progression_owned(ctx: Any, item_name: str) -> bool:

    return enabled(ctx) and state_ready(ctx) and _purchased_count(ctx, item_name) > 0





def _is_mercenary_unit(item_name: str, data: Any | None = None) -> bool:

    if item_name in TERRAN_MERCENARY_ITEMS or item_name in ZERG_MERCENARY_ITEMS:

        return True

    if data is None:

        data = _item_table().get(item_name)

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    return type_name.strip().casefold() == "mercenary"





def _is_kerrigan_level_item(item_name: str, data: Any | None = None) -> bool:

    if data is None:

        data = _item_table().get(item_name)

    if data is None:

        return False

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    return _item_race_key(item_name, data) == "zerg" and type_name.strip().casefold() == "level"





def _is_kerrigan_primal_form_item(item_name: str, data: Any | None = None) -> bool:

    if item_name == KERRIGAN_PRIMAL_FORM_ITEM:

        return True

    if data is None:

        data = _item_table().get(item_name)

    if data is None:

        return False

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    return _item_race_key(item_name, data) == "zerg" and type_name.strip().casefold() == "primal form"





def _is_kerrigan_item(item_name: str, data: Any | None = None) -> bool:

    if item_name in KERRIGAN_ABILITY_ITEMS:

        return True

    if data is None:

        data = _item_table().get(item_name)

    if _is_kerrigan_level_item(item_name, data):

        return True

    return _is_kerrigan_primal_form_item(item_name, data)





def _is_spear_item(item_name: str, data: Any | None = None) -> bool:

    if item_name in SPEAR_OF_ADUN_ITEMS:

        return True

    if data is None:

        data = _item_table().get(item_name)

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    return type_name.strip().casefold() == "spear of adun"





def _is_mercenary_general_upgrade(item_name: str, data: Any | None = None) -> bool:





    if item_name in {"Mechanical Know-how (Terran)", "Mercenary Munitions (Terran)"}:

        return False

    if item_name in MERCENARY_GENERAL_UPGRADE_ITEMS:

        return True

    if data is None:

        data = _item_table().get(item_name)

    parent_name = _parent_item_name(data) if data is not None else None

    return parent_name in {"Terran Mercenaries", "Zerg Mercenaries"}





def _is_explicit_race_global_upgrade(item_name: str) -> bool:

    return any(item_name in items for items in RACE_GLOBAL_UPGRADE_ITEMS.values())





def _unit_specific_parent_names(item_name: str, table: Mapping[str, Any] | None = None) -> tuple[str, ...]:

















    if table is None:

        table = _item_table()

    if _is_general_upgrade_item(item_name) or _is_explicit_race_global_upgrade(item_name):

        return ()

    data = table.get(item_name)

    if data is None:

        return ()



    candidates: list[str] = []

    if _AP_ITEM_PARENTS is not None:

        try:

            candidates.extend(str(x) for x in _AP_ITEM_PARENTS.child_item_to_parent_items.get(item_name, ()))

        except Exception:

            pass

        if not candidates:

            try:

                parent_id = getattr(data, "parent", None)

                rule = _AP_ITEM_PARENTS.parent_present.get(parent_id)

                if rule is not None:

                    candidates.extend(str(x) for x in rule.parent_items())

            except Exception:

                pass





    parent_name = _parent_item_name(data)

    if parent_name and parent_name in table:

        candidates.append(parent_name)





    match = re.search(r"\(([^()]+)\)\s*$", item_name)

    if match:

        candidates.append(match.group(1).strip())



    result: list[str] = []

    for candidate in candidates:

        parent_data = table.get(candidate)

        if parent_data is None:

            continue

        parent_type = str(getattr(getattr(parent_data, "type", None), "display_name", ""))

        if _is_specific_upgrade_parent_type(parent_type) and candidate not in result:

            result.append(candidate)

    return tuple(result)





def _unit_specific_parent_name(item_name: str, table: Mapping[str, Any] | None = None) -> str | None:

    parents = _unit_specific_parent_names(item_name, table)

    return parents[0] if parents else None





def _is_unit_specific_upgrade(item_name: str, table: Mapping[str, Any] | None = None) -> bool:

    return bool(_unit_specific_parent_names(item_name, table))





def _is_royal_guard_item(

    item_name: str, data: Any | None = None, table: Mapping[str, Any] | None = None,

) -> bool:

    if item_name in ROYAL_GUARD_UNIT_ITEMS:

        return True







    match = re.search(r"\(([^()]+)\)\s*$", item_name)

    if match and match.group(1).strip() in ROYAL_GUARD_UNIT_ITEMS:

        return True

    parent_name = _parent_item_name(data) if data is not None else ""

    if parent_name in ROYAL_GUARD_UNIT_ITEMS:

        return True

    if table is None:

        table = _item_table()

    return any(parent in ROYAL_GUARD_UNIT_ITEMS for parent in _unit_specific_parent_names(item_name, table))





def _mercenary_contract_for_item(item_name: str, data: Any | None = None) -> str | None:

    if data is None:

        data = _item_table().get(item_name)

    race = _item_race_key(item_name, data)

    if race == "terran" and (_is_mercenary_unit(item_name, data) or _is_mercenary_general_upgrade(item_name, data)):

        return TERRAN_CONTRACTS

    if race == "zerg" and (_is_mercenary_unit(item_name, data) or _is_mercenary_general_upgrade(item_name, data)):

        return ZERG_CONTRACTS

    table = _item_table()

    for parent in _unit_specific_parent_names(item_name, table):

        parent_data = table.get(parent)

        if _is_mercenary_unit(parent, parent_data):

            return TERRAN_CONTRACTS if _item_race_key(parent, parent_data) == "terran" else ZERG_CONTRACTS

    return None





def _is_general_upgrade_item(item_name: str) -> bool:

    return item_name in GENERIC_OTHER_UPGRADE_ITEMS or item_name in LEGACY_35_CREDIT_GENERIC_ITEMS or item_name == RESEARCH_SPEED_ITEM





def _one_kerrigan_level_item(table: Mapping[str, Any] | None = None) -> str | None:

    if table is None:

        table = _item_table()

    levels = [name for name, data in table.items() if getattr(data, "code", None) is not None and _is_kerrigan_level_item(name, data)]

    if not levels:

        return None

    exact = [name for name in levels if re.match(r"^1\s+Kerrigan\s+Level", name, re.IGNORECASE)]

    return sorted(exact or levels, key=lambda x: (len(x), x.casefold()))[0]





def _spear_cheap_item(item_name: str) -> bool:

    base = str(item_name).split(" (", 1)[0].strip()

    return base in SPEAR_CHEAP_BASE_NAMES





def _mercenary_equivalent_contract_for_parent(

    ctx: Any, parent_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None,

) -> str | None:



    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    variants = MERCENARY_BASE_UNIT_EQUIVALENTS.get(str(parent_name), set())

    for merc_name in variants:

        if merc_name not in owned_unlocks:

            continue

        merc_data = table.get(merc_name)

        contract = _mercenary_contract_for_item(merc_name, merc_data)

        if contract is not None and _progression_owned(ctx, contract):

            return contract

    return None





def _specific_parent_is_owned(

    ctx: Any, parent_name: str, owned_unlocks: set[str], table: Mapping[str, Any]

) -> bool:













    return parent_name in owned_unlocks





def _effective_mercenary_contract_for_item(

    ctx: Any, item_name: str, data: Any | None = None,

    owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None,

) -> str | None:



    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    direct = _mercenary_contract_for_item(item_name, data)

    if direct is not None:

        return direct







    return None





def _shop_unit_parent_is_available(

    ctx: Any, parent_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None, selected_races: set[str] | None = None,

) -> bool:

    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    if parent_name in owned_unlocks:

        return True

    data = table.get(parent_name)

    if data is None or getattr(data, "code", None) is None or _is_deprecated_item(parent_name, data):

        return False

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    if not _is_unit_or_morph_unlock_type(type_name) or _is_mercenary_unit(parent_name, data):

        return False

    if _is_nova_campaign_item(parent_name, data) or _is_royal_guard_item(parent_name, data, table):

        return False

    if selected_races is None:

        selected_races = {str(x).casefold() for x in ctx.slay_config.get("races", [])}

    race = _item_race_key(parent_name, data)

    if race not in selected_races and race not in {"any", "any race", ""}:

        return False

    # A morph/variant only counts as "available to purchase" if its own
    # prerequisite unit is available. This keeps race-upgrade eligibility in
    # lockstep with the actual unit shop instead of exposing upgrades for a
    # unit that still cannot be offered.
    if _unit_upgrade_requires_locked_unit(ctx, parent_name, owned_unlocks, table):

        return False

    return _eligible_to_buy(ctx, parent_name)


def _unit_upgrade_has_shop_available_parent(

    ctx: Any, item_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None, selected_races: set[str] | None = None,

) -> bool:

    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    return any(

        _shop_unit_parent_is_available(ctx, parent, owned_unlocks, table, selected_races)

        for parent in _unit_specific_parent_names(item_name, table)

    )


def _unit_upgrade_available_from_owned_or_current_stock(
    ctx: Any, item_name: str, owned_unlocks: set[str], current_unit_stock: Sequence[str],
    table: Mapping[str, Any] | None = None,
) -> bool:
    """Whether a race-upgrade item has its required unit owned or in this shop roll.

    This intentionally uses the actual unit items selected for the current shop,
    not every unit that would theoretically be eligible to roll.
    """
    if table is None:
        table = _item_table()
    available_unlocks = set(owned_unlocks)
    available_unlocks.update(str(name) for name in current_unit_stock)
    return not _unit_upgrade_requires_locked_unit(ctx, item_name, available_unlocks, table)


def _unit_upgrade_requires_locked_unit(

    ctx: Any, item_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None,

) -> bool:













    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)





    if item_name in {

        "Hive Mind Emulator",

        "Argus Amplifier (Hive Mind Emulator)",

        "Psi Indoctrinator (Hive Mind Emulator)",

    }:

        return False

    parents = _unit_specific_parent_names(item_name, table)

    if not parents:

        return False



    owned = lambda parent: _specific_parent_is_owned(ctx, parent, owned_unlocks, table)

    data = table.get(item_name)

    rule = None

    if data is not None and _AP_ITEM_PARENTS is not None:

        try:

            rule = _AP_ITEM_PARENTS.parent_present.get(getattr(data, "parent", None))

        except Exception:

            rule = None

    rule_name = type(rule).__name__ if rule is not None else ""



    if rule_name == "AllOf":

        return not all(owned(parent) for parent in parents)

    if rule_name == "AnyOfGroupAndOneOtherItem":

        required = str(getattr(rule, "item_name", ""))

        group = [str(x) for x in getattr(rule, "group", ()) if str(x) in parents]

        required_ok = True if required not in parents else owned(required)

        group_ok = True if not group else any(owned(parent) for parent in group)

        return not (required_ok and group_ok)





    return not any(owned(parent) for parent in parents)





def shop_candidates(

    ctx: Any, logic_counts: Mapping[str, int] | None = None,

    owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None,

) -> list[str]:















    if not enabled(ctx):

        return []

    if table is None:

        table = _item_table()

    if logic_counts is None:

        logic_counts = _logic_owned_item_counts(ctx)

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx, logic_counts)

    selected_races = {str(x).casefold() for x in ctx.slay_config.get("races", [])}

    purchases = state(ctx).get("purchases", {})

    combined: list[str] = []

    for name, data in table.items():

        if data is None or getattr(data, "code", None) is None:

            continue

        if _is_deprecated_item(name, data):

            continue

        type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

        classification = getattr(data, "classification", 0)

        if classification & ItemClassification.trap or type_name == "Max Supply Trap" or "key" in type_name.casefold():

            continue

        if _is_nova_campaign_item(name, data):

            continue

        if _is_royal_guard_item(name, data, table):

            continue

        if name in REDUNDANT_BASIC_STAT_UPGRADE_ITEMS:

            continue

        if name == SLAYER_PHASE_BLINK and int(logic_counts.get("Slayer", 0)) > 0:

            continue

        if name == KERRIGAN_PRIMAL_FORM_ITEM:

            continue







        if name in PROTOSS_WAR_COUNCIL_ITEMS or type_name.casefold().startswith("war council") or name in REDUNDANT_WAR_COUNCIL_UPGRADE_ITEMS:

            continue

        race = _item_race_key(name, data)

        special_global_track = (

            _is_mercenary_unit(name, data) or _is_mercenary_general_upgrade(name, data)

            or _is_kerrigan_item(name, data) or _is_spear_item(name, data)

            or (_unit_specific_parent_name(name, table) is not None and _mercenary_contract_for_item(name, data) is not None)







            or _effective_mercenary_contract_for_item(ctx, name, data, owned_unlocks, table) is not None

        )

        if not special_global_track and name not in DEFENSIVE_STRUCTURE_ITEMS and name not in DETECTOR_ITEMS:

            if race not in selected_races and race not in {"any", "any race", ""}:

                continue

        if (

            _unit_upgrade_requires_locked_unit(ctx, name, owned_unlocks, table)

            and not _unit_upgrade_has_shop_available_parent(ctx, name, owned_unlocks, table, selected_races)

        ):

            continue

        cap = _max_owned_copies(data)

        if cap is not None and not _is_kerrigan_level_item(name, data):

            effective_bought = _effective_shop_copies(name, int(purchases.get(name, 0)))

            raw_actual = max(0, int(logic_counts.get(name, 0)) - effective_bought)

            if name in FIVE_X_GENERIC_UPGRADE_ITEMS:

                raw_actual *= 5

            if raw_actual + effective_bought >= cap:

                continue

        combined.append(name)

    return combined





def _owned_unit_upgrade_parent(

    ctx: Any, item_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None,

) -> str | None:



    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    for parent in _unit_specific_parent_names(item_name, table):

        if _specific_parent_is_owned(ctx, parent, owned_unlocks, table):

            return parent

    return None







def _morph_source_is_owned(

    ctx: Any, item_name: str, owned_unlocks: set[str] | None = None,

    table: Mapping[str, Any] | None = None,

) -> bool | None:











    if table is None:

        table = _item_table()

    data = table.get(item_name)

    if data is None:

        return None

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    if not _is_morph_unlock_type(type_name):

        return None

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    parents = _unit_specific_parent_names(item_name, table)

    if not parents:

        return None

    return any(_specific_parent_is_owned(ctx, parent, owned_unlocks, table) for parent in parents)





def _shop_roll_weight(

    ctx: Any, item_name: str, owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None

) -> float:

    if item_name in RACE_WEAPON_ARMOR_UPGRADE_ITEMS:

        return 8.0

    if item_name == RESEARCH_SPEED_ITEM:

        return 6.0











    morph_source_owned = _morph_source_is_owned(ctx, item_name, owned_unlocks, table)

    if morph_source_owned is False:

        return 0.15

    if morph_source_owned is True:

        return 1.0

    if _owned_unit_upgrade_parent(ctx, item_name, owned_unlocks, table):

        return 8.0

    return 1.0





def _weighted_shop_sample(

    ctx: Any, rng: random.Random, items: Sequence[str], count: int,

    owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None,

    avoid_items: set[str] | None = None,

) -> list[str]:

    pool = list(dict.fromkeys(items))

    chosen: list[str] = []

    if table is None:

        table = _item_table()

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    target_count = min(max(0, int(count)), len(pool))

    weight_by_name = {name: _shop_roll_weight(ctx, name, owned_unlocks, table) for name in pool}

    expansion_item = _boon_id("shop_expansion")

    if expansion_item in weight_by_name and int(state(ctx).get("shop_expansion", 0)) <= 0:

        weight_by_name[expansion_item] *= 3.0

    reroll_effects_item = _boon_id("reroll")

    if reroll_effects_item in weight_by_name and victory_count(ctx) >= 8:

        weight_by_name[reroll_effects_item] *= 4.0







    chaos_blessings_item = _boon_id("chaos_blessings")

    if chaos_blessings_item in weight_by_name:

        weight_by_name[chaos_blessings_item] *= 0.25





    for name in list(weight_by_name):

        if _parse_boon(name)[0] == "permanent_blessing":

            weight_by_name[name] *= 2.0



    def draw_from(candidates: list[str], amount: int) -> None:

        nonlocal pool, chosen

        local = [name for name in candidates if name in pool]

        for _ in range(min(amount, len(local))):

            weights = [weight_by_name[name] for name in local]

            pick = rng.choices(local, weights=weights, k=1)[0]

            chosen.append(pick)

            pool.remove(pick)

            local.remove(pick)







    available_credits = credits(ctx)

    avoid = set(avoid_items or ())





    fresh = [name for name in pool if name not in avoid]

    affordable_fresh = [name for name in fresh if _price_for_item_before_sale(name, ctx) <= available_credits]

    draw_from(affordable_fresh, target_count)

    if len(chosen) < target_count:

        draw_from([name for name in fresh if name in pool], target_count - len(chosen))

    if len(chosen) < target_count:

        affordable_old = [name for name in pool if _price_for_item_before_sale(name, ctx) <= available_credits]

        draw_from(affordable_old, target_count - len(chosen))

    if len(chosen) < target_count:

        draw_from(list(pool), target_count - len(chosen))

    return chosen





def _item_race_key(item_name: str, data: Any | None = None) -> str:

    if data is None:

        data = _item_table().get(item_name)

    if data is None:

        return ""

    race = getattr(data, "race", None)

    getter = getattr(race, "get_title", None)

    if callable(getter):

        try:

            return str(getter()).casefold()

        except Exception:

            pass

    return str(getattr(race, "name", race) or "").casefold()



def shop_category_for_item(item_name: str, ctx: Any | None = None, owned_unlocks: set[str] | None = None) -> str:

    if item_name in POTION_CATALOG:
        return "Consumables"

    if item_name.startswith(BOON_PREFIX):

        return "Boons"

    if item_name in {TERRAN_CONTRACTS, ZERG_CONTRACTS}:

        return "Mercenary Contracts"

    if item_name in MERCENARY_CUSTOM_UPGRADE_ITEMS:

        return "Mercenaries"

    if item_name == KERRIGAN_UNLOCK or item_name in KERRIGAN_CUSTOM_ITEMS:

        return "Kerrigan"

    if item_name == SPEAR_UNLOCK or item_name in SPEAR_CUSTOM_ITEMS:

        return "Spear of Adun"









    if item_name in DEFENSIVE_STRUCTURE_ITEMS or item_name in DETECTOR_ITEMS:

        return "Defensive Structures & Detectors"

    data = _item_table().get(item_name)

    if data is None:

        return "General Upgrades" if _is_general_upgrade_item(item_name) else "Other"

    if _is_kerrigan_item(item_name, data):

        return "Kerrigan"

    if _is_spear_item(item_name, data):

        return "Spear of Adun"

    merc_contract = _mercenary_contract_for_item(item_name, data)

    if merc_contract is None and ctx is not None:

        merc_contract = _effective_mercenary_contract_for_item(ctx, item_name, data, owned_unlocks)

    if merc_contract is not None:

        return "Mercenaries"

    if _is_general_upgrade_item(item_name):

        return "General Upgrades"

    race = _item_race_key(item_name, data)

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    is_unit = _is_unit_or_morph_unlock_type(type_name) and not _is_mercenary_unit(item_name, data)

    specific = _is_unit_specific_upgrade(item_name)

    if race == "terran":

        return "Terran Units" if is_unit else "Terran Upgrades"

    if race == "zerg":

        return "Zerg Units" if is_unit else "Zerg Upgrades"

    if race == "protoss":

        return "Protoss Units" if is_unit else "Protoss Upgrades"

    return "General Upgrades"





def shop_sections(ctx: Any, stock: Sequence[str] | None = None) -> list[tuple[str, list[str]]]:

    if stock is None:

        stock = shop_stock(ctx)

    owned_unlocks = _owned_unlock_names(ctx)

    by_category: dict[str, list[str]] = {cat: [] for cat in SHOP_CATEGORY_ORDER}

    for item_name in stock:

        category = shop_category_for_item(item_name, ctx, owned_unlocks)

        if category in by_category:

            by_category[category].append(item_name)

    return [(cat, by_category[cat]) for cat in SHOP_CATEGORY_ORDER if by_category[cat]]





def frozen_shop_item(ctx: Any) -> str:
    if not enabled(ctx) or not state_ready(ctx):
        return ""
    return str(state(ctx).get("shop_frozen_item", "") or "")


def freeze_shop_item(ctx: Any, item_name: str) -> bool:
    """One persistent frozen offer, selectable in either shop view."""
    if not enabled(ctx) or not state_ready(ctx):
        return False
    name = str(item_name or "")
    if ctx is not None and str(getattr(ctx,"slay_config",{}).get("game_mode","adventure")) == "crew":
        # Crew stocks are counted roster offers, not normal AP unlock entries.
        if name and name not in ({
            e['name'] for entries in crew_catalog_offers(ctx).values() for e in entries
        } | {e['id'] for e in crew_boon_offers(ctx)}):
            return False
    elif name and name not in shop_stock(ctx):
        return False
    state(ctx)["shop_frozen_item"] = name
    _persist_state(ctx)
    return True


def _keep_frozen_shop_offer(ctx: Any, stock: Sequence[str]) -> list[str]:
    """Carry exactly one frozen offer forward without increasing stock size."""
    result = list(dict.fromkeys(str(item) for item in stock))
    frozen = frozen_shop_item(ctx)
    if not frozen or frozen in result:
        return result
    # Inventory capacity or current affordability never cancels a freeze.
    # Only purchasing the frozen item (handled by purchase()) clears it.
    category = shop_category_for_item(frozen, ctx)
    for i, candidate in enumerate(result):
        if candidate != _boon_id("reroll_shop") and shop_category_for_item(candidate, ctx) == category:
            result[i] = frozen
            return result
    # A category may disappear when an item becomes unlocked/rare. Keep the
    # frozen item at the expense of one non-guaranteed offer, never add a slot.
    for i, candidate in enumerate(result):
        if candidate != _boon_id("reroll_shop"):
            result[i] = frozen
            break
    return result


def preview_next_shop_reroll(ctx: Any) -> list[str]:



    if not enabled(ctx) or not state_ready(ctx):

        return []

    s = state(ctx)

    current = list(shop_stock(ctx))

    return _keep_frozen_shop_offer(ctx, _roll_shop_stock(

        ctx,

        victory_count(ctx),

        reroll_nonce=int(s.get("shop_reroll_nonce", 0)) + 1,

        previous_stock=current,

    ))





def is_reroll_shop_item(item_name: str) -> bool:

    return _parse_boon(str(item_name))[0] == "reroll_shop"





def shop_purchase_changes_stock(item_name: str) -> bool:



    kind = _parse_boon(str(item_name))[0]

    return (

        kind in {"reroll_shop", "shop_expansion"}

        or item_name in {TERRAN_CONTRACTS, ZERG_CONTRACTS, KERRIGAN_UNLOCK, SPEAR_UNLOCK}

    )





def _boon_id(kind: str, payload: str = "") -> str:

    return BOON_PREFIX + kind + ("::" + payload if payload else "")





def _parse_boon(item_name: str) -> tuple[str, str]:

    if not item_name.startswith(BOON_PREFIX): return "", ""

    parts = item_name.split("::", 2)

    return (parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "")





def boon_display_name(item_name: str) -> str:

    kind, payload = _parse_boon(item_name)

    if kind == "random_blessing":

        sev = int(payload or 1); rarity = {1:"Common",2:"Uncommon",3:"Rare",4:"Epic"}.get(sev,"Legendary")

        return f"Random Permanent Blessing ({rarity})"

    if kind == "permanent_blessing": return f"Permanent Blessing: {EFFECT_DISPLAY_NAMES.get(payload, payload)}"

    if kind == "upgrade_pack": return f"{payload.title()} Upgrade Pack"

    fixed = {

        "saving_grace":"Saving Grace", "reroll":"Reroll Mutations and Blessings", "shop_expansion":"Shop Expansion",

        "reroll_shop":"Reroll Shop", "deadly_weapons":"Deadly Weapons", "auto_repair":"Auto-repair",

        "rapid_fire":"Rapid-Fire", "shields_for_all":"Shields for all", "heavy_armor":"Heavy Armor",

        "unlimited_blink":"Unlimited Blink", "interplanetary_fortress":"Interplanetary Fortress",

        "roach_infestation":"Roach Infestation", "chain_reaction":"Chain Reaction",

        "aiur_recruitment":"For Aiur!", "toxic_observation":"Toxic Observation",

        "cloning_technology":"Cloning Technology", "defender":"Defender", "fire_power":"Fire Power",

        "roachling_mines":"Roachling Mines", "broodling_evolution":"Broodling evolution", "viking_anchors":"Viking Anchors",

        "adamantium_blades":"Adamantium Blades", "archon_cannons":"Archon Cannons",

        "corrosive_claws":"Corrosive Claws", "unlimited_power":"Unlimited Power", "unstable_colossi":"Unstable Colossi", "hyrda_storms":"Hyrda Storms", "mobile_siege":"Mobile Siege", "maddening_shades":"Maddening Shades", "concussed_shells":"Concussed Shells",

        "missile_defense":"Missile Defense System", "stretchy_spines":"Stretchy Spines", "gargantuan_units":"Gargantuan Units", "chaos_blessings":"Chaos Blessings", "risky_investment":"Risky Investment",

    }

    if kind in fixed: return fixed[kind]

    if kind in _NEW_BOON_TITLES: return _NEW_BOON_TITLES[kind]

    if kind == "golden_goose":

        return "Golden Goose Egg"









    effect_title = EFFECT_DISPLAY_NAMES.get("boon_" + kind, "")

    if effect_title:

        return effect_title

    return item_name





SHOP_DESCRIPTION_OVERRIDES = {
    SPEAR_BASE_PYLON_ITEM: "Your pylon now comes with a squad of reinforcements",
    **{name: "Allows the next tier of armor and weapon upgrades to be purchased during a mission."
       for name in RACE_WEAPON_ARMOR_UPGRADE_ITEMS},
}


def shop_entry_description(item_name: str) -> str:
    if item_name in SHOP_DESCRIPTION_OVERRIDES:
        return SHOP_DESCRIPTION_OVERRIDES[item_name]
    if item_name in POTION_CATALOG:
        return str(POTION_CATALOG[item_name]["description"])







    if item_name in {TERRAN_CONTRACTS, ZERG_CONTRACTS, SPEAR_UNLOCK}:
        return PROGRESSION_DESCRIPTIONS.get(item_name, "")

    if not item_name.startswith(BOON_PREFIX):

        documented = str(_AP_ITEM_DOCS.get(str(item_name), {}).get("description", "") or "").strip()

        if documented:

            return documented

    if item_name in PROGRESSION_DESCRIPTIONS:

        return PROGRESSION_DESCRIPTIONS[item_name]

    if item_name in _KERRIGAN_SHOP_CATALOG_ROWS:

        return str(_KERRIGAN_SHOP_CATALOG_ROWS[item_name].get(SHOP_CATALOG_DESCRIPTION_COLUMN, "")).strip()

    if item_name in _SPEAR_SHOP_CATALOG_ROWS:

        return str(_SPEAR_SHOP_CATALOG_ROWS[item_name].get(SHOP_CATALOG_DESCRIPTION_COLUMN, "")).strip()

    kind, payload = _parse_boon(item_name)

    if kind == "random_blessing":

        sev = int(payload or 1); rarity = {1:"Common",2:"Uncommon",3:"Rare",4:"Epic"}.get(sev,"Legendary")

        return "Permanently gain a random blessing (rarity) blessing".replace("(rarity)", rarity)

    if kind == "permanent_blessing":

        return f"Permanently gain the blessing: {EFFECT_DISPLAY_NAMES.get(payload,payload)}. {EFFECT_DESCRIPTIONS.get(payload,'')}".strip()

    if kind == "upgrade_pack": return "Gain 5 random upgrades for units you have already unlocked"







    if kind == "golden_goose":

        sev = GOLDEN_GOOSE_MUTATIONS.get(payload, 1)

        mutation_name = EFFECT_DISPLAY_NAMES.get(payload, payload)

        mutation_description = EFFECT_DESCRIPTIONS.get(payload, "")

        return f"Gain an extra {300 * sev} credits at the end of every mission, but permanently gain the mutation: {mutation_name}. {mutation_description}".strip()







    csv_title = boon_display_name(item_name)

    csv_description = str(_BOON_CATALOG_ROWS.get(csv_title, {}).get("Description", "")).strip()

    if csv_description:

        return csv_description

    descriptions = {

      "saving_grace":"Gain extra blessings just for the mission",

      "reroll":"Reroll all mutations and blessings for all missions. Credit rewards will be adjusted.",

      "shop_expansion":"There are more items available in the shop",

      "reroll_shop":"Reroll every item currently in the shop, including this one",

      "deadly_weapons":"Your units all deal 25% more damage",

      "auto_repair":"All of your units and structures gain 1 life and shield regeneration",

      "rapid_fire":"All your units and structures attack 30% faster",

      "shields_for_all":"Whenever you train a unit, it gains 50 shields",

      "heavy_armor":"Your thors, ultralisks, and archons gain 5 armor",

      "unlimited_blink":"Your stalkers can blink much more often",

      "interplanetary_fortress":"Your Planetary Fortresses gain 100 range",

      "roach_infestation":"Your roaches are free",

      "chain_reaction":"When an enemy dies, spawn a baneling where it died",

      "aiur_recruitment":"Whenever one of your zealots dies, there is a 10% chance of warping in reinforcements that automatically attack the enemy",

      "toxic_observation":"Enemies near your observers passively take damage",

      "cloning_technology":"Whenever you train a unit, also create a clone of that unit out of your control that automatically attacks the enemy",

      "defender":"Your defensive structures gain 50% range and damage",

      "fire_power":"Every time your fiery units kill an enemy, all fiery units gain 2% attack speed for the rest of the mission",

      "roachling_mines":"Your spider mines spawn 5 roachlings when they are destroyed",

      "broodling_evolution":"Your broodlings evolve permanently after kills: broodling to zergling to roach to ultralisk",

      "adamantium_blades":"All of your units' melee attacks deal double damage",

      "archon_cannons":"Your Photon Cannons and Dragoons shoot mini-archons with timed life",

      "viking_anchors":"While landed, Viking-family units cannot move but gain +10 armor, 2x attack speed, and +2 range.",

      "corrosive_claws":"Zergling-family attacks reduce the target's armor by 1 per hit, stacking indefinitely.",

      "unlimited_power":"Remove all cooldowns and energy requirements for all abilities.",

      "unstable_colossi":"Colossus-family units attack faster as they lose life, scaling from normal speed at full life to 5x speed near death.",

      "hyrda_storms":"Your hydralisk attack projectiles cause psionic storms when they land",

      "mobile_siege":"Siege tanks can still move while sieged",

      "maddening_shades":"When an adept shade successfully completes, spawn a random temporary unit at the destination",

      "concussed_shells":"Marauder missiles move 90% slower but deal 10x damage.",

      "missile_defense":"Your missile turrets gain +50% damage, range, hp, and attack speed",

      "stretchy_spines":"When a spine crawler kills a unit, permanently increase its range by 10%",

      "gargantuan_units":"All your units gain 50% health, armor, damage, and size",

      "chaos_blessings":"Randomly gain more blessings each mission",

      "risky_investment":"Add curses to the next mission, but gain 1000 extra credits on completion",

    }

    if kind in _NEW_BOON_TITLES:

        return str(_BOON_CATALOG_ROWS.get(_NEW_BOON_TITLES[kind], {}).get("Description", "")).strip()

    return descriptions.get(kind, "")





def shop_entry_display_name(item_name: str) -> str:
    if item_name in POTION_CATALOG:
        return str(POTION_CATALOG[item_name]["name"])

    if item_name in PROGRESSION_DISPLAY_NAMES:

        return PROGRESSION_DISPLAY_NAMES[item_name]

    hme_labels = {

        "Hive Mind Emulator": "Hive Mind Emulator (Zerg Control)",

        "Argus Amplifier (Hive Mind Emulator)": "Hive Mind Emulator (Protoss Control)",

        "Psi Indoctrinator (Hive Mind Emulator)": "Hive Mind Emulator (Terran Control)",

    }

    if item_name in hme_labels:

        return hme_labels[item_name]

    return boon_display_name(item_name) if item_name.startswith(BOON_PREFIX) else item_name





def _owned_name_contains(ctx: Any, terms: Sequence[str]) -> bool:



    return _owned_unlock_name_contains(_owned_unlock_names(ctx), terms)





def _owned_defensive_structure_count(ctx: Any) -> int:



    count = 0

    for name in DEFENSIVE_STRUCTURE_ITEMS:

        if _effective_owned_item_count(ctx, name) > 0:

            count += 1

    return count





def _boon_candidates(

    ctx: Any, rng: random.Random | None = None, shop_snapshot: Sequence[str] | None = None,

    owned_unlocks: set[str] | None = None,

) -> list[str]:



    if rng is None:

        seed = int.from_bytes(hashlib.sha256(f"{ctx.slay_config.get('run_seed',0)}:boon-candidates:{victory_count(ctx)}:{state(ctx).get('shop_reroll_nonce',0)}".encode()).digest()[:8], "big")

        rng = random.Random(seed)

    result: list[str] = []

    available_credits = credits(ctx)

    permanent = set(str(x) for x in state(ctx).get("permanent_blessings", []))

    owned_boons = set(str(x) for x in state(ctx).get("permanent_boons", []))







    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    owns = lambda terms: _owned_unlock_name_contains(owned_unlocks, terms)









    terran_infantry_terms = (

        "Marine", "War Pigs", "Firebat", "Devil Dogs", "Marauder",

        "Hammer Securities", "Medic", "Skibi", "Reaper", "Death Heads",

        "Ghost", "Spectre", "HERC", "Trooper",

    )

    has_terran_infantry = owns(terran_infantry_terms)



    if crew_mode(ctx):
        from .crew_challenge import eligible_effect
        severities = sorted({level for effect,level in BLESSING_SEVERITY.items()
                            if eligible_effect(effect,'blessing') and effect not in permanent})
    else:
        severities = sorted(set(BLESSING_SEVERITY.values()))

    affordable_severities = [sev for sev in severities if 250 * sev <= available_credits]

    if severities: result.append(_boon_id("random_blessing", str(rng.choice(affordable_severities or severities))))

    if crew_mode(ctx):
        from .crew_challenge import eligible_effect
        unowned = [x for x in BLESSING_SEVERITY if x not in permanent and eligible_effect(x,'blessing')]
    else:
        unowned = [x for x in BLESSING_SEVERITY if x not in permanent]

    affordable_specific = [x for x in unowned if 350 * BLESSING_SEVERITY[x] <= available_credits]

    if unowned: result.append(_boon_id("permanent_blessing", rng.choice(affordable_specific or unowned)))

    races = [str(x).casefold() for x in ctx.slay_config.get("races", []) if str(x).casefold() in {"terran","zerg","protoss"}]

    if shop_snapshot is None:

        shop_snapshot = shop_candidates(ctx)

    viable_races = [race for race in races if _upgrade_pack_race_is_unlocked(ctx, race, owned_unlocks) and _upgrade_pack_has_any_item(ctx, race, shop_snapshot, owned_unlocks)]

    if viable_races: result.append(_boon_id("upgrade_pack", rng.choice(viable_races)))

    frontier = current_frontier(ctx); choice_layers = int(ctx.slay_config.get("choice_layers", 11))

    frontier_layers = [int((node(ctx, mid) or {}).get("layer", 999)) for mid in frontier]

    if any(layer < choice_layers for layer in frontier_layers): result.append(_boon_id("saving_grace"))

    result.append(_boon_id("reroll"))





    if (int(state(ctx).get("shop_expansion", 0)) < SHOP_EXPANSION_MAX
            and any(layer < max(0, choice_layers - 2) for layer in frontier_layers)):

        result.append(_boon_id("shop_expansion"))

    result.append(_boon_id("reroll_shop"))



    fixed_effects = [

      ("deadly_weapons","boon_deadly_weapons",True),("auto_repair","boon_auto_repair",True),("rapid_fire","boon_rapid_fire",True),

      ("shields_for_all","boon_shields_for_all",True),("chain_reaction","boon_chain_reaction",owns(("Baneling",))),

      ("cloning_technology","boon_cloning_technology",True),

      ("heavy_armor","boon_heavy_armor",owns(("Thor","Ultralisk","Archon","Torrasque","Jotun"))),

      ("unlimited_blink","boon_unlimited_blink",owns(("Stalker","Slayer","Instigator"))),

      ("interplanetary_fortress","boon_interplanetary_fortress",owns(("Planetary Fortress",))),

      ("roach_infestation","boon_roach_infestation",owns(("Roach",))),

      ("aiur_recruitment","boon_aiur_recruitment",owns(("Zealot","Sentinel","Centurion"))),

      ("toxic_observation","boon_toxic_observation",owns(("Observer",))),

      ("defender","boon_defender",sum(1 for name in DEFENSIVE_STRUCTURE_ITEMS if name in owned_unlocks) >= 2),

      ("fire_power","boon_fire_power",owns(("Hellion","Firebat","Devil Dog","DevilDog","Hellbat","Colossus","Igniter","Flame","Fire","Perdition Turret","PerditionTurret"))),

      ("roachling_mines","boon_roachling_mines",owns(("Vulture","Spider Mine"))),

      ("broodling_evolution","boon_broodling_evolution",owns(("Brood Lord","BroodLord"))),

      ("adamantium_blades","boon_adamantium_blades",True),

      ("enhanced_control","boon_enhanced_control",owns(("Hive Mind Emulator","Dark Archon","Infestor"))),

      ("banshee_swarm","boon_banshee_swarm",owns(("Banshee",))),

      ("enlarged_banelings","boon_enlarged_banelings",owns(("Baneling",))),

      ("viking_anchors","boon_viking_anchors",owns(("Viking","Hel's Angel","HelsAngel","Brynhild","Brynhildr","Brynhilds"))),

      ("unlimited_power","boon_unlimited_power",True),

      ("unstable_colossi","boon_unstable_colossi",owns(("Colossus",))),

      ("archon_cannons","boon_archon_cannons",owns(("Photon Cannon","Dragoon"))),

      ("hyrda_storms","boon_hyrda_storms",owns(("Hydralisk","Hunter Killer","HunterKiller"))),

      ("maddening_shades","boon_maddening_shades",owns(("Adept",))),

      ("concussed_shells","boon_concussed_shells",owns(("Marauder","Hammer Securities","HammerSecurity","Hammer"))),

      ("missile_defense","boon_missile_defense",owns(("Missile Turret",))),

      ("stretchy_spines","boon_stretchy_spines",owns(("Spine Crawler",))),

      ("gargantuan_units","boon_gargantuan_units",True),

      ("chaos_blessings","boon_chaos_blessings",True),

      ("energized_queens","boon_energized_queens",owns(("Queen",))),

      ("goliaths_online","boon_goliaths_online",owns(("Goliath","Spartan Company","Spartan"))),

      ("regenerative_aberrations","boon_regenerative_aberrations",owns(("Aberration","Abberation"))),

      ("infantry_reinforcements","boon_infantry_reinforcements",has_terran_infantry),

      ("acidic_landing_markers","boon_acidic_landing_markers",owns(("Baneling",))),

      ("permanent_stimpack","boon_permanent_stimpack",has_terran_infantry),

      ("recycled_armor","boon_recycled_armor",has_terran_infantry),

      ("invasion_fleet","boon_invasion_fleet",True),

      ("dead_man_switch","boon_dead_man_switch",owns(("Spectre",))),

      ("reflective_carapace","boon_reflective_carapace",owns(("Roach","Ultralisk","Torrasque"))),

      ("cell_division","boon_cell_division",owns(("Ultralisk","Torrasque"))),

      ("spine_rifling","boon_spine_rifling",owns(("Hydralisk","Hunter Killer","HunterKiller"))),

      ("guided_shells","boon_guided_shells",owns(("Siege Tank","SiegeTank","Siege Breaker","SiegeBreaker"))),

      ("zergling_infestation","boon_zergling_infestation",owns(("Zergling",))),

      ("hyperion","boon_hyperion",owns(("Battlecruiser",))),

      ("leviathan","boon_leviathan",owns(("Corruptor",))),

      ("true_scouts","boon_true_scouts",owns(("Scout",))),

      ("true_carriers","boon_true_carriers",owns(("Carrier",))),

      ("deadly_vultures","boon_deadly_vultures",owns(("Vulture",))),

      ("immortal_immortals","boon_immortal_immortals",owns(("Immortal","Stalwart","Vanguard","Annihilator"))),

      ("kill_streak","boon_kill_streak",owns(("Ghost","Spectre"))),

      ("hit_and_run","boon_hit_and_run",owns(("Reaper","Death Heads","DeathHead"))),

      ("meat_grinder","boon_meat_grinder",owns(("Marine","War Pigs","WarPigs"))),

      ("reaper_blitz","boon_reaper_blitz",owns(("Reaper","Death Heads","DeathHead"))),

      ("purifier_alliance","boon_purifier_alliance",True),
      ("single_use_tools","boon_single_use_tools",True),
      ("eternal_perdition","boon_eternal_perdition",owns(("Perdition Turret","PerditionTurret"))),
      ("speedy_buildings","boon_speedy_buildings",True),
      ("enhanced_allies","boon_enhanced_allies",True),
      ("explosive_predators","boon_explosive_predators",owns(("Predator",))),
      ("harvesting_equipment","boon_harvesting_equipment",owns(("HERC","Herc"))),
      ("refective_diamondbacks","boon_refective_diamondbacks",owns(("Diamondback",))),
      ("psionic_guardians","boon_psionic_guardians",owns(("Guardian",))),
      ("improved_morphs","boon_improved_morphs",owns(("Igniter","Ravager","Guardian","Brood Lord","BroodLord","Overseer","Lurker","Impaler","Devourer","Baneling"))),
      ("psionic_lords","boon_psionic_lords",owns(("Templar","Archon","Sentry","Infestor","Oracle","Ghost","Spectre","Viper","HighTemplar"))),
      ("unlimited_scarabs","boon_unlimited_scarabs",owns(("Reaver",))),
      ("armor_disintegration","boon_armor_disintegration",owns(("Void Ray","VoidRay","Destroyer","Pulsar"))),

    ]

    for kind,effect,eligible in fixed_effects:

        if eligible and (effect not in owned_boons or kind in REPEATABLE_BOON_KINDS): result.append(_boon_id(kind))



    return list(dict.fromkeys(result))





def _roll_shop_stock(

    ctx: Any, cycle: int, *, reroll_nonce: int | None = None,

    previous_stock: Sequence[str] | None = None,

) -> list[str]:

    table = _item_table()

    logic_counts = _logic_owned_item_counts(ctx)

    owned_unlocks = _owned_unlock_names(ctx, logic_counts)

    candidates = shop_candidates(ctx, logic_counts, owned_unlocks, table)

    if reroll_nonce is None:

        reroll_nonce = int(state(ctx).get("shop_reroll_nonce", 0))

    avoid_items = set(str(x) for x in (previous_stock or ()))

    seed_material = f"{ctx.slay_config.get('run_seed', 0)}:shop-categories:{cycle}:{reroll_nonce}".encode("utf-8")

    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")

    rng = random.Random(seed)

    result: list[str] = []

    expansion = min(SHOP_EXPANSION_MAX, max(0, int(state(ctx).get("shop_expansion", 0))))



    def pool_for(category: str) -> list[str]:

        return [name for name in candidates if shop_category_for_item(name, ctx, owned_unlocks) == category]











    for race_name in ("Terran", "Zerg", "Protoss"):

        unit_category = f"{race_name} Units"

        unit_slots = (3 if cycle == 0 else SHOP_ITEMS_PER_CATEGORY) + expansion

        race_unit_stock = _weighted_shop_sample(
            ctx, rng, pool_for(unit_category), unit_slots, owned_unlocks, table, avoid_items
        )
        result.extend(race_unit_stock)



        upgrade_pool = [
            name for name in pool_for(f"{race_name} Upgrades")
            if _unit_upgrade_available_from_owned_or_current_stock(
                ctx, name, owned_unlocks, race_unit_stock, table
            )
        ]

        upgrade_slots = SHOP_ITEMS_PER_CATEGORY + expansion







        race_key = race_name.casefold()

        explicit_globals = [name for name in upgrade_pool if name in RACE_GLOBAL_UPGRADE_ITEMS.get(race_key, set())]

        chosen = _weighted_shop_sample(ctx, rng, explicit_globals, min(1, upgrade_slots), owned_unlocks, table, avoid_items)

        remainder = [name for name in upgrade_pool if name not in chosen]

        chosen.extend(_weighted_shop_sample(ctx, rng, remainder, max(0, upgrade_slots - len(chosen)), owned_unlocks, table, avoid_items))

        result.extend(chosen)







    result.extend(_weighted_shop_sample(

        ctx, rng, pool_for("Defensive Structures & Detectors"), 4 + expansion, owned_unlocks, table, avoid_items

    ))







    result.extend(_weighted_shop_sample(

        ctx, rng, pool_for("General Upgrades"), SHOP_ITEMS_PER_CATEGORY + expansion, owned_unlocks, table, avoid_items

    ))















    contracts = [item for item in (TERRAN_CONTRACTS, ZERG_CONTRACTS) if not _progression_owned(ctx, item)]

    result.extend(contracts)

    for contract in (TERRAN_CONTRACTS, ZERG_CONTRACTS):

        if not _progression_owned(ctx, contract):

            continue

        slot_count = 2 + expansion

        race_pool = [

            name for name in pool_for("Mercenaries")

            if _effective_mercenary_contract_for_item(ctx, name, table.get(name), owned_unlocks, table) == contract

        ]





        race_pool.extend(name for name in MERCENARY_CUSTOM_UPGRADE_ITEMS if can_buy_shop_item(ctx, name))

        race_pool = [name for name in dict.fromkeys(race_pool) if name not in result]

        new_merc_pool = [

            name for name in race_pool

            if table.get(name) is not None and _is_mercenary_unit(name, table.get(name))

            and not _progression_owned(ctx, name)

        ]

        chosen: list[str] = []

        if new_merc_pool and slot_count > 0:

            chosen.extend(_weighted_shop_sample(ctx, rng, new_merc_pool, 1, owned_unlocks, table, avoid_items))

        remainder = [name for name in race_pool if name not in chosen]

        chosen.extend(_weighted_shop_sample(

            ctx, rng, remainder, max(0, slot_count - len(chosen)), owned_unlocks, table, avoid_items

        ))

        result.extend(chosen)











    if not _progression_owned(ctx, KERRIGAN_UNLOCK):

        result.append(KERRIGAN_UNLOCK)

    else:

        kerrigan_pool = list(dict.fromkeys(pool_for("Kerrigan") + [

            name for name in KERRIGAN_CUSTOM_ITEMS if can_buy_shop_item(ctx, name)

        ]))

        kerrigan_slots = 2 + expansion

        level_pool = [name for name in kerrigan_pool if _is_kerrigan_level_item(name, table.get(name))]

        non_level_pool = [name for name in kerrigan_pool if name not in level_pool]

        kerrigan_chosen: list[str] = []









        if level_pool and kerrigan_slots > 0:

            kerrigan_chosen.extend(_weighted_shop_sample(

                ctx, rng, level_pool, 1, owned_unlocks, table, avoid_items

            ))

        remaining_slots = max(0, kerrigan_slots - len(kerrigan_chosen))

        if remaining_slots > 0:

            kerrigan_chosen.extend(_weighted_shop_sample(

                ctx, rng, non_level_pool, min(remaining_slots, len(non_level_pool)),

                owned_unlocks, table, avoid_items | set(kerrigan_chosen)

            ))

        result.extend(kerrigan_chosen)



    if not _progression_owned(ctx, SPEAR_UNLOCK):

        result.append(SPEAR_UNLOCK)

    else:

        spear_pool = pool_for("Spear of Adun") + [

            name for name in SPEAR_CUSTOM_ITEMS if can_buy_shop_item(ctx, name)

        ]

        result.extend(_weighted_shop_sample(ctx, rng, list(dict.fromkeys(spear_pool)), 2 + expansion, owned_unlocks, table, avoid_items))





    guaranteed_reroll = _boon_id("reroll_shop")

    boons = [x for x in _boon_candidates(ctx, rng, candidates, owned_unlocks) if x != guaranteed_reroll]

    boon_slots = 2 + expansion

    affordable = [x for x in boons if _price_for_item_before_sale(x, ctx) <= credits(ctx)]

    chosen = _weighted_shop_sample(ctx, rng, affordable, min(boon_slots, len(affordable)), owned_unlocks, table, avoid_items)

    if len(chosen) < boon_slots:

        chosen += _weighted_shop_sample(ctx, rng, [x for x in boons if x not in chosen], boon_slots-len(chosen), owned_unlocks, table, avoid_items)

    result.extend(chosen)

    result.append(guaranteed_reroll)
    # Shop Expansion also adds one independently rolled consumable offer.
    # This does not change the two-consumable carrying capacity.
    # Do not remove offers when inventory is full: present disabled purchase buttons.
    potion_offer_count = 2 + expansion
    potions = [p for p in POTION_CATALOG if not p.startswith(POTION_VARIANT_PREFIX) and _potion_unlock_eligible(ctx, p)]
    rng.shuffle(potions)
    # A random-spawn potion's generated title must be locked to the shop roll.
    # Roll a variant before storing stock, so rerolls can change the offered unit.
    chosen_potions = []
    for potion_id in (p for p in potions if p not in avoid_items):
        if len(chosen_potions) >= potion_offer_count:
            break
        if potion_id == POTION_PREFIX + "19":
            potion_id = POTION_VARIANT_PREFIX + str(rng.randint(1, len(POTION_RANDOM_UNITS)))
        chosen_potions.append(potion_id)
    if len(chosen_potions) < potion_offer_count:
        for potion_id in potions:
            if len(chosen_potions) >= potion_offer_count:
                break
            if potion_id == POTION_PREFIX + "19":
                potion_id = POTION_VARIANT_PREFIX + str(rng.randint(1, len(POTION_RANDOM_UNITS)))
            if potion_id not in chosen_potions:
                chosen_potions.append(potion_id)
    result.extend(chosen_potions)
    return list(dict.fromkeys(result))





def shop_stock(ctx: Any) -> list[str]:













    if not enabled(ctx) or not state_ready(ctx):

        return []

    cycle = victory_count(ctx)

    s = state(ctx)

    previous_cycle = int(s.get("shop_cycle", -1))

    purchase_cycle = int(s.get("shop_cycle_purchase_victory_count", -1))

    logic_version = int(s.get("shop_stock_logic_version", 0))

    if purchase_cycle != cycle:

        if purchase_cycle >= 0:

            s["shop_cycle_purchases"] = {}

        s["shop_cycle_purchase_victory_count"] = cycle

    if int(s.get("shop_reroll_purchase_victory_count", -1)) != cycle:

        s["shop_rerolls_this_cycle"] = 0

        s["shop_reroll_purchase_victory_count"] = cycle

    if previous_cycle != cycle or logic_version != SHOP_STOCK_LOGIC_VERSION:

        # Victory or a fresh stock generation restocks consumed shop offers.
        s["shop_potions_bought"] = []
        s["shop_cycle"] = cycle

        s["shop_stock_logic_version"] = SHOP_STOCK_LOGIC_VERSION

        s["shop_stock"] = _keep_frozen_shop_offer(ctx, _roll_shop_stock(ctx, cycle))



        s["shop_sale_items"] = []

        _persist_state(ctx)

    return [str(x) for x in s.get("shop_stock", [])]





def _eligible_sale_stock(ctx: Any) -> list[str]:





    return [name for name in shop_stock(ctx) if can_buy_shop_item(ctx, name)]





def preview_shop_sales(ctx: Any, stock: Sequence[str], *, reroll_nonce: int) -> list[str]:



    if not enabled(ctx) or not state_ready(ctx):

        return []

    eligible = [str(name) for name in stock if name not in POTION_CATALOG and can_buy_shop_item(ctx, str(name))]

    seed_material = f"{ctx.slay_config.get('run_seed',0)}:shop-sale:{victory_count(ctx)}:{int(reroll_nonce)}".encode("utf-8")

    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")

    rng = random.Random(seed)

    count = min(SHOP_SALE_COUNT, len(eligible))

    return rng.sample(eligible, count) if count else []





def _roll_shop_sales(ctx: Any) -> list[str]:

    if not enabled(ctx) or not state_ready(ctx):

        return []











    eligible = _eligible_sale_stock(ctx)

    s = state(ctx)





    sale = preview_shop_sales(ctx, eligible, reroll_nonce=int(s.get("shop_reroll_nonce", 0)))

    s["shop_sale_items"] = sale

    _persist_state(ctx)

    return sale





def begin_shop_visit(ctx: Any) -> list[str]:



    return shop_sale_items(ctx, preserve=True)





def shop_sale_items(ctx: Any, *, preserve: bool = True) -> list[str]:

    if not enabled(ctx) or not state_ready(ctx):

        return []

    s = state(ctx)

    current = [str(x) for x in s.get("shop_sale_items", [])]

    if current:

        return current

    return _roll_shop_sales(ctx)





def is_shop_sale_item(ctx: Any, item_name: str) -> bool:

    return str(item_name) in set(shop_sale_items(ctx, preserve=True))





def _price_for_item_before_track_discount(item_name: str, ctx: Any | None = None) -> int:

    cycle_buys = _shop_cycle_purchase_count(ctx, item_name) if ctx is not None and enabled(ctx) and state_ready(ctx) else 0

    kind, payload = _parse_boon(item_name)

    if kind:

        if kind == "random_blessing": return _same_shop_50_percent_price(250 * max(1, int(payload or 1)), cycle_buys)

        if kind == "permanent_blessing": return 350 * BLESSING_SEVERITY.get(payload, 1)

        if kind == "upgrade_pack": return _same_shop_50_percent_price(200, cycle_buys)

        if kind == "saving_grace": return _same_shop_50_percent_price(200, cycle_buys)

        if kind == "reroll": return _same_shop_50_percent_price(200, cycle_buys)

        if kind == "reroll_shop":

            reroll_buys = _shop_reroll_purchase_count(ctx) if ctx is not None and enabled(ctx) and state_ready(ctx) else 0

            return _same_shop_50_percent_price(100, reroll_buys)

        fixed_prices = {"shop_expansion":200,"deadly_weapons":800,"auto_repair":500,"rapid_fire":900,"shields_for_all":1000,"heavy_armor":500,"unlimited_blink":500,"interplanetary_fortress":1200,"roach_infestation":400,"chain_reaction":1600,"aiur_recruitment":700,"toxic_observation":500,"cloning_technology":1100,"defender":500,"fire_power":400,"roachling_mines":300,"broodling_evolution":400,"adamantium_blades":900,"enhanced_control":300,"banshee_swarm":400,"enlarged_banelings":500,"viking_anchors":300,"corrosive_claws":600,"unlimited_power":1400,"unstable_colossi":400,"archon_cannons":700,"hyrda_storms":400,"maddening_shades":500,"concussed_shells":400,"missile_defense":400,"stretchy_spines":300,"gargantuan_units":1600,"chaos_blessings":800,"risky_investment":50,"golden_goose":50,

            "energized_queens":400,"goliaths_online":400,"regenerative_aberrations":400,"infantry_reinforcements":600,"acidic_landing_markers":500,"permanent_stimpack":400,"recycled_armor":400,"invasion_fleet":1500,"dead_man_switch":500,"reflective_carapace":400,"cell_division":400,"spine_rifling":600,"guided_shells":500,"zergling_infestation":600,"hyperion":1400,"leviathan":1200,"true_scouts":300,"true_carriers":300,"deadly_vultures":400,"immortal_immortals":800,"kill_streak":400,"hit_and_run":400,"meat_grinder":500,"reaper_blitz":400,"purifier_alliance":1300,"single_use_tools":400,"eternal_perdition":400,"speedy_buildings":300,"enhanced_allies":600,"explosive_predators":400,"harvesting_equipment":400,"refective_diamondbacks":400,"psionic_guardians":400,"improved_morphs":600,"psionic_lords":800,"unlimited_scarabs":500,"armor_disintegration":500}

        base = fixed_prices.get(kind, 999999)

        csv_title = boon_display_name(item_name)

        csv_cost = str(_BOON_CATALOG_ROWS.get(csv_title, {}).get("Cost", "")).strip()

        if re.fullmatch(r"\d+", csv_cost):

            base = int(csv_cost)





        if kind in REPEATABLE_BOON_KINDS or kind in {"shop_expansion", "risky_investment"}:

            return _same_shop_50_percent_price(base, cycle_buys)

        return base

    if item_name == TERRAN_CONTRACTS or item_name == ZERG_CONTRACTS:

        return 100

    if item_name in MERCENARY_CUSTOM_UPGRADE_ITEMS:

        title = MERCENARY_CUSTOM_UPGRADE_TITLES[item_name]

        return _same_shop_50_percent_price(MERCENARY_SHOP_PRICE_OVERRIDES.get(title, 999999), cycle_buys)

    if item_name in MERCENARY_GENERAL_UPGRADE_ITEMS:

        return _same_shop_50_percent_price(MERCENARY_SHOP_PRICE_OVERRIDES.get(item_name, 200), cycle_buys)

    if item_name == KERRIGAN_UNLOCK:

        return KERRIGAN_SHOP_PRICE_OVERRIDES.get("Unlock Kerrigan", 400)

    if item_name in KERRIGAN_CUSTOM_ITEMS:

        title = PROGRESSION_DISPLAY_NAMES[item_name]

        return _same_shop_50_percent_price(KERRIGAN_SHOP_PRICE_OVERRIDES.get(title, 999999), cycle_buys)

    if item_name == SPEAR_UNLOCK:

        return SPEAR_SHOP_PRICE_OVERRIDES.get("Unlock Spear of Adun", 500)

    if item_name in SPEAR_CUSTOM_ITEMS:

        title = PROGRESSION_DISPLAY_NAMES[item_name]

        return _same_shop_50_percent_price(SPEAR_SHOP_PRICE_OVERRIDES.get(title, 999999), cycle_buys)



    data = _item_table().get(item_name)

    if data is None:

        return 999999

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))



    if _is_kerrigan_level_item(item_name, data):

        match = re.match(r"^\s*(\d+)\s+Kerrigan Levels?\b", str(item_name), re.IGNORECASE)

        level_count = max(1, int(match.group(1))) if match else 1

        return _same_shop_50_percent_price(15 * level_count, cycle_buys)

    if _is_kerrigan_item(item_name, data):

        return _same_shop_50_percent_price(KERRIGAN_SHOP_PRICE_OVERRIDES.get(item_name, 150), cycle_buys)

    if _is_spear_item(item_name, data):

        base = SPEAR_SHOP_PRICE_OVERRIDES.get(

            item_name, 100 if _spear_cheap_item(item_name) else 200

        )

        return _same_shop_50_percent_price(base, cycle_buys)

    if _is_mercenary_unit(item_name, data):

        return _same_shop_50_percent_price(100, cycle_buys)

    if _mercenary_contract_for_item(item_name, data) is not None:

        if _is_mercenary_general_upgrade(item_name, data):

            return _same_shop_50_percent_price(MERCENARY_SHOP_PRICE_OVERRIDES.get(item_name, 200), cycle_buys)

        if _is_unit_specific_upgrade(item_name):

            return _same_shop_50_percent_price(80, cycle_buys)

        return _same_shop_50_percent_price(150, cycle_buys)







    if item_name in UNIT_SHOP_PRICE_OVERRIDES:

        return _same_shop_50_percent_price(UNIT_SHOP_PRICE_OVERRIDES[item_name], cycle_buys)

    if item_name == RESEARCH_SPEED_ITEM:

        return _same_shop_50_percent_price(100, cycle_buys)

    if _is_general_upgrade_item(item_name):

        return _same_shop_50_percent_price(100, cycle_buys)

    if item_name in RACE_WEAPON_ARMOR_UPGRADE_ITEMS:

        return _same_shop_50_percent_price(100, cycle_buys)

    if _is_unit_specific_upgrade(item_name):

        return _same_shop_50_percent_price(80, cycle_buys)

    if _is_morph_unlock_type(type_name):





        return _same_shop_50_percent_price(80, cycle_buys)

    if _is_unit_unlock_type(type_name):

        variant_family_price = _variant_family_unit_price(item_name)

        base_unit_price = (

            int(variant_family_price)

            if variant_family_price is not None

            else UNIT_SHOP_PRICE_OVERRIDES.get(item_name, 150)

        )

        return _same_shop_50_percent_price(base_unit_price, cycle_buys)

    if shop_category_for_item(item_name) in {"Terran Upgrades", "Zerg Upgrades", "Protoss Upgrades"}:

        return _same_shop_50_percent_price(100, cycle_buys)

    if type_name == "Building":

        return _same_shop_50_percent_price(180, cycle_buys)

    if type_name in _ECONOMY_TYPES:

        return _same_shop_50_percent_price(100, cycle_buys)

    return _same_shop_50_percent_price(120, cycle_buys)





def _price_for_item_before_sale(item_name: str, ctx: Any | None = None) -> int:
    if item_name in POTION_CATALOG:
        return int(POTION_CATALOG[item_name]["price"])

    base = int(_price_for_item_before_track_discount(item_name, ctx))

    if ctx is None or not enabled(ctx) or not state_ready(ctx):

        return base

    data = _item_table().get(item_name)

    is_kerrigan_track = item_name == KERRIGAN_UNLOCK or item_name in KERRIGAN_CUSTOM_ITEMS or (data is not None and _is_kerrigan_item(item_name, data))

    is_spear_track = item_name == SPEAR_UNLOCK or item_name in SPEAR_CUSTOM_ITEMS or (data is not None and _is_spear_item(item_name, data))





    if is_kerrigan_track and item_name != KERRIGAN_PRICE_DISCOUNT and _progression_owned(ctx, KERRIGAN_PRICE_DISCOUNT):

        base = max(1, (base + 1) // 2)

    if is_spear_track and item_name != SPEAR_PRICE_DISCOUNT and _progression_owned(ctx, SPEAR_PRICE_DISCOUNT):

        base = max(1, (base + 1) // 2)

    return base





def price_for_item(

    item_name: str,

    ctx: Any | None = None,

    *,

    sale_items_override: Sequence[str] | None = None,

) -> int:

    if item_name in POTION_CATALOG:
        return int(POTION_CATALOG[item_name]["price"])  # fixed rarity price, not sale/stack-adjusted
    base = _price_for_item_before_sale(item_name, ctx)

    if ctx is not None and enabled(ctx) and state_ready(ctx):









        sale_source = sale_items_override if sale_items_override is not None else state(ctx).get("shop_sale_items", [])

        if str(item_name) in set(str(x) for x in sale_source):







            half_price = max(1, (int(base) + 1) // 2)

            capped_price = max(1, int(base) - 400)

            return max(half_price, capped_price)

    return int(base)





def purchased_count(ctx: Any, item_name: str) -> int:

    if not enabled(ctx) or not state_ready(ctx): return 0

    kind, _ = _parse_boon(item_name)

    if kind: return int(state(ctx).get("boon_purchases", {}).get(item_name, 0))

    return _purchased_count(ctx, item_name)





def can_buy_shop_item(ctx: Any, item_name: str) -> bool:

    if not enabled(ctx) or not state_ready(ctx): return False
    if item_name in POTION_CATALOG:
        # Each individual offer may be bought only once until reroll or victory,
        # even if the player uses it and opens an inventory slot again.
        return (item_name not in state(ctx).get("shop_potions_bought", ())
                and len(potion_inventory(ctx)) < POTION_CAPACITY
                and _potion_unlock_eligible(ctx, item_name))

    if item_name in {TERRAN_CONTRACTS, ZERG_CONTRACTS, KERRIGAN_UNLOCK, SPEAR_UNLOCK}:

        return not _progression_owned(ctx, item_name)

    if item_name in MERCENARY_CUSTOM_UPGRADE_ITEMS:

        return _progression_owned(ctx, TERRAN_CONTRACTS) or _progression_owned(ctx, ZERG_CONTRACTS)

    if item_name in {SPEAR_ENERGY_REGEN, SPEAR_COOLDOWN_REDUCTION}:

        return _progression_owned(ctx, SPEAR_UNLOCK) and _purchased_count(ctx, item_name) < 3

    if item_name == SPEAR_PRICE_DISCOUNT:

        return _progression_owned(ctx, SPEAR_UNLOCK) and not _progression_owned(ctx, item_name)

    if item_name in {KERRIGAN_RECKLESS_POWER, KERRIGAN_RECKLESS_SPEED}:

        return _progression_owned(ctx, KERRIGAN_UNLOCK)

    if item_name == KERRIGAN_PRICE_DISCOUNT:

        return _progression_owned(ctx, KERRIGAN_UNLOCK) and not _progression_owned(ctx, item_name)

    if _is_progression_item(item_name):

        return False

    table = _item_table()

    data = table.get(item_name)

    if data is not None and _is_deprecated_item(item_name, data):

        return False

    if data is not None and _is_kerrigan_level_item(item_name, data):

        return _progression_owned(ctx, KERRIGAN_UNLOCK)

    if data is not None:

        owned_unlocks = _owned_unlock_names(ctx)

        if (

            _unit_upgrade_requires_locked_unit(ctx, item_name, owned_unlocks, table)

            and not _unit_upgrade_has_shop_available_parent(ctx, item_name, owned_unlocks, table)

        ):

            return False

        contract = _effective_mercenary_contract_for_item(ctx, item_name, data)

        if contract is not None and not _progression_owned(ctx, contract):

            return False

        if _is_kerrigan_item(item_name, data) and not _progression_owned(ctx, KERRIGAN_UNLOCK):

            return False

        if _is_spear_item(item_name, data) and not _progression_owned(ctx, SPEAR_UNLOCK):

            return False

    kind, payload = _parse_boon(item_name)

    if not kind: return _eligible_to_buy(ctx, item_name)

    s = state(ctx)

    if kind == "shop_expansion":
        return int(s.get("shop_expansion", 0)) < SHOP_EXPANSION_MAX

    if kind == "permanent_blessing": return payload not in s.get("permanent_blessings", [])

    if kind == "upgrade_pack":
        return _upgrade_pack_race_is_unlocked(ctx, payload, _owned_unlock_names(ctx))

    if kind == "golden_goose": return payload in GOLDEN_GOOSE_MUTATIONS and payload not in DISABLED_MUTATIONS and payload not in s.get("permanent_mutations", [])

    effect = {

        "deadly_weapons":"boon_deadly_weapons", "auto_repair":"boon_auto_repair",

        "rapid_fire":"boon_rapid_fire", "shields_for_all":"boon_shields_for_all",

        "heavy_armor":"boon_heavy_armor", "unlimited_blink":"boon_unlimited_blink",

        "interplanetary_fortress":"boon_interplanetary_fortress", "roach_infestation":"boon_roach_infestation",

        "chain_reaction":"boon_chain_reaction", "aiur_recruitment":"boon_aiur_recruitment",

        "toxic_observation":"boon_toxic_observation", "cloning_technology":"boon_cloning_technology",

        "defender":"boon_defender", "fire_power":"boon_fire_power",

        "roachling_mines":"boon_roachling_mines", "broodling_evolution":"boon_broodling_evolution",

        "adamantium_blades":"boon_adamantium_blades", "enhanced_control":"boon_enhanced_control",

        "banshee_swarm":"boon_banshee_swarm", "enlarged_banelings":"boon_enlarged_banelings",

        "viking_anchors":"boon_viking_anchors",

        "corrosive_claws":"boon_corrosive_claws", "unlimited_power":"boon_unlimited_power",

        "unstable_colossi":"boon_unstable_colossi", "archon_cannons":"boon_archon_cannons", "hyrda_storms":"boon_hyrda_storms", "mobile_siege":"boon_mobile_siege", "maddening_shades":"boon_maddening_shades", "concussed_shells":"boon_concussed_shells",

        "missile_defense":"boon_missile_defense", "stretchy_spines":"boon_stretchy_spines", "gargantuan_units":"boon_gargantuan_units", "chaos_blessings":"boon_chaos_blessings",

        **_NEW_BOON_EFFECT_BY_KIND,

    }.get(kind)

    if effect is not None:

        return kind in REPEATABLE_BOON_KINDS or effect not in s.get("permanent_boons", [])

    if kind == "saving_grace":

        frontier = current_frontier(ctx)

        choice_layers = int(ctx.slay_config.get("choice_layers", 11))

        return any(int((node(ctx, mid) or {}).get("layer", 999)) < choice_layers for mid in frontier)

    return True







def shop_render_states(

    ctx: Any,

    item_names: Sequence[str],

    *,

    sale_items_override: Sequence[str] | None = None,

) -> dict[str, tuple[int, bool, int]]:













    names = [str(name) for name in item_names]

    table = _item_table()

    logic_counts = _logic_owned_item_counts(ctx)

    owned_unlocks = _owned_unlock_names(ctx, logic_counts)

    purchases = state(ctx).get("purchases", {}) if enabled(ctx) and state_ready(ctx) else {}

    result: dict[str, tuple[int, bool, int]] = {}

    for item_name in names:

        bought = purchased_count(ctx, item_name)

        price = price_for_item(item_name, ctx, sale_items_override=sale_items_override)

        kind, _ = _parse_boon(item_name)

        # Potions are native Slay shop entries, not Archipelago items. They
        # have no AP item-table code, so the generic branch below always
        # marked them unavailable even with two empty inventory slots.
        if item_name in POTION_CATALOG or kind or _is_progression_item(item_name):

            can_buy = can_buy_shop_item(ctx, item_name)

        else:

            data = table.get(item_name)

            if data is None or getattr(data, "code", None) is None:

                can_buy = False

            else:

                cap = _max_owned_copies(data)

                if cap is None:

                    can_buy = True

                else:

                    shop_copies = _effective_shop_copies(item_name, int(purchases.get(item_name, 0)))

                    raw_actual = max(0, int(logic_counts.get(item_name, 0)) - shop_copies)

                    if item_name in FIVE_X_GENERIC_UPGRADE_ITEMS:

                        raw_actual *= 5

                    can_buy = raw_actual + shop_copies < cap

        if can_buy and item_name not in POTION_CATALOG and not kind and not _is_progression_item(item_name):

            data = table.get(item_name)

            if data is not None:

                if (

                    _unit_upgrade_requires_locked_unit(ctx, item_name, owned_unlocks, table)

                    and not _unit_upgrade_has_shop_available_parent(ctx, item_name, owned_unlocks, table)

                ):

                    can_buy = False

                contract = _effective_mercenary_contract_for_item(ctx, item_name, data, owned_unlocks, table)

                if contract is not None and not _progression_owned(ctx, contract):

                    can_buy = False

                if _is_kerrigan_item(item_name, data) and not _progression_owned(ctx, KERRIGAN_UNLOCK):

                    can_buy = False

                if _is_spear_item(item_name, data) and not _progression_owned(ctx, SPEAR_UNLOCK):

                    can_buy = False

        result[item_name] = (bought, can_buy, price)

    return result



def _chat(ctx: Any, message: str) -> None:

    try: ctx.on_print_json({"data": [{"text": message}]})

    except Exception: logger.info(message)





def _game_chat(ctx: Any, message: str) -> None:



    announcements = getattr(ctx, "announcements", None)

    if announcements is None:

        return

    try:

        announcements.append(message)

    except Exception:

        try:

            announcements.put_nowait(message)

        except Exception:

            logger.debug("Could not queue SC2 announcement: %s", message)





def _choose_blessings_exact(target: int, rng: random.Random, forbidden: Iterable[str] = ()) -> list[str]:

    pool = [x for x in BLESSING_SEVERITY if x not in set(forbidden)]

    rng.shuffle(pool)



    def rec(index: int, remain: int, chosen: list[str]) -> list[str] | None:

        if remain == 0: return list(chosen)

        if remain < 0: return None

        for j in range(index, len(pool)):

            sev = BLESSING_SEVERITY[pool[j]]

            if sev <= remain:

                got = rec(j+1, remain-sev, chosen+[pool[j]])

                if got is not None: return got

        return None

    return rec(0, int(target), []) or []





def _assign_saving_grace(ctx: Any, mission_id: int) -> None:

    s = state(ctx)

    if int(s.get("saving_grace_charges", 0)) <= 0: return

    seed = int.from_bytes(hashlib.sha256(f"{ctx.slay_config.get('run_seed',0)}:saving:{mission_id}:{s.get('saving_grace_charges',0)}".encode()).digest()[:8], "big")

    data = node(ctx, mission_id) or {}

    existing = set(data.get("blessings", [])) | set(s.get("permanent_blessings", []))







    for effect in BLESSING_SEVERITY:

        if not _blessing_allowed_for_mission(ctx, mission_id, effect):

            existing.add(effect)

    pending = list(s.get("saving_grace_pending", []))
    chosen: list[str] = []
    if pending:
        candidate = [str(e) for e in pending[0]]
        if candidate and not any(e in existing for e in candidate):
            chosen = candidate
        # Never quietly discard an announced package: an unavailable mission
        # combination is surfaced and the charge remains for another choice.
        elif candidate:
            _chat(ctx, "Saving Grace: announced blessings are ineligible for this mission; charge preserved.")
            return

    for target in ([] if chosen else range(5, 0, -1)):

        chosen = _choose_blessings_exact(target, random.Random(seed + (5 - target)), existing)

        if chosen:

            break

    if not chosen:

        _chat(ctx, "Saving Grace: no legal blessing package exists for this mission; charge preserved.")

        return

    temp = dict(s.get("temporary_blessings", {}))

    temp[str(mission_id)] = chosen

    s["temporary_blessings"] = temp

    s["saving_grace_charges"] = max(0, int(s.get("saving_grace_charges", 0)) - 1)
    if pending:
        s["saving_grace_pending"] = pending[1:]

    _persist_state(ctx)

    _chat(ctx, "Saving Grace: " + ", ".join(EFFECT_DISPLAY_NAMES.get(x, x) for x in chosen))





def _owned_race_unit_unlock_count(
    ctx: Any, race: str, owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None,
) -> int:
    """Count actual owned unit/morph unlocks for a race (not buildings, mercenaries, or upgrades)."""
    if table is None:
        table = _item_table()
    if owned_unlocks is None:
        owned_unlocks = _owned_unlock_names(ctx)
    wanted = str(race).casefold()
    count = 0
    for name in owned_unlocks:
        data = table.get(name)
        if data is None:
            continue
        type_name = str(getattr(getattr(data, "type", None), "display_name", ""))
        if not _is_unit_or_morph_unlock_type(type_name):
            continue
        if _is_mercenary_unit(name, data) or _is_nova_campaign_item(name, data) or _is_royal_guard_item(name, data, table):
            continue
        if _item_race_key(name, data) == wanted:
            count += 1
    return count


def _upgrade_pack_race_is_unlocked(
    ctx: Any, race: str, owned_unlocks: set[str] | None = None, table: Mapping[str, Any] | None = None,
) -> bool:
    return _owned_race_unit_unlock_count(ctx, race, owned_unlocks, table) >= 3


def _eligible_upgrade_pack_items(

    ctx: Any, race: str, candidates: Sequence[str] | None = None, owned_unlocks: set[str] | None = None

) -> list[str]:



    if candidates is None:

        candidates = shop_candidates(ctx)

    if owned_unlocks is None:

        owned_unlocks = _owned_unlock_names(ctx)

    out: list[str] = []

    table = _item_table()

    for name in candidates:

        if _item_race_key(name) != race.casefold():

            continue

        if _owned_unit_upgrade_parent(ctx, name, owned_unlocks, table) is not None:

            out.append(name)

    return list(dict.fromkeys(out))





def _eligible_upgrade_pack_general_items(

    ctx: Any, candidates: Sequence[str] | None = None

) -> list[str]:



    if candidates is None:

        candidates = shop_candidates(ctx)

    return list(dict.fromkeys(name for name in candidates if _is_general_upgrade_item(name)))





def _upgrade_pack_has_any_item(

    ctx: Any, race: str, candidates: Sequence[str] | None = None, owned_unlocks: set[str] | None = None

) -> bool:

    return bool(

        _eligible_upgrade_pack_items(ctx, race, candidates, owned_unlocks)

        or _eligible_upgrade_pack_general_items(ctx, candidates)

    )





def _apply_upgrade_pack(ctx: Any, race: str, seed_tag: str) -> list[str]:

    candidates = shop_candidates(ctx)

    owned_unlocks = _owned_unlock_names(ctx)

    specific_pool = _eligible_upgrade_pack_items(ctx, race, candidates, owned_unlocks)

    rng = random.Random(int.from_bytes(hashlib.sha256(seed_tag.encode()).digest()[:8], "big"))

    picked = _weighted_shop_sample(ctx, rng, specific_pool, 5, owned_unlocks)

    if len(picked) < 5:

        fallback = [

            name for name in _eligible_upgrade_pack_general_items(ctx, candidates)

            if name not in picked

        ]

        picked.extend(_weighted_shop_sample(ctx, rng, fallback, 5 - len(picked), owned_unlocks))

    purchases = dict(state(ctx).get("purchases", {}))

    for name in picked:

        purchases[name] = int(purchases.get(name, 0)) + 1

    state(ctx)["purchases"] = purchases

    return picked





def _generator_module() -> Any | None:

    path=_archipelago_root()/"SlayTheStarCraft.py"

    if not path.is_file(): return None

    try:

        spec=importlib.util.spec_from_file_location("_slay_generator_runtime", path)

        if spec is None or spec.loader is None: return None

        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

    except Exception as exc:

        logger.warning("Slay boon reroll could not load generator: %s", exc); return None





def _reroll_future_nodes(ctx: Any, purchase_index: int) -> int:

    gen=_generator_module(); s=state(ctx)

    if gen is None: return 0

    current_nodes = nodes(ctx)















    easy_opening_mid = None

    easy_candidates = []

    for candidate_mid, candidate in current_nodes.items():

        if int(candidate.get("layer", 0)) != 0 or int(candidate.get("mission_pool", 0)) != 0:

            continue

        if node_status(ctx, candidate_mid) not in {"future", "available", "selected"}:

            continue

        locs = set(ctx.locations_for_mission_id(candidate_mid))

        missing = set(getattr(ctx, "missing_locations", set()))

        if locs and not locs.issubset(missing):

            continue

        easy_candidates.append((int(candidate.get("lane", 99)), int(candidate_mid)))

    if easy_candidates:

        easy_opening_mid = min(easy_candidates)[1]



    overrides=dict(s.get("node_effect_overrides",{})); changed=0

    for mid, original in sorted(current_nodes.items()):

        status=node_status(ctx,mid)

        if status not in {"future","available","selected"}: continue



        # The currently selected unfinished mission must reroll too. If it is
        # already running, the live SC2 process keeps its launch snapshot; the
        # persisted override is picked up automatically on the next retry/boot.
        # Unlike untouched future nodes, do not reject the selected mission just
        # because the player already collected a location during this attempt.
        if status != "selected":
            locs=set(ctx.locations_for_mission_id(mid)); missing=set(getattr(ctx,"missing_locations",set()))
            if locs and not locs.issubset(missing): continue

        seed=int.from_bytes(hashlib.sha256(f"{ctx.slay_config.get('run_seed',0)}:boon-reroll:{purchase_index}:{mid}".encode()).digest()[:8],"big")

        rng=random.Random(seed)

        mission_name=_mission_base_name(original.get("mission_name",""))

        forbidden_mut={"limited_bank"} if mission_name in {"Devil's Playground","Cutthroat"} else set()
        if mission_name.strip().casefold() == "the great train robbery":
            forbidden_mut.add("victory_is_temporary")

        if str(mission_name).startswith("Rak'Shir"): forbidden_mut.add("burrowed_zerglings")

        forbidden_mut.update(gen.crucible_mutation_exclusions(mission_name))
        if mission_name.strip().casefold() in {"evacuation", "the evacuation"}:
            forbidden_mut.add("nuclear_annihilation")

        if mission_name.casefold() in ISLAND_MISSION_NAMES:

            forbidden_mut.update({"torrasque", "ten_minutes_until_destruction"})

        dependency_forbidden_mut, dependency_forbidden_bless = gen.dependency_sensitive_effect_exclusions(

            mission_name

        )

        forbidden_mut.update(dependency_forbidden_mut)

        race=str(original.get("race","")).casefold()

        forbidden_bless=set(dependency_forbidden_bless)

        if race != "terran": forbidden_bless.add("rapid_repair")

        if race != "zerg": forbidden_bless.update({"stealth_tunnels","infinite_larva"})

        if mission_name == "Devil's Playground": forbidden_bless.add("rich_minerals")



        require_easy = not campaign_mode(ctx) and int(mid) == easy_opening_mid
        is_campaign_final = (campaign_mode(ctx) and
                             int(original.get("layer", 0)) >= int(ctx.slay_config.get("choice_layers", 11)))
        risk_threshold = (gen.campaign_final_risk_threshold(
            int(ctx.slay_config.get("choice_layers", 11)),
            str(ctx.slay_config.get("difficulty", "brutal")),
            ctx.slay_config.get("mutation_frequency", 1.0),
            ctx.slay_config.get("blessing_frequency", 1.0)) if is_campaign_final else None)
        attempts = (256 if is_campaign_final and
                    gen._frequency_factor(ctx.slay_config.get("mutation_frequency", 1.0)) > 0
                    else 32 if require_easy else 1)
        best_final_roll = None

        reward = 0

        muts = []

        bless = []

        mv = 0

        bv = 0

        for _attempt in range(attempts):

            muts,bless,mv,bv=gen.roll_effects(

                int(original.get("layer",0)), int(ctx.slay_config.get("choice_layers",11)),

                str(ctx.slay_config.get("difficulty","brutal")), rng,

                final=int(original.get("layer",0))>=int(ctx.slay_config.get("choice_layers",11)),

                forbidden_mutators=forbidden_mut, forbidden_blessings=forbidden_bless,

                mission_pool=int(original.get("mission_pool",0)),

                mutation_frequency=ctx.slay_config.get("mutation_frequency", 1.0),

                blessing_frequency=ctx.slay_config.get("blessing_frequency", 1.0),
                mutation_severity_bonus=(gen.campaign_mutation_severity_bonus(
                    int(original.get("layer", 0)), int(ctx.slay_config.get("choice_layers", 11)))
                    if campaign_mode(ctx) else 0),

            )

            reward=gen.credit_reward(

                int(original.get("mission_pool",0)), int(original.get("layer",0)),

                mv, bv, bool(bless), rng, mission_name=mission_name,

            )

            if is_campaign_final:
                score = gen.campaign_final_risk_score(
                    int(original.get("mission_pool", 0)), int(original.get("layer", 0)), mv, bv)
                if best_final_roll is None or score > best_final_roll[0]:
                    best_final_roll = (score, list(muts), list(bless), mv, bv)
                if score >= risk_threshold:
                    break
            elif not require_easy or reward <= 350:
                break

        if is_campaign_final and best_final_roll is not None:
            _score, muts, bless, mv, bv = best_final_roll



        if require_easy and reward > 350:







            legal_blessings = [name for name in gen.BLESSINGS if name not in forbidden_bless]

            if not legal_blessings:

                raise RuntimeError("No legal blessing is available for the guaranteed easy opening reroll")

            picked = rng.choice(legal_blessings)

            muts=[]; bless=[picked]; mv=0; bv=int(gen.BLESSINGS[picked])

            reward=gen.credit_reward(

                int(original.get("mission_pool",0)), int(original.get("layer",0)),

                mv, bv, True, rng, mission_name=mission_name,

            )

            if reward > 350:

                raise RuntimeError("Could not preserve a <=350-credit opening mission after effect reroll")



        reward = gen.credit_reward(

            int(original.get("mission_pool",0)), int(original.get("layer",0)),

            mv, bv, bool(bless), rng, mission_name=mission_name,

            victory_credit_reward_multiplier=float(ctx.slay_config.get("victory_credit_reward_multiplier", 1.0)),

        )

        commander_index, commander_name = (-1, "")

        if "general" in bless:

            commander_index, commander_name = _stable_commander_choice(

                int(ctx.slay_config.get("run_seed", 0)), int(mid)

            )

        overrides[str(mid)]={

            "mutators":muts,"blessings":bless,"mutation_value":mv,"blessing_value":bv,

            "credit_reward":reward,"commander_hero_index":int(commander_index),

            "commander_hero_name":commander_name,
            **({"high_risk": True} if is_campaign_final else {}),

        }

        changed+=1

    s["node_effect_overrides"]=overrides

    return changed





def _assign_risky_investment(ctx: Any, mission_id: int) -> None:

    s = state(ctx)

    charges = int(s.get("risky_investment_charges", 0))

    if charges <= 0:

        return

    data = _merged_nodes(ctx).get(int(mission_id), {})

    existing = set(data.get("mutators", [])) | set(s.get("permanent_mutations", []))

    seed = int.from_bytes(hashlib.sha256(

        f"{ctx.slay_config.get('run_seed',0)}:risky:{mission_id}:{charges}".encode()

    ).digest()[:8], "big")

    rng = random.Random(seed)

    pool = [x for x in GOLDEN_GOOSE_MUTATIONS if x not in existing and x not in DISABLED_MUTATIONS]

    rng.shuffle(pool)







    chosen: list[str] | None = None

    def rec(index: int, remain: int, picked: list[str]) -> None:

        nonlocal chosen

        if chosen is not None:

            return

        if remain == 0:

            chosen = list(picked)

            return

        if remain < 0:

            return

        for j in range(index, len(pool)):

            sev = int(GOLDEN_GOOSE_MUTATIONS[pool[j]])

            if sev <= remain:

                rec(j + 1, remain - sev, picked + [pool[j]])

                if chosen is not None:

                    return

    rec(0, 4, [])

    if not chosen:

        _chat(ctx, "Risky Investment could not find a legal exact 4-severity package; charge preserved.")

        return



    overrides = dict(s.get("node_effect_overrides", {}))

    current = copy.deepcopy(overrides.get(str(mission_id), data))

    current["mutators"] = list(dict.fromkeys(list(current.get("mutators", data.get("mutators", []))) + chosen))

    current["mutation_value"] = int(current.get("mutation_value", data.get("mutation_value", 0))) + 4

    current["credit_reward"] = int(current.get("credit_reward", data.get("credit_reward", 0))) + 1000

    overrides[str(mission_id)] = current

    s["node_effect_overrides"] = overrides

    s["risky_investment_charges"] = charges - 1

    _persist_state(ctx)

    _chat(ctx, "Risky Investment: +1000 credits on victory; added mutations: " + ", ".join(

        EFFECT_DISPLAY_NAMES.get(x, x) for x in chosen

    ))





def _set_shop_purchase_reveal(ctx: Any, title: str, rows: Sequence[Mapping[str, str]]) -> None:

    # UI-only transient data. Do not persist this in run state: it exists solely
    # to explain randomized purchases immediately after the successful click.
    try:
        setattr(ctx, "_slay_shop_purchase_reveal", {
            "title": str(title),
            "rows": [dict(row) for row in rows],
        })
    except Exception:
        pass


def consume_shop_purchase_reveal(ctx: Any) -> dict[str, Any] | None:

    reveal = getattr(ctx, "_slay_shop_purchase_reveal", None)
    try:
        setattr(ctx, "_slay_shop_purchase_reveal", None)
    except Exception:
        pass
    return dict(reveal) if isinstance(reveal, Mapping) else None


def _blessing_reveal_row(effect_id: str) -> dict[str, str]:

    return {
        "name": EFFECT_DISPLAY_NAMES.get(effect_id, effect_id),
        "description": EFFECT_DESCRIPTIONS.get(effect_id, ""),
        "icon": "",
    }


def _upgrade_reveal_row(item_name: str) -> dict[str, str]:

    return {
        "name": shop_entry_display_name(item_name),
        "description": shop_entry_description(item_name),
        "icon": shop_entry_icon(item_name),
    }


def _purchase_boon(

    ctx: Any, item_name: str, price: int, precomputed_reroll_stock: Sequence[str] | None = None,

) -> tuple[bool,str]:

    kind,payload=_parse_boon(item_name); s=state(ctx)

    try:
        setattr(ctx, "_slay_shop_purchase_reveal", None)
    except Exception:
        pass

    result=""

    if kind=="random_blessing":

        sev=int(payload); pool=[x for x,v in BLESSING_SEVERITY.items() if v==sev and x not in s.get("permanent_blessings",[])]
        if crew_mode(ctx):
            from .crew_challenge import eligible_effect
            pool=[x for x in pool if eligible_effect(x,'blessing')]

        if not pool: return False,"No unowned blessing of that rarity remains."

        seed=f"{ctx.slay_config.get('run_seed',0)}:random-boon:{item_name}:{s.get('boon_purchases',{}).get(item_name,0)}"

        pick=random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8],"big")).choice(pool)

        s["permanent_blessings"]=list(dict.fromkeys(list(s.get("permanent_blessings",[]))+[pick])); result=f"Permanently gained {EFFECT_DISPLAY_NAMES.get(pick,pick)}."
        _set_shop_purchase_reveal(ctx, "Random Blessing Received", [_blessing_reveal_row(pick)])

    elif kind=="permanent_blessing":

        if crew_mode(ctx):
            from .crew_challenge import eligible_effect
            if not eligible_effect(payload,'blessing'):
                return False,'That blessing is not permitted in Crew.'
        if payload in s.get("permanent_blessings",[]): return False,"That permanent blessing is already owned."

        s["permanent_blessings"]=list(dict.fromkeys(list(s.get("permanent_blessings",[]))+[payload])); result=f"Permanently gained {EFFECT_DISPLAY_NAMES.get(payload,payload)}."

    elif kind=="upgrade_pack":

        got=_apply_upgrade_pack(ctx,payload,f"{ctx.slay_config.get('run_seed',0)}:upgrade-pack:{payload}:{s.get('boon_purchases',{}).get(item_name,0)}")

        if not got: return False,"No eligible unlocked-unit upgrades are available for that race."

        result="Upgrade Pack: "+", ".join(got)
        _set_shop_purchase_reveal(ctx, f"{payload.title()} Upgrade Pack", [_upgrade_reveal_row(name) for name in got])

    elif kind=="saving_grace":
        frontier = [int(mid) for mid in current_frontier(ctx)]
        existing = set(s.get("permanent_blessings", []))
        for mid in frontier:
            existing.update((node(ctx, mid) or {}).get("blessings", []))
        eligible = [effect for effect in BLESSING_SEVERITY if
                    all(_blessing_allowed_for_mission(ctx, mid, effect) for mid in frontier)]
        forbidden = existing | (set(BLESSING_SEVERITY) - set(eligible))
        purchase_number = int(s.get("boon_purchases", {}).get(item_name, 0))
        seed = int.from_bytes(hashlib.sha256(
            f"{ctx.slay_config.get('run_seed',0)}:saving-grace-purchase:{purchase_number}".encode()
        ).digest()[:8], "big")
        chosen = []
        for target in range(5, 0, -1):
            chosen = _choose_blessings_exact(target, random.Random(seed + 5 - target), forbidden)
            if chosen:
                break
        if not chosen:
            return False, "Saving Grace has no legal blessing package for the available missions."
        s["saving_grace_charges"] = int(s.get("saving_grace_charges", 0)) + 1
        pending = list(s.get("saving_grace_pending", []))
        pending.append(chosen)
        s["saving_grace_pending"] = pending
        result = "Saving Grace: " + ", ".join(EFFECT_DISPLAY_NAMES.get(e,e) for e in chosen)
        _set_shop_purchase_reveal(ctx, "Saving Grace Blessings", [_blessing_reveal_row(e) for e in chosen])

    elif kind=="reroll":

        count=int(s.get("boon_purchases",{}).get("reroll",0))+1; changed=_reroll_future_nodes(ctx,count); result=f"Rerolled effects and rewards for {changed} unfinished reachable missions, including the current mission."

    elif kind=="shop_expansion":

        if int(s.get("shop_expansion", 0)) >= SHOP_EXPANSION_MAX:
            return False, "Shop Expansion can only be purchased three times per run."

        old_stock = list(s.get("shop_stock", ()))

        s["shop_expansion"] = min(SHOP_EXPANSION_MAX, int(s.get("shop_expansion", 0)) + 1)







        cycle = victory_count(ctx)

        expanded = _roll_shop_stock(ctx, cycle, previous_stock=old_stock)

        merged = list(old_stock)

        target_counts = Counter(shop_category_for_item(name, ctx) for name in expanded)

        current_counts = Counter(shop_category_for_item(name, ctx) for name in merged)

        for candidate in expanded:

            if candidate in merged:

                continue

            category = shop_category_for_item(candidate, ctx)

            if current_counts[category] >= target_counts[category]:

                continue

            merged.append(candidate)

            current_counts[category] += 1

        s["shop_cycle"] = cycle

        s["shop_stock_logic_version"] = SHOP_STOCK_LOGIC_VERSION

        s["shop_stock"] = merged

        result="Shop Expansion adds one slot to every shop category, including Consumables."

    elif kind=="reroll_shop":

        cycle = victory_count(ctx)

        previous_stock = list(s.get("shop_stock", ()))





        s["shop_cycle_purchases"] = {}
        s["shop_potions_bought"] = []

        s["shop_cycle_purchase_victory_count"] = cycle

        s["shop_rerolls_this_cycle"] = _shop_reroll_purchase_count(ctx) + 1

        s["shop_reroll_purchase_victory_count"] = cycle

        s["shop_reroll_nonce"] = int(s.get("shop_reroll_nonce",0)) + 1

        s["shop_cycle"] = cycle

        s["shop_stock_logic_version"] = SHOP_STOCK_LOGIC_VERSION

        if precomputed_reroll_stock:

            s["shop_stock"] = list(dict.fromkeys(str(x) for x in precomputed_reroll_stock))

        else:

            s["shop_stock"] = _roll_shop_stock(

                ctx, cycle,

                reroll_nonce=int(s["shop_reroll_nonce"]),

                previous_stock=previous_stock,

            )

        s["shop_stock"] = _keep_frozen_shop_offer(ctx, s["shop_stock"])
        s["shop_sale_items"] = []

        _roll_shop_sales(ctx)









        s = state(ctx)

        result = "Rerolled the current shop."

    elif kind=="risky_investment": s["risky_investment_charges"]=int(s.get("risky_investment_charges",0))+1; result="The next mission gains exactly 4 mutation severity and +1000 victory credits."

    elif kind=="golden_goose":

        sev=GOLDEN_GOOSE_MUTATIONS.get(payload,0)

        if sev<=0 or payload in DISABLED_MUTATIONS: return False,"That mutation is no longer eligible."

        s["permanent_mutations"]=list(dict.fromkeys(list(s.get("permanent_mutations",[]))+[payload]))

        added_bonus = 300 * sev



        s["golden_goose_credit_offset"] = int(s.get("golden_goose_credit_offset",0)) + victory_count(ctx) * added_bonus

        s["golden_goose_bonus_per_mission"]=int(s.get("golden_goose_bonus_per_mission",0))+added_bonus

        result=f"Permanently gained mutation {EFFECT_DISPLAY_NAMES.get(payload,payload)}; +{added_bonus} credits after every future mission."

    else:

        effect={"deadly_weapons":"boon_deadly_weapons","auto_repair":"boon_auto_repair","rapid_fire":"boon_rapid_fire","shields_for_all":"boon_shields_for_all","heavy_armor":"boon_heavy_armor","unlimited_blink":"boon_unlimited_blink","interplanetary_fortress":"boon_interplanetary_fortress","roach_infestation":"boon_roach_infestation","chain_reaction":"boon_chain_reaction","aiur_recruitment":"boon_aiur_recruitment","toxic_observation":"boon_toxic_observation","cloning_technology":"boon_cloning_technology","defender":"boon_defender","fire_power":"boon_fire_power","roachling_mines":"boon_roachling_mines","broodling_evolution":"boon_broodling_evolution","adamantium_blades":"boon_adamantium_blades","enhanced_control":"boon_enhanced_control","banshee_swarm":"boon_banshee_swarm","enlarged_banelings":"boon_enlarged_banelings","viking_anchors":"boon_viking_anchors","corrosive_claws":"boon_corrosive_claws","unlimited_power":"boon_unlimited_power","unstable_colossi":"boon_unstable_colossi","archon_cannons":"boon_archon_cannons","hyrda_storms":"boon_hyrda_storms","mobile_siege":"boon_mobile_siege","maddening_shades":"boon_maddening_shades","concussed_shells":"boon_concussed_shells","missile_defense":"boon_missile_defense","stretchy_spines":"boon_stretchy_spines","gargantuan_units":"boon_gargantuan_units","chaos_blessings":"boon_chaos_blessings",**_NEW_BOON_EFFECT_BY_KIND}.get(kind)

        if not effect: return False,"Unknown boon."

        if effect in s.get("permanent_boons",[]) and kind not in REPEATABLE_BOON_KINDS: return False,"That boon is already owned."

        s["permanent_boons"]=list(dict.fromkeys(list(s.get("permanent_boons",[]))+[effect]))
        if kind == "single_use_tools":
            s["single_use_tools_last_victory"] = victory_count(ctx)

        next_count = int(s.get("boon_purchases",{}).get(item_name,0)) + 1

        result = f"Permanently gained {EFFECT_DISPLAY_NAMES.get(effect,effect)}." if kind not in REPEATABLE_BOON_KINDS else f"{EFFECT_DISPLAY_NAMES.get(effect,effect)} stack {next_count} purchased."

    boon_counts=dict(s.get("boon_purchases",{})); boon_counts[item_name]=int(boon_counts.get(item_name,0))+1

    if kind=="reroll": boon_counts["reroll"]=int(boon_counts.get("reroll",0))+1

    s["boon_purchases"]=boon_counts





    if kind != "reroll_shop":

        cycle_counts = dict(s.get("shop_cycle_purchases", {}))

        cycle_counts[item_name] = int(cycle_counts.get(item_name, 0)) + 1

        s["shop_cycle_purchases"] = cycle_counts

        s["shop_cycle_purchase_victory_count"] = victory_count(ctx)

    s["spent"]=int(s.get("spent",0))+price

    if s.get("shop_frozen_item") == item_name:
        s["shop_frozen_item"] = ""
    _persist_state(ctx); return True,result





def grant_test_boon(ctx: Any, query: str) -> tuple[bool, str]:













    if not enabled(ctx):

        return False, "Slay the StarCraft mode is not active."

    if not state_ready(ctx):

        return False, "Run state is still loading."



    raw = str(query or "").strip()

    candidates: list[tuple[str, str, str]] = []

    for effect in EFFECT_BANK_BITS:

        if not effect.startswith("boon_"):

            continue

        if effect in {"boon_mobile_siege"}:





            continue

        kind = effect[len("boon_"):]

        item = _boon_id(kind)

        display = boon_display_name(item)

        normalized = re.sub(r"[^a-z0-9]+", " " , display.casefold()).strip()

        kind_normalized = re.sub(r"[^a-z0-9]+", " " , kind.casefold()).strip()

        candidates.append((item, display, kind_normalized + " | " + normalized))

    candidates.sort(key=lambda row: row[1].casefold())



    if not raw or raw.casefold() in {"list", "help", "?"}:

        names = ", ".join(display for _, display, _ in candidates)

        return False, "Usage: /boon <boon name>. Available: " + names



    needle = re.sub(r"[^a-z0-9]+", " " , raw.casefold()).strip()

    exact = [row for row in candidates if needle in {part.strip() for part in row[2].split("|")}]

    matches = exact or [row for row in candidates if needle and needle in row[2]]

    if not matches:

        return False, f"Unknown boon '{raw}'. Use /boon list to see available boon names."

    if len(matches) > 1:

        return False, "Ambiguous boon name. Matches: " + ", ".join(row[1] for row in matches[:12])



    item, display, _ = matches[0]

    ok, message = _purchase_boon(ctx, item, 0)

    if not ok:

        return False, message

    return True, f"TEST BOON: {display}. {message}"







def grant_test_credits(ctx: Any, amount: str | int) -> tuple[bool, str]:











    if not enabled(ctx):

        return False, "Slay the StarCraft mode is not active."

    if not state_ready(ctx):

        return False, "Run state is still loading."

    raw = str(amount if amount is not None else "").strip().replace(",", "")

    if not raw:

        return False, "Usage: /credits <signed amount>"

    try:

        grant = int(raw)

    except ValueError:

        return False, "Usage: /credits <signed amount>"

    if grant == 0:

        return False, "Credit adjustment must be a nonzero integer."





    grant = max(-1_000_000_000, min(grant, 1_000_000_000))

    s = state(ctx)

    s["test_credit_bonus"] = int(s.get("test_credit_bonus", 0)) + grant

    _persist_state(ctx)

    return True, f"TEST CREDITS: {grant:+d}. Balance: {credits(ctx)}."



def _request_live_item_refresh(ctx: Any) -> None:













    try:

        ctx.slay_item_revision = int(getattr(ctx, "slay_item_revision", 0)) + 1

    except Exception:

        pass

    bot = getattr(ctx, "last_bot", None)

    if bot is not None and hasattr(bot, "last_received_update"):

        try:

            bot.last_received_update = -1

        except Exception:

            pass





def _stock_after_progression_unlock(ctx: Any, purchased_item: str, previous_stock: Sequence[str]) -> list[str]:

















    cycle = victory_count(ctx)

    rolled = _roll_shop_stock(ctx, cycle)

    table = _item_table()

    owned_unlocks = _owned_unlock_names(ctx)



    def belongs(name: str) -> bool:

        if purchased_item == SPEAR_UNLOCK:

            return shop_category_for_item(name, ctx, owned_unlocks) == "Spear of Adun"

        if purchased_item == KERRIGAN_UNLOCK:

            return shop_category_for_item(name, ctx, owned_unlocks) == "Kerrigan"

        if purchased_item in {TERRAN_CONTRACTS, ZERG_CONTRACTS}:

            data = table.get(name)

            return (

                shop_category_for_item(name, ctx, owned_unlocks) == "Mercenaries"

                and _effective_mercenary_contract_for_item(ctx, name, data, owned_unlocks, table) == purchased_item

            )

        return False



    kept = [str(name) for name in previous_stock if str(name) != str(purchased_item)]

    target = [str(name) for name in rolled if belongs(str(name))]

    current_count = sum(1 for name in kept if belongs(name))

    for candidate in target:

        if current_count >= len(target):

            break

        if candidate in kept:

            continue

        kept.append(candidate)

        current_count += 1

    return list(dict.fromkeys(kept))





def purchase(

    ctx: Any, item_name: str, *, precomputed_reroll_stock: Sequence[str] | None = None,

) -> tuple[bool, str]:

    if not enabled(ctx): return False, "Slay the StarCraft mode is not active."

    if not state_ready(ctx): return False, "Run state is still loading."

    current_stock = list(shop_stock(ctx))

    if item_name not in current_stock: return False, "That item is not in the current shop stock."

    if item_name in POTION_CATALOG and item_name in state(ctx).get("shop_potions_bought", ()):
        return False, "That consumable has already been purchased from this stock. Reroll or win a mission to restock it."
    if not can_buy_shop_item(ctx,item_name): return False,"You already have the maximum useful number of this item."

    price=price_for_item(item_name,ctx)

    if credits(ctx)<price: return False,f"Need {price} credits; only {credits(ctx)} available."

    if item_name in POTION_CATALOG:
        slots = potion_inventory(ctx)
        if len(slots) >= POTION_CAPACITY:
            return False, "Both consumable slots are full (2/2). Use a consumable before buying another."
        s = state(ctx)
        serial = max(int(s.get("potion_serial", 0)),
                     *(int(row.get("serial", 0)) for row in s.get("potion_inventory", []) if isinstance(row, dict)), 0) + 1
        s["potion_serial"] = serial
        s["potion_inventory"] = slots + [{"id": item_name, "serial": serial}]
        # Persist per-stock purchases separately from inventory. Using a
        # consumable must not make the same offer purchasable a second time.
        s["shop_potions_bought"] = list(dict.fromkeys(
            list(s.get("shop_potions_bought", ())) + [item_name]
        ))
        s["spent"] = int(s.get("spent", 0)) + price
        if s.get("shop_frozen_item") == item_name:
            s["shop_frozen_item"] = ""
        _persist_state(ctx)
        return True, f"Purchased {POTION_CATALOG[item_name]['name']} for {price} credits ({len(slots)+1}/2 consumable slots)."

    if item_name.startswith(BOON_PREFIX):

        return _purchase_boon(ctx, item_name, price, precomputed_reroll_stock)



    s=state(ctx)

    purchases=dict(s.get("purchases",{}))

    purchases[item_name]=int(purchases.get(item_name,0))+1
    if item_name == SPEAR_UNLOCK:
        purchases[SPEAR_BASE_PYLON_ITEM] = max(1,int(purchases.get(SPEAR_BASE_PYLON_ITEM,0)))

    s["purchases"]=purchases

    cycle=dict(s.get("shop_cycle_purchases",{}))

    cycle[item_name]=int(cycle.get(item_name,0))+1

    s["shop_cycle_purchases"]=cycle

    s["spent"]=int(s.get("spent",0))+price



    granted = ""



    if item_name in {TERRAN_CONTRACTS, ZERG_CONTRACTS, KERRIGAN_UNLOCK, SPEAR_UNLOCK}:







        s["shop_cycle"] = victory_count(ctx)

        s["shop_stock_logic_version"] = SHOP_STOCK_LOGIC_VERSION

        s["shop_stock"] = _keep_frozen_shop_offer(ctx, _stock_after_progression_unlock(ctx, item_name, current_stock))

    if item_name == KERRIGAN_UNLOCK:

        _normalize_kerrigan_context(ctx)

    if s.get("shop_frozen_item") == item_name:
        s["shop_frozen_item"] = ""

    _persist_state(ctx)

    if item_name in _item_table() or item_name == SPEAR_UNLOCK:

        # The Spear unlock also grants the first real AP Deploy Pylon item.
        _request_live_item_refresh(ctx)

    return True,f"Purchased {shop_entry_display_name(item_name)} for {price} credits."





def _is_shop_only_reward_item(item_name: str, data: Any | None = None) -> bool:

    if data is None:

        data = _item_table().get(item_name)

    if data is None:

        return False

    return (

        _is_mercenary_unit(item_name, data)

        or _is_mercenary_general_upgrade(item_name, data)

        or _is_kerrigan_item(item_name, data)

        or _is_spear_item(item_name, data)

        or _is_unit_specific_upgrade(item_name)

    )





def _mission_reward_category(item_name: str, data: Any | None = None) -> str:

    if data is None:

        data = _item_table().get(item_name)

    if data is None:

        return "other"

    race = _item_race_key(item_name, data)

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    if item_name in DEFENSIVE_STRUCTURE_ITEMS or item_name in DETECTOR_ITEMS:

        return "defense"

    if _is_unit_or_morph_unlock_type(type_name):







        return f"unit:{race}"

    if _is_general_upgrade_item(item_name):

        return "general"

    if race in {"terran", "zerg", "protoss"}:

        return f"race-general:{race}"

    if type_name == "Building":

        return f"structure:{race}"

    return "other"





def _duplicate_pool(ctx: Any, owned: set[str], original: str | None = None) -> list[str]:

    table = _item_table()

    pool=[]











    replacement_names = list(dict.fromkeys(

        list(ctx.slay_config.get("shop_pool", [])) + shop_candidates(ctx)

    ))

    for name in replacement_names:

        data = table.get(name)

        if name in owned or data is None: continue

        if _is_deprecated_item(name, data): continue

        if _is_shop_only_reward_item(name, data): continue

        if _is_nova_campaign_item(name, data) or _is_royal_guard_item(name, data, table): continue

        if _unit_upgrade_requires_locked_unit(ctx,name): continue

        pool.append(name)

    if original is None or not pool:

        return pool

    original_data = table.get(original)

    target_category = _mission_reward_category(original, original_data)

    same = [name for name in pool if _mission_reward_category(name, table.get(name)) == target_category]

    if same:

        return same





    if target_category.startswith("unit:"):

        units = [name for name in pool if _mission_reward_category(name, table.get(name)).startswith("unit:")]

        if units:

            return units

    if target_category.startswith("race-general:"):

        race_globals = [name for name in pool if _mission_reward_category(name, table.get(name)).startswith("race-general:")]

        if race_globals:

            return race_globals

    return pool





def _bundled_weapon_armor_replacement(item_name: str) -> str | None:

    clean = str(item_name).strip()

    if clean not in REDUNDANT_BASIC_STAT_UPGRADE_ITEMS:

        return None

    if "Terran" in clean:

        return "Progressive Terran Weapon/Armor Upgrade"

    if "Zerg" in clean:

        return "Progressive Zerg Weapon/Armor Upgrade"

    if "Protoss" in clean:

        return "Progressive Protoss Weapon/Armor Upgrade"

    return None





def _is_stackable_progressive_item(item_name: str) -> bool:









    clean = str(item_name).strip()

    return clean in STACKABLE_GENERAL_UPGRADE_ITEMS or clean.casefold().startswith("progressive ")





def _campaign_allowed_item_reward(name: str, table: Mapping[str, Any]) -> bool:
    data = table.get(name)
    if data is None or getattr(data, "code", None) is None:
        return False
    if _is_deprecated_item(name, data) or _is_nova_campaign_item(name, data):
        return False
    if _is_royal_guard_item(name, data, table) or _is_shop_only_reward_item(name, data):
        return False
    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))
    if _is_unit_or_morph_unlock_type(type_name):
        return True
    if _is_unit_specific_upgrade(name, table):
        return False
    if _is_general_upgrade_item(name):
        return True
    category = _mission_reward_category(name, data)
    return (_is_explicit_race_global_upgrade(name)
            or (category.startswith("race-general:") and "upgrade" in type_name.lower()))


def _campaign_allowed_reward_pool(ctx: Any, owned: set[str], table: Mapping[str, Any]) -> list[str]:
    names = list(dict.fromkeys(list(ctx.slay_config.get("shop_pool", [])) + shop_candidates(ctx)))
    pool = [name for name in names if name not in owned and _campaign_allowed_item_reward(name, table)
            and not _unit_upgrade_requires_locked_unit(ctx, name)]
    # The shop pool may eventually run out after many campaign item rewards.
    # Fall back to the AP item table rather than silently grant an invalid item.
    if not pool:
        pool = [name for name in table if name not in owned and _campaign_allowed_item_reward(name, table)
                and not _unit_upgrade_requires_locked_unit(ctx, name)]
    return pool


def sync_duplicate_item_replacements(ctx: Any) -> None:

    if not enabled(ctx) or not state_ready(ctx): return
    if crew_mode(ctx):
        crew_sync_item_grants(ctx)
        return

    table=_item_table(); by_code={d.code:n for n,d in table.items() if d.code is not None}; s=state(ctx)

    replacements=dict(s.get("duplicate_replacements",{})); announced=set(str(x) for x in s.get("duplicate_announced",[]))

    owned={name for name,count in s.get("purchases",{}).items() if int(count)>0 and name in table}

    for pre in getattr(ctx,"items_received",[]):

        if int(getattr(pre,"location",0)) == -2:

            pre_name = by_code.get(pre.item)

            if pre_name: owned.add(pre_name)

    changed=False

    for item in getattr(ctx,"items_received",[]):

        loc=int(getattr(item,"location",0))

        if loc == -2 or _is_credit_replacement_location(ctx, loc):





            continue

        original=by_code.get(item.item)

        if not original: continue

        data=table.get(original)

        key=str(loc)

        if campaign_mode(ctx) and not _campaign_allowed_item_reward(original, table):
            existing = replacements.get(key)
            if existing and _campaign_allowed_item_reward(str(existing), table):
                owned.add(str(existing))
                continue
            pool = _campaign_allowed_reward_pool(ctx, owned, table)
            if pool:
                seed = int.from_bytes(hashlib.sha256(
                    f"{ctx.slay_config.get('run_seed', 0)}:campaign-item:{loc}".encode()
                ).digest()[:8], "big")
                replacement = random.Random(seed).choice(pool)
                replacements[key] = replacement
                owned.add(replacement)
                if key not in announced:
                    message = f"Campaign reward: obtained {replacement} instead of {original}"
                    _chat(ctx, message); _game_chat(ctx, message)
                    announced.add(key)
                changed = True
            continue



        bundled_replacement = _bundled_weapon_armor_replacement(original)

        if bundled_replacement:

            replacement = bundled_replacement

            replacements[key] = replacement

            owned.add(replacement)

            if key not in announced:

                message=f"Obtained {replacement} instead"

                _chat(ctx,message); _game_chat(ctx,message); announced.add(key)

            changed=True

            continue









        forced_out_of_scope = (

            _is_deprecated_item(original, data)

            or _is_nova_campaign_item(original, data)

            or _is_royal_guard_item(original, data, table)

        )

        forced_shop_only = _is_shop_only_reward_item(original, data)



        if not forced_shop_only and not forced_out_of_scope and _is_stackable_progressive_item(original):

            owned.add(original)

            if key in replacements:

                replacements.pop(key, None); announced.discard(key); changed=True

            continue



        cap = _duplicate_owned_cap(original, data) if data is not None else 1

        true_unique_duplicate = original in owned and cap == 1

        if key in replacements:

            replacement=str(replacements[key]); owned.add(replacement)

            if key not in announced:

                if forced_out_of_scope:

                    message=f"This item is outside Slay's active item pool. Obtained {replacement} instead"

                elif forced_shop_only:

                    message=f"Mission reward {original} is shop-only in Slay. Obtained {replacement} instead"

                else:

                    message=f"Already obtained {original}. Obtained {replacement} instead"

                _chat(ctx,message); _game_chat(ctx,message); announced.add(key); changed=True

            continue



        if forced_out_of_scope or forced_shop_only or true_unique_duplicate:

            pool=_duplicate_pool(ctx,owned,original)
            if campaign_mode(ctx):
                pool = [name for name in pool if _campaign_allowed_item_reward(name, table)]

            if not pool: continue

            seed=int.from_bytes(hashlib.sha256(f"{ctx.slay_config.get('run_seed',0)}:duplicate:{loc}:{original}".encode()).digest()[:8],"big")

            replacement=random.Random(seed).choice(pool); replacements[key]=replacement; owned.add(replacement)

            if forced_out_of_scope:

                message=f"This item is outside Slay's active item pool. Obtained {replacement} instead"

            elif forced_shop_only:

                message=f"Mission reward {original} is shop-only in Slay. Obtained {replacement} instead"

            else:

                message=f"Already obtained {original}. Obtained {replacement} instead"

            _chat(ctx,message); _game_chat(ctx,message); announced.add(key); changed=True

        else:

            owned.add(original)

    if changed:

        s["duplicate_replacements"]=replacements; s["duplicate_announced"]=sorted(announced); _persist_state(ctx)





def augment_network_items(ctx: Any, items: list[NetworkItem], item_list: Mapping[str, Any]) -> None:



    if not enabled(ctx) or not state_ready(ctx): return

    sync_duplicate_item_replacements(ctx)

    replacements=state(ctx).get("duplicate_replacements",{})





    crew_reward_locations = _crew_mission_reward_plan(ctx) if crew_mode(ctx) else {}
    # Crew AP mission checks never directly grant their original AP items.
    # Only separately bought upgrades (synthetic location=0) are injected.
    # Filter *all* ordinary location-backed AP items even if a location table
    # has not arrived yet; otherwise irrelevant generic upgrades leak through.
    items[:] = [
        item for item in items
        if (int(getattr(item,'location',0)) <= 0 if crew_mode(ctx)
            else int(getattr(item,'location',0)) not in crew_reward_locations
            and not _is_credit_replacement_location(ctx,int(getattr(item,'location',0))))
    ]

    for i,item in enumerate(list(items)):

        replacement=replacements.get(str(int(getattr(item,"location",0)))) if isinstance(replacements,Mapping) else None

        data=item_list.get(str(replacement)) if replacement else None

        if data is not None and data.code is not None:

            items[i]=NetworkItem(data.code,item.location,item.player,int(data.classification))

    by_code=Counter(item.item for item in items)











    by_source_code={data.code:name for name,data in item_list.items() if getattr(data,"code",None) is not None}

    for received in getattr(ctx,"items_received",[]):

        loc=int(getattr(received,"location",0))

        if loc in crew_reward_locations or _is_credit_replacement_location(ctx, loc):
            continue

        item_name=by_source_code.get(getattr(received,"item",None))

        replacement=replacements.get(str(loc)) if isinstance(replacements,Mapping) else None

        if replacement in item_list:

            item_name=str(replacement)

        if item_name not in FIVE_X_GENERIC_UPGRADE_ITEMS:

            continue

        data=item_list.get(item_name)

        if data is None or data.code is None:

            continue

        for _ in range(4):

            items.append(NetworkItem(data.code,0,0,int(data.classification)))

            by_code[data.code]+=1



    for item_name,bought_raw in state(ctx).get("purchases",{}).items():
        if crew_mode(ctx) and item_name == 'Bullfrog':
            continue
        data=item_list.get(item_name)

        if data is None or data.code is None: continue

        bought=max(0,int(bought_raw)); effective_bought=_effective_shop_copies(item_name,bought); cap=_max_owned_copies(data)

        inject=effective_bought if cap is None else max(0,min(effective_bought,cap-by_code[data.code]))

        for _ in range(inject): items.append(NetworkItem(data.code,0,0,int(data.classification))); by_code[data.code]+=1











    if crew_mode(ctx):
        # Real Crew shop purchases, mission prizes, and adopted units all
        # grant the same permanent AP tech unlock. Count each unit name ONCE;
        # paid copies remain independently tracked by banked unit tags.
        from .crew_catalog import preview_catalog
        from .crew_sc2_adapter import NATIVE_TYPES
        available={row['name'] for row in preview_catalog(('terran','zerg','protoss'))
                   if row['category']=='unit' and row['name'] in NATIVE_TYPES}
        roster=crew_roster(ctx)
        discovered=set(roster.get('discovered_unit_unlocks',()))
        discovered.update(c['name'] for c in roster.get('copies',())
                          if c.get('kind')=='unit' and c.get('status')!='lost')
        for item_name in sorted(discovered & available):
            data=item_list.get(item_name)
            if data is None or getattr(data,'code',None) is None:continue
            if by_code[data.code] == 0:
                items.append(NetworkItem(data.code,0,0,int(data.classification)))
                by_code[data.code]+=1
        # PF is an Archipelago BUILDING item, not a Crew 'unit' unlock.
        # A paid PF copy grants the native CC->PF button while that copy is
        # owned; its conversion still spends exactly one stock/receipt.
        # Do not grant this tech permanently after all copies are destroyed.
        has_fortress_stock=any(
            c.get('name')=='Planetary Fortress' and c.get('kind')=='structure'
            and c.get('status') in ('zone','reserve','deployed')
            for c in roster.get('copies',()))
        if has_fortress_stock:
            pf=item_list.get('Planetary Fortress')
            if pf is not None and getattr(pf,'code',None) is not None and by_code[pf.code]==0:
                items.append(NetworkItem(pf.code,0,0,int(pf.classification)))
                by_code[pf.code]+=1

    if int(ctx.slay_config.get("format_version", 0)) < 30:

        for council_name in sorted(PROTOSS_WAR_COUNCIL_ITEMS):

            council_data = item_list.get(council_name)

            if council_data is None or getattr(council_data, "code", None) is None:

                continue

            if by_code[council_data.code] > 0:

                continue

            parents = _unit_specific_parent_names(council_name, item_list)

            if not parents:

                continue

            if not any(

                (item_list.get(parent) is not None)

                and getattr(item_list[parent], "code", None) is not None

                and by_code[item_list[parent].code] > 0

                for parent in parents

            ):

                continue

            items.append(NetworkItem(council_data.code, 0, 0, int(council_data.classification)))

            by_code[council_data.code] += 1

    # Slay-only, no changes to shared AP mod data.  Remove the native upgrade
    # from the calculated item list AFTER all bought/received items were added:
    # its SC2 EffectArray performs an unchecked -60 on 14 starting AND reuse
    # mercenary cooldowns, which can produce negative engine timers.  The same
    # entitlement is transmitted separately in mercenary_upgrade_packed2 and
    # applied with a floor in Galaxy.  Keep raw receipts/purchases untouched,
    # so the shop, inventory, owned item count and AP item rewards are intact.
    rapid = item_list.get("Rapid Reinforcement (Terran)")
    if rapid is not None and getattr(rapid, "code", None) is not None:
        items[:] = [item for item in items if item.item != rapid.code]


def rewrite_print_json_for_effective_rewards(ctx: Any, args: dict[str, Any]) -> dict[str, Any]:















    if not enabled(ctx) or not isinstance(args, dict) or args.get("type") != "ItemSend":

        return args

    item = args.get("item")

    if item is None:

        return args

    try:

        location = int(getattr(item, "location", 0))

        finding_player = int(getattr(item, "player", 0))

    except (TypeError, ValueError):

        return args

    crew_reward = _crew_mission_reward_plan(ctx).get(location) if crew_mode(ctx) else None
    if crew_reward is None and not crew_mode(ctx) and not _is_credit_replacement_location(ctx, location):
        return args





    concerns_self = getattr(ctx, "slot_concerns_self", None)

    if callable(concerns_self):

        try:

            if not bool(concerns_self(finding_player)):

                return args

        except Exception:

            return args

    elif getattr(ctx, "slot", None) is not None and finding_player != int(ctx.slot):

        return args



    rewritten = copy.deepcopy(args)

    for part in rewritten.get("data", []):

        if not isinstance(part, dict):

            continue

        part_type = part.get("type")

        if part_type == "item_id" or getattr(part_type, "value", None) == "item_id":

            part.clear()

            caption = (f"{crew_reward['credits']} Credits" if crew_reward and crew_reward['kind']=='credits'
                       else f"{crew_reward['quantity']}x {crew_reward['name']} (Reserves)" if crew_reward
                       else 'Crew reward (awaiting mission mapping)' if crew_mode(ctx)
                       else f"{item_credit_reward(ctx)} Credits")
            part.update({"text": caption, "type": "color", "color": "green"})

            break

    return rewritten





def exact_item_for_location(ctx: Any, location_id: int) -> str:

    if crew_mode(ctx):
        reward = _crew_mission_reward_plan(ctx).get(int(location_id))
        if reward:
            return (f"{reward['credits']} Credits" if reward['kind']=='credits'
                    else f"{reward['quantity']}x {reward['name']} (Reserves)")
        # Crew never grants the AP scout's original item at this location.
        # Don't misrepresent a generic AP upgrade as the real Crew reward.
        return 'Crew reward (awaiting mission mapping)'
    if _is_credit_replacement_location(ctx, int(location_id)):

        return f"{item_credit_reward(ctx)} Credits"

    info = getattr(ctx, "locations_info", {}).get(int(location_id))

    if info is None:

        return "(scouting...)"





    for name, data in _item_table().items():

        if getattr(data, "code", None) == info.item:

            return name

    try:

        return ctx.item_names.lookup_in_game(info.item)

    except Exception:

        return f"Item #{info.item}"







_BASE_UPGRADE_TARGETS = (

    "Command Center", "Orbital Command", "Planetary Fortress",

    "Nexus", "Hatchery", "Lair", "Hive",

)





_RACE_ITEM_COLORS = {

    "terran": "6FA8FF",

    "zerg": "B57AE8",

    "protoss": "FFD166",

}





def _race_color_for_item(data: Any) -> str | None:

    race = getattr(data, "race", None)

    try:

        race_name = str(race.get_title()).strip().casefold()

    except Exception:

        race_name = str(getattr(race, "name", race) or "").strip().casefold()

    return _RACE_ITEM_COLORS.get(race_name)





def _race_color_for_item_name(item_name: str, data: Any | None = None) -> str | None:













    explicit = _explicit_race_global_upgrade_color(item_name)

    if explicit:

        return explicit

    table = _item_table()

    if data is None:

        data = table.get(item_name)

    direct = _race_color_for_item(data) if data is not None else None

    if direct:

        return direct



    parent_colors: set[str] = set()

    try:

        for parent in _unit_specific_parent_names(item_name, table):

            parent_data = table.get(parent)

            color = _race_color_for_item(parent_data) if parent_data is not None else None

            if color:

                parent_colors.add(color)

    except Exception:

        pass







    match = re.search(r"\(([^()]+)\)\s*$", str(item_name))

    if match:

        parent_name = match.group(1).strip()

        parent_data = table.get(parent_name)

        color = _race_color_for_item(parent_data) if parent_data is not None else None

        if color:

            parent_colors.add(color)



        suffix_color = _RACE_ITEM_COLORS.get(parent_name.casefold())

        if suffix_color:

            parent_colors.add(suffix_color)



    if len(parent_colors) == 1:

        return next(iter(parent_colors))

    return None





_DEFENSIVE_STRUCTURE_RACE_COLORS = {



    "Bunker": "6FA8FF", "Missile Turret": "6FA8FF", "Devastator Turret": "6FA8FF",

    "Planetary Fortress": "6FA8FF", "Perdition Turret": "6FA8FF", "Sensor Tower": "6FA8FF",

    "Psi Disrupter": "6FA8FF", "Hive Mind Emulator": "6FA8FF",

    "Argus Amplifier (Hive Mind Emulator)": "6FA8FF", "Psi Indoctrinator (Hive Mind Emulator)": "6FA8FF",



    "Spine Crawler": "B57AE8", "Spore Crawler": "B57AE8", "Bile Launcher": "B57AE8",

    "Infested Bunker": "B57AE8", "Infested Missile Turret": "B57AE8",



    "Photon Cannon": "FFD166", "Khaydarin Monolith": "FFD166", "Shield Battery": "FFD166",

}





def _defensive_structure_color(item_name: str, data: Any) -> str | None:









    return _race_color_for_item(data) or _DEFENSIVE_STRUCTURE_RACE_COLORS.get(item_name)





def _explicit_race_global_upgrade_color(item_name: str) -> str | None:





    colors = {"terran": "6FA8FF", "zerg": "B57AE8", "protoss": "FFD166"}

    for race_key, items in RACE_GLOBAL_UPGRADE_ITEMS.items():

        if item_name in items:

            return colors.get(race_key)

    return None





def _is_generic_race_upgrade(item_name: str, type_name: str) -> bool:



    if type_name == "Upgrade":

        return True





    lower = item_name.casefold()

    if type_name == "Progressive Upgrade" and (

        "weapon/armor upgrade" in lower

        or "weapon upgrade" in lower

        or "armor upgrade" in lower

        or "weapons upgrade" in lower

    ):

        return True





    return any(target.casefold() in lower for target in _BASE_UPGRADE_TARGETS)





def item_reward_markup(item_name: str) -> str:



    if (re.fullmatch(r"\d+ Credits", str(item_name)) or
            re.fullmatch(r"\d+x .+ \(Reserves\)", str(item_name))):

        return f"[color=72E09D]{item_name}[/color]"

    explicit_race_color = _explicit_race_global_upgrade_color(item_name)

    if explicit_race_color:

        return f"[color={explicit_race_color}]{item_name}[/color]"

    data = _item_table().get(item_name)

    if data is None:

        return item_name

    type_name = str(getattr(getattr(data, "type", None), "display_name", ""))

    normalized_type = type_name.replace("_", " ").strip().casefold()



    if _is_general_upgrade_item(item_name):

        return f"[color=72E09D]{item_name}[/color]"





    if _is_unit_unlock_type(type_name) or normalized_type == "morph":

        color = _race_color_for_item_name(item_name, data)

        return f"[color={color or '72E09D'}]{item_name}[/color]"



    if item_name in DEFENSIVE_STRUCTURE_ITEMS:

        color = _defensive_structure_color(item_name, data)

        return f"[color={color or '72E09D'}]{item_name}[/color]"







    if _is_generic_race_upgrade(item_name, type_name):

        color = _race_color_for_item_name(item_name, data)

        return f"[color={color or '72E09D'}]{item_name}[/color]"









    if _is_unit_specific_upgrade(item_name):

        color = _race_color_for_item_name(item_name, data)

        if color:

            return f"[color={color}]{item_name}[/color]"



    return item_name





def _mutation_tooltip_name_markup(ctx: Any, mission_id: int, effect_id: str) -> str:













    name = _mission_effect_name(ctx, mission_id, effect_id)

    severity = int(GOLDEN_GOOSE_MUTATIONS.get(str(effect_id), 0))

    if severity < 4:

        return f"[b]{name}[/b]"

    colors = {

        4: "FFB0B0",

        5: "FF8888",

        6: "FF5C5C",

        7: "FF3333",

    }

    color = colors.get(min(7, severity), colors[7])

    return f"[b][color={color}]{name}[/color][/b]"





def mission_tooltip_section(ctx: Any, mission_id: int, remaining_locations: Sequence[tuple[Any, str, int]]) -> str:

    if not enabled(ctx):

        return ""

    data = node(ctx, mission_id)

    if data is None:

        return ""

    status = node_status(ctx, mission_id)

    status_names = {

        "loading": "LOADING RUN STATE",

        "available": "AVAILABLE",

        "selected": "SELECTED - RETRY ALLOWED UNTIL VICTORY",

        "future": "FUTURE",

        "completed": "COMPLETED - PERMANENTLY CLOSED",

        "abandoned": "ABANDONED",

    }

    mission_name = str(data.get("mission_name", "")).strip() or f"Mission {mission_id}"

    lines = [

        f"[b][color=FFD166]{mission_name}[/color][/b]",

        f"State: {status_names.get(status, status.upper())}",

        f"Layer: {int(data.get('layer', 0)) + 1}",

        f"Victory reward: +{crew_effective_victory_reward(ctx,data)} Credits",

    ]

    if data.get("kerrigan") and _progression_owned(ctx, KERRIGAN_UNLOCK):

        lines.append("[color=72E09D][b]Kerrigan available[/b][/color]")

    if data.get("lotv"):

        lines.append("[color=FFD166][b]Spear of Adun available[/b][/color]")



    muts = list(data.get("mutators", []))

    bless = list(data.get("blessings", []))

    lines.append("[b][color=FF7777]Mutators[/color][/b]")

    if muts:

        lines.extend(f"- {_mutation_tooltip_name_markup(ctx, mission_id, x)}: {_mission_effect_description(ctx, mission_id, x)}" for x in muts)

    else:

        lines.append("- None")

    lines.append("[b][color=72E09D]Blessings[/color][/b]")

    if bless:

        lines.extend(f"- [b]{_mission_effect_name(ctx, mission_id, x)}[/b]: {_mission_effect_description(ctx, mission_id, x)}" for x in bless)

    else:

        lines.append("- None")



    if remaining_locations:

        heading = "Crew unit and credit rewards" if crew_mode(ctx) else "Available Archipelago items"

        if status in {"completed", "abandoned"}:

            heading = ("Forfeited Crew rewards" if crew_mode(ctx)
                       else "Forfeited items (eligible for shop salvage)")

        lines.append(f"[b]{heading}[/b]")

        for _, location_name, location_id in remaining_locations:

            item_name = exact_item_for_location(ctx, location_id)

            lines.append(f"- {location_name} -> {item_reward_markup(item_name)}")

    return "\n".join(lines)





def decorate_mission_text(ctx: Any, mission_id: int, text: str) -> str:

    if not enabled(ctx):

        return text

    data = node(ctx, mission_id) or {}

    race = str(data.get("race", "")).strip()

    mission_name = str(data.get("mission_name", ""))

    if race in {"Terran", "Zerg", "Protoss"} and f"({race})" not in mission_name:

        suffix = f" ({race})"





        if text.endswith("[/color]"):

            text = text[:-8] + suffix + "[/color]"

        else:

            text += suffix



    status = node_status(ctx, mission_id)

    prefix = {

        "loading": "[color=AAAAAA]…[/color] ",

        "available": "[color=FFE08A]▶[/color] ",

        "selected": "[color=FFE08A]▶[/color] ",

        "completed": "",

        "abandoned": "",

        "future": "[color=A9A9A9]·[/color] ",

    }.get(status, "")

    return prefix + text





def ui_signature(ctx: Any) -> tuple[Any, ...]:

    if not enabled(ctx):

        return ()

    sync_commit_from_checks(ctx)

    sync_duplicate_item_replacements(ctx)

    s = state(ctx)

    return (

        bool(state_ready(ctx)),

        tuple(s.get("chosen", [])),

        tuple(sorted(s.get("purchases", {}).items())),

        int(s.get("spent", 0)),

        int(s.get("shop_cycle", -1)),

        tuple(s.get("shop_stock", [])),
        str(s.get("shop_frozen_item", "")),
        tuple((row["id"], row["serial"]) for row in potion_inventory(ctx)),

        tuple(s.get("permanent_blessings", [])),

        tuple(sorted(s.get("duplicate_replacements", {}).items())),

        repr(s.get("node_effect_overrides", {})),

        victory_count(ctx),

        credits(ctx),

        len(getattr(ctx, "locations_info", {})),

    )





def edge_pairs(ctx: Any) -> list[tuple[int, int]]:
    if endless_mode(ctx):
        return []

    graph = nodes(ctx)

    result: list[tuple[int, int]] = []

    for source, data in graph.items():

        for dest in data.get("next", []):

            if dest in graph:

                result.append((source, dest))

    return result





def route_layout_x_fractions(ctx: Any) -> dict[int, float]:
    if endless_mode(ctx):
        return {}



    raw = state(ctx).get("route_layout_x_fractions", {})

    if not isinstance(raw, Mapping):

        return {}

    graph = nodes(ctx)

    result: dict[int, float] = {}

    for raw_mid, raw_fraction in raw.items():

        try:

            mid = int(raw_mid)

            fraction = float(raw_fraction)

        except (TypeError, ValueError):

            continue

        if mid in graph and math.isfinite(fraction) and 0.0 <= fraction <= 1.0:

            result[mid] = fraction

    return result





def remember_route_layout_x_fractions(ctx: Any, positions: Mapping[int, float]) -> dict[int, float]:













    existing = route_layout_x_fractions(ctx)

    if existing:

        return existing

    graph = nodes(ctx)

    expected = {int(mid) for mid in graph}

    clean: dict[str, float] = {}

    for raw_mid, raw_fraction in positions.items():

        try:

            mid = int(raw_mid)

            fraction = float(raw_fraction)

        except (TypeError, ValueError):

            continue

        if mid in expected and math.isfinite(fraction) and 0.0 <= fraction <= 1.0:

            clean[str(mid)] = fraction





    if not expected or set(map(int, clean)) != expected:

        return {}

    s = state(ctx)

    if s.get("route_layout_x_fractions"):

        return route_layout_x_fractions(ctx)

    s["route_layout_x_fractions"] = clean

    _persist_state(ctx)

    return route_layout_x_fractions(ctx)





def route_horizontal_positions(ctx: Any) -> dict[int, float]:
    if endless_mode(ctx):
        return {}















    graph = nodes(ctx)

    incoming: dict[int, list[int]] = {int(mid): [] for mid in graph}

    for source, data in graph.items():

        for dest in data.get("next", []):

            if int(dest) in incoming:

                incoming[int(dest)].append(int(source))



    resolved: dict[int, float] = {}

    ordered = sorted(

        graph.items(),

        key=lambda pair: (int(pair[1].get("layer", 0)), int(pair[1].get("lane", 0)), int(pair[0])),

    )

    for mid, data in ordered:

        own = float(data.get("lane", 0))

        parents = incoming.get(int(mid), [])

        parent_positions = [

            resolved.get(parent, float(graph.get(parent, {}).get("lane", own)))

            for parent in parents

        ]

        resolved[int(mid)] = (own + sum(parent_positions)) / (1.0 + len(parent_positions))

    return resolved





def traversed_edge_pairs(ctx: Any) -> set[tuple[int, int]]:
    if endless_mode(ctx):
        return []



    path = [int(x) for x in chosen_path(ctx)]

    return {(path[i], path[i + 1]) for i in range(len(path) - 1)}



def endless_mode(ctx: Any) -> bool:
    return enabled(ctx) and ctx.slay_config.get("game_mode", "adventure") == "endless"

def _new_endless_floor(ctx: Any, progress: dict[str, Any]) -> None:
    from SlayTheStarCraft import generate_endless_layer, endless_map_key
    choices = generate_endless_layer(ctx.slay_config, progress)
    progress["choices"] = choices
    progress["selected"] = None
    progress["offers"] = (progress.get("offers", []) + [[endless_map_key(n) for n in choices]])[-4:]

def complete_endless_mission(ctx: Any, mission_id: int, floor: int) -> bool:
    if not endless_mode(ctx):
        return False
    progress = state(ctx)["endless"]
    if progress["floor"] != floor or progress["selected"] != int(mission_id):
        return False
    winner = next(n for n in progress["choices"] if int(n["mission_id"]) == int(mission_id))
    updated = copy.deepcopy(progress)
    updated["history"].append(copy.deepcopy(node(ctx, mission_id) or winner))
    updated["floor"] += 1
    _new_endless_floor(ctx, updated)
    s = state(ctx)
    s["endless"] = updated
    s["chosen"] = []
    for key in ("temporary_blessings", "temporary_mutations", "node_effect_overrides", "test_mission_overrides"):
        s.get(key, {}).pop(str(mission_id), None)
    _persist_state(ctx)
    ctx.finished_game = False
    credits(ctx)
    return True
