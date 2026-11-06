# Update an existing Slay installation from Downloads, from any directory.
# Detect the newest Slay Dev ZIP and the installed folder with Runtime.
[CmdletBinding()]
param([string]$ZipPath = "", [string]$ExistingInstall = "")
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$downloads = Join-Path $HOME "Downloads"
if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw "Downloads not found: $downloads" }
if (-not $ZipPath) {
    $latest = @(Get-ChildItem -LiteralPath $downloads -Filter '*.zip' -File |
        Where-Object { $_.Name -match 'Dev\d+' -and $_.Name -match 'Slay' } |
        Sort-Object LastWriteTime -Descending)
    if ($latest.Count -eq 0) { throw "No Slay Dev ZIP found in Downloads." }
    $ZipPath = $latest[0].FullName
}
$ZipPath = (Resolve-Path -LiteralPath $ZipPath).Path
if (-not $ExistingInstall) {
    $folders = @(Get-ChildItem -LiteralPath $downloads -Directory)
    foreach ($folder in @(Get-ChildItem -LiteralPath $downloads -Directory)) {
        $folders += @(Get-ChildItem -LiteralPath $folder.FullName -Directory -ErrorAction SilentlyContinue)
    }
    $candidates = @($folders | Where-Object {
        (Test-Path -LiteralPath (Join-Path $_.FullName 'Runtime\runtime.json') -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $_.FullName 'SlayTheStarCraft.exe') -PathType Leaf)
    } | Sort-Object FullName -Unique)
    if ($candidates.Count -eq 0) {
        throw "Cannot locate an installed Slay folder in Downloads. Provide -ExistingInstall 'C:\actual\folder'."
    }
    if ($candidates.Count -eq 1) { $ExistingInstall = $candidates[0].FullName }
    else {
        Write-Host "Select the installed folder to update (not the extracted new build):"
        for ($i=0; $i -lt $candidates.Count; $i++) {
            Write-Host "[$($i+1)] $($candidates[$i].FullName)"
        }
        $choice = Read-Host "Installation number"
        $index = 0
        if (-not [int]::TryParse($choice, [ref]$index) -or
            $index -lt 1 -or $index -gt $candidates.Count) { throw "Invalid installation selection." }
        $ExistingInstall = $candidates[$index-1].FullName
    }
}
$ExistingInstall = (Resolve-Path -LiteralPath $ExistingInstall).Path
Write-Host "Full new build: $ZipPath" -ForegroundColor Cyan
Write-Host "Existing install: $ExistingInstall" -ForegroundColor Cyan
$temp = Join-Path $env:TEMP ("SlayFullUpdate_" + [guid]::NewGuid().ToString('N'))
try {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $temp -Force
    $source = $temp
    if (-not (Test-Path -LiteralPath (Join-Path $source 'Tools\Update-ExistingSlay.ps1') -PathType Leaf)) {
        $options = @(Get-ChildItem -LiteralPath $temp -Directory | Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName 'Tools\Update-ExistingSlay.ps1') -PathType Leaf
        })
        if ($options.Count -ne 1) { throw "ZIP does not contain a complete Dev15-or-newer Slay build." }
        $source = $options[0].FullName
    }
    $updater = Join-Path $source 'Tools\Update-ExistingSlay.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $updater -ExistingInstall $ExistingInstall -NewBuild $source
    if ($LASTEXITCODE -ne 0) { throw "Full update failed with exit code $LASTEXITCODE" }
    Write-Host "Update complete. Slay was launched from $ExistingInstall" -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue }
}
