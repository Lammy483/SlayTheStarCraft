# v1.1.2 Dev2 — timing audit

All times below are game-time seconds. The **macro base established** event is the existing `APRG_UpdateMacroBaseReady` gate; Lab Rat additionally requires a *completed* supply provider, 300 minerals collected since initialization, and seven seconds since the supply completion. Timers are initialized once at that event, not at mission load.

## Timed gameplay re-anchored to the macro-base-established clock

- **Too Many Wraiths:** first raid after +60 seconds; accelerated raid interval uses time since base (60–720 seconds ramp), instead of global mission time.
- **Viking Raids:** first random attack after +20–180 seconds; attacking Viking wave size scales with base-relative minutes.
- **Dark Templar, Occasional Thor/Ultralisk/Colossus:** +60–160 seconds for the first Dark Templar raid; +60 seconds for each occasional unit type.
- **Golden Armada / True Golden Armada:** first four-minute protection from player/allied buildings, and True Armada's ten-minute unrestricted-patrol transition, use base-relative time. Their spawn and normal retarget logic is otherwise unchanged.
- **Heroes of the Storm:** initial patrol/defense escalation clocks +300/+240 seconds; four-minute route safety uses base-relative time.
- **Sniper Thor:** timed-defense base attack only after base +900 seconds.
- **Tower Defense:** initial timing +30 seconds (but ineligible on Lab Rat).
- **Jetpacks:** first attack +120 seconds, next attack +240 seconds, then recurring at 60-second intervals.
- **Zagara's Banelings / Zagara's Aid:** first waves +600 seconds, then normal recurrence.
- **Air Support, Lost Vikings, Warfield's Reinforcements, Another Gorgon blessing, Horde Mode larva:** their first timed actions are now scheduled from base establishment.
- **Multi-Class blessing:** extra hero spawns no earlier than base +30 seconds.
- **Arms Race, Rapid Evolution (player and enemy), Compounding Interest, Energy Leak, Enemy Regeneration, Decay, Inflatable Soldiers:** recurring timed stat/economy changes don't tick early on mission load.
- **Baneling Stream:** does not spawn timed banelings before base establishment; retains Dev1 attack-move logic.
- **Mineral Thieves and Active Enemies:** their initial scan/event timing is rebased to macro readiness.

## Explicit mission-clock exceptions retained

- **10 Minutes Until Destruction**: after 10 mission-time minutes, as specified by its named effect/description.
- **Tal'darim Reinforcements**: after the **20-minute mark**.
- **Invasion Fleet**: begins at the **5-minute mark of the mission**, runs for 2 minutes.
- **Purifier Alliance**: spawns at the **5-minute mark of the mission** (base-ready required to place it).

## Existing base-relative or event-relative timing left intact

- Base-relative gates already in use (Leviathan approach, Drop Pods, Void Thrashers, Tosh, delayed Odin, Brakk, Marauder Kill Teams, Hellion Run-By, Diamondback Wanderers, Combined Raids, etc.) remain as-is.
- Death-triggered respawns, per-cast cooldowns, potion durations, ability AI throttles, actor visual effects, and post-spawn attack/repair timers remain relative to the **event that starts them**, not the base clock, as they should be.
- Passive static modifiers and starting-unit/resource effects remain applied when effects initialize; a base-relative timer is not needed for an instantaneous adjustment.

## Lab Rat

- `tower_defense` added to the mission's generator exclusion set.
- When and only when Lab Rat has **Horde Mode**, 25 minerals are added once at initial effect activation. This compensates the discounted Drone catalog price affecting a morph building's actual mineral spend. This intentionally does not fix the underlying general Horde Mode/Drone morph interaction on other maps, per request.

## Validation

- Python regression tests (excluding the standalone CLI-only `test_endless_mode.py` that requires external arguments).
- `python Payload/verify_release.py --source-only`.
- Live SC2 gameplay not available in this environment; runtime event scheduling still needs field verification before a stable release.
