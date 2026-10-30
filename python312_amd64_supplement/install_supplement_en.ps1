# Append supplement wheels onto an existing venv of this Python version.
# Does not modify original requirements_lock_en.txt.
# Usage (from an environment directory that already has .venv):
#   powershell -ExecutionPolicy Bypass -File ..\..\python312_amd64_supplement\install_supplement_en.ps1
param(
  [string]$PythonExe = "C:\Python312\python.exe",
  [string]$VenvPython = ""
)
$ErrorActionPreference = "Stop"
$Supp = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $VenvPython) {
  $VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
}
if (-not (Test-Path $VenvPython)) {
  throw "venv python not found: $VenvPython ; create the original env first with install_offline_en.ps1"
}
$whl = Join-Path $Supp "packages_wheel"
$lock = Join-Path $Supp "requirements_supplement_en.txt"
if (Test-Path $lock) {
  & $VenvPython -m pip install --no-index --find-links $whl -r $lock
}
Write-Host "sdist packages are NOT installed by this script (unbuilt). See requirements_supplement_sdist_en.txt"
