# Dev11 — Spear of Adun passive initialization

## Root cause
In `Payload/APRogue.galaxy`, `APRG_PinSpearPreBase` disabled all abilities on both the regular and autonomous Spear casters before macro-base establishment. When the base became ready, `APRG_TickSpearBaseGate` only called `APRG_ReleaseSpearCooldownsAtBase` on the regular caster, so the autonomous caster's ability-enabled flags remained false for the rest of the mission. That caster supports autonomous Spear abilities such as Reconstruction Beam.

## Fix
`APRG_ReleaseSpearAutonomousAbilitiesAtBase` re-enables abilities on `AP_SoAAutonomousCaster` once the base-ready condition is true. It does not call the regular Spear cooldown reset routine on passive actions. This keeps the pre-base gate and avoids global catalog changes.

## Other checks
- Slay already injects shop-bought Spear items into Archipelago's `calculate_items` input using `augment_network_items`, including the Solarite Core flag for Reconstruction Beam.
- `apply_spear_options` already enables passive Spear availability when the Spear unlock is owned.
- Thus the problem is not the shop ledger or the mission payload: it is the autonomous-caster gate's unmatched disable/enable operations.

Live SC2 verification: buy Reconstruction Beam, damage an eligible mechanical unit and non-biological building, confirm zero repair before base-ready and normal autonomous repair after base-ready. Repeat with the other autonomous Spear passives, and with the regular active Spear powers.
