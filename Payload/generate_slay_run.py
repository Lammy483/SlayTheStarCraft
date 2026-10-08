

















from __future__ import annotations



import argparse

import hashlib

import json

import math

import random

import subprocess

import sys

from collections import Counter

from pathlib import Path

from typing import Any, Iterable



import yaml



FORMAT_VERSION = 39

PACKAGE_VERSION = "1.1.0"

DEFAULT_CHOICE_LAYERS = 11

LANES = 4

CANVAS_WIDTH = 7

LANE_X = {0: 0, 1: 2, 2: 4, 3: 6}

FINAL_LANE = 1

FINAL_X = 3

MAX_LAYERS = 30



DEFAULT_CAMPAIGNS = [

    "Wings of Liberty",

    "Heart of the Swarm",

    "Legacy of the Void",

    "Prophecy",

    "Whispers of Oblivion (Legacy of the Void: Prologue)",

    "Into the Void (Legacy of the Void: Epilogue)",

]















SWARM_DEPENDENCY_MUTATIONS = {"dehakas_pack", "another_gorgon_mutation", "brakk_primal_army"}

SWARM_DEPENDENCY_BLESSINGS = {"another_gorgon_blessing", "lurker_defense", "specialists"}

VOID_DEPENDENCY_MUTATIONS = {"void_thrashers", "taldarim_reinforcements", "heroes_of_the_storm", "enemy_spear_of_adun", "true_golden_armada"}

DEPENDENCY_SENSITIVE_MISSIONS = {"safe haven", "haven's fall"}



def dependency_sensitive_effect_exclusions(mission_name: str) -> tuple[set[str], set[str]]:

    name = str(mission_name or "").strip()

    for suffix in (" (Terran)", " (Zerg)", " (Protoss)"):

        if name.endswith(suffix):

            name = name[:-len(suffix)].strip()

            break

    name = name.casefold()

    if name not in DEPENDENCY_SENSITIVE_MISSIONS:

        return set(), set()

    return (

        set(SWARM_DEPENDENCY_MUTATIONS) | set(VOID_DEPENDENCY_MUTATIONS),

        set(SWARM_DEPENDENCY_BLESSINGS),

    )



MUTATORS = {'golden_armada': 2, 'true_golden_armada': 6, 'low_quality_minerals': 2, 'conga_line': 3, 'ten_minutes_until_destruction': 4, 'siege_mode': 1, 'drakken_laser_drill_enemy': 4, 'dark_archons': 1, 'drop_pods': 3, 'dark_templar': 3, 'fragile_workers': 1, 'decay': 3, 'zombies_mutation': 3, 'limited_bank': 1, 'leviathan_in_orbit': 5, 'heroes_of_the_storm': 3, 'too_many_wraiths': 2, 'void_thrashers': 4, 'not_enough_energy': 1, 'viking_raids': 2, 'nuclear_annihilation': 3, 'darkness': 2, 'adrenaline': 3, 'picky_eaters': 2, 'arms_race': 3, 'rising_gas_prices': 2, 'squishy': 2, 'forced_variety': 2, 'occasional_thor_mutation': 1, 'occasional_ultralisk_mutation': 1, 'occasional_colossus_mutation': 1, 'enemy_regeneration': 3, 'sniper_thor': 1, 'another_gorgon_mutation': 2, 'burrowed_zerglings': 1, 'tower_defense': 2, 'cloaked_nightmare': 5, 'jetpacks': 2, 'tactical_binoculars': 4, 'no_deaths_allowed': 7, 'victory_is_temporary': 5, 'nuclear_workers': 1, 'taldarim_reinforcements': 4, 'miras_mercenaries': 2, 'double_time': 1, 'shrinkage': 3, 'mineral_thieves': 1, 'active_enemies': 2, 'zagaras_banelings': 3, 'buddy_system': 3, 'torrasque': 3, 'nexus_shield': 4, 'gargantuan_enemies': 5, 'raynors_raiders': 6, 'purifier': 4, 'dehakas_pack': 5, 'zombie_apocalypse': 5, 'arguments': 2, 'combat_pay': 2, 'marauder_kill_teams': 2, 'dark_archons_x5': 4, 'siege_mode_x5': 4, 'nuclear_structures': 1, 'hellion_run_by': 2, 'diamondback_wanderers': 3, 'leviathan_outside_base': 5, 'odin_delayed_assault': 3, 'combined_raids': 5, 'brakk_primal_army': 5, 'orlan_fortress': 4, 'enemy_spear_of_adun': 7, 'immortal_zergling': 1}

BLESSINGS = {'investors': 1, 'multi_class': 1, 'speedy': 3, 'general': 2, 'farseers': 1, 'air_support': 2, 'fire_squad': 1, 'fuel_pipeline': 2, 'rapid_evolution': 2, 'zombies_blessing': 4, 'compounding_interest': 2, 'transports': 1, 'lost_vikings': 1, 'warfields_reinforcements': 4, 'energy_overload': 1, 'explosive_armor': 3, 'instant_workers': 2, 'juggernaut': 1, 'assembly_line': 2, 'elite_soldiers': 2, 'blinding_light': 2, 'specialists': 1, 'fortifications': 1, 'baneling_stream': 4, 'tychus': 1, 'zagaras_aid': 2, 'logistics': 1, 'occasional_thor_blessing': 1, 'occasional_ultralisk_blessing': 1, 'occasional_colossus_blessing': 1, 'horde_mode': 3, 'unexpected_evolution': 2, 'another_gorgon_blessing': 2, 'rapid_repair': 1, 'blink_blessing': 2, 'power_overwhelming': 2, 'drakken_laser_drill_blessing': 4, 'lurker_defense': 1, 'combat_workers': 2, 'glass_cannons': 1, 'odin': 4, 'bounty_kills': 1, 'building_overcharge': 3, 'ghost_reporting': 1, 'glorious_martyrs': 4, 'infinite_larva': 2, 'reflective_armor': 2, 'rich_minerals': 1, 'resource_pickups': 1}





def _blessing_severity_for_layer(effect_id: str, layer: int) -> int:



    if str(effect_id) == "power_overwhelming":





        if int(layer) <= 0:

            return 4

        if int(layer) <= 2:

            return 3

        return 2

    return int(BLESSINGS[effect_id])



DEFERRED_EFFECTS: list[str] = ["shrinkage", "enemy_spear_of_adun"]







LIMITED_BANK_MISSION_EXCLUSIONS = {"Devil's Playground", "Cutthroat"}



DESTRUCTION_MISSION_EXCLUSIONS = {"The Essence of Eternity", "Essence of Eternity", "In Utter Darkness", "Last Stand"}







DESTRUCTION_TIMED_DEFENSE_ALLOWLIST = {"Zero Hour", "All-In"}

RICH_MINERALS_MISSION_EXCLUSIONS = {"Devil's Playground"}
GORGON_MISSION_EXCLUSIONS = {"fire in the sky"}









ISLAND_MISSION_NAMES = {

    "maw of the void",

    "the moebius factor",

    "the mobius factor",

    "templar's charge",

}









DETECTOR_OPTIONS_BY_RACE = {

    "terran": ("Missile Turret", "Raven", "Science Vessel"),

    "zerg": ("Spore Crawler", "Overseer"),

    "protoss": ("Photon Cannon", "Observer"),

}

OPENING_DETECTOR_ITEMS = tuple(dict.fromkeys(

    item for options in DETECTOR_OPTIONS_BY_RACE.values() for item in options

))









STARTING_STRUCTURE_UNIT_EXCLUSIONS = {

    "Spore Crawler", "Spine Crawler", "Infested Bunker", "Nydus Worm",

    "Echidna Worm", "Infested Missile Turret", "Bile Launcher",

}











DEFENSIVE_STRUCTURE_ITEMS = {



    "Bunker", "Missile Turret", "Devastator Turret", "Planetary Fortress",

    "Perdition Turret", "Sensor Tower", "Psi Disrupter", "Hive Mind Emulator",

    "Argus Amplifier (Hive Mind Emulator)", "Psi Indoctrinator (Hive Mind Emulator)",



    "Spine Crawler", "Spore Crawler", "Bile Launcher", "Infested Bunker",

    "Infested Missile Turret",



    "Photon Cannon", "Khaydarin Monolith", "Shield Battery",

}









OPENING_POOL_WEIGHTS = {

    0: 0.480,

    1: 0.380,

    2: 0.120,

    3: 0.019,

    4: 0.001,

}

# AP mission difficulty starts at the established opening distribution and is
# exponentially tilted toward harder pools according to fraction of the run
# completed. This is length-independent: the same fractional progress gets the
# same distribution at every campaign length.
MISSION_POOL_TILT_STEEPNESS = 1.8
MISSION_TIER_MUTATION_SEVERITY_PER_TIER = 2.0
RED_DANGER_MARGIN = 250

















EXPECTED_OPENING_CREDIT_AVERAGE = {

    ("easy", "less", "less"): 391.0,

    ("easy", "less", "normal"): 278.0,

    ("easy", "less", "more"): 258.0,

    ("easy", "normal", "less"): 441.0,

    ("easy", "normal", "normal"): 297.0,

    ("easy", "normal", "more"): 263.0,

    ("easy", "more", "less"): 510.0,

    ("easy", "more", "normal"): 335.0,

    ("easy", "more", "more"): 281.0,

    ("medium", "less", "less"): 407.0,

    ("medium", "less", "normal"): 287.0,

    ("medium", "less", "more"): 259.0,

    ("medium", "normal", "less"): 469.0,

    ("medium", "normal", "normal"): 317.0,

    ("medium", "normal", "more"): 267.0,

    ("medium", "more", "less"): 555.0,

    ("medium", "more", "normal"): 372.0,

    ("medium", "more", "more"): 294.0,

    ("hard", "less", "less"): 428.0,

    ("hard", "less", "normal"): 291.0,

    ("hard", "less", "more"): 260.0,

    ("hard", "normal", "less"): 498.0,

    ("hard", "normal", "normal"): 331.0,

    ("hard", "normal", "more"): 271.0,

    ("hard", "more", "less"): 594.0,

    ("hard", "more", "normal"): 407.0,

    ("hard", "more", "more"): 311.0,

    ("brutal", "less", "less"): 435.0,

    ("brutal", "less", "normal"): 300.0,

    ("brutal", "less", "more"): 262.0,

    ("brutal", "normal", "less"): 528.0,

    ("brutal", "normal", "normal"): 342.0,

    ("brutal", "normal", "more"): 280.0,

    ("brutal", "more", "less"): 644.0,

    ("brutal", "more", "normal"): 443.0,

    ("brutal", "more", "more"): 319.0,

}



def _linear_extrapolate_points(points: Sequence[tuple[float, float]], x: float) -> float:
    pts = sorted((float(px), float(py)) for px, py in points)
    if x <= pts[0][0]: a, b = pts[0], pts[1]
    elif x >= pts[-1][0]: a, b = pts[-2], pts[-1]
    else:
        a, b = pts[0], pts[-1]
        for left, right in zip(pts, pts[1:]):
            if left[0] <= x <= right[0]: a, b = left, right; break
    t = 0.0 if abs(b[0] - a[0]) < 1e-9 else (x - a[0]) / (b[0] - a[0])
    return a[1] + ((b[1] - a[1]) * t)


def expected_opening_credit_average(difficulty: str, mutation_frequency: Any = 1.0, blessing_frequency: Any = 1.0, victory_credit_reward_multiplier: float = 1.0) -> float:
    difficulty_key = str(difficulty).strip().casefold()
    if difficulty_key not in GAME_DIFFICULTY: difficulty_key = "brutal"
    mf, bf = _frequency_factor(mutation_frequency), _frequency_factor(blessing_frequency)
    labels = ((0.5, "less"), (1.0, "normal"), (1.5, "more"))
    def at_bless(mut_label: str) -> float:
        return _linear_extrapolate_points([(x, EXPECTED_OPENING_CREDIT_AVERAGE[(difficulty_key, mut_label, lab)]) for x, lab in labels], bf)
    base = _linear_extrapolate_points([(x, at_bless(lab)) for x, lab in labels], mf)
    return max(0.0, base) * max(0.0, float(victory_credit_reward_multiplier))


RACE_WEAPON_ARMOR_UPGRADE_ITEMS = {

    "terran": "Progressive Terran Weapon/Armor Upgrade",

    "zerg": "Progressive Zerg Weapon/Armor Upgrade",

    "protoss": "Progressive Protoss Weapon/Armor Upgrade",

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



NOVA_CAMPAIGN_ITEM_SUFFIXES = (

    "(Nova Equipment)", "(Nova Ability)", "(Nova Suit Module)",

    "(Nova Weapon)", "(Nova Gadget)",

)



ROYAL_GUARD_UNIT_ITEMS = {

    "Pride of Augustgrad", "Sky Fury", "Shock Division", "Blackhammer",

    "Aegis Guard", "Emperor's Shadow", "Son of Korhal", "Bulwark Company",

    "Field Response Theta", "Emperor's Guardian", "Night Hawk", "Night Wolf",

}



def _is_nova_campaign_item(item_name: str, type_name: str = "") -> bool:

    clean = str(item_name).strip()

    normalized_type = str(type_name).replace("_", " ").strip().casefold()

    return any(clean.endswith(suffix) for suffix in NOVA_CAMPAIGN_ITEM_SUFFIXES) or normalized_type.startswith("nova ")





def _is_deprecated_item(item_name: str, type_name: str = "") -> bool:



    clean = str(item_name).replace("_", " ").strip().casefold()

    normalized_type = str(type_name).replace("_", " ").strip().casefold()

    return "deprecated" in clean or "deprecated" in normalized_type



SHOP_PRIORITY_ITEMS = tuple(RACE_WEAPON_ARMOR_UPGRADE_ITEMS.values()) + (

    "Increased Building Construction Speed",

    "Increased Shield Regeneration",

    "Increased Upgrade Research Speed",

    "Reduced Upgrade Research Cost",

)





ARMOR_GRANTING_BLESSINGS = {"juggernaut", "elite_soldiers", "fortifications"}

SUPPLY_CONFLICT_BLESSINGS: set[str] = set()





GAME_SPEEDS = ("default", "slower", "slow", "normal", "fast", "faster")



GAME_DIFFICULTY = {

    "easy": "casual",

    "medium": "normal",

    "hard": "hard",

    "brutal": "brutal",

}

DIFFICULTY_OFFSET = {

    "easy": -0.75,

    "medium": 0.0,

    "hard": 0.75,

    "brutal": 1.25,

}



COMMANDER_HERO_CHOICES: tuple[tuple[int, str], ...] = (

    (0, "Raynor"), (5, "Swann"), (7, "Zeratul"),

    (9, "Artanis"), (10, "Alarak"), (13, "Mohandar"), (14, "Selendis"),

    (15, "Karax"), (18, "Zagara"), (19, "Dehaka"), (20, "Nova"),

    (23, "Tosh"), (24, "Stukov"), (27, "Fenix"), (30, "Vorazun"),

    (32, "Urun"), (33, "Niadra"), (34, "Karass"),

)



def commander_choice(run_seed: int, mission_id: int) -> tuple[int, str]:

    digest = hashlib.sha256(f"{int(run_seed)}:commander:{int(mission_id)}".encode("utf-8")).digest()

    return COMMANDER_HERO_CHOICES[int.from_bytes(digest[:8], "big") % len(COMMANDER_HERO_CHOICES)]



POOL_NAMES = {

    0: "starter",

    1: "easy",

    2: "medium",

    3: "hard",

    4: "very hard",

    5: "very hard",

}





def stable_seed(text: str) -> int:



    import hashlib

    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")





def canvas_index(choice_layers: int, layer: int, lane: int) -> int:



    row = choice_layers - layer

    if layer == choice_layers:

        return FINAL_X

    return row * CANVAS_WIDTH + LANE_X[lane]





def make_canvas(

    choice_layers: int, positions: Iterable[tuple[int, int]] | None = None,

) -> list[str]:



    rows = [[" " for _ in range(CANVAS_WIDTH)] for _ in range(choice_layers + 1)]

    rows[0][FINAL_X] = "X"

    if positions is None:

        active = {(layer, lane) for layer in range(choice_layers) for lane in range(LANES)}

    else:

        active = {(int(layer), int(lane)) for layer, lane in positions if int(layer) < choice_layers}

    for layer, lane in active:

        if 0 <= layer < choice_layers and lane in LANE_X:

            rows[choice_layers - layer][LANE_X[lane]] = "X"

    return ["".join(row) for row in rows]





def _weighted_lane_choice(rng: random.Random, lanes: list[int], preferred_lane: int) -> int:



    if not lanes:

        raise ValueError("lanes must not be empty")

    distance_weight = {0: 40.0, 1: 2.0, 2: 0.35, 3: 0.08}

    weights = [distance_weight.get(abs(lane - preferred_lane), 0.1) for lane in lanes]

    return rng.choices(lanes, weights=weights, k=1)[0]





def _connection_allowed(source_lane: int, target_lane: int, target_lanes: Iterable[int]) -> bool:



    source_lane = int(source_lane)

    target_lane = int(target_lane)

    if abs(source_lane - target_lane) <= 1:

        return True

    occupied = {int(lane) for lane in target_lanes}

    lo, hi = sorted((source_lane, target_lane))

    return all(lane not in occupied for lane in range(lo + 1, hi))





def _weighted_lane_order(rng: random.Random, lanes: list[int], preferred_lane: int) -> list[int]:



    remaining = list(lanes)

    ordered: list[int] = []

    while remaining:

        pick = _weighted_lane_choice(rng, remaining, preferred_lane)

        ordered.append(pick)

        remaining.remove(pick)

    return ordered





def _generate_active_lanes(choice_layers: int, rng: random.Random) -> list[tuple[int, ...]]:















    if choice_layers < 1:

        raise ValueError("choice_layers must be >= 1")



    from itertools import combinations



    layouts: list[tuple[int, ...]] = []

    all_layouts = {

        size: [tuple(c) for c in combinations(range(LANES), size)]

        for size in (2, 3, 4)

    }







    current = tuple(sorted(rng.sample(range(LANES), 3)))

    first_run = min(choice_layers, rng.choice((1, 2, 2)))

    layouts.extend([current] * first_run)







    active_streak = [0] * LANES

    for lane in range(LANES):

        active_streak[lane] = first_run if lane in current else 0



    while len(layouts) < choice_layers:

        previous = set(current)

        remaining = choice_layers - len(layouts)

        size = rng.choices((2, 3, 4), weights=(0.42, 0.50, 0.08), k=1)[0]

        if len(current) == 4 and size == 4:

            size = rng.choices((2, 3), weights=(0.52, 0.48), k=1)[0]



        candidates = [c for c in all_layouts[size] if c != current]





        connected = [c for c in candidates if previous.intersection(c)]

        if connected:

            candidates = connected







        streak_safe = [

            c for c in candidates

            if all((lane not in c) or active_streak[lane] < 5 for lane in range(LANES))

        ]

        if streak_safe:

            candidates = streak_safe



        weights: list[float] = []

        for candidate in candidates:

            cand = set(candidate)

            overlap = len(previous & cand)

            newly_filled = len(cand - previous)

            newly_empty = len(previous - cand)





            shift = newly_filled + newly_empty

            score = 1.0 + 2.2 * shift + 0.75 * min(overlap, 2)



            score += sum(0.9 * active_streak[lane] for lane in previous - cand)



            score += 1.1 * newly_filled

            weights.append(max(0.1, score))



        current = rng.choices(candidates, weights=weights, k=1)[0]





        if len(current) == 4:

            run = 1

        else:

            run = rng.choices((1, 2, 3), weights=(0.18, 0.57, 0.25), k=1)[0]

        run = min(remaining, run)

        layouts.extend([current] * run)



        for lane in range(LANES):

            if lane in current:

                active_streak[lane] += run

            else:

                active_streak[lane] = 0



    layouts = layouts[:choice_layers]









    if choice_layers >= 4:

        mutable_layers = list(range(1, choice_layers - 1)) or list(range(choice_layers))

        for lane in range(LANES):

            if not any(lane in row for row in layouts):

                layer = rng.choice(mutable_layers)

                row = set(layouts[layer])

                if len(row) >= 3:

                    row.remove(rng.choice(sorted(row)))

                row.add(lane)

                layouts[layer] = tuple(sorted(row))

            if all(lane in row for row in layouts):

                eligible = [i for i in mutable_layers if lane in layouts[i] and len(layouts[i]) > 2]

                if eligible:

                    layer = rng.choice(eligible)

                    row = set(layouts[layer])

                    row.remove(lane)

                    layouts[layer] = tuple(sorted(row))



    return layouts





def generate_edges(choice_layers: int, rng: random.Random) -> dict[tuple[int, int], list[tuple[int, int]]]:















    if choice_layers < 1:

        raise ValueError("choice_layers must be >= 1")



    for _layout_attempt in range(64):

        active_by_layer = _generate_active_lanes(choice_layers, rng)

        edges: dict[tuple[int, int], set[tuple[int, int]]] = {

            (layer, lane): set()

            for layer, active_lanes in enumerate(active_by_layer)

            for lane in active_lanes

        }

        final = (choice_layers, FINAL_LANE)

        edges[final] = set()

        valid = True



        for layer in range(choice_layers - 1):

            sources = list(active_by_layer[layer])

            targets = list(active_by_layer[layer + 1])

            target_set = set(targets)



            allowed_by_target = {

                target_lane: [

                    source_lane for source_lane in sources

                    if _connection_allowed(source_lane, target_lane, target_set)

                ]

                for target_lane in targets

            }

            if any(not parents for parents in allowed_by_target.values()):

                valid = False

                break









            ordered_targets = list(targets)

            rng.shuffle(ordered_targets)

            ordered_targets.sort(key=lambda lane: len(allowed_by_target[lane]))



            def assign_target(index: int) -> bool:

                if index >= len(ordered_targets):

                    return True

                target_lane = ordered_targets[index]

                candidates = [

                    lane for lane in allowed_by_target[target_lane]

                    if len(edges[(layer, lane)]) < 2

                ]

                for parent_lane in _weighted_lane_order(rng, candidates, target_lane):

                    edge = (layer + 1, target_lane)

                    edges[(layer, parent_lane)].add(edge)

                    if assign_target(index + 1):

                        return True

                    edges[(layer, parent_lane)].remove(edge)

                return False



            if not assign_target(0):

                valid = False

                break







            for source_lane in sources:

                source = (layer, source_lane)

                legal_targets = [

                    lane for lane in targets

                    if _connection_allowed(source_lane, lane, target_set)

                ]

                if not legal_targets:

                    valid = False

                    break

                if not edges[source]:

                    target_lane = _weighted_lane_choice(rng, legal_targets, source_lane)

                    edges[source].add((layer + 1, target_lane))

                if len(edges[source]) < 2 and len(legal_targets) > 1 and rng.random() < 0.24:

                    candidates = [

                        lane for lane in legal_targets

                        if (layer + 1, lane) not in edges[source]

                    ]

                    if candidates:

                        target_lane = _weighted_lane_choice(rng, candidates, source_lane)

                        edges[source].add((layer + 1, target_lane))

            if not valid:

                break



        if not valid:

            continue







        for lane in active_by_layer[-1]:

            if not _connection_allowed(lane, FINAL_LANE, {FINAL_LANE}):

                valid = False

                break

            edges[(choice_layers - 1, lane)].add(final)

        if not valid:

            continue



        result = {key: sorted(value) for key, value in edges.items()}

        validate_graph(choice_layers, result)

        return result



    raise RuntimeError("Could not build a legal sparse four-column route within 64 bounded attempts")





def validate_graph(choice_layers: int, edges: dict[tuple[int, int], list[tuple[int, int]]]) -> None:

    final = (choice_layers, FINAL_LANE)

    if final not in edges:

        raise ValueError("Graph is missing the final node")

    if any(layer < 0 or layer > choice_layers or lane not in range(LANES) for layer, lane in edges):

        raise ValueError("Graph contains an invalid layer/lane position")

    if any(layer == choice_layers and node != final for node in edges for layer, _lane in [node]):

        raise ValueError("Graph contains an extra final-layer node")



    choice_nodes = {node for node in edges if node[0] < choice_layers}

    for layer in range(choice_layers):

        count = sum(1 for node in choice_nodes if node[0] == layer)

        if not 2 <= count <= 4:

            raise ValueError(f"Choice layer {layer} has {count} nodes; expected 2-4")

    if sum(1 for node in choice_nodes if node[0] == 0) != 3:

        raise ValueError("Opening layer must contain exactly three choices")



    incoming = Counter(dest for destinations in edges.values() for dest in destinations)

    for node in edges:

        layer, _lane = node

        if layer == 0:

            continue

        if incoming[node] < 1:

            raise ValueError(f"Graph node {node} has no predecessor")

    for source, destinations in edges.items():

        layer, _lane = source

        if layer == choice_layers:

            if destinations:

                raise ValueError("Final node has outgoing edges")

            continue

        if not 1 <= len(destinations) <= 2:

            raise ValueError(f"Ordinary node {source} has {len(destinations)} exits")

        for dest in destinations:

            if dest not in edges:

                raise ValueError(f"Edge {source}->{dest} points at a missing node")

            if dest[0] != layer + 1:

                raise ValueError(f"Non-adjacent layer edge {source}->{dest}")

            target_lanes = {lane for node_layer, lane in edges if node_layer == dest[0]}

            if not _connection_allowed(source[1], dest[1], target_lanes):

                raise ValueError(f"Wide edge {source}->{dest} crosses an occupied destination column")















_BRUTAL_POOL_TARGET_PROFILE = (0.0, 1.316, 1.575, 1.959, 2.388, 2.684, 2.558, 3.056, 3.526, 3.545, 4.0)
DEFAULT_CAMPAIGN_LENGTH = 12





def _profile_value(profile: Sequence[float], frac: float) -> float:



    if not profile:

        return 0.0

    if len(profile) == 1:

        return float(profile[0])

    x = max(0.0, min(1.0, float(frac))) * (len(profile) - 1)

    lo = int(x)

    hi = min(len(profile) - 1, lo + 1)

    t = x - lo

    return float(profile[lo]) * (1.0 - t) + float(profile[hi]) * t





def mission_pool_distribution(layer: int, choice_layers: int, final: bool = False) -> dict[int, float]:
    """AP difficulty-tier probabilities at this fraction of the run.

    ``layer`` is zero-based and ``choice_layers`` is the final layer index, so
    progress = layer / choice_layers. At progress 0 this is exactly the
    48/38/12/1.9/0.1 opening distribution. The final mission is forced to pool 4.
    """
    if final or layer >= choice_layers:
        return {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 1.0}

    progress = 0.0 if choice_layers <= 0 else max(0.0, min(1.0, layer / max(1, choice_layers)))
    remaining = max(1.0e-9, 1.0 - progress)
    beta = -MISSION_POOL_TILT_STEEPNESS * math.log(remaining)
    raw = {
        tier: OPENING_POOL_WEIGHTS[tier] * math.exp(tier * beta)
        for tier in range(5)
    }
    total = sum(raw.values())
    if total <= 0.0:
        return dict(OPENING_POOL_WEIGHTS)
    return {tier: raw[tier] / total for tier in range(5)}


def target_pool(layer: int, choice_layers: int, difficulty: str, final: bool = False) -> float:
    """Expected AP pool under the smooth length-independent tier distribution."""
    distribution = mission_pool_distribution(layer, choice_layers, final)
    return sum(float(tier) * probability for tier, probability in distribution.items())


_EXPECTED_MUTATION_SEVERITY_PROFILE = (

    2.42, 2.83, 3.92, 4.59, 5.73, 6.81, 7.66, 8.85, 10.24, 11.51, 12.97, 15.36,

)

_EXPECTED_BLESSING_SEVERITY_PROFILE = (

    8.01, 6.39, 6.11, 5.71, 5.07, 4.67, 3.99, 3.66, 3.42, 2.14, 1.79, 1.80,

)





def expected_danger_score(

    layer: int, choice_layers: int, difficulty: str,

    mutation_frequency: Any = 1.0, blessing_frequency: Any = 1.0,

    final: bool = False,

) -> int:













    frac = 1.0 if final else (0.0 if choice_layers <= 0 else layer / max(1, choice_layers))
    if int(choice_layers) + 1 == DEFAULT_CAMPAIGN_LENGTH:
        mutation_mean = _profile_value(_EXPECTED_MUTATION_SEVERITY_PROFILE, frac)
        blessing_mean = _profile_value(_EXPECTED_BLESSING_SEVERITY_PROFILE, frac)
    else:
        mutation_mean, blessing_mean = _base_effect_means(layer, choice_layers, final)
    mutation_mean = max(0.0, mutation_mean + {"easy": -1.25, "medium": -0.75, "hard": -0.30, "brutal": 0.0}[difficulty]) * _frequency_factor(mutation_frequency)
    blessing_mean = max(0.0, blessing_mean) * _frequency_factor(blessing_frequency)

    layer_number = max(1, int(layer) + 1)

    expected_tier_zero_based = ((layer_number + 2) // 3) - 1

    expected_pool = target_pool(layer, choice_layers, difficulty, final)

    map_premium = 300.0 * (expected_pool - expected_tier_zero_based)

    return int(round(map_premium + (150.0 * mutation_mean) - (100.0 * blessing_mean)))





def minimum_pool_for_layer(layer: int, choice_layers: int, final: bool = False) -> int:
    # The smooth distribution controls pacing. Only the final mission has a hard floor.
    return 4 if final else 0




def choose_mission(

    candidates: list[dict[str, Any]], used_ids: set[int], used_short_names: set[str],

    race_counts: Counter[str], target: int, rng: random.Random, *, min_pool: int = 0,

    opening_bias: bool = False, required_race: str | None = None,

    exact_pool: int | None = None, tier_weights: dict[int, float] | None = None,

) -> dict[str, Any]:

    remaining = [m for m in candidates if m["id"] not in used_ids]

    if not remaining:

        raise RuntimeError("No unused missions remain")



    if required_race is not None:

        race_remaining = [m for m in remaining if str(m["race"]).casefold() == required_race.casefold()]

        if not race_remaining:

            raise RuntimeError(f"No unused missions remain for required race {required_race}")

        remaining = race_remaining



    if exact_pool is not None:

        exact_pool = max(0, min(4, int(exact_pool)))

        exact = [m for m in remaining if int(m["pool"]) == exact_pool]

        if not exact:

            race_note = f" for race {required_race}" if required_race is not None else ""

            raise RuntimeError(f"No unused pool-{exact_pool} mission remains{race_note}")

        remaining = exact

        min_pool = 0



    min_pool = max(0, min(4, int(min_pool)))

    if min_pool > 0:

        hard_enough = [m for m in remaining if int(m["pool"]) >= min_pool]

        if hard_enough:

            remaining = hard_enough

        else:





            hardest = max(int(m["pool"]) for m in remaining)

            remaining = [m for m in remaining if int(m["pool"]) == hardest]







    unique = [m for m in remaining if m["short_name"] not in used_short_names]

    pool = unique if unique else remaining



    if opening_bias and tier_weights is None:
        tier_weights = dict(OPENING_POOL_WEIGHTS)

    # Roll the AP tier before the mission. This prevents a tier with many missions
    # from becoming more likely merely because it has more individual candidates.
    if tier_weights is not None:
        by_pool: dict[int, list[dict[str, Any]]] = {}
        for mission in pool:
            pool_id = max(0, min(4, int(mission["pool"])))
            by_pool.setdefault(pool_id, []).append(mission)
        available_pools = sorted(by_pool)
        if not available_pools:
            raise RuntimeError("No eligible mission difficulty pools remain")

        all_tiers = list(range(5))
        roll_weights = [max(0.0, float(tier_weights.get(tier, 0.0))) for tier in all_tiers]
        if sum(roll_weights) <= 0.0:
            roll_weights = [1.0 for _ in all_tiers]
        desired_pool = rng.choices(all_tiers, weights=roll_weights, k=1)[0]

        # Race locks, uniqueness, or depletion can empty the rolled tier. Preserve
        # the intended roll by falling back to the nearest available tier.
        if desired_pool not in by_pool:
            nearest_distance = min(abs(pool_id - desired_pool) for pool_id in available_pools)
            nearest = [pool_id for pool_id in available_pools if abs(pool_id - desired_pool) == nearest_distance]
            nearest_weights = [max(0.0, float(tier_weights.get(pool_id, 0.0))) for pool_id in nearest]
            if sum(nearest_weights) <= 0.0:
                nearest_weights = [1.0 for _ in nearest]
            desired_pool = rng.choices(nearest, weights=nearest_weights, k=1)[0]

        tier_missions = by_pool[desired_pool]
        race_weights = [
            max(0.001, 1.0 / (1.0 + 0.28 * race_counts[mission["race"]]))
            for mission in tier_missions
        ]
        return rng.choices(tier_missions, weights=race_weights, k=1)[0]

    # Compatibility fallback for any special caller that omits tier weights.
    weights: list[float] = []
    for mission in pool:
        distance = abs(int(mission["pool"]) - target)
        difficulty_weight = 1.0 / ((1.0 + distance) ** 2)
        race_weight = 1.0 / (1.0 + 0.28 * race_counts[mission["race"]])
        weights.append(max(0.001, difficulty_weight * race_weight))
    return rng.choices(pool, weights=weights, k=1)[0]



# Blessing weighting is unchanged. Mutations use a softer profile so low-severity
# effects remain meaningfully represented even late in a run.
EFFECT_SELECTION_WEIGHT = {1: 0.25, 2: 0.45, 3: 1.10, 4: 1.55, 5: 1.95}
MUTATION_SELECTION_WEIGHT = {1: 0.40, 2: 0.65, 3: 1.10, 4: 1.50, 5: 1.85}

def _effect_selection_weight(severity: int, mutation_profile: bool = False) -> float:
    table = MUTATION_SELECTION_WEIGHT if mutation_profile else EFFECT_SELECTION_WEIGHT
    return table[max(1, min(5, int(severity)))]

EFFECT_SELECTION_MULTIPLIER = {"general": 3.0, "multi_class": 2.0}





def _pick_effects_for_budget(

    catalog: dict[str, int], target: int, rng: random.Random, *, max_total: int = 8,

    high_severity_bias: bool = False, max_count: int | None = None,
    mutation_profile: bool = False,

) -> list[str]:















    target = max(0, min(max_total, int(target)))

    if target <= 0:

        return []



    def effect_weight(name: str, value: int) -> float:

        weight = _effect_selection_weight(int(value), mutation_profile)









        if high_severity_bias:

            weight *= max(1.0, float(value) ** (0.80 if mutation_profile else 1.35))

        return weight



    names = list(catalog)

    # Draw candidate order without replacement using any intentional effect
    # multiplier. Development-only boosts for newly added effects are not used;
    # new content follows the same normal weighting as established effects.
    weighted_order: list[str] = []
    pool = list(names)
    while pool:
        if high_severity_bias:
            order_weights = [
                _effect_selection_weight(int(catalog[name]), mutation_profile)
                * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0)
                * max(1.0, float(catalog[name]) ** (0.80 if mutation_profile else 1.35))
                for name in pool
            ]
        else:
            order_weights = [EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in pool]
        pick = rng.choices(pool, weights=order_weights, k=1)[0]
        weighted_order.append(pick)
        pool.remove(pick)
    names = weighted_order
    chosen: list[str] = []

    total = 0







    for name in names:

        value = int(catalog[name])

        if total >= target or (max_count is not None and len(chosen) >= max_count):

            break

        select_weight = effect_weight(name, value)

        if total + value <= target:

            if rng.random() < 0.86 * select_weight:

                chosen.append(name)

                total += value

        elif total + value <= max_total and rng.random() < 0.16 * select_weight:

            chosen.append(name)

            total += value







    remaining = [name for name in names if name not in chosen]

    for _ in range(len(remaining)):

        if total >= target or (max_count is not None and len(chosen) >= max_count):

            break

        fits = [name for name in remaining if total + int(catalog[name]) <= max_total]

        if not fits:

            break

        best_distance = min(abs(target - (total + int(catalog[name]))) for name in fits)

        best = [name for name in fits if abs(target - (total + int(catalog[name]))) == best_distance]

        pick = rng.choices(

            best,

            weights=[effect_weight(name, int(catalog[name])) for name in best],

            k=1,

        )[0]

        value = int(catalog[pick])





        exact_small_repair = best_distance == 0 and target - total == value and value <= 2

        repair_chance = 0.20 if value == 1 else (0.35 if value == 2 else 1.0)

        if exact_small_repair and rng.random() > repair_chance:

            remaining.remove(pick)

            continue

        chosen.append(pick)

        total += value

        remaining.remove(pick)

    return chosen





LEGACY_FREQUENCY_FACTORS = {"less": 0.5, "normal": 1.0, "more": 1.5}













OPENING_EFFECT_COUNT_SOFT_CAP = 4

EARLY_EFFECT_COUNT_SOFT_CAP = 5

LATE_EFFECT_COUNT_SOFT_CAP = 6

EFFECT_COUNT_COMPACTION_CHANCE = 0.65



def _effect_count_soft_cap(layer: int, final: bool = False) -> int:











    if not final and int(layer) <= 0:

        return OPENING_EFFECT_COUNT_SOFT_CAP

    if not final and int(layer) <= 3:

        return EARLY_EFFECT_COUNT_SOFT_CAP

    return LATE_EFFECT_COUNT_SOFT_CAP





def _frequency_factor(value: Any) -> float:
    """Parse a numeric multiplier, while accepting old less/normal/more run files."""
    if isinstance(value, str):
        key = value.strip().casefold()
        if key in LEGACY_FREQUENCY_FACTORS:
            return LEGACY_FREQUENCY_FACTORS[key]
        raw = key
    else:
        raw = value
    try:
        factor = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported effect frequency multiplier: {value}") from exc
    if not math.isfinite(factor) or factor < 0.0:
        raise ValueError(f"Effect frequency multiplier must be finite and non-negative: {value}")
    return factor



def _scale_selected_effects(

    chosen: list[str], catalog: dict[str, int], factor: float, rng: random.Random,

    *, max_total: int, forbidden: Iterable[str] = (),

) -> list[str]:

















    factor = float(factor)

    if abs(factor - 1.0) < 1e-9 or not chosen and factor <= 1.0:

        return list(chosen)

    result = list(chosen)

    forbidden_set = {str(x) for x in forbidden}

    current = sum(int(catalog[name]) for name in result)

    scaled_target = max(0.0, current * factor)

    target_floor = int(math.floor(scaled_target))





    target = target_floor + (1 if rng.random() < (scaled_target - target_floor) else 0)



    if factor < 1.0:













        return [name for name in result if rng.random() < factor]







    available = [name for name in catalog if name not in result and name not in forbidden_set]

    while available and current < target and current < max_total:

        candidates = [name for name in available if current + int(catalog[name]) <= max_total]

        if not candidates:

            break

        current_distance = abs(target - current)

        best_distance = min(abs(target - (current + int(catalog[name]))) for name in candidates)

        if best_distance > current_distance:

            break

        best = [name for name in candidates if abs(target - (current + int(catalog[name]))) == best_distance]





        pick = rng.choices(

            best,

            weights=[_effect_selection_weight(int(catalog[name])) * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in best],

            k=1,

        )[0]

        result.append(pick)

        current += int(catalog[pick])

        available.remove(pick)

    return result





def _compact_effect_package(

    mutators: list[str], blessings: list[str],

    mutation_catalog: dict[str, int], blessing_catalog: dict[str, int],

    rng: random.Random, *, target_count: int = OPENING_EFFECT_COUNT_SOFT_CAP,

) -> tuple[list[str], list[str]]:















    target_count = max(1, int(target_count))

    if len(mutators) + len(blessings) <= target_count:

        return list(mutators), list(blessings)



    mut_value = sum(int(mutation_catalog.get(name, 0)) for name in mutators)

    bless_value = sum(int(blessing_catalog.get(name, 0)) for name in blessings)

    mut_slots = len(mutators)

    bless_slots = len(blessings)









    max_mut_sev = max((int(v) for v in mutation_catalog.values()), default=1)

    max_bless_sev = max((int(v) for v in blessing_catalog.values()), default=1)

    min_mut_slots = int(math.ceil(mut_value / max_mut_sev)) if mut_value > 0 else 0

    min_bless_slots = int(math.ceil(bless_value / max_bless_sev)) if bless_value > 0 else 0



    while mut_slots + bless_slots > target_count:

        can_reduce_mut = mut_slots > min_mut_slots

        can_reduce_bless = bless_slots > min_bless_slots

        if not can_reduce_mut and not can_reduce_bless:





            break

        if can_reduce_mut and not can_reduce_bless:

            mut_slots -= 1

            continue

        if can_reduce_bless and not can_reduce_mut:

            bless_slots -= 1

            continue

        mut_density = mut_value / max(1, mut_slots)

        bless_density = bless_value / max(1, bless_slots)

        if mut_density <= bless_density:

            mut_slots -= 1

        else:

            bless_slots -= 1



    compact_mutators = _pick_effects_for_budget(

        mutation_catalog, mut_value, rng,

        max_total=max(1, mut_value), high_severity_bias=True, max_count=mut_slots, mutation_profile=True,

    ) if mut_slots > 0 and mut_value > 0 else []

    compact_blessings = _pick_effects_for_budget(

        blessing_catalog, bless_value, rng,

        max_total=max(1, bless_value), high_severity_bias=True, max_count=bless_slots,

    ) if bless_slots > 0 and bless_value > 0 else []

    return compact_mutators, compact_blessings





def _reroll_no_deaths_allowed(
    mutators: list[str], mutation_catalog: Mapping[str, int], rng: random.Random,
) -> list[str]:
    """Reroll No Deaths Allowed half the time after normal generation selects it."""
    if "no_deaths_allowed" not in mutators or rng.random() >= 0.50:
        return list(mutators)
    current = list(mutators)
    used = set(current)
    candidates = [name for name in mutation_catalog if name != "no_deaths_allowed" and name not in used]
    if not candidates:
        return current
    replacement = rng.choices(
        candidates,
        weights=[
            _effect_selection_weight(int(mutation_catalog[name]))
            * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0)
            for name in candidates
        ],
        k=1,
    )[0]
    current[current.index("no_deaths_allowed")] = replacement
    return current


def _is_final_quarter(layer: int, choice_layers: int, final: bool = False) -> bool:
    total_missions = max(1, int(choice_layers) + 1)
    mission_number = max(1, int(layer) + 1)
    return bool(final) or mission_number >= (math.floor(total_missions * 0.75) + 1)


def _is_past_halfway(layer: int, choice_layers: int, final: bool = False) -> bool:
    total_missions = max(1, int(choice_layers) + 1)
    mission_number = max(1, int(layer) + 1)
    return bool(final) or mission_number > (total_missions / 2.0)


def _base_effect_means(layer: int, choice_layers: int, final: bool = False) -> tuple[float, float]:
    total_missions = max(1, int(choice_layers) + 1)
    mission_number = max(1, int(layer) + 1)
    if total_missions == DEFAULT_CAMPAIGN_LENGTH:
        frac = 1.0 if final else (0.0 if choice_layers <= 0 else layer / max(1, choice_layers))
        mutation_budget_profile = (1.95, 1.91, 2.80, 3.50, 4.60, 5.55, 6.45, 6.95, 8.45, 9.60, 11.15, 12.87)
        blessing_budget_profile = (7.65, 6.95, 6.68, 6.28, 5.60, 5.20, 4.55, 4.45, 4.05, 3.65, 3.25, 3.25)
        mut_mean = _profile_value(mutation_budget_profile, frac)
        if final: mut_mean += 2.0
        bless_mean = _profile_value(blessing_budget_profile, frac)
        if final or (choice_layers >= 2 and layer >= choice_layers - 2): bless_mean -= 2.2
        elif layer > 0: bless_mean -= 1.1
        return mut_mean, bless_mean
    mut_mean = float(mission_number + 2) + (2.0 if final else 0.0)
    third_last = max(1, total_missions - 2)
    if mission_number >= third_last or third_last <= 1: bless_mean = 1.0
    else: bless_mean = 7.0 - (6.0 * ((mission_number - 1) / max(1, third_last - 1)))
    return mut_mean, bless_mean


def roll_effects(

    layer: int, choice_layers: int, difficulty: str, rng: random.Random,

    final: bool = False,

    forbidden_mutators: Iterable[str] = (), forbidden_blessings: Iterable[str] = (), mission_pool: int = 0,

    mutation_frequency: Any = 1.0, blessing_frequency: Any = 1.0,

) -> tuple[list[str], list[str], int, int]:



















    frac = 1.0 if final else (0.0 if choice_layers <= 0 else layer / max(1, choice_layers))

    forbidden = {str(x) for x in forbidden_mutators}

    forbidden_help = {str(x) for x in forbidden_blessings}







    max_opening_mutation_severity = 99

    if not final and layer == 0:

        max_opening_mutation_severity = 3

    elif not final and layer == 1:

        max_opening_mutation_severity = 4

    elif not final and layer == 2:

        max_opening_mutation_severity = 5



    mutation_catalog = {

        name: value for name, value in MUTATORS.items()

        if name not in forbidden

        and name not in DEFERRED_EFFECTS

        and int(value) <= max_opening_mutation_severity

    }

    blessing_catalog = {

        name: _blessing_severity_for_layer(name, layer)

        for name in BLESSINGS

        if name not in forbidden_help

    }









    mut_mean, bless_mean = _base_effect_means(layer, choice_layers, final)
    difficulty_mut_shift = {"easy": -1.25, "medium": -0.75, "hard": -0.30, "brutal": 0.0}[difficulty]
    expected_pool = target_pool(layer, choice_layers, difficulty, final)
    # Balance AP mission tier against mutation severity. A mission one full AP
    # tier below the layer average receives +2 mean mutation severity; one
    # tier above average receives -2. Fractional expected tiers interpolate.
    mission_tier_mut_shift = (expected_pool - float(mission_pool)) * MISSION_TIER_MUTATION_SEVERITY_PER_TIER
    mut_factor = _frequency_factor(mutation_frequency)
    bless_factor = _frequency_factor(blessing_frequency)
    scaled_mut_mean = max(0.0, (mut_mean + difficulty_mut_shift + mission_tier_mut_shift) * mut_factor)
    scaled_bless_mean = max(0.0, bless_mean * bless_factor)
    mut_target = max(0, min(20, int(round(rng.gauss(scaled_mut_mean, 1.35)))))
    bless_target = max(0, min(12, int(round(rng.gauss(scaled_bless_mean, 2.0)))))


    if not final and frac < 0.35 and int(mission_pool) >= 3:

        bless_target = min(12, bless_target + min(2, int(mission_pool) - 2))



    late_bias = _is_past_halfway(layer, choice_layers, final)

    mutators = _pick_effects_for_budget(

        mutation_catalog, mut_target, rng, max_total=20,

        high_severity_bias=late_bias, max_count=(4 if late_bias else None), mutation_profile=True,

    )

    blessings = _pick_effects_for_budget(blessing_catalog, bless_target, rng, max_total=12)









    major_required = _is_final_quarter(layer, choice_layers, final)

    if major_required and not any(int(mutation_catalog.get(name, 0)) >= 4 for name in mutators):

        major_candidates = [name for name, value in mutation_catalog.items() if int(value) >= 4 and name not in mutators]

        if major_candidates:

            major = rng.choices(

                major_candidates,

                weights=[_effect_selection_weight(int(mutation_catalog[name])) * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in major_candidates],

                k=1,

            )[0]

            if mutators:

                smallest = min(mutators, key=lambda name: int(mutation_catalog.get(name, 99)))

                mutators.remove(smallest)

            mutators.append(major)



    if "squishy" in mutators:

        blessings = [name for name in blessings if name not in ARMOR_GRANTING_BLESSINGS]



    mut_value = sum(MUTATORS[x] for x in mutators)

    bless_value = sum(blessing_catalog[x] for x in blessings)







    if _is_past_halfway(layer, choice_layers, final) and mut_value <= bless_value:

        while blessings and mut_value <= bless_value:

            removed = max(blessings, key=lambda x: blessing_catalog[x])

            blessings.remove(removed)

            bless_value = sum(blessing_catalog[x] for x in blessings)

        if mut_value <= bless_value:

            for name, value in sorted(mutation_catalog.items(), key=lambda kv: kv[1]):

                if name not in mutators:

                    mutators.append(name)

                    mut_value += value

                    if mut_value > bless_value:

                        break



    if "squishy" in mutators:

        blessings = [name for name in blessings if name not in ARMOR_GRANTING_BLESSINGS]

    bless_value = sum(blessing_catalog[x] for x in blessings)













    if "squishy" in mutators:

        blessings = [name for name in blessings if name not in ARMOR_GRANTING_BLESSINGS]













    effect_count_soft_cap = _effect_count_soft_cap(layer, final)







    effect_count_compaction_chance = (

        0.25 if (mut_factor > 1.0 or bless_factor > 1.0) else EFFECT_COUNT_COMPACTION_CHANCE

    )

    if (

        len(mutators) + len(blessings) > effect_count_soft_cap

        and rng.random() < effect_count_compaction_chance

    ):

        mutators, blessings = _compact_effect_package(

            mutators, blessings, mutation_catalog, blessing_catalog, rng,

            target_count=effect_count_soft_cap,

        )

        if "squishy" in mutators:

            blessings = [name for name in blessings if name not in ARMOR_GRANTING_BLESSINGS]



    # No Deaths Allowed is intentionally less common than its raw selection weight:
    # half of naturally generated copies are rerolled into another legal mutation.
    mutators = _reroll_no_deaths_allowed(mutators, mutation_catalog, rng)
    # A No Deaths Allowed reroll must not accidentally remove the final-quarter
    # guarantee of at least one severity-4+ mutation.
    if major_required and not any(int(mutation_catalog.get(name, 0)) >= 4 for name in mutators):
        major_candidates = [name for name, value in mutation_catalog.items() if int(value) >= 4 and name not in mutators]
        if major_candidates:
            major = rng.choices(major_candidates, weights=[_effect_selection_weight(int(mutation_catalog[name])) * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0) for name in major_candidates], k=1)[0]
            if mutators:
                mutators.remove(min(mutators, key=lambda name: int(mutation_catalog.get(name, 99))))
            mutators.append(major)
    if "squishy" in mutators:
        blessings = [name for name in blessings if name not in ARMOR_GRANTING_BLESSINGS]

    mut_value = sum(MUTATORS[x] for x in mutators)

    bless_value = sum(blessing_catalog[x] for x in blessings)

    return mutators, blessings, mut_value, bless_value





def credit_reward(

    mission_pool: int, layer: int, mutation_value: int, blessing_value: int,

    has_blessings: bool, rng: random.Random, mission_name: str = "",

    victory_credit_reward_multiplier: float = 1.0,

) -> int:











    layer_number = max(1, int(layer) + 1)

    mission_tier = max(1, int(mission_pool) + 1)

    expected_tier = (layer_number + 2) // 3















    base_reward = 400

    layer_reward = 50 * layer_number

    difficulty_reward = 300 * (mission_tier - expected_tier)

    effect_reward = (150 * int(mutation_value)) - (100 * int(blessing_value)) + (100 * layer_number)

    old_reward = base_reward + layer_reward + difficulty_reward + effect_reward

    reward = max(250, old_reward - (100 * layer_number))

    if str(mission_name).strip().casefold() == "lab rat":

        reward -= 100

    multiplier = max(0.0, float(victory_credit_reward_multiplier))

    return max(0, int(math.floor((reward * multiplier) + 0.5)))





def _is_unit_unlock_type(type_name: str) -> bool:

    normalized = str(type_name).replace("_", " ").strip().casefold()

    return normalized == "mercenary" or normalized.startswith("unit")





def _is_specific_upgrade_parent_type(type_name: str) -> bool:

    normalized = str(type_name).replace("_", " ").strip().casefold()

    return normalized in {"building", "morph"} or _is_unit_unlock_type(type_name)





def load_archipelago_catalog(

    ap_root: Path, races: set[str], allow_race_swap: bool,

) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]], list[str]]:

    root_str = str(ap_root)

    if root_str not in sys.path:

        sys.path.insert(0, root_str)

    from BaseClasses import ItemClassification

    from worlds.sc2.mission_tables import SC2Campaign, SC2Mission, SC2Race, MissionFlag

    from worlds.sc2.item.item_tables import get_full_item_list

    try:

        from worlds.sc2.item.item_groups import item_name_groups

    except Exception:

        item_name_groups = {}

    try:

        from worlds.sc2.item import item_parents as ap_item_parents

    except Exception:

        ap_item_parents = None



    race_lookup = {"terran": SC2Race.TERRAN, "zerg": SC2Race.ZERG, "protoss": SC2Race.PROTOSS}

    selected = {race_lookup[r] for r in races}

    allowed_campaigns = set(DEFAULT_CAMPAIGNS)



    missions: list[dict[str, Any]] = []

    for mission in SC2Mission:

        if mission.campaign == SC2Campaign.GLOBAL or mission.campaign.campaign_name not in allowed_campaigns:

            continue

        if MissionFlag.NoBuild in mission.flags:

            continue









        if mission.race not in selected:

            continue

        if not allow_race_swap and MissionFlag.RaceSwap in mission.flags:

            continue

        missions.append({

            "id": int(mission.id),

            "name": mission.mission_name,

            "short_name": mission.get_short_name(),

            "race": mission.race.get_title(),

            "pool": int(mission.pool),

            "campaign": mission.campaign.campaign_name,

            "race_swap": bool(MissionFlag.RaceSwap in mission.flags),

            "kerrigan": (

                mission.campaign == SC2Campaign.HOTS

                and mission.race == SC2Race.ZERG

                and MissionFlag.Kerrigan in mission.flags

            ),

            "lotv": mission.campaign == SC2Campaign.LOTV,

            "timed_defense": bool(MissionFlag.TimedDefense in mission.flags),

        })



    if not missions:

        raise RuntimeError("No eligible build missions remain for the selected races/settings")









    shop_candidates: list[str] = []

    unit_candidates_by_race: dict[str, list[str]] = {r: [] for r in races}

    banned_items: list[str] = []

    full_item_table = get_full_item_list()

    terran_mercenaries = set(item_name_groups.get("Terran Mercenaries", ()))

    zerg_mercenaries = set(item_name_groups.get("Zerg Mercenaries", ()))

    kerrigan_abilities = set(item_name_groups.get("Kerrigan Abilities", ()))

    spear_items = set(item_name_groups.get("SOA", ()))

    war_council_baseline_items = set(item_name_groups.get("Protoss War Council Upgrades", ()))

    mercenary_general_upgrades = {

        "Rogue Forces (Terran)", "Progressive Fast Delivery (Terran)",

        "Rapid Reinforcement (Terran)", "Signal Beacon (Terran)",

        "Cell Division (Zerg)", "Self-Sufficient (Zerg)",

        "Unrestricted Mutation (Zerg)", "Evolutionary Leap (Zerg)",

    }











    mission_reward_global_items = {

        "Progressive Terran Weapon/Armor Upgrade",

        "Progressive Zerg Weapon/Armor Upgrade",

        "Progressive Protoss Weapon/Armor Upgrade",

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

        "Automated Extractors (Zerg)", "Improved Overlords (Overlord)",

        "Malignant Creep (Zerg)", "Twin Drones (Zerg)",

        "Vespene Efficiency (Zerg)", "Zergling Reconstitution (Zerg)",

        "Excavating Claws (Zerg)", "Creep Stomach (Zerg)",

        "Hive Cluster Maturation (Zerg)", "Macroscopic Recuperation (Zerg)",

        "Broodling Spore Saturation (Zerg)",

        "Amplified Assimilators (Protoss)", "Elder Probes (Protoss)",

        "Khalai Ingenuity (Protoss)", "Matrix Overload (Protoss)",

        "Nexus Overcharge (Protoss)", "Optimized Ordnance (Protoss)",

        "Orbital Assimilators (Protoss)", "Warp Harmonization (Protoss)",

        "Superior Warp Gates (Protoss)", "Progressive Warp Relocate (Protoss)",

        "Probe Warp-In (Protoss)", "Quatro (Protoss)",

        "Increased Building Construction Speed",

        "Increased Shield Regeneration",

        "Increased Upgrade Research Speed",

        "Reduced Upgrade Research Cost",

        "Additional Starting Minerals",

        "Additional Starting Vespene",

        "Additional Starting Supply",

        "Additional Maximum Supply",

    }



    def direct_unit_parent(item_name: str, item_data: Any) -> str | None:







        if item_name in mission_reward_global_items:

            return None



        candidates: list[str] = []

        if ap_item_parents is not None:

            try:

                candidates.extend(str(x) for x in ap_item_parents.child_item_to_parent_items.get(item_name, ()))

            except Exception:

                pass

            if not candidates:

                try:

                    parent_id = getattr(item_data, "parent", None)

                    rule = ap_item_parents.parent_present.get(parent_id)

                    if rule is not None:

                        candidates.extend(str(x) for x in rule.parent_items())

                except Exception:

                    pass





        parent = getattr(item_data, "parent", None) or getattr(item_data, "parent_item", None)

        if isinstance(parent, str) and parent in full_item_table:

            candidates.append(parent)





        if " (" in item_name and item_name.endswith(")"):

            candidates.append(item_name.rsplit(" (", 1)[1][:-1])



        for candidate in candidates:

            if candidate in ROYAL_GUARD_UNIT_ITEMS:

                return candidate

            if candidate not in full_item_table:

                continue

            parent_type = str(getattr(full_item_table[candidate].type, "display_name", ""))

            if _is_specific_upgrade_parent_type(parent_type):

                return candidate

        return None



    def shop_only_reward(item_name: str, item_data: Any) -> bool:

        type_name = str(getattr(item_data.type, "display_name", ""))

        parent = getattr(item_data, "parent", None) or getattr(item_data, "parent_item", None)









        if item_name in war_council_baseline_items or type_name.casefold().startswith("war council"):

            return False

        if item_name in terran_mercenaries or item_name in zerg_mercenaries or type_name.casefold() == "mercenary":

            return True

        if item_name in mercenary_general_upgrades or parent in {"Terran Mercenaries", "Zerg Mercenaries"}:

            return True

        if item_name in kerrigan_abilities or type_name.casefold() in {"level", "primal form"}:

            return True

        if item_name in spear_items or type_name.casefold() == "spear of adun":

            return True

        return direct_unit_parent(item_name, item_data) is not None



    for name, data in full_item_table.items():

        if data.code is None:

            continue

        type_name = str(getattr(data.type, "display_name", ""))

        if _is_deprecated_item(name, type_name):





            banned_items.append(name)

            continue

        if data.classification & ItemClassification.trap or type_name == "Max Supply Trap" or "key" in type_name.casefold():

            banned_items.append(name)

            continue

        if _is_nova_campaign_item(name, type_name):





            banned_items.append(name)

            continue

        royal_parent = direct_unit_parent(name, data)

        if name in ROYAL_GUARD_UNIT_ITEMS or royal_parent in ROYAL_GUARD_UNIT_ITEMS:

            banned_items.append(name)

            continue

        if name in REDUNDANT_BASIC_STAT_UPGRADE_ITEMS:

            banned_items.append(name)

            continue







        if shop_only_reward(name, data):

            banned_items.append(name)

        if int(getattr(data, "quantity", 0)) <= 0:

            continue



        detector_races = {

            race for race, options in DETECTOR_OPTIONS_BY_RACE.items()

            if race in races and name in options

        }

        if detector_races or name in DEFENSIVE_STRUCTURE_ITEMS:

            shop_candidates.append(name)

        elif data.race not in selected and data.race != SC2Race.ANY:

            continue

        else:





            shop_candidates.append(name)



        if (

            name not in OPENING_DETECTOR_ITEMS

            and name not in STARTING_STRUCTURE_UNIT_EXCLUSIONS

            and name not in DEFENSIVE_STRUCTURE_ITEMS

            and _is_unit_unlock_type(type_name)

            and data.race in selected

        ):

            race_key = str(data.race.get_title()).casefold()

            if race_key in unit_candidates_by_race:

                unit_candidates_by_race[race_key].append(name)



    return missions, shop_candidates, unit_candidates_by_race, sorted(set(banned_items))





def select_starting_shop(

    unit_candidates_by_race: dict[str, list[str]], races: list[str], rng: random.Random, count: int = 3,

) -> list[str]:



    required = 2 * len(races)

    if count < required:

        raise RuntimeError("Starting shop is too small to provide two units per selected race")



    selected: list[str] = []

    for race in races:

        candidates = list(dict.fromkeys(unit_candidates_by_race.get(race.casefold(), [])))

        if len(candidates) < 2:

            raise RuntimeError(f"Fewer than two eligible Unit unlocks found for starting-shop race {race}")

        picks = rng.sample(candidates, 2)

        selected.extend(picks)



    remaining = [

        name

        for race in races

        for name in dict.fromkeys(unit_candidates_by_race.get(race.casefold(), []))

        if name not in selected

    ]

    while len(selected) < count:

        if not remaining:

            raise RuntimeError(f"Only {len(selected)} distinct starting Unit unlocks found; need {count}")

        pick = rng.choice(remaining)

        selected.append(pick)

        remaining.remove(pick)

    return selected





def select_opening_detectors(

    shop_candidates: list[str], races: list[str], rng: random.Random,

) -> list[str]:



    available = set(shop_candidates)

    chosen: list[str] = []

    for race in races:

        options = [name for name in DETECTOR_OPTIONS_BY_RACE.get(race.casefold(), ()) if name in available]

        if not options:

            raise RuntimeError(f"No detector unlock is available for starting-shop race {race}")

        chosen.append(rng.choice(options))

    return chosen





def add_opening_detector_items(starting_units: list[str], detectors: list[str]) -> list[str]:



    overlap = sorted(set(starting_units) & set(detectors))

    if overlap:

        raise RuntimeError(f"Detector items leaked into random starting Unit slots: {overlap}")

    opening = list(dict.fromkeys(list(starting_units) + list(detectors)))

    if len(opening) != len(starting_units) + len(detectors):

        raise RuntimeError("Opening shop contains duplicate items")

    return opening





def select_shop_pool(

    candidates: list[str], starting_shop: list[str], rng: random.Random, count: int = 20,

) -> list[str]:



    starting = list(dict.fromkeys(starting_shop))

    unique = [name for name in dict.fromkeys(candidates) if name not in starting]

    priority = [name for name in SHOP_PRIORITY_ITEMS if name in unique]

    random_candidates = [name for name in unique if name not in priority]

    needed_random = count - len(starting) - len(priority)

    if needed_random < 0:

        raise RuntimeError(

            f"Starting+priority shop package has {len(starting) + len(priority)} items but base pool size is only {count}"

        )

    if len(random_candidates) < needed_random:

        raise RuntimeError(

            f"Only {len(random_candidates)} eligible random shop items found; need {needed_random}"

        )

    return starting + priority + rng.sample(random_candidates, needed_random)







def _route_paths(

    choice_layers: int, edges: dict[tuple[int, int], list[tuple[int, int]]]

) -> list[list[tuple[int, int]]]:



    final = (choice_layers, FINAL_LANE)

    paths: list[list[tuple[int, int]]] = []



    def walk(node: tuple[int, int], path: list[tuple[int, int]]) -> None:

        next_path = path + [node]

        if node == final:

            paths.append(next_path)

            return

        for child in edges.get(node, ()):

            walk(child, next_path)



    for node in sorted(pos for pos in edges if pos[0] == 0):

        walk(node, [])

    return paths





def _long_same_race_nodes(

    choice_layers: int,

    edges: dict[tuple[int, int], list[tuple[int, int]]],

    assigned: dict[tuple[int, int], dict[str, Any]],

    minimum_run: int = 4,

) -> set[tuple[int, int]]:



    flagged: set[tuple[int, int]] = set()

    for path in _route_paths(choice_layers, edges):

        start = 0

        while start < len(path):

            race = str(assigned[path[start]].get("race", ""))

            end = start + 1

            while end < len(path) and str(assigned[path[end]].get("race", "")) == race:

                end += 1

            if race and end - start >= minimum_run:

                flagged.update(path[start:end])

            start = end

    return flagged





def _effect_exclusions_for_mission(mission: dict[str, Any]) -> tuple[set[str], set[str]]:



    forbidden_mutators = (

        {"limited_bank"} if mission.get("name") in LIMITED_BANK_MISSION_EXCLUSIONS else set()

    )

    if str(mission.get("name", "")).startswith("Rak'Shir"):

        forbidden_mutators.add("burrowed_zerglings")

    mission_short_name = str(mission.get("short_name", "") or mission.get("name", ""))
    if mission_short_name.strip().casefold() in GORGON_MISSION_EXCLUSIONS:
        forbidden_mutators.add("another_gorgon_mutation")


    if mission_short_name.strip().casefold() in ISLAND_MISSION_NAMES:

        forbidden_mutators.update({"torrasque", "ten_minutes_until_destruction", "hellion_run_by", "odin_delayed_assault", "combined_raids", "brakk_primal_army"})

    destruction_explicitly_forbidden = (

        mission_short_name in DESTRUCTION_MISSION_EXCLUSIONS

        or any(mission_short_name.startswith(name) for name in DESTRUCTION_MISSION_EXCLUSIONS)

    )

    destruction_timed_defense_forbidden = (

        bool(mission.get("timed_defense", False))

        and mission_short_name not in DESTRUCTION_TIMED_DEFENSE_ALLOWLIST

        and not any(mission_short_name.startswith(name) for name in DESTRUCTION_TIMED_DEFENSE_ALLOWLIST)

    )

    if destruction_explicitly_forbidden or destruction_timed_defense_forbidden:

        forbidden_mutators.add("ten_minutes_until_destruction")



    forbidden_blessings: set[str] = set()
    if mission_short_name.strip().casefold() in GORGON_MISSION_EXCLUSIONS:
        forbidden_blessings.add("another_gorgon_blessing")

    dependency_forbidden_mutators, dependency_forbidden_blessings = dependency_sensitive_effect_exclusions(

        mission_short_name

    )

    forbidden_mutators.update(dependency_forbidden_mutators)

    forbidden_blessings.update(dependency_forbidden_blessings)

    mission_race = str(mission.get("race", "")).lower()

    if mission_race != "terran":

        forbidden_blessings.add("rapid_repair")

    if mission_race != "zerg":

        forbidden_blessings.add("stealth_tunnels")

        forbidden_blessings.add("infinite_larva")

    if any(str(mission.get("name", "")).startswith(name) for name in RICH_MINERALS_MISSION_EXCLUSIONS):

        forbidden_blessings.add("rich_minerals")

    return forbidden_mutators, forbidden_blessings





def _assigned_danger_score(data: dict[str, Any]) -> int:

    layer_number = max(1, int(data.get("layer", 0)) + 1)

    mission_tier = max(1, int(data.get("pool", 0)) + 1)

    expected_tier = (layer_number + 2) // 3

    return (

        300 * (mission_tier - expected_tier)

        + 150 * int(data.get("mutation_value", 0))

        - 100 * int(data.get("blessing_value", 0))

    )





def _assigned_node_is_red(

    assigned: dict[tuple[int, int], dict[str, Any]], pos: tuple[int, int], choice_layers: int,

) -> bool:



    data = assigned[pos]

    layer = int(data.get("layer", -1))

    if layer < 0 or layer >= choice_layers:

        return False

    if layer == 0:





        expected_average = float(data.get("expected_opening_credit_average", 0.0))

        if expected_average <= 0.0:

            expected_average = EXPECTED_OPENING_CREDIT_AVERAGE[("brutal", "normal", "normal")]

        return float(data.get("credit_reward", 0)) > (2.5 * expected_average)

    return _assigned_danger_score(data) >= int(data.get("expected_danger_score", 0)) + RED_DANGER_MARGIN





def _forced_red_nodes_for_reroll(

    choice_layers: int,

    edges: dict[tuple[int, int], list[tuple[int, int]]],

    assigned: dict[tuple[int, int], dict[str, Any]],

) -> set[tuple[int, int]]:



    flagged: set[tuple[int, int]] = set()

    for path in _route_paths(choice_layers, edges):

        run: list[tuple[int, int]] = []

        for pos in path:

            if pos[0] < choice_layers and len(edges.get(pos, ())) == 1:

                run.append(pos)

                continue

            red_in_run = [p for p in run if _assigned_node_is_red(assigned, p, choice_layers)]

            if len(red_in_run) >= 3:

                flagged.update(red_in_run)

            run = []

        red_in_run = [p for p in run if _assigned_node_is_red(assigned, p, choice_layers)]

        if len(red_in_run) >= 3:

            flagged.update(red_in_run)

    return flagged





def _red_free_paths(

    choice_layers: int,

    edges: dict[tuple[int, int], list[tuple[int, int]]],

    assigned: dict[tuple[int, int], dict[str, Any]],

) -> list[list[tuple[int, int]]]:

    return [

        path for path in _route_paths(choice_layers, edges)

        if not any(_assigned_node_is_red(assigned, pos, choice_layers) for pos in path)

    ]





def assign_missions(

    choice_layers: int, difficulty: str, candidates: list[dict[str, Any]],

    edges: dict[tuple[int, int], list[tuple[int, int]]], rng: random.Random,

    mutation_frequency: Any = 1.0, blessing_frequency: Any = 1.0,

    victory_credit_reward_multiplier: float = 1.0,

) -> dict[tuple[int, int], dict[str, Any]]:

    required_nodes = len(edges)

    if len(candidates) < required_nodes:

        raise RuntimeError(f"Need {required_nodes} mission variants but only {len(candidates)} are eligible")



    used_ids: set[int] = set()

    used_short_names: set[str] = set()

    race_counts: Counter[str] = Counter()

    assigned: dict[tuple[int, int], dict[str, Any]] = {}

    opening_expected_average = expected_opening_credit_average(

        difficulty, mutation_frequency, blessing_frequency, victory_credit_reward_multiplier

    )



    def finish_node(

        mission: dict[str, Any], layer: int, lane: int, final: bool, *, opening_easy: bool = False

    ) -> dict[str, Any]:





        forbidden_mutators, forbidden_blessings = _effect_exclusions_for_mission(mission)













        attempts = 32 if opening_easy else 1

        base_reward = 0

        reward = 0

        for _attempt in range(attempts):

            mutators, blessings, mut_value, bless_value = roll_effects(

                layer, choice_layers, difficulty, rng, final=final,

                forbidden_mutators=forbidden_mutators, forbidden_blessings=forbidden_blessings,

                mission_pool=int(mission["pool"]),

                mutation_frequency=mutation_frequency, blessing_frequency=blessing_frequency,

            )





            base_reward = credit_reward(

                mission["pool"], layer, mut_value, bless_value, bool(blessings), rng,

                mission_name=str(mission.get("name", "")),

            )

            if not opening_easy or base_reward <= 350:

                break

        if opening_easy and base_reward > 350:

            legal_blessings = [

                name for name in BLESSINGS

                if name not in forbidden_blessings

            ]

            if not legal_blessings:

                raise RuntimeError("No legal blessing is available for the guaranteed easy opening route")

            fallback_blessing = rng.choice(legal_blessings)

            mutators = []

            blessings = [fallback_blessing]

            mut_value = 0

            bless_value = _blessing_severity_for_layer(fallback_blessing, layer)

            base_reward = credit_reward(

                mission["pool"], layer, mut_value, bless_value, True, rng,

                mission_name=str(mission.get("name", "")),

            )

            if base_reward > 350:

                raise RuntimeError("Could not produce a <=350-credit guaranteed easy opening route")

        reward = credit_reward(

            mission["pool"], layer, mut_value, bless_value, bool(blessings), rng,

            mission_name=str(mission.get("name", "")),

            victory_credit_reward_multiplier=victory_credit_reward_multiplier,

        )

        return {

            **mission,

            "layer": layer,

            "lane": lane,

            "mutators": mutators,

            "blessings": blessings,

            "mutation_value": mut_value,

            "blessing_value": bless_value,

            "expected_danger_score": expected_danger_score(

                layer, choice_layers, difficulty, mutation_frequency, blessing_frequency, final

            ),

            "expected_opening_credit_average": float(opening_expected_average),

            "credit_reward": reward,

            "next_positions": [] if final else edges[(layer, lane)],

        }



    available_races = sorted({str(m["race"]) for m in candidates})

    canonical_opening_races = ["Terran", "Zerg", "Protoss"]

    canonical_three_race = all(race in available_races for race in canonical_opening_races)

    opening_lanes = sorted(lane for layer, lane in edges if layer == 0)

    if len(opening_lanes) != 3:

        raise RuntimeError(f"Opening layer must contain exactly three nodes, got lanes {opening_lanes}")



    if canonical_three_race:

        opening_races = list(canonical_opening_races)

        rng.shuffle(opening_races)







        easy_races = [

            race for race in opening_races

            if any(str(m["race"]) == race and int(m["pool"]) == 0 for m in candidates)

        ]

        if not easy_races:

            raise RuntimeError("No pool-0 mission is available for the guaranteed easy opening route")

        easy_race = rng.choice(easy_races)

        easy_index = opening_races.index(easy_race)

        opening_races[0], opening_races[easy_index] = opening_races[easy_index], opening_races[0]

    else:





        opening_races = list(available_races)

        rng.shuffle(opening_races)

        while len(opening_races) < len(opening_lanes):

            opening_races.append(rng.choice(available_races))

    opening_race_by_lane = {lane: opening_races[i] for i, lane in enumerate(opening_lanes)}

    easy_opening_lane = opening_lanes[0]









    late_race_by_layer: dict[int, str] = {}

    if canonical_three_race and choice_layers >= 3:

        late_races = list(canonical_opening_races)

        rng.shuffle(late_races)

        late_race_by_layer = {

            choice_layers - 2: late_races[0],

            choice_layers - 1: late_races[1],

            choice_layers: late_races[2],

        }



    for layer in range(choice_layers):

        active_lanes = sorted(lane for node_layer, lane in edges if node_layer == layer)

        for lane in active_lanes:

            target = target_pool(layer, choice_layers, difficulty)

            opening_easy = canonical_three_race and layer == 0 and lane == easy_opening_lane

            required_race = opening_race_by_lane.get(lane) if layer == 0 else late_race_by_layer.get(layer)

            mission = choose_mission(

                candidates, used_ids, used_short_names, race_counts, target, rng,

                min_pool=minimum_pool_for_layer(layer, choice_layers),

                opening_bias=(layer == 0 and not opening_easy),

                required_race=required_race,

                exact_pool=(0 if opening_easy else None),

                tier_weights=mission_pool_distribution(layer, choice_layers),

            )

            used_ids.add(mission["id"])

            used_short_names.add(mission["short_name"])

            race_counts[mission["race"]] += 1

            assigned[(layer, lane)] = finish_node(

                mission, layer, lane, False, opening_easy=opening_easy

            )



    final_pos = (choice_layers, FINAL_LANE)

    mission = choose_mission(

        candidates, used_ids, used_short_names, race_counts,

        target_pool(choice_layers, choice_layers, difficulty, True), rng,

        min_pool=minimum_pool_for_layer(choice_layers, choice_layers, True),

        required_race=late_race_by_layer.get(choice_layers),

        exact_pool=4,

        tier_weights=mission_pool_distribution(choice_layers, choice_layers, True),

    )

    assigned[final_pos] = finish_node(mission, choice_layers, FINAL_LANE, True)



















    if canonical_three_race:

        for _pass in range(3):

            flagged = {

                pos for pos in _long_same_race_nodes(choice_layers, edges, assigned, 4)

                if 0 < pos[0] < choice_layers - 2 and pos != final_pos

            }

            if not flagged:

                break

            changed = False

            for pos in sorted(flagged):

                layer, lane = pos

                old_node = assigned[pos]

                old_race = str(old_node["race"])











                neighbor_positions = list(edges.get(pos, ())) + [

                    source for source, destinations in edges.items() if pos in destinations

                ]

                neighbor_races = Counter(

                    str(assigned[neighbor]["race"])

                    for neighbor in neighbor_positions if neighbor in assigned

                )

                target_races = list(canonical_opening_races)

                rng.shuffle(target_races)

                target_races.sort(key=lambda race: neighbor_races[race])













                other_nodes = [node for other_pos, node in assigned.items() if other_pos != pos]

                reroll_used_ids = {int(node["id"]) for node in other_nodes}

                reroll_used_short_names = {str(node["short_name"]) for node in other_nodes}

                reroll_race_counts = Counter(str(node["race"]) for node in other_nodes)

                replacement = None

                for target_race in target_races:

                    try:

                        replacement = choose_mission(

                            candidates, reroll_used_ids, reroll_used_short_names, reroll_race_counts,

                            target_pool(layer, choice_layers, difficulty), rng,

                            min_pool=minimum_pool_for_layer(layer, choice_layers),

                            required_race=target_race,

                            tier_weights=mission_pool_distribution(layer, choice_layers),

                        )

                    except RuntimeError:

                        replacement = None

                    if replacement is not None:

                        break



                if replacement is None:

                    continue



                assigned[pos] = finish_node(replacement, layer, lane, False)

                changed = True

            if not changed:

                break















        for _pass in range(2):









            window_keys: set[tuple[tuple[int, int], ...]] = set()

            for path in _route_paths(choice_layers, edges):

                for start in range(0, max(0, len(path) - 4)):

                    window = tuple(path[start:start + 5])

                    if len(window) == 5:

                        window_keys.add(window)

            problems = [list(window) for window in window_keys]

            if not problems:

                break

            rng.shuffle(problems)

            changed = False

            for window in problems:



                present = {str(assigned[pos]["race"]) for pos in window}

                missing = [race for race in canonical_opening_races if race not in present]

                if not missing:

                    continue

                mutable = [

                    pos for pos in window

                    if 0 < pos[0] < choice_layers - 2 and pos != final_pos

                ]

                if not mutable:

                    continue









                window_counts = Counter(str(assigned[pos]["race"]) for pos in window)

                rng.shuffle(mutable)

                mutable.sort(key=lambda pos: window_counts[str(assigned[pos]["race"])], reverse=True)

                target_races = list(missing)

                rng.shuffle(target_races)

                repaired = False

                for target_race in target_races:

                    for pos in mutable:

                        layer, lane = pos

                        other_nodes = [node for other_pos, node in assigned.items() if other_pos != pos]

                        reroll_used_ids = {int(node["id"]) for node in other_nodes}

                        reroll_used_short_names = {str(node["short_name"]) for node in other_nodes}

                        reroll_race_counts = Counter(str(node["race"]) for node in other_nodes)

                        try:

                            replacement = choose_mission(

                                candidates, reroll_used_ids, reroll_used_short_names, reroll_race_counts,

                                target_pool(layer, choice_layers, difficulty), rng,

                                min_pool=minimum_pool_for_layer(layer, choice_layers),

                                required_race=target_race,

                                tier_weights=mission_pool_distribution(layer, choice_layers),

                            )

                        except RuntimeError:

                            replacement = None

                        if replacement is None:

                            continue

                        old_node = assigned[pos]

                        assigned[pos] = finish_node(replacement, layer, lane, False)

                        if _long_same_race_nodes(choice_layers, edges, assigned, 4):

                            assigned[pos] = old_node

                            continue

                        repaired = True

                        changed = True

                        break

                    if repaired:

                        break

            if not changed:

                break



    def reroll_node_effects_once(pos: tuple[int, int]) -> None:



        data = assigned[pos]

        layer, _lane = pos

        forbidden_mutators, forbidden_blessings = _effect_exclusions_for_mission(data)

        mutators, blessings, mut_value, bless_value = roll_effects(

            layer, choice_layers, difficulty, rng, final=(layer == choice_layers),

            forbidden_mutators=forbidden_mutators,

            forbidden_blessings=forbidden_blessings,

            mission_pool=int(data["pool"]),

            mutation_frequency=mutation_frequency,

            blessing_frequency=blessing_frequency,

        )

        data["mutators"] = mutators

        data["blessings"] = blessings

        data["mutation_value"] = mut_value

        data["blessing_value"] = bless_value

        data["credit_reward"] = credit_reward(

            int(data["pool"]), layer, mut_value, bless_value, bool(blessings), rng,

            mission_name=str(data.get("name", "")),

            victory_credit_reward_multiplier=victory_credit_reward_multiplier,

        )











    forced_red_nodes = _forced_red_nodes_for_reroll(choice_layers, edges, assigned)

    for pos in sorted(forced_red_nodes):

        reroll_node_effects_once(pos)



    def add_mutations_until_red(pos: tuple[int, int]) -> bool:



        data = assigned[pos]

        layer = int(data.get("layer", pos[0]))

        if layer < 3 or layer >= choice_layers:

            return False

        forbidden_mutators, _forbidden_blessings = _effect_exclusions_for_mission(data)

        current = list(data.get("mutators", ()))

        current_set = set(current)

        armor_help = set(data.get("blessings", ())) & ARMOR_GRANTING_BLESSINGS

        available = [

            name for name in MUTATORS

            if name not in current_set

            and name not in forbidden_mutators

            and name not in DEFERRED_EFFECTS

            and not (name == "squishy" and armor_help)

        ]

        changed = False

        while available and not _assigned_node_is_red(assigned, pos, choice_layers):

            score = _assigned_danger_score(data)

            threshold = int(data.get("expected_danger_score", 0)) + RED_DANGER_MARGIN

            severity_needed = max(1, int(math.ceil(max(0, threshold - score) / 150.0)))

            enough = [name for name in available if int(MUTATORS[name]) >= severity_needed]

            if enough:

                best_value = min(int(MUTATORS[name]) for name in enough)

                best = [name for name in enough if int(MUTATORS[name]) == best_value]

            else:

                best_value = max(int(MUTATORS[name]) for name in available)

                best = [name for name in available if int(MUTATORS[name]) == best_value]

            pick = rng.choices(

                best,

                weights=[

                    _effect_selection_weight(int(MUTATORS[name]))

                    * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0)

                    for name in best

                ],

                k=1,

            )[0]
            if pick == "no_deaths_allowed" and rng.random() < 0.50:
                reroll_pool = [name for name in available if name != "no_deaths_allowed"]
                if reroll_pool:
                    pick = rng.choices(
                        reroll_pool,
                        weights=[
                            _effect_selection_weight(int(MUTATORS[name]))
                            * EFFECT_SELECTION_MULTIPLIER.get(name, 1.0)
                            for name in reroll_pool
                        ],
                        k=1,
                    )[0]

            current.append(pick)

            current_set.add(pick)

            available.remove(pick)

            changed = True

            data["mutators"] = current

            data["mutation_value"] = sum(int(MUTATORS[name]) for name in current)



        if changed:

            data["credit_reward"] = credit_reward(

                int(data["pool"]), layer,

                int(data.get("mutation_value", 0)), int(data.get("blessing_value", 0)),

                bool(data.get("blessings", ())), rng,

                mission_name=str(data.get("name", "")),

                victory_credit_reward_multiplier=victory_credit_reward_multiplier,

            )

        return _assigned_node_is_red(assigned, pos, choice_layers)











    for _safe_pass in range(max(1, len(assigned))):

        safe_paths = _red_free_paths(choice_layers, edges, assigned)

        if not safe_paths:

            break

        coverage: Counter[tuple[int, int]] = Counter()

        for path in safe_paths:

            for pos in path:

                if 3 <= pos[0] < choice_layers:

                    coverage[pos] += 1

        if not coverage:

            break

        candidates_to_harden = list(coverage)

        rng.shuffle(candidates_to_harden)

        candidates_to_harden.sort(

            key=lambda pos: (

                -coverage[pos],

                max(0, int(assigned[pos].get("expected_danger_score", 0)) + RED_DANGER_MARGIN - _assigned_danger_score(assigned[pos])),

                pos[0],

            )

        )

        if not any(add_mutations_until_red(pos) for pos in candidates_to_harden):

            break



    return assigned





def build_custom_order(choice_layers: int, assigned: dict[tuple[int, int], dict[str, Any]]) -> dict[str, Any]:

    mission_overrides: list[dict[str, Any]] = []

    for pos, data in sorted(assigned.items()):

        layer, lane = pos

        idx = canvas_index(choice_layers, layer, lane)

        nxt = [canvas_index(choice_layers, nlayer, nlane) for nlayer, nlane in data["next_positions"]]

        entry = {

            "index": idx,

            "mission_pool": [data["name"]],

            "difficulty": POOL_NAMES.get(int(data["pool"]), "relative"),

            "entrance": layer == 0,

            "exit": layer == choice_layers,

            "goal": layer == choice_layers,

            "next": nxt,

            "victory_cache": 0,

        }

        mission_overrides.append(entry)



    return {

        "Slay the StarCraft": {

            "display_name": "Slay the StarCraft",

            "goal": True,

            "Run": {

                "display_name": "",

                "type": "canvas",

                "canvas": make_canvas(choice_layers, assigned.keys()),

                "jump_distance_orthogonal": 1,

                "jump_distance_diagonal": 1,

                "goal": True,

                "exit": True,

                "missions": mission_overrides,

            },

        }

    }





def build_run_json(

    name: str, run_seed: int, choice_layers: int, difficulty: str,

    assigned: dict[tuple[int, int], dict[str, Any]], shop_pool: list[str], starting_shop: list[str],

    races: list[str], allow_race_swap: bool, starting_credits: int = 700,

    mutation_frequency: Any = 1.0, blessing_frequency: Any = 1.0,

    victory_credit_reward_multiplier: float = 1.0, item_credit_reward: int = 50,

    game_speed: str = "default", extra_shop_slots: int = 0,
    start_with_spear: bool = False, start_with_kerrigan: bool = False,

) -> dict[str, Any]:

    by_pos = {pos: data["id"] for pos, data in assigned.items()}

    nodes: dict[str, Any] = {}

    for pos, data in sorted(assigned.items()):

        layer, lane = pos

        mission_id = int(data["id"])

        commander_index, commander_name = (-1, "")

        if "general" in data.get("blessings", []):

            commander_index, commander_name = commander_choice(run_seed, mission_id)

        nodes[str(mission_id)] = {

            "mission_id": mission_id,

            "mission_name": data["name"],

            "layer": layer,

            "lane": lane,

            "canvas_index": canvas_index(choice_layers, layer, lane),

            "next": [int(by_pos[p]) for p in data["next_positions"]],

            "credit_reward": int(data["credit_reward"]),

            "mutators": list(data["mutators"]),

            "blessings": list(data["blessings"]),

            "commander_hero_index": int(commander_index),

            "commander_hero_name": commander_name,

            "mission_difficulty": POOL_NAMES.get(int(data["pool"]), "unknown"),

            "mission_pool": int(data["pool"]),

            "race": data["race"],

            "campaign": data.get("campaign", ""),

            "kerrigan": bool(data.get("kerrigan", False)),

            "lotv": bool(data.get("lotv", False)),

            "mutation_value": int(data.get("mutation_value", 0)),

            "blessing_value": int(data.get("blessing_value", 0)),

            "expected_danger_score": int(data.get("expected_danger_score", 0)),

            "expected_opening_credit_average": float(data.get("expected_opening_credit_average", 0.0)),

        }







    identity_payload = json.dumps({

        "version": FORMAT_VERSION,

        "player": name,

        "seed": run_seed,

        "layers": choice_layers,

        "difficulty": difficulty,

        "game_speed": str(game_speed),

        "races": races,

        "race_swap": allow_race_swap,

        "starting_credits": int(starting_credits),

        "campaign_length": int(choice_layers) + 1,

        "extra_shop_slots": max(0, min(3, int(extra_shop_slots))),

        "start_with_spear": bool(start_with_spear),

        "start_with_kerrigan": bool(start_with_kerrigan),

        "mutation_frequency": float(_frequency_factor(mutation_frequency)),

        "blessing_frequency": float(_frequency_factor(blessing_frequency)),

        "victory_credit_reward_multiplier": float(victory_credit_reward_multiplier),

        "item_credit_reward": int(item_credit_reward),

        "shop_pool": shop_pool,

        "starting_shop": starting_shop,

        "nodes": nodes,

    }, sort_keys=True, separators=(",", ":"))

    import hashlib

    run_id = hashlib.sha256(identity_payload.encode("utf-8")).hexdigest()[:16]

    return {

        "format_version": FORMAT_VERSION,

        "enabled": True,

        "run_id": run_id,

        "player_name": name,

        "run_seed": run_seed,

        "starting_credits": int(starting_credits),

        "campaign_length": int(choice_layers) + 1,

        "extra_shop_slots": max(0, min(3, int(extra_shop_slots))),

        "start_with_spear": bool(start_with_spear),

        "start_with_kerrigan": bool(start_with_kerrigan),

        "mutation_frequency": float(_frequency_factor(mutation_frequency)),

        "blessing_frequency": float(_frequency_factor(blessing_frequency)),

        "victory_credit_reward_multiplier": float(victory_credit_reward_multiplier),

        "item_credit_reward": int(item_credit_reward),

        "expected_opening_credit_average": expected_opening_credit_average(

            difficulty, mutation_frequency, blessing_frequency, victory_credit_reward_multiplier

        ),

        "choice_layers": choice_layers,

        "difficulty": difficulty,

        "game_speed": str(game_speed),

        "races": races,

        "allow_race_swap": allow_race_swap,

        "shop_pool": shop_pool,

        "starting_shop": starting_shop,

        "nodes": nodes,

    }





def build_yaml(

    name: str, run_seed: int, difficulty: str, races: list[str], allow_race_swap: bool,

    custom_order: dict[str, Any], banned_items: list[str], game_speed: str = "default",

) -> dict[str, Any]:

    title_races = [race.title() for race in races]

    excluded_items = {name: -1 for name in banned_items}

    sc2 = {

        "progression_balancing": "disabled",









        "accessibility": "minimal",

        "start_inventory": {},

        "disable_forced_camera": True,

        "plando_items": [],

        "skip_cutscenes": True,

        "game_difficulty": GAME_DIFFICULTY[difficulty],

        "game_speed": game_speed,

        "starter_unit": "off",

        "required_tactics": "no_logic",

        "war_council_nerfs": False,

        "difficulty_curve": "standard",

        "mission_order": "custom",

        "enabled_campaigns": DEFAULT_CAMPAIGNS,





        "enable_race_swap": "shuffle_all" if allow_race_swap else "disabled",

        "shuffle_no_build": False,

        "all_in_map": "random",

        "two_start_positions": False,

        "key_mode": "disabled",

        "selected_races": title_races,

        "mission_race_balancing": "disabled",

        "shuffle_campaigns": False,

        "ensure_generic_items": 25,

        "min_number_of_upgrades": 2,

        "max_number_of_upgrades": -1,

        "max_upgrade_level": 5,

        "generic_upgrade_missions": 0,

        "generic_upgrade_research": "vanilla",

        "generic_upgrade_research_speedup": False,

        "generic_upgrade_items": "bundle_all",







        "kerrigan_presence": "not_present",

        "kerrigan_levels_per_mission_completed": 0,

        "kerrigan_levels_per_mission_completed_cap": 0,

        "kerrigan_level_item_sum": 0,

        "kerrigan_level_item_distribution": "size_1",

        "kerrigan_total_level_cap": -1,

        "start_primary_abilities": 0,

        "kerrigan_primal_status": "always_zerg",

        "kerrigan_max_active_abilities": 12,

        "kerrigan_max_passive_abilities": 5,

        "grant_story_levels": "minimum",

        "spear_of_adun_presence": "not_present",

        "spear_of_adun_present_in_no_build": False,

        "spear_of_adun_passive_ability_presence": "not_present",

        "spear_of_adun_passive_present_in_no_build": False,

        "spear_of_adun_max_active_abilities": 13,

        "spear_of_adun_max_passive_abilities": 3,

        "nova_max_weapons": 5,

        "nova_max_gadgets": 5,

        "nova_ghost_of_a_chance_variant": "wol",

        "mercenary_highlanders": False,

        "enable_morphling": False,

        "victory_cache": 0,

        "vanilla_locations": "enabled",

        "extra_locations": "enabled",

        "challenge_locations": "enabled",

        "mastery_locations": "enabled",

        "basebust_locations": "enabled",

        "speedrun_locations": "enabled",

        "preventative_locations": "enabled",

        "filler_percentage": 0,

        "minerals_per_item": 25,

        "vespene_per_item": 25,

        "starting_supply_per_item": 2,

        "maximum_supply_per_item": 3,

        "maximum_supply_reduction_per_item": 1,

        "lowest_maximum_supply": 100,

        "research_cost_reduction_per_item": 2,

        "filler_items_distribution": {

            "Additional Starting Minerals": 1,

            "Additional Starting Vespene": 1,

            "Additional Starting Supply": 1,

            "Additional Maximum Supply": 1,

            "Increased Shield Regeneration": 1,

            "Increased Building Construction Speed": 1,

            "1 Kerrigan Level": 0,

            "Increased Upgrade Research Speed": 6,

            "Reduced Upgrade Research Cost": 1,

            "Decreased Maximum Supply": 0,

        },

        "locked_items": {},

        "excluded_items": excluded_items,

        "unexcluded_items": {},

        "excluded_missions": [],

        "vanilla_items_only": False,

        "exclude_overpowered_items": False,

        "difficulty_damage_modifier": True,

        "enable_void_trade": False,



        "grant_story_tech": "grant",

        "take_over_ai_allies": False,

        "mission_order_scouting": "all",

        "local_items": [],

        "non_local_items": [],

        "start_hints": [],

        "start_location_hints": [],

        "exclude_locations": [],

        "exclude_very_hard_missions": "false",

        "priority_locations": [],

        "custom_mission_order": custom_order,

    }

    return {

        "name": name,

        "description": f"Slay the StarCraft v{PACKAGE_VERSION} run, seed {run_seed}",

        "game": "Starcraft 2",

        "Starcraft 2": sc2,

    }





def write_outputs(

    ap_root: Path, yaml_path: Path, run_path: Path, yaml_data: dict[str, Any], run_data: dict[str, Any],

) -> None:

    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    run_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_path.write_text(yaml.safe_dump(yaml_data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    run_path.write_text(json.dumps(run_data, indent=2, sort_keys=False) + "\n", encoding="utf-8")





def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Generate a Slay the StarCraft single-player run")

    parser.add_argument("--archipelago", type=Path, default=Path.cwd(), help="Archipelago source checkout (default: cwd)")

    parser.add_argument("--name", default="Player", help="Archipelago player/slot name")

    parser.add_argument("--layers", type=int, default=DEFAULT_CHOICE_LAYERS, help="Number of 3-choice layers before the final mission (default 11 = 12 missions along a route; 1-30)")

    parser.add_argument("--difficulty", choices=list(GAME_DIFFICULTY), default="brutal")

    parser.add_argument("--game-speed", choices=list(GAME_SPEEDS), default="default", help="SC2 game speed override; default follows Archipelago's normal behavior")

    parser.add_argument("--starting-credits", type=int, default=700, help="Starting shop credits (default 700)")

    parser.add_argument("--mutation-frequency", dest="mutation_frequency", default=None, help=argparse.SUPPRESS)

    parser.add_argument("--mutation-frequency-multiplier", type=float, default=1.0, help="Multiplier applied to each mission mutation-severity mean")

    parser.add_argument("--blessing-frequency", dest="blessing_frequency", default=None, help=argparse.SUPPRESS)

    parser.add_argument("--blessing-frequency-multiplier", type=float, default=1.0, help="Multiplier applied to each mission blessing-severity mean")

    parser.add_argument("--victory-credit-reward-multiplier", type=float, default=1.0, help="Multiplier applied to mission victory credit rewards (default 1.0)")

    parser.add_argument("--item-credit-reward", type=int, default=50, help="Credits granted by each credit-item replacement (default 50)")

    parser.add_argument("--extra-shop-slots", type=int, choices=(0, 1, 2, 3), default=0)

    parser.add_argument("--start-with-spear", action="store_true")

    parser.add_argument("--start-with-kerrigan", action="store_true")

    parser.add_argument("--races", nargs="+", choices=["terran", "zerg", "protoss"], default=["terran", "zerg", "protoss"])

    parser.add_argument("--race-swap", action=argparse.BooleanOptionalAction, default=True, help="Allow race-swapped mission variants")

    parser.add_argument("--seed", type=int, default=None, help="Run/AP seed; random if omitted")

    parser.add_argument("--yaml", type=Path, default=None, help="Output YAML path")

    parser.add_argument("--generate-ap", action="store_true", help="Run Generate.py immediately using only this generated player YAML")

    parser.add_argument("--reset-state", action="store_true", help="Delete saved route/shop state for this exact generated run ID")

    return parser.parse_args()





def validate_singleplayer_player_dir(player_dir: Path, intended_yaml: Path) -> None:



    if not player_dir.exists():

        return

    intended = intended_yaml.resolve()

    extras = []

    for pattern in ("*.yaml", "*.yml", "*.json"):

        for path in player_dir.glob(pattern):

            if path.resolve() != intended:

                extras.append(path.name)

    if extras:

        raise RuntimeError(

            "SlayTheStarCraftPlayers contains other player files; this mode is single-player only. "

            "Move these files elsewhere first: " + ", ".join(sorted(extras))

        )





def main() -> int:

    args = parse_args()

    ap_root = args.archipelago.resolve()

    if not (ap_root / "Generate.py").is_file() or not (ap_root / "worlds" / "sc2").is_dir():

        print(f"ERROR: not an Archipelago source checkout: {ap_root}", file=sys.stderr)

        return 2

    if not 1 <= args.layers <= MAX_LAYERS:

        print(f"ERROR: --layers must be between 1 and {MAX_LAYERS}", file=sys.stderr)

        return 2

    if args.starting_credits < 0:

        print("ERROR: --starting-credits cannot be negative", file=sys.stderr)

        return 2

    if not math.isfinite(args.victory_credit_reward_multiplier) or args.victory_credit_reward_multiplier < 0:

        print("ERROR: --victory-credit-reward-multiplier must be a finite non-negative number", file=sys.stderr)

        return 2

    if args.item_credit_reward < 0:

        print("ERROR: --item-credit-reward cannot be negative", file=sys.stderr)

        return 2
    mutation_frequency = args.mutation_frequency if args.mutation_frequency is not None else args.mutation_frequency_multiplier
    blessing_frequency = args.blessing_frequency if args.blessing_frequency is not None else args.blessing_frequency_multiplier
    try:
        mutation_frequency = _frequency_factor(mutation_frequency)
        blessing_frequency = _frequency_factor(blessing_frequency)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


    races = list(dict.fromkeys(args.races))

    run_seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2**63 - 1)

    rng = random.Random(stable_seed(f"SlayTheStarCraft:v{FORMAT_VERSION}:{run_seed}"))



    try:

        candidates, shop_candidates, unit_candidates_by_race, banned_items = load_archipelago_catalog(

            ap_root, set(races), args.race_swap

        )

        edges = generate_edges(args.layers, rng)

        validate_graph(args.layers, edges)

        assigned = assign_missions(

            args.layers, args.difficulty, candidates, edges, rng,

            mutation_frequency=mutation_frequency, blessing_frequency=blessing_frequency,

            victory_credit_reward_multiplier=args.victory_credit_reward_multiplier,

        )





        starting_shop: list[str] = []

        shop_pool = list(dict.fromkeys(shop_candidates))

        custom_order = build_custom_order(args.layers, assigned)

        run_data = build_run_json(

            args.name, run_seed, args.layers, args.difficulty, assigned,

            shop_pool, starting_shop, races, args.race_swap, args.starting_credits,

            mutation_frequency, blessing_frequency,

            args.victory_credit_reward_multiplier, args.item_credit_reward, args.game_speed,
            args.extra_shop_slots, args.start_with_spear, args.start_with_kerrigan,

        )

        yaml_data = build_yaml(args.name, run_seed, args.difficulty, races, args.race_swap, custom_order, banned_items, args.game_speed)

    except Exception as exc:

        print(f"ERROR generating run: {exc}", file=sys.stderr)

        return 1



    player_dir = ap_root / "SlayTheStarCraftPlayers"

    yaml_path = args.yaml.resolve() if args.yaml else player_dir / "SlayTheStarCraft.yaml"

    run_path = ap_root / "slay_the_starcraft_run.json"

    try:

        validate_singleplayer_player_dir(player_dir, yaml_path)

    except Exception as exc:

        print(f"ERROR: {exc}", file=sys.stderr)

        return 2

    write_outputs(ap_root, yaml_path, run_path, yaml_data, run_data)

    if args.reset_state:

        state_path = ap_root / f"slay_the_starcraft_state_{run_data['run_id']}.json"

        if state_path.exists():

            state_path.unlink()

            print(f"Reset prior run state: {state_path.name}")



    print(f"Slay the StarCraft v{PACKAGE_VERSION} run generated successfully.")

    print(f"  Run seed:      {run_seed}")

    print(f"  Run ID:        {run_data['run_id']}")

    print(f"  Route length:  {args.layers + 1} missions ({args.layers} choice layers + final)")

    print(f"  Nodes:         {len(run_data['nodes'])}")

    print(f"  Difficulty:    {args.difficulty} ({GAME_DIFFICULTY[args.difficulty]} SC2)")

    print(f"  Game speed:    {args.game_speed}")

    print(f"  Races:         {', '.join(races)}")

    print(f"  Race swaps:    {'enabled' if args.race_swap else 'disabled'}")

    print(f"  Starting cr:   {run_data['starting_credits']}")

    print(f"  Mutation multiplier: {run_data['mutation_frequency']}")

    print(f"  Blessing multiplier: {run_data['blessing_frequency']}")

    print(f"  Victory x:     {run_data['victory_credit_reward_multiplier']:.2f}")

    print(f"  Item credits:  {run_data['item_credit_reward']}")

    print(f"  Starting shop: {', '.join(run_data['starting_shop'])}")

    print(f"  YAML:          {yaml_path}")

    print(f"  Runtime file:  {run_path}")



    if args.generate_ap:

        cmd = [

            sys.executable,

            str(ap_root / "Generate.py"),

            "--player_files_path", str(player_dir),

            "--multi", "1",

            "--seed", str(run_seed),

            "--outputpath", str(ap_root / "output"),

        ]

        print("\nRunning Archipelago generator:")

        print("  " + " ".join(f'\"{x}\"' if " " in x else x for x in cmd))

        result = subprocess.run(cmd, cwd=ap_root)

        if result.returncode != 0:

            print(f"ERROR: Generate.py exited with {result.returncode}", file=sys.stderr)

            return result.returncode

        print("Archipelago seed generated in the output folder.")

    else:

        print("\nNext:")

        print(f'  python Generate.py --player_files_path "{player_dir}" --multi 1 --seed {run_seed}')

    return 0





if __name__ == "__main__":

    raise SystemExit(main())



def endless_map_key(node: dict[str, Any]) -> str:
    name = str(node.get("mission_name", node.get("name", "")))
    for suffix in (" (Terran)", " (Zerg)", " (Protoss)"):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name.strip().casefold()

def generate_endless_layer(run: dict[str, Any], progress: dict[str, Any]) -> list[dict[str, Any]]:
    """Use the existing mission pools, effect rolls and rewards for one three-choice floor."""
    import copy
    floor = int(progress["floor"])
    rng = random.Random(f"{run['run_seed']}:endless:{floor}")
    excluded = {key for offer in progress.get("offers", [])[-4:] for key in offer}
    from worlds.sc2.mission_tables import lookup_id_to_mission, MissionFlag
    candidates = []
    for original in run["nodes"].values():
        if endless_map_key(original) in excluded:
            continue
        native = lookup_id_to_mission[int(original["mission_id"])]
        candidates.append(dict(original, id=int(original["mission_id"]), name=original["mission_name"],
                               short_name=native.get_short_name(), pool=int(original.get("mission_pool", 0)),
                               timed_defense=bool(MissionFlag.TimedDefense in native.flags),
                               race_swap=bool(MissionFlag.RaceSwap in native.flags)))
    if len({m["short_name"] for m in candidates}) < 3:
        raise RuntimeError("Not enough distinct maps for the five-floor exclusion rule.")
    capacity = min(4, len({endless_map_key(n) for n in run["nodes"].values()}) // 5)
    choice_count = min(rng.choice((2, 3, 3, 4)), capacity, len({m["short_name"] for m in candidates}))
    selected = []
    used = set()
    counts = Counter()
    risk_count = 2 if floor >= 5 and rng.random() < .25 else 1
    risky_lanes = set(rng.sample(range(choice_count), min(risk_count, choice_count-1)))
    tier = min(3, floor // 4)
    difficulty = ("easy", "medium", "hard", "brutal")[tier]
    length = max(11, floor + 3)
    for lane in range(choice_count):
        remaining = [m for m in candidates if m["short_name"] not in used]
        mission = choose_mission(remaining, set(), used, counts, min(4, floor / 4), rng)
        used.add(mission["short_name"])
        counts[mission["race"]] += 1
        risk = lane in risky_lanes
        roll_layer = floor + int(risk)
        exclusions, help_exclusions = _effect_exclusions_for_mission(mission)
        effects = roll_effects(roll_layer, length, difficulty, rng,
                              forbidden_mutators=exclusions, forbidden_blessings=help_exclusions,
                              mission_pool=mission["pool"], mutation_frequency=run.get("mutation_frequency", "normal"),
                              blessing_frequency=run.get("blessing_frequency", "normal"))
        # Risk uses the same legal rolls; pick the harder of three, without new enemy stat rules.
        if risk:
            for _ in range(2):
                trial = roll_effects(roll_layer, length, difficulty, rng,
                                     forbidden_mutators=exclusions, forbidden_blessings=help_exclusions,
                                     mission_pool=mission["pool"], mutation_frequency=run.get("mutation_frequency", "normal"),
                                     blessing_frequency=run.get("blessing_frequency", "normal"))
                if trial[2] * 150 - trial[3] * 100 > effects[2] * 150 - effects[3] * 100:
                    effects = trial
        mutators, blessings, mut_value, bless_value = effects
        multiplier = float(run.get("victory_credit_reward_multiplier", 1))
        base_reward = credit_reward(mission["pool"], floor, mut_value, bless_value, bool(blessings), rng,
                                    mission_name=mission["name"], victory_credit_reward_multiplier=1)
        node = copy.deepcopy(mission)
        node.update(layer=floor, lane=lane, lane_count=choice_count, next=[], high_risk=risk, mutators=mutators, blessings=blessings,
                    mutation_value=mut_value, blessing_value=bless_value,
                    credit_reward=round((base_reward + 50 * floor + (100 if risk else 0)) * multiplier),
                    danger_credit_bonus=0, difficulty_override=tier)
        node["commander_hero_index"], node["commander_hero_name"] = commander_choice(run["run_seed"], mission["id"]) if "general" in blessings else (-1, "")
        selected.append(node)
    return selected
