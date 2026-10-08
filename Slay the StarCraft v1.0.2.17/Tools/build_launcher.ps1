$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $PSScriptRoot "slay_launcher_windows.go"
$Output = Join-Path $Root "SlayTheStarCraft.exe"

if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go is required to build SlayTheStarCraft.exe. Install Go and retry."
}

Push-Location $Root
try {
    & go build -trimpath -ldflags "-s -w -H=windowsgui" -o $Output $Source
    if ($LASTEXITCODE -ne 0) { throw "Go launcher build failed with exit code $LASTEXITCODE." }
    Write-Host "Built $Output"
}
finally {
    Pop-Location
}
