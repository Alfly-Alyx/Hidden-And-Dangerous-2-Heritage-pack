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

& (Join-Path $projectRoot 'build-custom-mission-manager.ps1')
& (Join-Path $projectRoot 'build-network-bridge.ps1')

$build = Join-Path $projectRoot 'build'
$dist = Join-Path $projectRoot 'dist'
$guide = Join-Path $projectRoot 'output\pdf\HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf'
$report = Join-Path $projectRoot 'output\pdf\HD2-Rapport-des-Decouvertes.pdf'
$guideEn = Join-Path $projectRoot 'output\pdf\HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf'
$reportEn = Join-Path $projectRoot 'output\pdf\HD2-Discovery-Report-EN.pdf'
$icon = Join-Path $projectRoot 'installer\assets\hd2-heritage-icon.ico'
$widescreen = Join-Path $projectRoot 'installer\assets\HiddenandDangerous2.WidescreenFix.zip'
$missionManager = Join-Path $projectRoot 'dist\HD2-Custom-Mission-Manager.exe'
$missionManagerHash = Join-Path $build 'HD2-Custom-Mission-Manager.sha256'
$masterBridge = Join-Path $build 'HD2-Master-Bridge.exe'
$masterBridgeHash = Join-Path $build 'HD2-Master-Bridge.sha256'
$customMissionReadme = Join-Path $projectRoot 'custom-missions\README.md'
$customMissionSchema = Join-Path $projectRoot 'custom-missions\mission.schema.json'
$customMissionTemplate = Join-Path $projectRoot 'custom-missions\_modele\mission.json'
$customMissionTemplateReadme = Join-Path $projectRoot `
    'custom-missions\_modele\payload\Missions\MaMission\LISEZ_MOI.txt'
foreach ($customMissionResource in @(
    $missionManager,
    $customMissionReadme,
    $customMissionSchema,
    $customMissionTemplate,
    $customMissionTemplateReadme
)) {
    if (-not (Test-Path -LiteralPath $customMissionResource)) {
        throw "The custom mission manager resource is missing: $customMissionResource"
    }
}
$managerSha256 = (Get-FileHash -LiteralPath $missionManager -Algorithm SHA256).Hash
[IO.File]::WriteAllText(
    $missionManagerHash, $managerSha256 + "`n", [Text.Encoding]::ASCII)
$bridgeSha256 = (Get-FileHash -LiteralPath $masterBridge -Algorithm SHA256).Hash
[IO.File]::WriteAllText(
    $masterBridgeHash, $bridgeSha256 + "`n", [Text.Encoding]::ASCII)
foreach ($pdf in @($guide, $report, $guideEn, $reportEn)) {
    if (-not (Test-Path -LiteralPath $pdf)) {
        throw "The final PDF must be generated before building the installer: $pdf"
    }
}
$pdfCommon = Join-Path $projectRoot 'tools\pdf\pdf_common.py'
$playerSource = Join-Path $projectRoot 'tools\pdf\build_player_guide.py'
$reportSource = Join-Path $projectRoot 'tools\pdf\build_report.py'
$playerSourceEn = Join-Path $projectRoot 'tools\pdf\build_player_guide_en.py'
$reportSourceEn = Join-Path $projectRoot 'tools\pdf\build_report_en.py'
foreach ($pair in @(
    @($guide, $pdfCommon, $playerSource),
    @($report, $pdfCommon, $reportSource),
    @($guideEn, $pdfCommon, $playerSourceEn),
    @($reportEn, $pdfCommon, $reportSourceEn)
)) {
    $outputInfo = Get-Item -LiteralPath $pair[0]
    $latestSource = Get-Item -LiteralPath $pair[1], $pair[2] |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if ($outputInfo.LastWriteTimeUtc -lt $latestSource.LastWriteTimeUtc) {
        throw "PDF output is older than its source: $($outputInfo.Name). Regenerate and verify it first."
    }
}
if (-not (Test-Path -LiteralPath $icon)) {
    throw 'The Windows icon is missing.'
}
if (-not (Test-Path -LiteralPath $widescreen)) {
    throw 'The embedded widescreen fix is missing.'
}
New-Item -ItemType Directory -Force $build, $dist | Out-Null
$sources = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'installer') -Filter '*.cs' |
    ForEach-Object FullName)
$references = @(
    '/reference:System.dll',
    '/reference:System.Core.dll',
    '/reference:System.Drawing.dll',
    '/reference:System.Windows.Forms.dll',
    '/reference:System.Management.dll',
    '/reference:System.ServiceProcess.dll',
    '/reference:System.IO.Compression.dll',
    '/reference:System.IO.Compression.FileSystem.dll'
)
$common = @('/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu', '/optimize+') +
    $references + @(
        "/resource:$guide,HD2CommunityInstaller.GuideJoueur.pdf",
        "/resource:$report,HD2CommunityInstaller.RapportDecouvertes.pdf",
        "/resource:$guideEn,HD2CommunityInstaller.PlayerGuideEN.pdf",
        "/resource:$reportEn,HD2CommunityInstaller.DiscoveryReportEN.pdf",
        "/resource:$widescreen,HD2CommunityInstaller.WidescreenFix.zip",
        "/resource:$missionManager,HD2CommunityInstaller.CustomMissionManager.exe",
        "/resource:$missionManagerHash,HD2CommunityInstaller.CustomMissionManager.sha256",
        "/resource:$masterBridge,HD2CommunityInstaller.MasterBridge.exe",
        "/resource:$masterBridgeHash,HD2CommunityInstaller.MasterBridge.sha256",
        "/resource:$customMissionReadme,HD2CommunityInstaller.CustomMissions.Readme",
        "/resource:$customMissionSchema,HD2CommunityInstaller.CustomMissions.Schema",
        "/resource:$customMissionTemplate,HD2CommunityInstaller.CustomMissions.TemplateManifest",
        "/resource:$customMissionTemplateReadme,HD2CommunityInstaller.CustomMissions.TemplateReadme"
    ) + $sources

$consoleOut = Join-Path $build 'HD2CommunityInstaller.Console.exe'
$consoleArgs = @('/target:exe', "/out:$consoleOut") + $common
& $csc $consoleArgs
if ($LASTEXITCODE -ne 0) {
    throw "Console validation build failed: $LASTEXITCODE"
}

if (-not $ConsoleOnly) {
    $finalOut = Join-Path $dist 'H-D2-Heritage-Pack-Setup.exe'
    $manifest = Join-Path $projectRoot 'installer\app.manifest'
    $finalArgs = @('/target:winexe', "/win32manifest:$manifest", "/win32icon:$icon", "/out:$finalOut") + $common
    & $csc $finalArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Installer build failed: $LASTEXITCODE"
    }
    Get-FileHash -LiteralPath $finalOut -Algorithm SHA256

}
