param(
    [ValidateSet("host", "docker")]
    [string]$Mode = "host"
)

$ErrorActionPreference = "Stop"

if ($Mode -eq "host") {
    Set-Location (Join-Path $PSScriptRoot "..")
    python scripts\ingest_pipeline.py
    exit 0
}

Set-Location (Join-Path $PSScriptRoot "..\..")
docker compose --profile manual run --rm graph-init

