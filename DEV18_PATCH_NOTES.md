# v1.1.2 Dev18 — Artanis commander uses the LotV ground hero

- Request the Void campaign catalog when the General blessing selects Artanis (commander index 9), the same as Alarak and Vorazun.
- Use the actual campaign unit `ArtanisVoid` (Twilight Blades) directly, bypassing the normal AP production replacement for this hero. Fall back to `AP_ArtanisVoid` only if the native unit is missing.
- Never replace an explicit Artanis commander with an unrelated random hero such as Urun if the catalog is unavailable. Display a clear in-game warning in that case.
- Keep the Haven dependency compatibility restriction intact; on sensitive Haven maps lacking Void data, display the warning rather than summoning Urun.
- Preserve respawns, commander bonuses, and every earlier Dev17 change. No release or GitHub branch updates.

