# Collect Windows GPU/CPU facts for choosing a CUDA stack later.
# Run on the target Windows machine. Writes hardware_report_en.json in this folder.
# Does not install drivers, CUDA, or Python packages.

[CmdletBinding()]
param(
    [string]$OutFile = ""
)
$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $OutFile) {
    $OutFile = Join-Path $Root "hardware_report_en.json"
}

function Get-Safe {
    param([scriptblock]$Block)
    try { & $Block } catch { $_.Exception.Message }
}

$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object {
    [ordered]@{
        Name = $_.Name
        AdapterRAM = $_.AdapterRAM
        DriverVersion = $_.DriverVersion
        DriverDate = [string]$_.DriverDate
        PNPDeviceID = $_.PNPDeviceID
        VideoProcessor = $_.VideoProcessor
    }
})

$nvidiaSmi = $null
$smiCmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($smiCmd) {
    $nvidiaSmi = & nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv
}

$dxdiagExists = Test-Path "$env:WINDIR\system32\dxdiag.exe"
$wsl = Get-Safe { wsl --status }

$report = [ordered]@{
    collected_at_local = [string](Get-Date)
    computer_name = $env:COMPUTERNAME
    os_caption = $os.Caption
    os_version = $os.Version
    os_architecture = $os.OSArchitecture
    cpu_name = $cpu.Name
    cpu_address_width = $cpu.AddressWidth
    gpus = $gpus
    nvidia_smi = $nvidiaSmi
    dxdiag_present = $dxdiagExists
    wsl_status = [string]$wsl
    python_on_path = [string](Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    note = "No credentials included. Use this report to pick one CUDA combination; do not download multiple GPU wheel sets."
}

$report | ConvertTo-Json -Depth 6 | Set-Content -Path $OutFile -Encoding UTF8
Write-Host "Wrote $OutFile"
if (-not $nvidiaSmi) {
    Write-Host "nvidia-smi not found. If this PC has an NVIDIA GPU, install/update the Game Ready or Studio driver first."
}
