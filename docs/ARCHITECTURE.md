# Architecture Notes

Slay the StarCraft is intentionally a lightweight layer on top of a pinned Archipelago StarCraft II runtime rather than a fork that bundles the entire upstream project.

A typical launch is:

1. `SlayTheStarCraft.exe` locates the portable folder and StarCraft II.
2. `Tools/bootstrap_slay_runtime.ps1` creates/repairs the private runtime when required.
3. `Payload/install_slay.py` patches the pinned Archipelago SC2 integration and installs Slay payload files.
4. `Payload/slay_launcher.py` manages run configuration and launches the Slay client.
5. `Payload/generate_slay_run.py` produces the branching campaign/run data.
6. The patched SC2 client sends the `?APRogue` handshake into the mission.
7. `Payload/APRogue.galaxy` interprets that state and runs mission-side Slay gameplay.

Persistent progression belongs primarily in Python/run state. Mission-local combat behavior belongs in Galaxy. New features that cross mission boundaries generally need both sides of that boundary plus a backwards-compatible handshake field or persistent run-state representation.
