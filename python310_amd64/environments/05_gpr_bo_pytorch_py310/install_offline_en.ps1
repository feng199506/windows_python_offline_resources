# Offline venv install for 05_gpr_bo_pytorch_py310
# Run in Windows PowerShell. Does not use the system site-packages.
# Does not request Administrator rights. Stops on first error.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1
#   powershell -ExecutionPolicy Bypass -File .\install_offline_en.ps1 -PythonExe "C:\Python310\python.exe"

[CmdletBinding()]
param(
    [string]$PythonExe = "",
    [string]$VenvDir = ".\.venv"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Wheelhouse = Join-Path $Root "wheelhouse"
$Req = Join-Path $Root "requirements_lock_en.txt"

if (-not (Test-Path $Wheelhouse)) { throw "wheelhouse not found: $Wheelhouse" }
if (-not (Test-Path $Req)) { throw "lock file not found: $Req" }

if (-not $PythonExe) {
    $candidates = @(
        "C:\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:ProgramFiles\Python310\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $PythonExe = $c; break }
    }
}
if (-not $PythonExe) {
    throw "Python 3.10 x64 not found. Install python-3.10-amd64.exe first, then rerun with -PythonExe."
}

$ver = & $PythonExe -c "import sys,struct; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} {struct.calcsize(chr(80))*8} {sys.platform}')"
Write-Host "Using interpreter: $PythonExe ($ver)"
& $PythonExe -c "import sys,struct; assert sys.version_info[:2] == (3, 10), sys.version; assert struct.calcsize(chr(80))*8 == 64; assert sys.platform == 'win32'"

if (Test-Path $VenvDir) {
    throw "Refusing to reuse existing venv: $VenvDir. Delete it or pass -VenvDir."
}

Write-Host "Creating venv at $VenvDir"
& $PythonExe -m venv $VenvDir
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { throw "venv python missing: $VenvPy" }

Write-Host "Installing from local wheelhouse (no index, no network fallback)"
& $VenvPy -m pip install --no-index --find-links $Wheelhouse --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "Failed to install pip/setuptools/wheel from wheelhouse" }
& $VenvPy -m pip install --no-index --find-links $Wheelhouse -r $Req
if ($LASTEXITCODE -ne 0) { throw "Offline install failed. Not falling back to network." }

Write-Host "Install finished. Run: $VenvPy .\check_environment_en.py"
