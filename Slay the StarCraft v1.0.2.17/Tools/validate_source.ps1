$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
& python (Join-Path $Root "Payload\verify_release.py") --source-only
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
