# Contributing to Slay the StarCraft

Contributions are welcome through normal GitHub pull requests.

## Branching

- `main` should represent the current stable public release.
- Development for the next patch should happen on `develop` or focused branches created from it.
- Use short branch names such as `fix/golden-armada-pathing` or `feature/new-mutation`.

## Before opening a pull request

1. Keep the change focused. Avoid unrelated formatting or broad refactors of working Galaxy code.
2. Run `python .\Payload\verify_release.py --source-only`.
3. For Galaxy/gameplay changes, test the affected mechanic in StarCraft II when practical.
4. Do not commit `Runtime/`, `Runs/`, logs, generated ZIPs, compiled executables, downloaded Archipelago source, or Blizzard assets.
5. Describe what changed, how it was tested, and any mission/campaign-specific limitations.

## StarCraft II / Archipelago caveats

Campaign missions can expose different unit links, abilities, dependencies, and script behavior. A unit ID that works in one campaign may fail in another. Prefer existing compatibility helpers and catalog checks over assuming one alias is globally valid.

Generated enemy/allied units should use the established Slay AI helpers where possible. Be explicit about whether a mechanic should attack-move, patrol by attack-moving, directly attack a target, or simply move.

## Versioning

The stable release currently follows patch versions such as `1.0.2`. Development builds based on that release use `1.0.2.1`, `1.0.2.2`, etc. When a bug-fix branch is ready for public release, promote it to the next patch release, e.g. `1.0.3`. Reserve minor versions such as `1.1.0` for feature releases.
