# Append signal-processing wheels onto original 03_signal_image_audio_py310 venv.
# Does not modify original requirements_lock_en.txt.
param(
  [string]$VenvPython = "",
  [string]$OriginalWheelhouse = "..\python310_amd64\environments\03_signal_image_audio_py310\wheelhouse"
)
$ErrorActionPreference = "Stop"
$Supp = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $VenvPython) {
  $VenvPython = Join-Path (Resolve-Path "..\python310_amd64\environments\03_signal_image_audio_py310").Path ".venv\Scripts\python.exe"
}
if (-not (Test-Path $VenvPython)) { throw "venv python not found: $VenvPython" }
$whl = Join-Path $Supp "packages_wheel"
$lock = Join-Path $Supp "requirements_supplement_en.txt"
& $VenvPython -m pip install --no-index --find-links $whl --find-links $OriginalWheelhouse -r $lock
Write-Host "sdist in packages_sdist_unbuilt is NOT installed (unbuilt)."
