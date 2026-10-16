# Dev48 — Nydus timing, Tosh raids, Roachling exclusion, Multiple Air Bogies VO

Based on Dev47; preserves the native Galaxy declaration repair from Dev46, the Dev36 wave-variable fix and all previous mutation/blessing/consumable features.

## Nydus Worms
- Subsequent releases from each living worm begin at independently randomized 40–50 second intervals (measured between wave starts) instead of 60 seconds.
- Choose a valid position and queue a Horner/Adjutant announcement two *game seconds* before creating the Nydus Worm. Do not queue a new announcement while the campaign VO queue is occupied. Pending positions are held through the two-second warning.
- The first worm still appears at four minutes after player base establishment: first warning scheduled at 3:58; next worm warnings scheduled 58–68 seconds after each birth so later births remain 60–70 seconds apart.
- Previous continuous sight, pathable placement, and per-unit unload animation remain unchanged.

## Roachling zombie exclusions
- Roachlings are exempt from recursive death-spawn effects through the shared disposable-summon exclusion, covering zombie mutations and blessings, without changing Roachling Mines spawning itself.

## Tosh
- Covert Assistance Tosh reserves energy for Defensive Matrix/Psi Shield. His dedicated tick and shared autonomous ability dispatcher now gate optional offensive casts below 200 energy.
- Hostile Tosh in Tosh and His Boys uses the same reserve in the shared dispatcher and checks before using optional hero abilities.
- Hostile Tosh patrols to more varied, distant enemy/neutral destinations beginning three minutes after base establishment, with reassignment at most every twenty seconds rather than tiny frequent hops.
- Spectres first attempt to appear four minutes after base establishment, retry failed spawns at five-second intervals, receive immediate movement orders toward player structures, remain in approach mode until within 12 range of a structure, and only then start a visible 12-second scripted nuke warning. Death during the warning cancels the strike. Subsequent Spectres attempt to spawn every 60 seconds after a successful spawn.
- Hostile Tosh's code retains existing island exclusion and one-life policy.

## Multiple Air Bogies sound
- Queue exactly one campaign VO per successfully spawned wave of Mutalisks (with any accompanying Brood Lords), using the selected file `Campaigns\\Liberty.SC2Campaign\\enUS.SC2Assets\\LocalizedData\\Sounds\\TerranVO\\CampaignVO\\traynor03tychus00013.ogg`.
- Slay-local `APRogueVO_TRaynor03Tychus00013` is registered as a fallback, preferring a loaded Blizzard Sound entry; playback uses the shared campaign transmission queue, never a global campaign dependency.
- Retry silently when no Mutalisks are created.

## Validation
- `python Payload/verify_release.py --source-only`: passed.
- 450 offline unittest checks passed, including six focused Dev48 checks and updated historic assertions for intentional timing/catalog changes.
- These checks do **not** replace in-game SC2 Galaxy compilation or gameplay validation.
