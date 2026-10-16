# v1.1.2 Dev20 — Regenerative Aberrations detection follow-up

- Dev19's unconditional +10 HP per second code has not been confirmed functional in SC2. The shop flag and item transport are correctly mapped, but its target-selection code only recognized Aberrations whose internal catalog IDs contain that name.
- Match internal unit links, localized unit-type display names, and per-unit name overrides (both Aberration/Abberation spellings), using cached localized type lookups. This follows the established Energized Queens fix.
- Search all player-owned units rather than only those included in the mobile-unit filter, allowing for unusual Archipelago/campaign flags.
- Run the same capped +10 HP tick through both the existing fast scheduler and the one-second main scheduler, sharing the one-second timer to prevent double-healing.
- Added an opt-in diagnostic: select an Aberration and type `?SlayAberrationDebug` into mission chat. Output includes whether the boon flag reached Galaxy, base-established state, the selected unit's internal ID, display name, owner, match status, and HP. No automatic chat messages.
- Monstrous Resilience's native Archipelago regeneration remains unchanged, and the Slay +10 heal remains additive. This patch is an evidence-guided correction; exact runtime failure still requires an SC2 test.
- Everything from Dev19 is retained; GitHub unchanged.
