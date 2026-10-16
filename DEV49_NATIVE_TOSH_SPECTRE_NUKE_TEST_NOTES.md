# Dev49 — Native Spectre nuclear strike test

This is a **diagnostic build**. Normal design: Spectres first appear **5 minutes after the base is established**. To speed up testing, Dev49 spawns the first Spectre after **1 minute** and subsequent Spectres every 60 seconds while hostile Tosh survives.

The nuke no longer uses custom `NukeDamage`/fake nuke actor for the Tosh and His Boys Spectres. Instead it calls `TacNukeStrike` with a real Galaxy order, matching Blizzard's Cutthroat (`THorner02`) mission implementation. It adds `TacNukeStrike` to a Spectre if needed, and provisions a *temporary, non-targetable enemy Ghost Academy* to stock one warhead using `UnitMagazineArm(..., AbilityCommand("ArmSiloWithNuke",0),1)`. That temporary structure is removed once the native cast is over or the Spectre dies. No campaign-wide dependency added.

The tester prints distinct diagnostics for missing catalog entries, failed Academy creation, unstocked ammo, invalid native order, rejected order, and accepted order. Acceptance alone does not prove a missile actually landed. No fake damage fallback. If stock/academy causes a mission-objective problem, identify mission and timing.

Native research: StarCraft II Cutthroat `gf_GhostNukeEm` (`THorner02`), SC2GameData / mapster; Ghost Academy `ArmSiloWithNuke` and Spectre `TacNukeStrike`.

Once confirmed, change `APRG_TOSH_SPECTRE_FIRST_SPAWN_DELAY` in `APRogue.galaxy` from 60.0 to 300.0 for normal release.

Offline tests are not an in-game Galaxy compile or behavior test. No GitHub push.
