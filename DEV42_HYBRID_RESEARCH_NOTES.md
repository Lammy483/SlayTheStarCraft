# Dev42 — Hybrid Research mutation

Based on Dev41, preserving the Dev28/Dev36 three-race Galaxy fix and all later effects, voice lines, and launcher behavior.

## Behavior
- Registered **Hybrid Research**, Mutation, severity **4**.
- Exact display text: **Each enemy structure releases a random hybrid when destroyed**.
- Every eligible enemy-owned structure destroyed after the player's macro base is established produces one enemy-owned hybrid at its death location. Creep tumors and spider mines are excluded following Slay's standard structure-only eligibility.
- The independent selection roll is 40% Hybrid Reaver; 40% Hybrid Destroyer; 10% Hybrid Nemesis; 5% Hybrid Behemoth; 5% Hybrid Dominator.
- When a selected hybrid's catalog unit is not loaded by the mission, fall back to the first available hybrid unit type. This preserves one spawned enemy hybrid per building where any hybrid type is available, but can affect the observed type distribution on missions lacking specific hybrid unit catalog entries.
- Newly created hybrids use Slay's standardized hostile-raider registration, removal of Void Entity vulnerability, and attack orders toward the player base.
- Uses a previously unallocated bank-E bit (268435456) and Slay's existing unit-death trigger. No extra global dependency or polling trigger.
- Excluded from all missions flagged timed defense and from The Crucible, which has no enemy-owned structures to serve as sources. Exclusions aligned across both run-generator implementations.

## Validation
- Source verifier: pass. Focused Dev42 tests: 6 pass. Previous Dev41 and Dev10 tests: pass.
- Full regression suite will be checked before release.
- No StarCraft II runtime compiler available here; in-game testing is still required.
