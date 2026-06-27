$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

uv run xbrl-financial-compare sample --out sample/20260627/processed
uv run xbrl-financial-compare compare "sample/20260627/processed/*.json" --out sample/20260627
