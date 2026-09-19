param(
    [Parameter(Mandatory = $true)][string]$Game,
    [Parameter(Mandatory = $true)][string]$State,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$Harness = "build\HD2GuiTestHarness3.exe",
    [string]$MenuModule = "build\HD2.CustomMenu.experimental.asi"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$harnessPath = Join-Path $root $Harness
$statePath = Join-Path $root $State
$outputPath = Join-Path $root $OutputDirectory
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

function Invoke-Harness {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $harnessPath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Le banc GUI a échoué." }
}

function Move-And-Click {
    param([int]$X, [int]$Y, [string]$Capture)
    Invoke-Harness legacyrelmove --state $statePath --dx -5000 --dy -5000 --delay 100
    Invoke-Harness legacyrelmove --state $statePath --dx $X --dy $Y --delay 150
    Invoke-Harness legacydragclick --state $statePath --pulses 1 --delay 850 --output (Join-Path $outputPath $Capture)
}

Invoke-Harness launch --game $Game --state $statePath --timeout 30
Start-Sleep -Milliseconds 2500
Invoke-Harness key --state $statePath --name ESC --delay 1400
Invoke-Harness capture --state $statePath --output (Join-Path $outputPath "01-main.png") --delay 300

Move-And-Click 1250 635 "02-single-player.png"
Move-And-Click 1250 862 "03-categories.png"
Move-And-Click 1250 220 "04-community.png"
Move-And-Click 1250 967 "05-back-from-community.png"
