# Release Process

1. Start from a validated development branch.
2. Update all version constants and `VERSION.txt`/`launcher_manifest.json` together.
3. Run:

```powershell
python .\Payload\verify_release.py --source-only
.\Tools\build_launcher.ps1
```

4. Test the portable installer on a machine or environment without relying on an existing `Runtime/` or pip cache when practical.
5. Test representative Wings of Liberty, Heart of the Swarm, and Legacy of the Void missions for cross-campaign gameplay changes.
6. Build the end-user ZIP separately from the Git repository. Do not commit the ZIP or `SlayTheStarCraft.exe` to normal Git history.
7. Tag the release and attach the end-user ZIP to the GitHub Release.

For bug-fix development based on a stable release such as `1.0.2`, use development versions `1.0.2.1`, `1.0.2.2`, and so on. Promote a completed bug-fix line to the next patch release such as `1.0.3`. Reserve `1.1.0` for a feature release.
