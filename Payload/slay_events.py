"""Standard-mode encounter catalog and durable event checkpoints.

Descriptions and outcomes below are the author's original event text.
Gameplay implementation lives in slay_the_starcraft.py / APRogue.galaxy.
"""
from __future__ import annotations

import hashlib
import math
import random
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
REGULAR_ENABLED = ("merchant",)
IMPLEMENTED_OPTIONS: dict[str, tuple[int, ...]] = {
    "merchant": (0, 1, 2, 3, 4),
    "abathur": (1,),
    "organism": (1,),
    "mechanical": (1,),
    "colonists": (1,),
    "crystalis": (1,),
    "solarite": (2,),
    "vortex": (1,),
}

def checkpoints(total_missions: int) -> tuple[int, ...]:
    """One before the opening mission, plus ceil(missions / 3).

    Put the final scheduled encounter before the final mission if its
    three-mission boundary would otherwise be after the run is over.
    """
    count = max(1, int(total_missions))
    return (0, *sorted({min(count - 1, 3 * index)
                       for index in range(1, math.ceil(count / 3) + 1)}))

def deterministic_event(seed: int, checkpoint: int, used: tuple[str, ...] = ()) -> str:
    pool = [event_id for event_id in REGULAR_ENABLED if event_id not in used]
    if not pool:
        pool = list(REGULAR_ENABLED)
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
                used = tuple(str(x) for k, x in s.get("event_assignments", {}).items()
                             if k != "0" and x in REGULAR_ENABLED)
                event_id = deterministic_event(seed, checkpoint, used)
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
        shown.append({"text": label, "enabled": can, "implemented": implemented})
    return dict(p, name=data["name"], description=data["description"], options=shown)

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
            bonus = rng.randint(50, 200)
            s["event_credit_bonus"] = int(s.get("event_credit_bonus", 0)) + bonus
            s["event_merchant_raid_pending"] = True
            message = f'Raided merchant vessel; gained {slay.POTION_CATALOG[pid]["name"]} and {bonus} credits. Mercenaries attack next mission.'
        else:
            message = "Left the merchant vessel."
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
