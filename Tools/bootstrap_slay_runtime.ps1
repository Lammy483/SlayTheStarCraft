param(
    [string]$Sc2Root = "",
    [switch]$ElevatedResume,
    [switch]$NonInteractive,
    [string]$LogPath = "",
    [string]$StatusPath = "",
    [string]$ErrorPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0
$BootstrapScriptPath = $PSCommandPath

$PackageVersion = "1.1.0"
$RuntimeRevision = "lab-rat-r6"
$PythonVersion = "3.13.16"
$PythonArchiveName = "python-$PythonVersion-embed-amd64.zip"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/$PythonArchiveName"
$PythonSha256 = "97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297"

$ArchipelagoRef = "c311685"
$ArchipelagoUrl = "https://github.com/ArchipelagoMW/Archipelago/archive/$ArchipelagoRef.zip"
$Sc2DataApiUrl = "https://api.github.com/repos/archipelago-sc2/Archipelago-SC2-data/releases/tags/API4"
$PipUrl = "https://bootstrap.pypa.io/pip/pip.pyz"

$PortableRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ErrorPath) { $ErrorPath = Join-Path $PortableRoot "install-error.txt" }
$RuntimeRoot = Join-Path $PortableRoot "Runtime"
$DownloadsRoot = Join-Path $RuntimeRoot "Downloads"
$PythonRoot = Join-Path $RuntimeRoot "Python"
$ArchipelagoRoot = Join-Path $RuntimeRoot "Archipelago"
$PayloadRoot = Join-Path $PortableRoot "Payload"
$PythonExe = Join-Path $PythonRoot "python.exe"
$PipPyz = Join-Path $DownloadsRoot "pip.pyz"
$RuntimeMarker = Join-Path $RuntimeRoot "runtime.json"
$DependencyMarker = Join-Path $RuntimeRoot ".slay_dependencies_v4"
$CurrentStep = "Preparing data download"

function Set-Status([string]$Message) {
    if ($StatusPath) {
        try {
            $parent = Split-Path -Parent $StatusPath
            if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
            Set-Content -LiteralPath $StatusPath -Value $Message -Encoding UTF8
        } catch { }
    }
}

if ($LogPath) {
    try {
        $logParent = Split-Path -Parent $LogPath
        if ($logParent -and -not (Test-Path -LiteralPath $logParent)) { New-Item -ItemType Directory -Path $logParent -Force | Out-Null }
        Start-Transcript -Path $LogPath -Append | Out-Null
    } catch { }
}

function Write-Step([string]$Message) {
    $script:CurrentStep = $Message
    Set-Status $Message
    Write-Host ""
    Write-Host "== $Message ==" -ForegroundColor Cyan
}

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Assert-Writable([string]$Path, [string]$Label) {
    Ensure-Directory $Path
    $probe = Join-Path $Path (".slay_write_test_" + [Guid]::NewGuid().ToString("N"))
    try {
        [IO.File]::WriteAllText($probe, "test")
        Remove-Item -LiteralPath $probe -Force
        return $true
    }
    catch {
        Write-Host "$Label is not writable without elevation: $Path" -ForegroundColor Yellow
        return $false
    }
}

function Download-File([string]$Url, [string]$Destination, [int]$Attempts = 3) {
    Ensure-Directory (Split-Path -Parent $Destination)
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            Write-Host "Downloading $Url"
            Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination -Headers @{"User-Agent"="Slay-the-StarCraft/$PackageVersion"}
            if (-not (Test-Path -LiteralPath $Destination) -or (Get-Item -LiteralPath $Destination).Length -le 0) {
                throw "Download produced an empty file."
            }
            return
        }
        catch {
            if ($attempt -eq $Attempts) { throw }
            Write-Host "Download failed; retrying ($attempt/$Attempts)..." -ForegroundColor Yellow
            Start-Sleep -Seconds (2 * $attempt)
        }
    }
}

function Test-Sc2Root([string]$Candidate) {
    if (-not $Candidate) { return $false }
    try { $full = [IO.Path]::GetFullPath($Candidate) } catch { return $false }
    if (-not (Test-Path -LiteralPath $full -PathType Container)) { return $false }
    if (Test-Path -LiteralPath (Join-Path $full "Versions") -PathType Container) { return $true }
    if (Test-Path -LiteralPath (Join-Path $full "Support64\SC2Switcher_x64.exe") -PathType Leaf) { return $true }
    return $false
}

function Find-Sc2FromExecuteInfo {
    try {
        $docs = [Environment]::GetFolderPath("MyDocuments")
        $executeInfo = Join-Path $docs "StarCraft II\ExecuteInfo.txt"
        if (Test-Path -LiteralPath $executeInfo) {
            $text = Get-Content -LiteralPath $executeInfo -Raw
            $match = [regex]::Match($text, "=\s*(.+?)Versions", [Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if ($match.Success) {
                $candidate = $match.Groups[1].Value.Trim().Trim('"').TrimEnd('\','/')
                if (Test-Sc2Root $candidate) { return [IO.Path]::GetFullPath($candidate) }
            }
        }
    } catch { }
    return $null
}

function Select-Sc2Root {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select your StarCraft II installation folder (the folder containing Versions)."
    $dialog.ShowNewFolderButton = $false
    $result = $dialog.ShowDialog()
    if ($result -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $dialog.SelectedPath
}

function Resolve-Sc2Root([string]$Requested) {
    if (Test-Sc2Root $Requested) { return [IO.Path]::GetFullPath($Requested) }

    $executeInfoPath = Find-Sc2FromExecuteInfo
    if ($executeInfoPath) { return $executeInfoPath }

    $candidates = @()
    if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} "StarCraft II") }
    if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles "StarCraft II") }
    if ($env:SystemDrive) { $candidates += (Join-Path $env:SystemDrive "Games\StarCraft II") }
    foreach ($candidate in $candidates) {
        if (Test-Sc2Root $candidate) { return [IO.Path]::GetFullPath($candidate) }
    }

    $selected = Select-Sc2Root
    if (-not $selected -or -not (Test-Sc2Root $selected)) {
        throw "A valid StarCraft II installation was not selected. Select the folder that contains the Versions directory."
    }
    return [IO.Path]::GetFullPath($selected)
}

function Relaunch-Elevated([string]$ResolvedSc2Root) {
    Set-Status "Waiting for administrator permission to update StarCraft II"
    Write-Host "StarCraft II needs administrator permission for Slay/AP map and mod files. Requesting elevation..." -ForegroundColor Yellow
    if (-not $BootstrapScriptPath) { throw "Could not determine the data-download script path for elevation." }
    $parts = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ('"' + $BootstrapScriptPath + '"'),
        "-Sc2Root", ('"' + $ResolvedSc2Root + '"'),
        "-ElevatedResume"
    )
    if ($NonInteractive) { $parts += "-NonInteractive" }
    if ($LogPath) { $parts += @("-LogPath", ('"' + $LogPath + '"')) }
    if ($StatusPath) { $parts += @("-StatusPath", ('"' + $StatusPath + '"')) }
    if ($ErrorPath) { $parts += @("-ErrorPath", ('"' + $ErrorPath + '"')) }
    $args = ($parts -join " ")
    if ($LogPath) { try { Stop-Transcript | Out-Null } catch { } }
    $proc = Start-Process -FilePath "powershell.exe" -Verb RunAs -WindowStyle Hidden -ArgumentList $args -Wait -PassThru
    exit $proc.ExitCode
}

function Ensure-PortablePython {
    $versionMarker = Join-Path $PythonRoot ".slay_python_version"
    if ((Test-Path -LiteralPath $PythonExe) -and (Test-Path -LiteralPath $versionMarker)) {
        $installed = (Get-Content -LiteralPath $versionMarker -Raw).Trim()
        if ($installed -eq $PythonVersion) {
            Write-Host "Portable Python $PythonVersion already present."
            return
        }
    }

    Write-Step "Downloading private Python runtime"
    if (Test-Path -LiteralPath $PythonRoot) { Remove-Item -LiteralPath $PythonRoot -Recurse -Force }
    if (Test-Path -LiteralPath $DependencyMarker) { Remove-Item -LiteralPath $DependencyMarker -Force }
    Ensure-Directory $PythonRoot
    $archive = Join-Path $DownloadsRoot $PythonArchiveName
    Download-File $PythonUrl $archive
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    if ($actualHash -ne $PythonSha256) {
        throw "Python archive SHA-256 mismatch. Expected $PythonSha256 but got $actualHash."
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $PythonRoot -Force

    $pth = Get-ChildItem -LiteralPath $PythonRoot -Filter "python*._pth" | Select-Object -First 1
    if (-not $pth) { throw "Python embedded runtime did not contain a python*._pth file." }
    @(
        "python313.zip",
        ".",
        "Lib\site-packages",
        "..\Archipelago",
        "import site"
    ) | Set-Content -LiteralPath $pth.FullName -Encoding ASCII
    Ensure-Directory (Join-Path $PythonRoot "Lib\site-packages")
    Set-Content -LiteralPath $versionMarker -Value $PythonVersion -Encoding ASCII

    & $PythonExe -c "import sys; assert sys.version_info[:2] == (3, 13); print(sys.version)"
    if ($LASTEXITCODE -ne 0) { throw "Portable Python failed its smoke test." }
}

function Limit-ArchipelagoToSc2AtRoot([string]$SourceRoot) {
    $worldsRoot = Join-Path $SourceRoot "worlds"
    if (-not (Test-Path -LiteralPath (Join-Path $worldsRoot "sc2\client.py"))) {
        throw "Archipelago source is missing worlds\sc2\client.py."
    }
    $keep = @("sc2", "generic")
    Get-ChildItem -LiteralPath $worldsRoot -Directory | ForEach-Object {
        if ((-not $_.Name.StartsWith("_")) -and (-not ($keep -contains $_.Name))) {
            Remove-Item -LiteralPath $_.FullName -Recurse -Force
        }
    }
}

function Ensure-ArchipelagoSource {
    $refMarker = Join-Path $ArchipelagoRoot ".slay_archipelago_ref"
    if ((Test-Path -LiteralPath (Join-Path $ArchipelagoRoot "Generate.py")) -and (Test-Path -LiteralPath $refMarker)) {
        $installedRef = (Get-Content -LiteralPath $refMarker -Raw).Trim()
        if ($installedRef -eq $ArchipelagoRef) {
            Write-Host "Pinned Archipelago source $ArchipelagoRef already present."
            return
        }
    }

    Write-Step "Downloading private Archipelago runtime"
    $archive = Join-Path $DownloadsRoot ("Archipelago-" + $ArchipelagoRef + ".zip")
    Download-File $ArchipelagoUrl $archive

    # PowerShell 5.1 Expand-Archive still uses legacy MAX_PATH handling. Extract
    # under the user's short temp path first so a descriptive Slay folder name
    # cannot make Archipelago's nested source paths exceed 260 characters.
    $tempBase = [IO.Path]::GetTempPath()
    $extractRoot = Join-Path $tempBase ("SlayAP-" + $ArchipelagoRef + "-" + $PID)
    if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
    Ensure-Directory $extractRoot
    try {
        Expand-Archive -LiteralPath $archive -DestinationPath $extractRoot -Force
        $sourceDir = Get-ChildItem -LiteralPath $extractRoot -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "Generate.py") } | Select-Object -First 1
        if (-not $sourceDir) { throw "Downloaded Archipelago archive did not contain Generate.py." }

        # Remove unrelated worlds before moving the source into the portable
        # Runtime folder. This both keeps Slay small and minimizes final paths.
        Limit-ArchipelagoToSc2AtRoot $sourceDir.FullName

        if (Test-Path -LiteralPath $ArchipelagoRoot) { Remove-Item -LiteralPath $ArchipelagoRoot -Recurse -Force }
        Move-Item -LiteralPath $sourceDir.FullName -Destination $ArchipelagoRoot
    }
    finally {
        if (Test-Path -LiteralPath $extractRoot) {
            try { Remove-Item -LiteralPath $extractRoot -Recurse -Force } catch { }
        }
    }
    Set-Content -LiteralPath $refMarker -Value $ArchipelagoRef -Encoding ASCII
    if (Test-Path -LiteralPath $DependencyMarker) { Remove-Item -LiteralPath $DependencyMarker -Force }
}

function Limit-ArchipelagoToSc2 {
    Limit-ArchipelagoToSc2AtRoot $ArchipelagoRoot
}

function Assert-ArchipelagoVersion {
    $utils = Join-Path $ArchipelagoRoot "Utils.py"
    if (-not (Test-Path -LiteralPath $utils)) { throw "Archipelago Utils.py is missing." }
    $text = Get-Content -LiteralPath $utils -Raw
    if ($text -notmatch '__version__\s*=\s*["'']0\.6\.8["'']') {
        throw "The pinned Archipelago snapshot is not version 0.6.8. Refusing to patch an unexpected source layout."
    }
}

function Make-RequirementsGitless {
    $requirementFiles = @((Join-Path $ArchipelagoRoot "requirements.txt"), (Join-Path $ArchipelagoRoot "setup_constraints.txt"))
    $worldsRoot = Join-Path $ArchipelagoRoot "worlds"
    if (Test-Path -LiteralPath $worldsRoot) {
        $requirementFiles += @(Get-ChildItem -LiteralPath $worldsRoot -Filter "requirements.txt" -File -Recurse | ForEach-Object { $_.FullName })
    }
    $requirementFiles = @($requirementFiles | Sort-Object -Unique)
    foreach ($requirements in $requirementFiles) {
        if (-not (Test-Path -LiteralPath $requirements)) { continue }
        $text = Get-Content -LiteralPath $requirements -Raw
        $text = [regex]::Replace(
            $text,
            '(?im)^(\s*[A-Za-z0-9_.-]+(?:\[[^\]]+\])?\s*@\s*)git\+https://github\.com/([^/\s]+)/([^@\s]+)@([^#\s]+)(?:#[^\r\n]*)?\s*$',
            '$1https://github.com/$2/$3/archive/$4.zip'
        )
        Set-Content -LiteralPath $requirements -Value $text -Encoding ASCII
        $rewritten = Get-Content -LiteralPath $requirements -Raw
        if ($rewritten -match 'git\+') {
            throw "A retained Archipelago requirement still needs Git after conversion: $requirements. Slay intentionally does not install Git globally."
        }
    }
}

function Ensure-PythonPackages {
    $dependencySignature = "$PythonVersion|$ArchipelagoRef|kivy-deps-sdl2-0.8.0|kivy-deps-glew-0.3.1|native-launcher-v2|all-retained-world-requirements-v3-direct-mpyq"
    if (Test-Path -LiteralPath $DependencyMarker) {
        $installedSignature = (Get-Content -LiteralPath $DependencyMarker -Raw).Trim()
        if ($installedSignature -eq $dependencySignature) {
            Write-Host "Private Python dependencies already present."
            return
        }
    }

    Write-Step "Downloading private Python packages"
    if (-not (Test-Path -LiteralPath $PipPyz)) { Download-File $PipUrl $PipPyz }

    $oldNoUser = $env:PYTHONNOUSERSITE
    $oldPipCheck = $env:PIP_DISABLE_PIP_VERSION_CHECK
    $oldPipWarn = $env:PIP_NO_WARN_SCRIPT_LOCATION
    $env:PYTHONNOUSERSITE = "1"
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    $env:PIP_NO_WARN_SCRIPT_LOCATION = "1"
    try {
        & $PythonExe $PipPyz install --upgrade --only-binary=:all: "pip<27" "setuptools>=75,<81" wheel
        if ($LASTEXITCODE -ne 0) { throw "Could not bootstrap pip/setuptools into the private runtime." }

        $constraints = Join-Path $ArchipelagoRoot "setup_constraints.txt"
        if (-not (Test-Path -LiteralPath $constraints)) {
            $constraints = Join-Path $PSScriptRoot "archipelago_setup_constraints.txt"
            if (-not (Test-Path -LiteralPath $constraints)) {
                throw "Neither Archipelago nor Slay supplied setup constraints."
            }
            Write-Host "Pinned Archipelago snapshot predates setup_constraints.txt; using Slay's bundled compatibility constraint." -ForegroundColor DarkGray
        }

        $requirementFiles = @((Join-Path $ArchipelagoRoot "requirements.txt"))
        $worldsRoot = Join-Path $ArchipelagoRoot "worlds"
        if (Test-Path -LiteralPath $worldsRoot) {
            $requirementFiles += @(Get-ChildItem -LiteralPath $worldsRoot -Filter "requirements.txt" -File -Recurse | ForEach-Object { $_.FullName })
        }
        $requirementFiles = @($requirementFiles | Sort-Object -Unique)

        $reqIndex = 0
        foreach ($requirementsPath in $requirementFiles) {
            $reqIndex++
            $relativeLabel = $requirementsPath
            if ($requirementsPath.StartsWith($ArchipelagoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                $relativeLabel = $requirementsPath.Substring($ArchipelagoRoot.Length).TrimStart('\','/')
            }
            Write-Host "Installing retained Archipelago requirements: $relativeLabel"
            $lines = @(Get-Content -LiteralPath $requirementsPath)
            $directArchiveLines = @($lines | Where-Object { $_ -match '^\s*[^#].*\s@\s*https://github\.com/.+/archive/.+\.zip\s*$' })
            foreach ($directLine in $directArchiveLines) {
                Write-Host "Installing direct archive requirement: $directLine"
                & $PythonExe -m pip install --no-deps ([string]$directLine)
                if ($LASTEXITCODE -ne 0) { throw "Could not install direct archive requirement from ${relativeLabel}: $directLine" }
            }

            $sourceOnlyLines = @($lines | Where-Object { $_ -match '^\s*mpyq(?:\s*[<>=!~].*)?(?:\s*;.*)?\s*$' })
            foreach ($sourceLine in $sourceOnlyLines) {
                # mpyq 0.2.5 is a single pure-Python module from 2014 and PyPI only
                # publishes an sdist. Building that legacy sdist under modern embedded
                # Python/setuptools is unnecessarily fragile, so install the module
                # directly instead. The pinned AP source only needs `import mpyq`.
                Write-Host "Installing pure-Python mpyq module directly: $sourceLine"
                $sitePackages = Join-Path $PythonRoot "Lib\site-packages"
                Ensure-Directory $sitePackages
                $mpyqDestination = Join-Path $sitePackages "mpyq.py"
                try {
                    Download-File "https://raw.githubusercontent.com/eagleflo/mpyq/master/mpyq.py" $mpyqDestination
                    & $PythonExe -c "import mpyq; assert getattr(mpyq, '__version__', '') == '0.2.5'; print('mpyq direct module passed', mpyq.__version__)"
                    if ($LASTEXITCODE -ne 0) { throw "Direct mpyq module validation failed." }
                }
                catch {
                    # Some networks block raw.githubusercontent.com even when PyPI is reachable.
                    # Fall back to pip's legacy source path rather than failing solely on that host.
                    Write-Host "Direct mpyq module download failed; trying legacy pip source install." -ForegroundColor Yellow
                    if (Test-Path -LiteralPath $mpyqDestination) { Remove-Item -LiteralPath $mpyqDestination -Force -ErrorAction SilentlyContinue }
                    & $PythonExe -m pip install --no-deps --no-binary=:all: --no-build-isolation -c $constraints ([string]$sourceLine)
                    if ($LASTEXITCODE -ne 0) { throw "Could not install mpyq required by ${relativeLabel}: $sourceLine" }
                }
            }

            $binaryLines = @($lines | Where-Object {
                $_ -notmatch '^\s*[^#].*\s@\s*https://github\.com/.+/archive/.+\.zip\s*$' -and
                $_ -notmatch '^\s*mpyq(?:\s*[<>=!~].*)?(?:\s*;.*)?\s*$'
            })
            if (@($binaryLines | Where-Object { $_ -match '^\s*[^#]' }).Count -gt 0) {
                $binaryRequirements = Join-Path $DownloadsRoot ("archipelago-binary-requirements-" + $reqIndex + ".txt")
                $binaryLines | Set-Content -LiteralPath $binaryRequirements -Encoding ASCII
                & $PythonExe -m pip install --only-binary=:all: -r $binaryRequirements -c $constraints
                if ($LASTEXITCODE -ne 0) { throw "Could not install retained Archipelago requirements from prebuilt wheels: $relativeLabel" }
            }
        }

        & $PythonExe -m pip install --only-binary=:all: -c $constraints "kivy_deps.sdl2==0.8.0" "kivy_deps.glew==0.3.1" "requests>=2.32,<3"
        if ($LASTEXITCODE -ne 0) { throw "Could not install the Windows GUI/runtime dependencies from prebuilt wheels." }

        Set-Content -LiteralPath $DependencyMarker -Value $dependencySignature -Encoding ASCII
    }
    finally {
        $env:PYTHONNOUSERSITE = $oldNoUser
        $env:PIP_DISABLE_PIP_VERSION_CHECK = $oldPipCheck
        $env:PIP_NO_WARN_SCRIPT_LOCATION = $oldPipWarn
    }
}

function Test-PrivateRuntime {
    Write-Step "Validating the private runtime"
    $oldNoUser = $env:PYTHONNOUSERSITE
    $oldSkip = $env:SKIP_REQUIREMENTS_UPDATE
    $oldKivyHome = $env:KIVY_HOME
    $env:PYTHONNOUSERSITE = "1"
    $env:SKIP_REQUIREMENTS_UPDATE = "1"
    $env:KIVY_HOME = Join-Path $RuntimeRoot "KivyHome"
    Ensure-Directory $env:KIVY_HOME
    try {
        $smoke = @'
import os, sys
from pathlib import Path
from importlib import metadata
root = Path.cwd()
assert (root / "Generate.py").is_file()
assert sys.version_info[:3] == (3, 13, 16), sys.version
import yaml, websockets, requests, kivy, loguru, mpyq
assert metadata.version("kivy-deps.sdl2") == "0.8.0"
assert metadata.version("kivy-deps.glew") == "0.3.1"
assert metadata.version("kivymd").startswith("2.0.1")
import MultiServer
from worlds.sc2 import client as sc2_client
print("private runtime imports passed", sys.version)
'@
        $smokePath = Join-Path $RuntimeRoot "private_runtime_smoke.py"
        Set-Content -LiteralPath $smokePath -Value $smoke -Encoding ASCII
        Push-Location $ArchipelagoRoot
        try {
            & $PythonExe $smokePath
            if ($LASTEXITCODE -ne 0) { throw "Private Python/Archipelago runtime import smoke test failed." }
        }
        finally {
            Pop-Location
            Remove-Item -LiteralPath $smokePath -Force -ErrorAction SilentlyContinue
        }
    }
    finally {
        $env:PYTHONNOUSERSITE = $oldNoUser
        $env:SKIP_REQUIREMENTS_UPDATE = $oldSkip
        $env:KIVY_HOME = $oldKivyHome
    }
}

function Test-InstalledSc2DataApi4([string]$ResolvedSc2Root) {
    $metadataPath = Join-Path $ResolvedSc2Root "ArchipelagoSC2Metadata.txt"
    $triggerPath = Join-Path $ResolvedSc2Root "Mods\ArchipelagoTriggers.SC2Mod\Base.SC2Data\LibABFE498B.galaxy"
    if (-not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) { return $false }
    if (-not (Test-Path -LiteralPath $triggerPath -PathType Leaf)) { return $false }
    try {
        $metadataText = Get-Content -LiteralPath $metadataPath -Raw
        return $metadataText.Contains("'tag_name': 'API4'") -or $metadataText.Contains('"tag_name": "API4"')
    }
    catch { return $false }
}

function Install-Sc2ArchipelagoData([string]$ResolvedSc2Root) {
    if (Test-InstalledSc2DataApi4 $ResolvedSc2Root) {
        Write-Step "Checking Archipelago StarCraft II maps and mods"
        Write-Host "Official Archipelago SC2 API4 data is already installed; skipping the large SC2 data download."
        return
    }
    Write-Step "Downloading Archipelago StarCraft II maps and mods"
    $metadataJson = Join-Path $DownloadsRoot "Archipelago-SC2-data-API4.json"
    Download-File $Sc2DataApiUrl $metadataJson
    $release = Get-Content -LiteralPath $metadataJson -Raw | ConvertFrom-Json
    if (-not $release.assets -or $release.assets.Count -lt 1) { throw "The API4 SC2 data release did not contain any assets." }

    $asset = @($release.assets)[0]
    if (-not $asset.browser_download_url) { throw "Could not find the SC2 data release download URL." }
    Write-Host ("SC2 data asset: " + $asset.name)
    $dataZip = Join-Path $DownloadsRoot "Archipelago-SC2-data-API4.zip"
    Download-File ([string]$asset.browser_download_url) $dataZip

    if ($asset.PSObject.Properties.Name -contains "digest" -and $asset.digest) {
        $digestText = [string]$asset.digest
        if ($digestText -match '^sha256:([0-9A-Fa-f]{64})$') {
            $expected = $Matches[1].ToLowerInvariant()
            $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $dataZip).Hash.ToLowerInvariant()
            if ($actual -ne $expected) { throw "SC2 data archive SHA-256 mismatch." }
        }
    }

    & $PythonExe (Join-Path $PSScriptRoot "install_sc2_data.py") --sc2-root $ResolvedSc2Root --metadata-json $metadataJson --data-zip $dataZip
    if ($LASTEXITCODE -ne 0) { throw "Archipelago SC2 map/mod installation failed." }
}

try {
    if ([Environment]::Is64BitOperatingSystem -ne $true) {
        throw "Slay the StarCraft data download currently requires 64-bit Windows."
    }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Set-Status "Preparing data download"
    if ($env:SLAY_PORTABLE_BUILD -eq "1") {
        Write-Host "Slay the StarCraft v$PackageVersion portable release runtime builder" -ForegroundColor Green
        Write-Host "Building the complete private Windows runtime and bundled SC2 payload."
    }
    else {
        Write-Host "Slay the StarCraft v$PackageVersion data download" -ForegroundColor Green
        Write-Host "Large runtime files are downloaded privately into this folder; AP maps/mods are copied into the existing StarCraft II folder."
    }
    Write-Host "No system Python, PATH changes, or global Python packages are used."

    if (-not (Assert-Writable $PortableRoot "Slay folder")) {
        throw "Move/extract the Slay folder to a writable location such as Desktop or Documents, then click Download Data again."
    }

    $ResolvedSc2Root = Resolve-Sc2Root $Sc2Root
    Write-Host "StarCraft II: $ResolvedSc2Root"

    Ensure-Directory $RuntimeRoot
    Ensure-Directory $DownloadsRoot
    Ensure-Directory (Join-Path $PortableRoot "Runs")
    Ensure-Directory (Join-Path $PortableRoot "Config")

    Ensure-PortablePython
    Ensure-ArchipelagoSource
    Assert-ArchipelagoVersion
    Limit-ArchipelagoToSc2
    Make-RequirementsGitless
    Ensure-PythonPackages
    Test-PrivateRuntime

    if (-not (Assert-Writable $ResolvedSc2Root "StarCraft II folder")) {
        if (-not $ElevatedResume) { Relaunch-Elevated $ResolvedSc2Root }
        throw "The StarCraft II directory is still not writable after elevation."
    }

    Install-Sc2ArchipelagoData $ResolvedSc2Root

    Write-Step "Applying Slay patches"
    $env:PYTHONNOUSERSITE = "1"
    $env:SKIP_REQUIREMENTS_UPDATE = "1"
    $env:SC2PATH = $ResolvedSc2Root
    $setupLogPath = Join-Path $RuntimeRoot "Logs\slay-setup.log"
    if (Test-Path -LiteralPath $setupLogPath) { Remove-Item -LiteralPath $setupLogPath -Force -ErrorAction SilentlyContinue }

    $savedErrorActionPreference = $ErrorActionPreference
    $setupExitCode = 1
    try {
        $ErrorActionPreference = "Continue"
        & $PythonExe (Join-Path $PSScriptRoot "setup_slay_launcher.py") --archipelago $ArchipelagoRoot --sc2 $ResolvedSc2Root --python $PythonExe --portable-runtime --archipelago-ref $ArchipelagoRef --non-interactive *>> $setupLogPath
        $setupExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
    }
    if ($setupExitCode -ne 0) {
        Write-Host "Slay setup helper log: $setupLogPath" -ForegroundColor Yellow
        if (Test-Path -LiteralPath $setupLogPath) {
            Write-Host "Last setup helper output:" -ForegroundColor Yellow
            Get-Content -LiteralPath $setupLogPath -Tail 20 | ForEach-Object { Write-Host $_ }
        }
        throw "Slay setup failed with exit code $setupExitCode. See $setupLogPath."
    }

    Write-Step "Validating the final Slay launcher entry"
    $oldEntrySmoke = $env:SLAY_ENTRY_SMOKE
    $oldLauncherMode = $env:SLAY_LAUNCHER_MODE
    $oldPortableRoot = $env:SLAY_PORTABLE_ROOT
    $oldManagedData = $env:SLAY_MANAGED_SC2_DATA
    $oldKivyHome2 = $env:KIVY_HOME
    try {
        $env:SLAY_ENTRY_SMOKE = "1"
        $env:SLAY_LAUNCHER_MODE = "1"
        $env:SLAY_PORTABLE_ROOT = $PortableRoot
        $env:SLAY_MANAGED_SC2_DATA = "1"
        $env:KIVY_HOME = Join-Path $RuntimeRoot "KivyHome"
        Push-Location $ArchipelagoRoot
        try {
            & $PythonExe (Join-Path $ArchipelagoRoot "SlayTheStarCraftLauncher.py")
            if ($LASTEXITCODE -ne 0) { throw "Final Slay launcher entry smoke test failed." }
        }
        finally { Pop-Location }
    }
    finally {
        $env:SLAY_ENTRY_SMOKE = $oldEntrySmoke
        $env:SLAY_LAUNCHER_MODE = $oldLauncherMode
        $env:SLAY_PORTABLE_ROOT = $oldPortableRoot
        $env:SLAY_MANAGED_SC2_DATA = $oldManagedData
        $env:KIVY_HOME = $oldKivyHome2
    }

    $runtimeInfo = [ordered]@{
        format_version = 1
        slay_version = $PackageVersion
        runtime_revision = $RuntimeRevision
        python_version = $PythonVersion
        archipelago_ref = $ArchipelagoRef
        sc2_data_api = "API4"
        installed_utc = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json
    Set-Content -LiteralPath $RuntimeMarker -Value $runtimeInfo -Encoding UTF8

    if (Test-Path -LiteralPath $DownloadsRoot) {
        Remove-Item -LiteralPath $DownloadsRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Set-Status "Data download complete"
    Write-Host "Data download complete." -ForegroundColor Green
    Write-Host "Return to SlayTheStarCraft.exe and click Launch Slay."
    if ($LogPath) { try { Stop-Transcript | Out-Null } catch { } }
    exit 0
}
catch {
    Write-Host ""
    $failureMessage = "Data download failed during '" + $CurrentStep + "': " + $_.Exception.Message
    Set-Status $failureMessage
    if ($ErrorPath) {
        try {
            $errorParent = Split-Path -Parent $ErrorPath
            if ($errorParent -and -not (Test-Path -LiteralPath $errorParent)) { New-Item -ItemType Directory -Path $errorParent -Force | Out-Null }
            Set-Content -LiteralPath $ErrorPath -Value $failureMessage -Encoding UTF8
        } catch { }
    }
    Write-Host ("ERROR: " + $failureMessage) -ForegroundColor Red
    if ($_.ScriptStackTrace) { Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray }
    Write-Host ""
    if ($LogPath) { try { Stop-Transcript | Out-Null } catch { } }
    if (-not $NonInteractive) { Read-Host "Press Enter to close" }
    exit 1
}
