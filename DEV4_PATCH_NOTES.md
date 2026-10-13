# Slay the StarCraft v1.1.2 Dev4 (unpublished)

## Effect-frequency multiplier behavior

- For every mission, roll the unmodified Gaussian mutation and blessing severity budgets first. Only after the severity roll, multiply by the respective user frequency multiplier and round/clamp to the usual budgets. Previously the mean was multiplied but the Gaussian variance was not, so even a frequency setting of zero could roll effects.
- Early high-tier mission blessing-severity bonuses are part of the pre-multiplier budget and therefore respect the setting of zero.
- A zero blessing multiplier now produces **no blessings** in generated runs, including the normally guaranteed easy opening route, which previously could inject a forced blessing. With reduced blessing frequency the <=400-credit cheap opening can no longer be guaranteed; preserving an absolute zero takes precedence.
- A zero mutation multiplier now produces **no mutations**, including final-quarter forced major mutations and later balance adjustments. Runs with mutation frequency less than 1.0 also skip forced red-path mutation injection so that reduced frequency is meaningful; runs with the default or higher multiplier retain it.
- This affects newly generated runs, not previously saved missions.

## Gameplay difficulty

- Mutation-severity Gaussian mean is reduced by 2 per step below Brutal: Brutal 0, Hard -2, Medium -4, Easy -6. This applies to every mission, including finales and higher/lower mission-pool balancing.
- The expected danger score uses the same difficulty offsets, keeping route labels broadly aligned with the difficulty setting.
- Gameplay difficulty still controls SC2's ordinary game difficulty. It does not otherwise change the mission tier distribution or blessing mean.

## Launcher text

Replaced the second paragraph of the difficulty description with:

> If you are not comfortable playing the default campaigns on Brutal difficulty, or do not want the challenge described above, then it is recommended to try on a reduced gameplay difficulty before tweaking other settings.

## Validation

- Regression tests cover scaling order, zero frequency across all 12 mission layers, early high-tier bonus, gameplay difficulty offsets, and complete run assignment for zero multipliers.
- Source verification and Python compilation performed; no live SC2 mission test.
- Builds on Dev3 and retains the Zagara/Purifier, Dev2 timing/Lab Rat, and Dev1 Baneling Stream changes.
