[CmdletBinding()]
param(
    [switch]$ConsoleOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $csc)) {
    $csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $csc)) {
    throw '.NET Framework C# compiler not found.'
}

$build = Join-Path $projectRoot 'build'
$dist = Join-Path $projectRoot 'dist'
$icon = Join-Path $projectRoot 'installer\assets\hd2-heritage-icon.ico'
$manifest = Join-Path $projectRoot 'custom-mission-tool\app.manifest'
New-Item -ItemType Directory -Force $build, $dist | Out-Null
$nativeMenu = Join-Path $build 'HD2.CustomMenu.experimental.asi'
& python (Join-Path $projectRoot 'tools\build_native_custom_menu.py')
if ($LASTEXITCODE -ne 0) {
    throw "Native custom-menu build failed: $LASTEXITCODE"
}
if (-not (Test-Path -LiteralPath $nativeMenu)) {
    throw 'HD2.CustomMenu.experimental.asi is missing.'
}

$sources = @(
    (Join-Path $projectRoot 'custom-mission-tool\Program.cs'),
    (Join-Path $projectRoot 'custom-mission-tool\SimpleMainForm.cs'),
    (Join-Path $projectRoot 'custom-mission-tool\MissionPackageCore.cs'),
    (Join-Path $projectRoot 'custom-mission-tool\AssemblyInfo.cs'),
    (Join-Path $projectRoot 'installer\DtaArchive.cs')
)
$common = @(
    '/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu', '/optimize+',
    '/reference:System.dll', '/reference:System.Core.dll', '/reference:System.Drawing.dll',
    '/reference:System.Windows.Forms.dll', '/reference:System.Web.Extensions.dll',
    "/resource:$nativeMenu,HD2CustomMissionManager.CustomMenu.asi"
) + $sources

$consoleOut = Join-Path $build 'HD2CustomMissionManager.Console.exe'
& $csc (@('/target:exe', "/out:$consoleOut") + $common)
if ($LASTEXITCODE -ne 0) {
    throw "Custom mission manager validation build failed: $LASTEXITCODE"
}

if (-not $ConsoleOnly) {
    $finalOut = Join-Path $dist 'HD2-Custom-Mission-Manager.exe'
    & $csc (@(
        '/target:winexe', "/win32manifest:$manifest", "/win32icon:$icon",
        "/out:$finalOut"
    ) + $common)
    if ($LASTEXITCODE -ne 0) {
        throw "Custom mission manager build failed: $LASTEXITCODE"
    }
    $portable = Join-Path $dist 'CustomMissions'
    New-Item -ItemType Directory -Force $portable | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot 'custom-missions\README.md') `
        -Destination (Join-Path $portable 'README.md') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'custom-missions\mission.schema.json') `
        -Destination (Join-Path $portable 'mission.schema.json') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'custom-missions\_modele') `
        -Destination $portable -Recurse -Force
    Get-FileHash -LiteralPath $finalOut -Algorithm SHA256
}
