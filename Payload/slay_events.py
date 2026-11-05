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
