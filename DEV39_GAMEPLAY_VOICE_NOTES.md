# Dev39 — tested WoL voices moved into gameplay

Based on Dev38, retaining all gameplay, the confirmed Dev36 reserved-keyword fix, 21 local Sound catalog registrations, and shared Warfield/VO queue.

- Player-built Drakken drill: `TTychus02Tychus00008`, first 7 real seconds.
- Enemy Drakken mutation created: `TTychus02Raynor00020`.
- Enemy Purifier begins its approach 120 s after base: `TTychus05Horner00013`.
- Allied Purifier first attack-move order: `THanson03AHorner00001`.
- True Golden Armada successful spawn: `TTychus05Horner00032`.
- First *successfully spawned* Air Support aircraft: `TValerian01Raynor00043`, now **2.5 real seconds** (+0.5).
- Orlan fortress first HP loss: `THorner02Orlan00012`; its death: `THorner02Orlan00019`.
- Enemy Leviathan starts moving after delay: `TValerian02BAdjutant00035`; arrival/ability unlock: `TValerian02BAdjutant00017`.
- First hostile zombie in Zombies or Zombie Apocalypse: `THanson02BriefingHanson00001`.
- Marauder Kill Teams first spawn and Mira mercenary purchase keep their Dev32 event hooks.
- The six Horner alternatives (`TValerian01Horner00015/27/31/32/36/37`) rotate for **later** Drop Pods mutation raids only when the landing point is within range 8 of a player's unit or building. The VO is queued 5 seconds before the *drop-pod visual appears*, and the pod is held for that delay. The initial hostile drop remains unchanged pending a working Archangel line. In a busy VO queue, audible start may occur later; no overlap is forced.
- The automatic audio tester and `?SlayVOTest` now play **only the two silent Archangel clips** 123 and 124. No Archangel gameplay events are assigned. Try a HotS mission if they remain silent in WoL. A registered catalog entry is not proof the underlying SwarmStory voice asset is available.

No global campaign dependencies; no additional foreign audio assets. Offline source checks are not in-game SC2 compilation or sound verification.
