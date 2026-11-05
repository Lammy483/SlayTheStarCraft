# Update an existing portable Slay the StarCraft installation without Download Data.
# Run this file from the Tools directory of the NEW build, or supply -NewZip.
# Preserve Runtime, Runs, Config preferences, and previously imported UI textures.
[CmdletBinding()]
param(
    [string]$ExistingInstall = "",
    [string]$NewBuild = "",
    [string]$NewZip = ""
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$temporaryExtraction = $null

function Get-FullDirectory([string]$Candidate) {
    if (-not (Test-Path -LiteralPath $Candidate -PathType Container)) {
        throw "Folder not found: $Candidate"
    }
    return (Resolve-Path -LiteralPath $Candidate).Path.TrimEnd('\', '/')
}

function Select-ExistingInstall {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.FolderBrowserDialog
    $picker.Description = "Select your EXISTING Dev14 Slay folder (the one with Runtime and Runs)."
    $picker.ShowNewFolderButton = $false
    if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "No existing installation was selected."
    }
    return $picker.SelectedPath
}

function Get-SourceRoot {
    if ($NewBuild -and $NewZip) {
        throw "Use either -NewBuild or -NewZip, not both."
    }
    if ($NewZip) {
        $archive = (Resolve-Path -LiteralPath $NewZip).Path
        $script:temporaryExtraction = Join-Path ([IO.Path]::GetTempPath()) ("SlayUpgrade_" + [Guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $script:temporaryExtraction -Force | Out-Null
        Expand-Archive -LiteralPath $archive -DestinationPath $script:temporaryExtraction -Force
        $candidates = @($script:temporaryExtraction)
        $candidates += @(Get-ChildItem -LiteralPath $script:temporaryExtraction -Directory | Select-Object -ExpandProperty FullName)
        foreach ($candidate in $candidates) {
            if ((Test-Path -LiteralPath (Join-Path $candidate "Payload\install_slay.py") -PathType Leaf) -and
                (Test-Path -LiteralPath (Join-Path $candidate "SlayTheStarCraft.exe") -PathType Leaf)) {
                return (Get-FullDirectory $candidate)
            }
        }
        throw "ZIP does not contain a complete Slay build with Payload and SlayTheStarCraft.exe."
    }
    if ($NewBuild) { return (Get-FullDirectory $NewBuild) }
    return (Get-FullDirectory (Join-Path $PSScriptRoot ".."))
}

function Assert-Writable([string]$Folder) {
    $probe = Join-Path $Folder (".slay_upgrade_probe_" + [Guid]::NewGuid().ToString("N"))
    try {
        [IO.File]::WriteAllText($probe, "ok")
    }
    catch {
        throw "Cannot write to $Folder. Run PowerShell as Administrator and retry."
    }
    finally {
        if (Test-Path -LiteralPath $probe) { Remove-Item -LiteralPath $probe -Force }
    }
}

try {
    $sourceRoot = Get-SourceRoot
    if (-not $ExistingInstall) { $ExistingInstall = Select-ExistingInstall }
    $targetRoot = Get-FullDirectory $ExistingInstall
    if ($sourceRoot -eq $targetRoot -or
        $sourceRoot.StartsWith($targetRoot + "\", [StringComparison]::OrdinalIgnoreCase) -or
        $targetRoot.StartsWith($sourceRoot + "\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "New build and existing installation must be in separate, non-nested folders."
    }

    $oldRuntime = Join-Path $targetRoot "Runtime"
    $markerPath = Join-Path $oldRuntime "runtime.json"
    $python = Join-Path $oldRuntime "Python\python.exe"
    $apRoot = Join-Path $oldRuntime "Archipelago"
    $installConfig = Join-Path $targetRoot "Config\slay_install.json"
    foreach ($required in @($markerPath, $python, (Join-Path $apRoot "Generate.py"), $installConfig)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Existing installation is missing $required. It must have completed Download Data once."
        }
    }
    foreach ($required in @("Payload\install_slay.py", "Tools\setup_slay_launcher.py", "Tools\slay_launcher_windows.go", "SlayTheStarCraft.exe")) {
        if (-not (Test-Path -LiteralPath (Join-Path $sourceRoot $required) -PathType Leaf)) {
            throw "New build is incomplete: $required"
        }
    }
    if (Get-Process -Name "SlayTheStarCraft" -ErrorAction SilentlyContinue) {
        throw "Close SlayTheStarCraft.exe before updating."
    }

    $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
    $oldConfig = Get-Content -LiteralPath $installConfig -Raw | ConvertFrom-Json
    $sc2Root = [string]$oldConfig.sc2_root
    if (-not $sc2Root -or -not (Test-Path -LiteralPath $sc2Root -PathType Container)) {
        throw "Could not locate your existing StarCraft II path in Config\slay_install.json."
    }
    $modDir = Join-Path $sc2Root "Mods\ArchipelagoTriggers.SC2Mod\Base.SC2Data"
    if (-not (Test-Path -LiteralPath (Join-Path $modDir "APRogue.galaxy") -PathType Leaf)) {
        throw "The existing SC2 Galaxy mod is missing; Download Data is needed to restore the SC2 files."
    }

    $goSource = Get-Content -LiteralPath (Join-Path $sourceRoot "Tools\slay_launcher_windows.go") -Raw
    if ($goSource -notmatch '(?m)^\s*version\s*=\s*"([^"]+)"') {
        throw "Could not determine the new launcher's version."
    }
    $newVersion = $Matches[1]
    if ($goSource -notmatch '(?m)^\s*runtimeRevision\s*=\s*"([^"]+)"') {
        throw "Could not determine the new launcher's runtime revision."
    }
    $newRuntimeRevision = $Matches[1]
    if ([string]$marker.runtime_revision -ne $newRuntimeRevision) {
        throw "This update requires runtime revision $newRuntimeRevision but the installed runtime is $($marker.runtime_revision). Download Data is required for a changed runtime."
    }

    # Check permissions before touching files. The installer also patches SC2.
    Assert-Writable $targetRoot
    Assert-Writable $modDir
    Write-Host "Upgrading Slay $($marker.slay_version) -> $newVersion" -ForegroundColor Cyan
    Write-Host "Existing installation: $targetRoot"
    Write-Host "New build: $sourceRoot"
    Write-Host "Keeping Runtime, Runs, saved preferences and restored PNG artwork."

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupRoot = Join-Path $oldRuntime ("UpdateBackups\" + $stamp)
    $toCopy = New-Object System.Collections.Generic.List[string]
    foreach ($folderName in @("Payload", "Tools")) {
        $sourceFolder = Join-Path $sourceRoot $folderName
        foreach ($file in (Get-ChildItem -LiteralPath $sourceFolder -Recurse -File)) {
            # Keep the user's existing assets when a build ships only JSON mappings.
            $toCopy.Add($file.FullName)
        }
    }
    foreach ($name in @("SlayTheStarCraft.exe", "launcher_manifest.json", "VERSION.txt", "README.md",
                         "README.txt", "CHANGELOG.md", "INTEGRATION_BUILD.txt")) {
        $candidate = Join-Path $sourceRoot $name
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $toCopy.Add($candidate) }
    }
    foreach ($sourceFile in $toCopy) {
        $relative = $sourceFile.Substring($sourceRoot.Length + 1)
        $destination = Join-Path $targetRoot $relative
        $parent = Split-Path -Parent $destination
        if (-not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            $backupFile = Join-Path $backupRoot $relative
            $backupParent = Split-Path -Parent $backupFile
            if (-not (Test-Path -LiteralPath $backupParent)) {
                New-Item -ItemType Directory -Path $backupParent -Force | Out-Null
            }
            Copy-Item -LiteralPath $destination -Destination $backupFile -Force
        }
        Copy-Item -LiteralPath $sourceFile -Destination $destination -Force
    }
    # Import only NEW default config files; do not overwrite local preferences.
    $sourceConfig = Join-Path $sourceRoot "Config"
    if (Test-Path -LiteralPath $sourceConfig -PathType Container) {
        foreach ($file in (Get-ChildItem -LiteralPath $sourceConfig -Recurse -File)) {
            $relative = $file.FullName.Substring($sourceRoot.Length + 1)
            $destination = Join-Path $targetRoot $relative
            if (-not (Test-Path -LiteralPath $destination)) {
                $parent = Split-Path -Parent $destination
                if (-not (Test-Path -LiteralPath $parent)) {
                    New-Item -ItemType Directory -Path $parent -Force | Out-Null
                }
                Copy-Item -LiteralPath $file.FullName -Destination $destination
            }
        }
    }
    Write-Host "Copied $($toCopy.Count) updated program files. Reinstalling Slay patches locally..."

    # This does NOT run bootstrap_slay_runtime.ps1 and downloads no new runtime.
    $priorEnv = @{
        PYTHONNOUSERSITE = $env:PYTHONNOUSERSITE
        SKIP_REQUIREMENTS_UPDATE = $env:SKIP_REQUIREMENTS_UPDATE
        SC2PATH = $env:SC2PATH
        SLAY_PORTABLE_ROOT = $env:SLAY_PORTABLE_ROOT
        KIVY_HOME = $env:KIVY_HOME
    }
    try {
        $env:PYTHONNOUSERSITE = "1"
        $env:SKIP_REQUIREMENTS_UPDATE = "1"
        $env:SC2PATH = $sc2Root
        $env:SLAY_PORTABLE_ROOT = $targetRoot
        $env:KIVY_HOME = Join-Path $oldRuntime "KivyHome"
        $setupArgs = @(
            (Join-Path $targetRoot "Tools\setup_slay_launcher.py"),
            "--archipelago", $apRoot,
            "--sc2", $sc2Root,
            "--python", $python,
            "--portable-runtime",
            "--archipelago-ref", [string]$marker.archipelago_ref,
            "--non-interactive"
        )
        & $python @setupArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Local Slay installer exited with code $LASTEXITCODE. Source backup: $backupRoot"
        }
    }
    finally {
        foreach ($key in $priorEnv.Keys) {
            [Environment]::SetEnvironmentVariable($key, $priorEnv[$key], "Process")
        }
    }

    # The runtime revision is unchanged, and local install succeeded, so
    # let the lightweight launcher recognize this code-only version update.
    $marker.slay_version = $newVersion
    $marker | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $markerPath -Encoding UTF8

    Write-Host ""
    Write-Host "Update complete. Launch your EXISTING Dev14-folder SlayTheStarCraft.exe." -ForegroundColor Green
    Write-Host "No Download Data needed. Runtime, runs, configs and artwork were kept."
    Write-Host "Backup of overwritten program files: $backupRoot"
}
finally {
    if ($temporaryExtraction -and (Test-Path -LiteralPath $temporaryExtraction)) {
        Remove-Item -LiteralPath $temporaryExtraction -Recurse -Force -ErrorAction SilentlyContinue
    }
}
