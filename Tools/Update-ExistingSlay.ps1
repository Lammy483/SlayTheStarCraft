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
    Write-Host "Keeping Runtime, Runs, user preferences and extracted SC2 artwork; replacing complete program folders."

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupRoot = Join-Path $oldRuntime ("UpdateBackups\" + $stamp)
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

    # Replace the COMPLETE source folders, including files we did not modify.
    # This avoids stale scripts from a previous build silently surviving.
    # The old folders are kept in Runtime/UpdateBackups for manual recovery.
    foreach ($folderName in @("Payload", "Tools")) {
        $oldFolder = Join-Path $targetRoot $folderName
        $newFolder = Join-Path $sourceRoot $folderName
        if (-not (Test-Path -LiteralPath $newFolder -PathType Container)) {
            throw "The new ZIP is missing the $folderName folder."
        }
        if (Test-Path -LiteralPath $oldFolder) {
            Move-Item -LiteralPath $oldFolder -Destination (Join-Path $backupRoot $folderName)
        }
        Copy-Item -LiteralPath $newFolder -Destination $oldFolder -Recurse -Force
    }

    # These copyrighted SC2 texture/audio assets are extracted locally, not
    # included in GitHub source builds. Restore ONLY those art files from the
    # previous installation; do not copy any old Python/Galaxy/catalog code.
    $oldArt = Join-Path $backupRoot "Payload\slay_assets"
    $newArt = Join-Path $targetRoot "Payload\slay_assets"
    if (Test-Path -LiteralPath $oldArt -PathType Container) {
        $assetExtensions = @('.png', '.jpg', '.jpeg', '.dds', '.tga', '.webp', '.wav', '.ogg', '.mp3')
        foreach ($file in (Get-ChildItem -LiteralPath $oldArt -Recurse -File)) {
            if (-not ($assetExtensions -contains $file.Extension.ToLowerInvariant())) { continue }
            $relativeArt = $file.FullName.Substring($oldArt.Length + 1)
            $destination = Join-Path $newArt $relativeArt
            if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
                $parent = Split-Path -Parent $destination
                if (-not (Test-Path -LiteralPath $parent)) {
                    New-Item -ItemType Directory -Force -Path $parent | Out-Null
                }
                Copy-Item -LiteralPath $file.FullName -Destination $destination
            }
        }
    }

    # Overwrite EVERY shipped top-level file, including release notes and
    # manifests, rather than maintaining an error-prone allowlist.
    $rootFiles = @(Get-ChildItem -LiteralPath $sourceRoot -File)
    foreach ($file in $rootFiles) {
        $destination = Join-Path $targetRoot $file.Name
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            Copy-Item -LiteralPath $destination -Destination (Join-Path $backupRoot $file.Name) -Force
        }
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }

    # Replace packaged Config defaults too, preserving only user-created
    # preferences and the installed SC2/Archipelago location. These are not
    # downloaded code and must never be reset by an update.
    $sourceConfig = Join-Path $sourceRoot "Config"
    if (Test-Path -LiteralPath $sourceConfig -PathType Container) {
        foreach ($file in (Get-ChildItem -LiteralPath $sourceConfig -Recurse -File)) {
            $relative = $file.FullName.Substring($sourceConfig.Length + 1)
            if (@('slay_preferences.ini', 'slay_install.json') -contains $relative) { continue }
            $destination = Join-Path (Join-Path $targetRoot "Config") $relative
            $parent = Split-Path -Parent $destination
            if (-not (Test-Path -LiteralPath $parent)) {
                New-Item -ItemType Directory -Force -Path $parent | Out-Null
            }
            Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
        }
    }
    Write-Host "Replaced complete Payload/Tools directories and $($rootFiles.Count) root files. Reinstalling Slay locally..."

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
    Write-Host "Update complete. Runtime, runs, configs and artwork were kept." -ForegroundColor Green
    Write-Host "Backup of overwritten program files: $backupRoot"
    # A successful update launches the already installed portable executable.
    Write-Host "Launching Slay the StarCraft..." -ForegroundColor Cyan
    Start-Process -FilePath (Join-Path $targetRoot "SlayTheStarCraft.exe") -WorkingDirectory $targetRoot
}
finally {
    if ($temporaryExtraction -and (Test-Path -LiteralPath $temporaryExtraction)) {
        Remove-Item -LiteralPath $temporaryExtraction -Recurse -Force -ErrorAction SilentlyContinue
    }
}
