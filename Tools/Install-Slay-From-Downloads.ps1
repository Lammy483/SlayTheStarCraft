# Slay the StarCraft v1.3.0 update for the user's existing Dev24 installation.
# Put this script and SlayTheStarCraft_v1.3.0_Full_Windows.zip in Downloads.
# Do not ask for a folder or select an unrelated Slay installation.
[CmdletBinding()]
param()
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$downloads = Join-Path $env:USERPROFILE 'Downloads'
$zip = Join-Path $downloads 'SlayTheStarCraft_v1.3.0_Full_Windows.zip'
if (-not (Test-Path -LiteralPath $zip -PathType Leaf)) {
    throw "v1.3.0 complete Windows ZIP not found in Downloads: $zip"
}

$targets = @(
    (Join-Path $downloads 'SlayTheStarCraft_Dev24_Full_Windows'),
    (Join-Path (Join-Path $downloads 'SlayTheStarCraft_Dev24_Full_Windows') 'SlayTheStarCraft_Dev24'),
    (Join-Path (Join-Path $downloads 'SlayTheStarCraft_Dev24_Complete_Windows') 'SlayTheStarCraft_Dev24'),
    (Join-Path $downloads 'SlayTheStarCraft_Dev24')
)
$existing = $null
foreach ($candidate in $targets) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) { continue }
    if ((Test-Path -LiteralPath (Join-Path $candidate 'Runtime\runtime.json') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $candidate 'Config\slay_install.json') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $candidate 'SlayTheStarCraft.exe') -PathType Leaf)) {
        $existing = $candidate
        break
    }
}
if (-not $existing) {
    throw ('No initialized Dev24 installation found at these known Downloads paths:' +
        [Environment]::NewLine + ($targets -join [Environment]::NewLine))
}

$temp = Join-Path $env:TEMP ('Slay_v130_' + [guid]::NewGuid().ToString('N'))
try {
    Expand-Archive -LiteralPath $zip -DestinationPath $temp -Force
    $root = $temp
    if (-not (Test-Path -LiteralPath (Join-Path $root 'Tools\Update-ExistingSlay.ps1') -PathType Leaf)) {
        $folders = @(Get-ChildItem -LiteralPath $temp -Directory | Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName 'Tools\Update-ExistingSlay.ps1') -PathType Leaf
        })
        if ($folders.Count -ne 1) { throw 'Complete release ZIP is missing Tools\Update-ExistingSlay.ps1.' }
        $root = $folders[0].FullName
    }
    Write-Host "Installing Slay the StarCraft v1.3.0 into $existing" -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'Tools\Update-ExistingSlay.ps1') -ExistingInstall $existing -NewBuild $root
    if ($LASTEXITCODE -ne 0) { throw "v1.3.0 updater failed with code $LASTEXITCODE" }
}
finally {
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
