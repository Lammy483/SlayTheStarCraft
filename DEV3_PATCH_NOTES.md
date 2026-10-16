# Slay the StarCraft v1.1.2 Dev3: Zagara and Purifier

Build base: v1.1.2 Dev2 (`SlayTheStarCraft_v1.1.2_Base_Timing_LabRat_Dev2_Windows.zip`).

## Enemy Zagara dies at <=4 HP

The existing generated-hero workaround triggered at <=3.1 HP. It now triggers at <=4.0 HP. A second 0.5-second periodic sweep catches hostile Zagara units not registered by the Slay hero spawner (e.g. campaign-owned enemies), stripping revival/death prevention and invoking `UnitKill` with `UnitRemove` fallback if still alive.

## Purifier invulnerability and native mission preservation

Only the Slay-created mutation Purifier (when mutation active) or Slay-created Purifier Alliance (when boon active) loses `InvulnerabilityShield`. The helper checks both the specific tracked unit reference and the corresponding active effect flag before touching shield state. It will not touch a mission-owned Purifier, so Safe Haven's normal Nexus-related invulnerability remains under the original mission triggers. No global Purifier catalog or native mission script has been edited.

## Preserved changes

All prior v1.1.2 Dev1/Dev2 changes, including the Baneling Stream attack-move behavior, Too Many Wraiths macro-base-relative timer, other timing changes, Lab Rat Tower Defense exclusion, and Lab Rat Horde Mode +25 mineral compensation.

## Verification

- 228 offline Python unit tests passed; `test_endless_mode.py` is a parameterized integration harness and is not counted in the unit suite.
- No SC2 live test or Galaxy compiler execution has been performed; verify in game before release.
- Development-only; no GitHub branches were modified.
