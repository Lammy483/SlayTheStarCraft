# Dev44 - Nydus Worms VO and Immortals display name

- On every mutation-created Nydus emergence, randomly queue one of the WoL campaign recordings `ttychus03horner00009.ogg` or `tvalerian03adjutant00039.ogg`.
- When three or more mutation-created worms are alive, queue `ttychus03horner00033.ogg`, rate-limited to once every 240 game seconds. The scan checks the owned 32-slot Nydus pool at most every five game seconds.
- Uses the serialized Warfield/campaign queue and three Slay-local sound catalog fallbacks, without global campaign dependencies.
- Renames displayed mutation `50 immortals` to `Immortals` everywhere in runtime UI, Galaxy effect summary, and effect CSV, while preserving the stable internal `fifty_immortals` effect ID/bit for compatibility and exactly 30 Immortals.
- No changes to Nydus spawning or army logic.
- The new VO still needs live SC2 playback confirmation.
