$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) {throw 'Python 3.11 or newer is required'}
& .venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {throw 'Dependency installation failed'}
if (-not (Test-Path config.local.json)) {Copy-Item config.example.json config.local.json}
Write-Host 'Edit config.local.json, then run run.cmd. Closing the terminal stops services.'
