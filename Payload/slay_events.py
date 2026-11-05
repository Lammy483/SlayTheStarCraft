"""Standard-mode encounter catalog and durable event checkpoints.

Descriptions and outcomes below are the author's original event text.
Gameplay implementation lives in slay_the_starcraft.py / APRogue.galaxy.
"""
from __future__ import annotations

import hashlib
import math
import random
import time
import xml.etree.ElementTree as ET
from typing import Any

# The test encounter at floor zero is separate from the regular
# ceil(number_of_missions / 3) encounters.
EVENTS: dict[str, dict[str, Any]] = {
    "nova": {
        "name": "Nova's Mission",
        "description": "Nova is willing to offer her services. Tosh does not want you to accept.",
        "options": [
            "Choose Nova: Costs 200 credits. Unlock the Ghost and gain Nova until she dies in a mission. Tosh joins the enemy team until slain",
            "Refuse: Unlock the spectre. Nova joins the enemy team until she dies in a mission.",
        ],
    },
    "abathur": {
        "name": "Abathur's Evolution",
        "description": 'Abathur approaches. ""Must evolve. Swarm not good enough. Not." He wishes to experiment on your Zerg units.',
        "options": [
            "Agree to let Abathur experiment: lose a random half of your unlocked zerg units, but gain many upgrades for each of your remaining zerg units",
            "Refuse: zerg upgrades become 50% more expensive for the rest of the campaign",
        ],
    },
    "merchant": {
        "name": "Merchant Vessel",
        "description": "A merchent vessel passes by.",
        "options": [
            "Buy [potion] (rarityx80 credits)",
            "Buy [potion] (rarityx60 credits)",
            "Buy [potion] (rarityx40 credits)",
            "Raid the merchant vessel: Gain a random potion for free, but at some point next mission a mercenary force will attack your base.",
            "Leave",
        ],
    },
    "zagara": {
        "name": "Zagara",
        "description": "Zagara wishes you to aid her against Brakk's Pack.",
        "options": [
            "Ally with Zagara: Brakk with a massive primal zerg army are in next mission and will eventually attack your base. If you slay Brakk, for the rest of the campaign, Zagara sends 100 banelings every 10 minutes to aid you.",
            "Ally with Brakk: Brakk joins you for the rest of the campaign until Zagara is slain. Zagara is on the map and until she is slain she sends 100 banelings to attack your base every 10 minutes.",
        ],
    },
    "organism": {
        "name": "Organism Field Test",
        "description": "Abathur wishes to test the capabilities of the Brutalisk. He requests to deploy somewhere on the map next mission for you to kill.",
        "options": [
            "Agree: Add a brutalisk on the map next mission. If you kill it, permanently start with a brutalisk on all future missions. If you fail to kill it, the enemy gains a brutalisk on all future missions.",
            "Refuse: Zerg unit upgrades become 20% more expensive for the rest of the campaign.",
        ],
    },
    "mechanical": {
        "name": "[Mechanical Ground Terran Unit] Field Test",
        "description": "Rory Swann wants to test [Mechanical Ground Terran Unit] in the field. He offers you some schematics and upgrades if you complete the task.",
        "options": [
            "Agree: Start next mission with [amount] [Mechanical Ground Terran Unit]. If they get a total of 50 kills then you succeed, unlocking that unit and giving that unit a permanent +20% hp, speed, and damage. If you fail, Rory Swann will give [Mechanical Ground Terran Unit] to the enemy team for all remaining missions with those same bonuses.",
            "Refuse: unlocking terran units costs 50% additional credits for the rest of the campaign",
        ],
    },
    "colonists": {
        "name": "Dr Hansen's Colonists",
        "description": "Dr Hansen wishes for her perfectly healthy colonists to live with you for a while. In return she will give you 150 credits at the end of each mission as long as the colonists are safe.",
        "options": [
            "Agree: Gain a colony hut in your base in every mission until they are destroyed. You just have to deal with any infested terran that might come out of it.",
            "Refuse: nothing happens",
        ],
    },
    "crystalis": {
        "name": "The Primal Crystalis",
        "description": "Kerrigan has the opportunity to gain primal power by entering the crystalis. However, this will enrage the primal zerg.",
        "options": [
            "Enter the Crystalis: Kerrigan gains 70 levels, but every remaining mission will randomly gain the Brakk's Pack or Dehaka's Pack mutation.",
            "Refuse: Kerrigan upgrades become 20% more expensive",
        ],
    },
    "solarite": {
        "name": "Solarite Conversion",
        "description": "Karax proposes a method of converting minerals or gas into solarite. He wants to test it out next mission",
        "options": [
            "Convert Minerals: next mission if you have 5000 minerals, instantly spend them all to permanently increase the energy regeneration of the Spear of Adun. If you fail, permanently reduce the energy regeneration instead.",
            "Convert Gas: next mission if you have 5000 gas, instantly spend them all to permanently reduce the cooldowns of the Spear of Adun. If you fail, permanently increase the cooldowns instead.",
            "Refuse: Spear of adun upgrades become 20% more expensive.",
        ],
    },
    "vortex": {
        "name": "Unstable Vortex",
        "description": "An unstable vortex appears. Do you enter?",
        "options": [
            "Enter: Lose all upgrades, units, items, etc. Gain credit refunds for everything you lose.",
            "Avoid: nothing happens",
        ],
    },
}

# Only expose encounters with fully implemented outcomes in ordinary runs.
# The initial development encounter can display all ten for inspection, but
# unfinished options are visibly disabled rather than silently doing nothing.
REGULAR_ENABLED = ("merchant", "abathur", "vortex", "crystalis", "nova", "colonists", "zagara", "organism")
IMPLEMENTED_OPTIONS: dict[str, tuple[int, ...]] = {
    "merchant": (0, 1, 2, 3, 4),
    "nova": (0, 1),
    "zagara": (0, 1),
    "abathur": (0, 1),
    "organism": (0, 1),
    "mechanical": (1,),
    "colonists": (0, 1),
    "crystalis": (0, 1),
    "solarite": (2,),
    "vortex": (0, 1),
}

def checkpoints(total_missions: int) -> tuple[int, ...]:
    """One before the opening mission, plus ceil(missions / 3).

    Put the final scheduled encounter before the final mission if its
    three-mission boundary would otherwise be after the run is over.
    """
    count = max(1, int(total_missions))
    return (0, *sorted({min(count - 1, 3 * index)
                       for index in range(1, math.ceil(count / 3) + 1)}))

def deterministic_event(seed: int, checkpoint: int, used: tuple[str, ...] = (),
                        available: tuple[str, ...] | None = None) -> str:
    # Do not repeat an event until every eligible event has already appeared.
    # If the pool is exhausted, allow repetition rather than blocking progression.
    eligible = REGULAR_ENABLED if available is None else available
    pool = [event_id for event_id in eligible if event_id not in used]
    if not pool:
        pool = list(eligible)
    value = hashlib.sha256(f"{seed}:event:{checkpoint}".encode()).digest()
    return random.Random(int.from_bytes(value[:8], "big")).choice(pool)

def potion_offers(seed: int, checkpoint: int, names: list[str]) -> tuple[str, ...]:
    """Stable distinct potions, independent of UI refreshes and rerolls."""
    value = hashlib.sha256(f"{seed}:merchant:{checkpoint}".encode()).digest()
    rng = random.Random(int.from_bytes(value[:8], "big"))
    valid = sorted(set(names))
    rng.shuffle(valid)
    return tuple(valid[:3])


def _slay():
    # Local import avoids importing the runtime until its module initialization
    # and Archipelago item catalog are complete.
    from . import slay_the_starcraft
    return slay_the_starcraft

def _owned_zerg_units(ctx: Any) -> list[str]:
    slay = _slay()
    table = slay._item_table()
    counts = slay._logic_owned_item_counts(ctx)
    return sorted(
        name for name, count in counts.items()
        if int(count) > 0 and name in table
        and slay._item_race_key(name, table[name]) == "zerg"
        and slay._is_unit_unlock_type(str(getattr(getattr(table[name], "type", None),
                                                "display_name", "")))
        and not slay._is_mercenary_unit(name, table[name])
    )

def eligible_regular(ctx: Any) -> tuple[str, ...]:
    # Check eligibility at event assignment, then persist the selected event
    # so reconnecting cannot reroll it based on inventory or purchases.
    enough_zerg = len(_owned_zerg_units(ctx)) >= 4
    slay = _slay()
    kerrigan = slay._progression_owned(ctx, slay.KERRIGAN_UNLOCK)
    return tuple(x for x in REGULAR_ENABLED
                 if (x != "abathur" or enough_zerg)
                 and (x != "crystalis" or kerrigan))

def pending(ctx: Any) -> dict[str, Any] | None:
    slay = _slay()
    if not slay.events_enabled(ctx) or not slay.state_ready(ctx):
        return None
    s = slay.state(ctx)
    count = slay.victory_count(ctx)
    for checkpoint in checkpoints(int(ctx.slay_config.get("campaign_length", 12))):
        key = str(checkpoint)
        if checkpoint > count:
            break
        if key in s.get("event_resolutions", {}):
            continue
        event_id = str(s.get("event_assignments", {}).get(key, ""))
        if not event_id:
            if checkpoint == 0:
                event_id = "__test_select__"
            else:
                seed = int(ctx.slay_config.get("run_seed", 0))
                # Include the opening test event: it counts toward the no-repeat rule.
                used = tuple(str(x) for x in s.get("event_assignments", {}).values()
                             if x in REGULAR_ENABLED)
                event_id = deterministic_event(seed, checkpoint, used, eligible_regular(ctx))
            s.setdefault("event_assignments", {})[key] = event_id
            slay._persist_state(ctx)
        return {"checkpoint": checkpoint, "key": key, "id": event_id}
    return None

def select_test(ctx: Any, event_id: str) -> tuple[bool, str]:
    slay = _slay()
    p = pending(ctx)
    if p is None or p["checkpoint"] != 0 or (event_id not in EVENTS and event_id != "__test_select__"):
        return False, "There is no opening test event to select."
    slay.state(ctx).setdefault("event_assignments", {})["0"] = event_id
    slay._persist_state(ctx)
    if event_id == "__test_select__":
        return True, "Choose a different event to test."
    return True, "Selected " + EVENTS[event_id]["name"]

def _merchant_offers(ctx: Any, key: str) -> tuple[str, ...]:
    slay = _slay()
    s = slay.state(ctx)
    saved = s.setdefault("event_merchant_potions", {}).get(key)
    if isinstance(saved, list) and len(saved) == 3 and all(x in slay.POTION_CATALOG for x in saved):
        return tuple(saved)
    candidates = [name for name in slay.POTION_CATALOG
                  if not name.startswith(slay.POTION_VARIANT_PREFIX)
                  and slay._potion_unlock_eligible(ctx, name)]
    names = list(potion_offers(int(ctx.slay_config.get("run_seed", 0)), int(key), candidates))
    if len(names) < 3:
        for emergency in (slay.POTION_PREFIX + "1", slay.POTION_PREFIX + "2", slay.POTION_PREFIX + "7"):
            if emergency not in names:
                names.append(emergency)
            if len(names) >= 3:
                break
    seed = hashlib.sha256(f'{ctx.slay_config.get("run_seed", 0)}:merchant-units:{key}'.encode()).digest()
    rng = random.Random(int.from_bytes(seed[:8], "big"))
    # Potion 19 must carry a concrete unit variant, never its roll placeholder.
    names = [(slay.POTION_VARIANT_PREFIX + str(rng.randint(1, len(slay.POTION_RANDOM_UNITS))))
             if x == slay.POTION_PREFIX + "19" else x for x in names[:3]]
    s.setdefault("event_merchant_potions", {})[key] = names
    slay._persist_state(ctx)
    return tuple(names)

def display(ctx: Any) -> dict[str, Any] | None:
    slay = _slay()
    p = pending(ctx)
    if p is None:
        return None
    key, event_id = p["key"], p["id"]
    if event_id == "__test_select__":
        return dict(p, name="Event Test Selection",
                    description="Choose an event to test at the start of the run.",
                    options=[{"text": event["name"], "enabled": True, "implemented": True}
                             for event in EVENTS.values()],
                    selector_ids=list(EVENTS))
    data = EVENTS.get(event_id)
    if data is None:
        return None
    bought = set(slay.state(ctx).get("event_merchant_purchases", {}).get(key, []))
    shown = []
    for i, original in enumerate(data["options"]):
        label = original
        implemented = i in IMPLEMENTED_OPTIONS.get(event_id, ())
        can = implemented
        if event_id == "merchant" and i < 3:
            potion_id = _merchant_offers(ctx, key)[i]
            potion = slay.POTION_CATALOG[potion_id]
            price = int(potion["severity"]) * (80 - 20 * i)
            label = f'Buy {potion["name"]} ({price} credits)'
            can = (can and i not in bought and slay.credits(ctx) >= price
                   and len(slay.potion_inventory(ctx)) < slay.POTION_CAPACITY)
        elif event_id == "merchant" and i == 3:
            can = can and len(slay.potion_inventory(ctx)) < slay.POTION_CAPACITY
        elif event_id == "abathur" and i == 0:
            can = can and len(_owned_zerg_units(ctx)) >= 4
        elif event_id == "crystalis":
            can = can and slay._progression_owned(ctx, slay.KERRIGAN_UNLOCK)
            if i == 0:
                can = can and slay._one_kerrigan_level_item(slay._item_table()) is not None
        elif event_id == "nova":
            item = "Ghost" if i == 0 else "Spectre"
            can = can and item in slay._item_table()
            if i == 0:
                can = can and slay.credits(ctx) >= 200
        shown.append({"text": label, "enabled": can, "implemented": implemented})
    return dict(p, name=data["name"], description=data["description"], options=shown)

# Event-native bits are transported separately from APRogue's occupied
# mutation/boon banks. This tuple has a stable wire format for Galaxy.
NOVA_ALLY = 1
TOSH_ENEMY = 2
NOVA_ENEMY = 4
COLONY_HUT = 8
ZAGARA_BRAKK_QUEST = 16
ZAGARA_ALLIED_BANELINGS = 32
ZAGARA_ENEMY = 64
BRAKK_ALLY = 128
ORGANISM_TEST = 256
ORGANISM_ALLY = 512
ORGANISM_ENEMY = 1024

def native_bank_values(ctx: Any) -> dict[str, int]:
    """Read per-run event receipts from SC2 banks, never alter the bank files."""
    slay = _slay()
    if not slay.events_enabled(ctx) or not slay.state_ready(ctx):
        return {}
    token = int(slay.test_potion_run_token(ctx))
    cached = getattr(ctx, "_slay_event_bank_cache", None)
    now = time.monotonic()
    if cached is not None and cached[0] == token and now < cached[1]:
        return dict(cached[2])
    from .crew_live_bot import banks
    paths = []
    for root in banks():
        try:
            paths.extend(root.rglob("SlayTheStarCraftEvents.SC2Bank"))
        except OSError:
            continue
    values: dict[str, int] = {}
    for path in sorted(set(paths), key=lambda p: p.stat().st_mtime if p.is_file() else 0,
                       reverse=True):
        try:
            doc = ET.fromstring(path.read_bytes())
            sections = doc.findall(".//Section[@name='Run" + str(token) + "']")
            if len(sections) != 1:
                continue
            for item in sections[0].findall("Key"):
                name = item.get("name", "")
                value = item.find("Value")
                if name and value is not None:
                    raw = value.get("int", "")
                    if raw.lstrip("-").isdecimal():
                        values[name] = int(raw)
            break
        except (OSError, ET.ParseError, ValueError):
            continue
    ctx._slay_event_bank_cache = (token, now + 2.0, values)
    return dict(values)

def colony_earned_credits(ctx: Any) -> int:
    slay = _slay()
    if not slay.events_enabled(ctx) or not slay.state_ready(ctx):
        return 0
    s = slay.state(ctx)
    checkpoint = int(s.get("event_colonists_checkpoint", -1))
    if checkpoint < 0:
        return 0
    bank = native_bank_values(ctx)
    if "ColonyStartedAt" not in bank:
        return 0
    victories = slay.victory_count(ctx)
    death_layer = int(bank.get("ColonyDeadAt", 0))
    if death_layer > 0:
        victories = min(victories, death_layer - 1)
    return 150 * max(0, victories - checkpoint)

def native_values(ctx: Any, mission_id: int) -> tuple[int, int, int]:
    slay = _slay()
    if not slay.events_enabled(ctx) or not slay.state_ready(ctx):
        return 0, 0, 0
    s = slay.state(ctx)
    mission = slay.node(ctx, int(mission_id)) or {}
    layer = int(mission.get("layer", -1))
    mask = 0
    if layer >= int(s.get("event_nova_checkpoint", 10000)):
        side = str(s.get("event_nova_side", ""))
        if side == "nova":
            mask |= NOVA_ALLY | TOSH_ENEMY
        elif side == "tosh":
            mask |= NOVA_ENEMY
    if layer >= int(s.get("event_colonists_checkpoint", 10000)):
        mask |= COLONY_HUT
    if layer >= int(s.get("event_zagara_checkpoint", 10000)):
        side = str(s.get("event_zagara_side", ""))
        if side == "zagara":
            mask |= ZAGARA_ALLIED_BANELINGS
            if int(s.get("event_zagara_quest_target", 0)) == int(mission_id):
                mask |= ZAGARA_BRAKK_QUEST
        elif side == "brakk":
            mask |= ZAGARA_ENEMY | BRAKK_ALLY
    if layer >= int(s.get("event_organism_checkpoint", 10000)):
        target = int(s.get("event_organism_target", 0))
        if target == int(mission_id):
            mask |= ORGANISM_TEST
        elif target > 0 and slay.victory_count(ctx) > int(s.get("event_organism_checkpoint", 10000)):
            bank = native_bank_values(ctx)
            if int(bank.get("OrganismOutcome", 0)) == 1:
                mask |= ORGANISM_ALLY
            elif int(bank.get("OrganismStartedAt", 0)) > 0:
                mask |= ORGANISM_ENEMY
    return mask, 0, 0

def apply_choice(ctx: Any, index: int) -> tuple[bool, str, bool]:
    slay = _slay()
    p = pending(ctx)
    if p is None or p["id"] not in EVENTS:
        return False, "No event is ready.", False
    key, event_id = p["key"], p["id"]
    data = EVENTS[event_id]
    if index < 0 or index >= len(data["options"]) or index not in IMPLEMENTED_OPTIONS.get(event_id, ()):
        return False, "This option is not implemented yet.", False
    active = display(ctx)
    if active is None or not active["options"][index]["enabled"]:
        return False, "This option is not currently available.", False
    s = slay.state(ctx)
    done = True
    if event_id == "merchant":
        if index < 3:
            pid = _merchant_offers(ctx, key)[index]
            potion = slay.POTION_CATALOG[pid]
            price = int(potion["severity"]) * (80 - 20 * index)
            slots = slay.potion_inventory(ctx)
            if slay.credits(ctx) < price or len(slots) >= slay.POTION_CAPACITY:
                return False, "Cannot purchase that potion.", False
            serial = max([int(s.get("potion_serial", 0))] + [int(x.get("serial", 0)) for x in slots]) + 1
            s["potion_serial"] = serial
            s["potion_inventory"] = slots + [{"id": pid, "serial": serial}]
            s["spent"] = int(s.get("spent", 0)) + price
            s.setdefault("event_merchant_purchases", {}).setdefault(key, []).append(index)
            done = False
            message = f'Bought {potion["name"]} for {price} credits.'
        elif index == 3:
            slots = slay.potion_inventory(ctx)
            if len(slots) >= slay.POTION_CAPACITY:
                return False, "Both potion slots are full.", False
            seed = hashlib.sha256(f'{ctx.slay_config.get("run_seed",0)}:raid:{key}'.encode()).digest()
            rng = random.Random(int.from_bytes(seed[:8], "big"))
            pid = rng.choice(_merchant_offers(ctx, key))
            serial = max([int(s.get("potion_serial", 0))] + [int(x.get("serial", 0)) for x in slots]) + 1
            s["potion_serial"] = serial
            s["potion_inventory"] = slots + [{"id": pid, "serial": serial}]
            # Raiding awards only the free potion; the mercenary retaliation remains.
            s["event_merchant_raid_pending"] = True
            message = f'Raided merchant vessel; gained {slay.POTION_CATALOG[pid]["name"]}. Mercenaries attack next mission.'
        else:
            message = "Left the merchant vessel."
    elif event_id == "organism" and index == 0:
        s["event_organism_checkpoint"] = int(key)
        s["event_organism_pending"] = True
        s["event_organism_target"] = 0
        message = ("A hostile Brutalisk will spawn near enemy structures next mission. "
                   "Kill it to gain an allied Brutalisk every future mission; "
                   "otherwise the enemy gains one every future mission.")
    elif event_id == "zagara":
        side = "zagara" if index == 0 else "brakk"
        s["event_zagara_side"] = side
        s["event_zagara_checkpoint"] = int(key)
        s["event_zagara_quest_pending"] = side == "zagara"
        s["event_zagara_quest_target"] = 0
        message = ("Zagara will send 100 allied Banelings every ten minutes after "
                   "you slay Brakk's Pack next mission." if index == 0 else
                   "Brakk joins until enemy Zagara is slain; Zagara sends hostile "
                   "Banelings every ten minutes while alive.")
    elif event_id == "colonists" and index == 0:
        s["event_colonists_checkpoint"] = int(key)
        message = ("Dr Hansen's colony hut will appear at your base. "
                   "Each mission completed with the hut surviving earns 150 credits.")
    elif event_id == "nova":
        unit_name = "Ghost" if index == 0 else "Spectre"
        item = slay._item_table().get(unit_name)
        if item is None or getattr(item, "code", None) is None:
            return False, f"Archipelago {unit_name} is not available in this item table.", False
        if index == 0 and slay.credits(ctx) < 200:
            return False, "Need 200 credits to hire Nova.", False
        if index == 0:
            s["spent"] = int(s.get("spent", 0)) + 200
        awards = dict(s.get("event_awarded_items", {}))
        awards[unit_name] = max(1, int(awards.get(unit_name, 0)))
        s["event_awarded_items"] = awards
        s["event_nova_side"] = "nova" if index == 0 else "tosh"
        s["event_nova_checkpoint"] = int(key)
        message = (f"Unlocked {unit_name} through an Archipelago item. " +
                   ("Nova joins until killed; enemy Tosh patrols until slain." if index == 0
                    else "Enemy Nova patrols until slain."))
    elif event_id == "crystalis" and index == 0:
        level_item = slay._one_kerrigan_level_item(slay._item_table())
        if not slay._progression_owned(ctx, slay.KERRIGAN_UNLOCK) or not level_item:
            return False, "Kerrigan and her Archipelago level item must be unlocked.", False
        awards = dict(s.get("event_awarded_items", {}))
        awards[level_item] = int(awards.get(level_item, 0)) + 70
        s["event_awarded_items"] = awards
        s["event_crystalis_checkpoint"] = int(key)
        message = (f"Kerrigan received 70 Archipelago levels ({level_item}). "
                   "All remaining missions gain Brakk's Pack or Dehaka's Pack without increased credit rewards.")
    elif event_id == "vortex" and index == 0:
        # Preserve the AP server's append-only receipt history while locally
        # suppressing all previously received AP items for mission startup.
        # New rewards after the event are usable as normal.
        raw = slay._raw_logic_owned_item_counts(ctx)
        s["event_forfeited_ap_counts"] = {
            name: int(count) for name, count in raw.items() if int(count) > 0
        }
        # Refund *the existing total-spent tracker*, not the current shop
        # catalog's recalculated prices. Setting spent to zero performs the
        # refund exactly once through the ordinary credits() formula.
        refund = max(0, int(s.get("spent", 0)))
        s["spent"] = 0
        s["purchases"] = {}
        s["event_awarded_items"] = {}
        s["event_crystalis_checkpoint"] = -1
        s["event_nova_side"] = ""
        s["event_colonists_checkpoint"] = -1
        s["event_zagara_side"] = ""
        s["event_zagara_quest_pending"] = False
        s["event_zagara_quest_target"] = 0
        s["event_organism_checkpoint"] = -1
        s["event_organism_pending"] = False
        s["event_organism_target"] = 0
        s["boon_purchases"] = {}
        s["permanent_boons"] = []
        s["permanent_blessings"] = []
        s["permanent_mutations"] = []
        s["potion_inventory"] = []
        s["shop_potions_bought"] = []
        s["shop_cycle_purchases"] = {}
        s["shop_cycle_purchase_victory_count"] = -1
        s["shop_frozen_item"] = ""
        s["shop_stock"] = []
        s["shop_cycle"] = -1
        s["shop_reroll_nonce"] = int(s.get("shop_reroll_nonce", 0)) + 1
        s["shop_expansion"] = 0
        s["risky_investment_charges"] = 0
        s["saving_grace_charges"] = 0
        s["saving_grace_pending"] = []
        s["golden_goose_bonus_per_mission"] = 0
        s["golden_goose_credit_offset"] = 0
        message = f"Unstable Vortex erased your owned items and effects. Refunded {refund} spent credits."
    elif event_id == "abathur" and index == 0:
        units = _owned_zerg_units(ctx)
        if len(units) < 4:
            return False, "Abathur requires at least four unlocked Zerg units.", False
        seed = hashlib.sha256(f'{ctx.slay_config.get("run_seed", 0)}:abathur:{key}'.encode()).digest()
        rng = random.Random(int.from_bytes(seed[:8], "big"))
        rng.shuffle(units)
        lost = sorted(units[:len(units) // 2])
        survivors = sorted(set(units) - set(lost))
        table = slay._item_table()
        raw_counts = slay._raw_logic_owned_item_counts(ctx)
        forfeited = dict(s.get("event_forfeited_ap_counts", {}))
        purchases = dict(s.get("purchases", {}))
        for name in lost:
            # Undo shop ownership; remove the original AP receipts from
            # mission launches without altering append-only server history.
            purchases.pop(name, None)
            forfeited[name] = max(int(forfeited.get(name, 0)), int(raw_counts.get(name, 0)))
        s["purchases"] = purchases
        s["event_forfeited_ap_counts"] = forfeited
        awards = dict(s.get("event_awarded_items", {}))
        current = slay._logic_owned_item_counts(ctx)
        given: list[str] = []
        for unit in survivors:
            candidates = [
                name for name, data in table.items()
                if getattr(data, "code", None) is not None
                and slay._item_race_key(name, data) == "zerg"
                and unit in slay._unit_specific_parent_names(name, table)
                and slay._is_unit_specific_upgrade(name, table)
                and int(current.get(name, 0)) + int(awards.get(name, 0)) < (
                    int(getattr(data, "quantity", 0)) if int(getattr(data, "quantity", 0)) > 0 else 1)
            ]
            rng.shuffle(candidates)
            for name in candidates[:3]:
                awards[name] = int(awards.get(name, 0)) + 1
                given.append(name)
        s["event_awarded_items"] = awards
        message = ("Abathur's experiment completed. Lost units: " +
                   ", ".join(lost) + ".\nUpgrades gained: " +
                   (", ".join(given) if given else "none available") + ".")
    else:
        penalty = {
            ("abathur", 1): "zerg_upgrade_50",
            ("organism", 1): "zerg_upgrade_20",
            ("mechanical", 1): "terran_unlock_50",
            ("crystalis", 1): "kerrigan_upgrade_20",
            ("solarite", 2): "spear_upgrade_20",
        }.get((event_id, index))
        if penalty:
            penalties = list(s.get("event_price_penalties", []))
            if penalty not in penalties:
                penalties.append(penalty)
            s["event_price_penalties"] = penalties
        message = data["options"][index]
    if done:
        s.setdefault("event_resolutions", {})[key] = {"id": event_id, "option": index}
    slay._persist_state(ctx)
    return True, message, done
