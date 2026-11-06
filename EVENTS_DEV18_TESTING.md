# Dev18 — Event and installer regression patch

- Rory Swann's gifted surviving units receive +20% HP, speed and damage on their 50th kill, immediately in the trial mission.
- Rory Swann, Abathur's Organism Field Test and Solarite Conversion fail if the player advances to the subsequent layer without an explicit successful objective receipt. Handles /victory and mission layer 0.
- Zagara only starts sending allied Banelings after Brakk is genuinely killed.
- Hansen's hut only appears when accepted. It is neutral, targetable by the player and infested emerge immediately adjacent to it.
- Meat Grinder mutation uses the correct Protoss race code for Zealot production.
- All event popups permit selecting a different event for testing purposes.
- Existing-install update scripts auto-launch the installed game following a successful full replacement. The Downloads wrapper delegates launching to the updater.
- Offline regression tests are included. SC2 gameplay and Windows process startup still need live verification.
