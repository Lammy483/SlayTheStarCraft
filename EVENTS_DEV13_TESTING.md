# Slay the StarCraft — Events Dev13 integration test

Branch: `develop/v1.2.3.1-odin-missions`. Date: 2026-11-05.
**Experimental; no live SC2 gameplay has been verified by CI.**

## Changes since Dev12

1. **Native event heroes:** enemy Nova/Tosh and enemy Zagara now spawn on
   nearby hostile-side pathable ground instead of at the center of an enemy
   structure. If a suitable point is unavailable, creation is retried on a
   later tick rather than trapping the actor inside the structure.
2. **Zagara's allied Banelings:** each ten-minute 100-Baneling wave spawns in
   five 20-unit groups spread around safe points near the player's base, then
   issues attack-move orders toward enemy structures.
3. **Solarite replay safety:** once a successful 5,000-mineral/gas conversion
   has been committed to the per-run SC2 event bank, relaunching the trial
   mission cannot charge the player a second time.
4. **Swann performance:** permanent +20% mechanical weapon damage traverses
   native effect trees once per owner/root effect, not once every two seconds
   for every matching unit. Newly encountered weapon types can still be
   processed when they first appear.

## Test plan

1. Launch the extracted Windows build, choose Standard Mode and opt in to
   **Events (BETA)**. The opening selector can force any of the ten events.
2. **Nova's Mission:** test both sides. Observe where Tosh/Nova spawns,
   movement, the ally's behavior, and permanent death persistence after
   a restart or mission change.
3. **Zagara:** test both sides. Check enemy Zagara can navigate off its spawn
   and that allied 100-Baneling waves are spread out, attack-move, and do not
   cause a major lag spike.
4. **Solarite Conversion:** select minerals or gas, accumulate at least 5,000
   of the chosen resource, verify it is spent once, then replay the trial
   mission if possible. Success should not take another 5,000.
5. **Rory Swann:** succeed at a 50-kill field test; then recruit many copies
   of the tested unit and verify their HP, speed and actual weapon damage
   are increased by 20% without per-tick lag. Also verify failed trials
   spawn enemy patrols headed for your base.
6. Verify all three races can launch a mission without the historical
   Galaxy three-race critical error. Run normal Standard (Events off), Crew,
   and Campaign to ensure event behavior stays disabled.
7. Confirm resolving events does not count as a mission win, reroll stock,
   reset sold-out counters, or restock potions.

## Validation limits

GitHub Actions runs Python compilation, source-only release checks,
static Galaxy declaration/call checks, and the event regression suite,
then packages a Windows launcher. It cannot validate actual SC2 map
compilation, unit availability under each campaign dependency, or gameplay
without a real mission playtest.
