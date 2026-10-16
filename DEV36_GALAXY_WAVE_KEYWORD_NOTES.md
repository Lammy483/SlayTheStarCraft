# Dev36: Dev28 baneling compiler regression (reserved identifier)

## Findings
- The regression was bisected by the player: Dev27 works, Dev28 fails, and Dev28 with the two older baneling functions restored works.
- Inside `APRG_TickZagarasBanelings`, Dev28 declared `unitgroup wave;`. `wave` is already a built-in Galaxy type (`native wave EventPlayerWave();` and related AI wave natives), so it cannot be used as an identifier in Galaxy source.
- Dev36 renames just that local from `wave` to `spawnedBanelings` and fixes its four uses in the same function; **no gameplay algorithm changes**. The baneling logic added in Dev28 remains intact, including spawn spreading, pathable targets, and attack-moving.
- Dev36 uses Dev34 as its complete base. It retains Odin/Torrasque mineral-line exclusion, Jackson's Revenge Sniper Mercenaries range, the Dev32 voice assignments, and all features up through Dev31.
- Dev35's launcher hash assertion was NOT retained: the installer correctly transforms LF source to CRLF on Windows, but Dev35 incorrectly compared raw byte hashes.
- No globally added SC2 dependency.

## Validation
Offline source verifier and automatic Python unit tests pass. These cannot substitute for an SC2 Galaxy compile test. Use the same mission to confirm the three-race critical error is absent. If the error remains, this is a confirmed identifier defect but not necessarily the only Galaxy defect.

## Switching test
For a minimal A/B comparison, use the separate Dev28_RenameWave diagnostic source against the existing Dev31 runtime; it differs from broken Dev28 only in the five local identifier references.
