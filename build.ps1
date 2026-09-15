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
$guide = Join-Path $projectRoot 'output\pdf\HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf'
$report = Join-Path $projectRoot 'output\pdf\HD2-Rapport-des-Decouvertes.pdf'
$icon = Join-Path $projectRoot 'installer\assets\hd2-heritage-icon.ico'
$widescreen = Join-Path $projectRoot 'installer\assets\HiddenandDangerous2.WidescreenFix.zip'
if (-not (Test-Path -LiteralPath $guide) -or -not (Test-Path -LiteralPath $report)) {
    throw 'The two final PDF guides must be generated before building the installer.'
}
$pdfCommon = Join-Path $projectRoot 'tools\pdf\pdf_common.py'
$playerSource = Join-Path $projectRoot 'tools\pdf\build_player_guide.py'
$reportSource = Join-Path $projectRoot 'tools\pdf\build_report.py'
foreach ($pair in @(
    @($guide, $pdfCommon, $playerSource),
    @($report, $pdfCommon, $reportSource)
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
    '/reference:System.IO.Compression.dll',
    '/reference:System.IO.Compression.FileSystem.dll'
)
$common = @('/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu', '/optimize+') +
    $references + @(
        "/resource:$guide,HD2CommunityInstaller.GuideJoueur.pdf",
        "/resource:$report,HD2CommunityInstaller.RapportDecouvertes.pdf",
        "/resource:$widescreen,HD2CommunityInstaller.WidescreenFix.zip"
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
