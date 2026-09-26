[CmdletBinding()]
param(
    [string]$GamePath = 'D:\Games\Hidden and Dangerous 2',
    [switch]$KeepPayload
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

$build = Join-Path $projectRoot 'build\solo-mission-pack'
$payload = Join-Path $build 'payload'
$payloadZip = Join-Path $build 'SoloMissionPayload.zip'
$sourceArchiveZip = Join-Path $build 'SourceArchives.zip'
$dist = Join-Path $projectRoot 'dist'
$icon = Join-Path $projectRoot 'installer\assets\hd2-heritage-icon.ico'
$manifest = Join-Path $projectRoot 'custom-mission-tool\app.manifest'
$nativeMenu = Join-Path $projectRoot 'build\HD2.CustomMenu.experimental.asi'
$bootstrap = Join-Path $build 'HD2-Solo-Mission-Pack-Bootstrap.exe'
$final = Join-Path $dist 'HD2-Solo-Mission-Pack-Setup.exe'

New-Item -ItemType Directory -Force $build, $dist | Out-Null
& python (Join-Path $projectRoot 'tools\build_native_custom_menu.py')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $nativeMenu)) {
    throw 'Native custom-menu build failed.'
}

$sources = @(
    (Join-Path $projectRoot 'solo-mission-pack\Program.cs'),
    (Join-Path $projectRoot 'solo-mission-pack\SoloMissionPackForm.cs'),
    (Join-Path $projectRoot 'solo-mission-pack\SoloMissionPackBuilder.cs'),
    (Join-Path $projectRoot 'solo-mission-pack\AssemblyInfo.cs'),
    (Join-Path $projectRoot 'custom-mission-tool\MissionPackageCore.cs'),
    (Join-Path $projectRoot 'installer\DtaArchive.cs')
)
$common = @(
    '/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu', '/optimize+',
    '/reference:System.dll', '/reference:System.Core.dll', '/reference:System.Drawing.dll',
    '/reference:System.Windows.Forms.dll', '/reference:System.Web.Extensions.dll',
    '/reference:System.IO.Compression.dll', '/reference:System.IO.Compression.FileSystem.dll',
    "/resource:$nativeMenu,HD2CustomMissionManager.CustomMenu.asi"
) + $sources

& $csc (@('/target:exe', "/out:$bootstrap") + $common)
if ($LASTEXITCODE -ne 0) {
    throw "Solo mission bootstrap build failed: $LASTEXITCODE"
}
& $bootstrap --self-test
if ($LASTEXITCODE -ne 0) {
    throw 'Solo mission pack self-tests failed.'
}

if (Test-Path -LiteralPath $payload) {
    Remove-Item -LiteralPath $payload -Recurse -Force
}
New-Item -ItemType Directory -Force $payload | Out-Null
& $bootstrap --export-library $GamePath $payload
if ($LASTEXITCODE -ne 0) {
    throw 'Commercial mission payload export failed.'
}
if (Test-Path -LiteralPath $payloadZip) {
    Remove-Item -LiteralPath $payloadZip -Force
}
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $payload, $payloadZip, [System.IO.Compression.CompressionLevel]::Optimal, $false)

$sourceNames = @('missions.dta', 'Scripts.dta', 'Patch.dta', 'SabreSquadron.dta')
$sourceRecords = @()
foreach ($name in $sourceNames) {
    $source = Join-Path $GamePath $name
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Required commercial source archive is missing: $source"
    }
    $sourceItem = Get-Item -LiteralPath $source
    $sourceRecords += [ordered]@{
        name = $name
        size = $sourceItem.Length
        sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    }
}
if (Test-Path -LiteralPath $sourceArchiveZip) {
    Remove-Item -LiteralPath $sourceArchiveZip -Force
}
$zipStream = [System.IO.File]::Open(
    $sourceArchiveZip, [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
try {
    $zip = New-Object System.IO.Compression.ZipArchive(
        $zipStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
    try {
        foreach ($record in $sourceRecords) {
            $entry = $zip.CreateEntry(
                $record.name, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            $input = [System.IO.File]::OpenRead((Join-Path $GamePath $record.name))
            try { $input.CopyTo($entryStream) }
            finally {
                $input.Dispose()
                $entryStream.Dispose()
            }
        }
        $manifestEntry = $zip.CreateEntry(
            'source-archives.json', [System.IO.Compression.CompressionLevel]::Optimal)
        $manifestStream = $manifestEntry.Open()
        try {
            $manifestJson = [ordered]@{
                format = 1
                archives = $sourceRecords
            } | ConvertTo-Json -Depth 4 -Compress
            $manifestBytes = [System.Text.UTF8Encoding]::new($false).GetBytes($manifestJson)
            $manifestStream.Write($manifestBytes, 0, $manifestBytes.Length)
        }
        finally { $manifestStream.Dispose() }
    }
    finally { $zip.Dispose() }
}
finally { $zipStream.Dispose() }

& $csc (@(
    '/target:winexe', "/win32manifest:$manifest", "/win32icon:$icon",
    "/out:$final", "/resource:$payloadZip,HD2SoloMissionPack.SoloMissionPayload.zip",
    "/resource:$sourceArchiveZip,HD2SoloMissionPack.SourceArchives.zip"
) + $common)
if ($LASTEXITCODE -ne 0) {
    throw "Self-contained solo mission pack build failed: $LASTEXITCODE"
}

$selfTest = Start-Process -FilePath $final -ArgumentList '--self-test' `
    -Wait -PassThru -WindowStyle Hidden
if ($selfTest.ExitCode -ne 0) {
    throw 'Final self-contained executable failed its self-tests.'
}

$hash = Get-FileHash -LiteralPath $final -Algorithm SHA256
$details = Get-Item -LiteralPath $final
[pscustomobject]@{
    Installer = $details.FullName
    Missions = 11
    SizeBytes = $details.Length
    SHA256 = $hash.Hash
}

if (-not $KeepPayload) {
    Remove-Item -LiteralPath $payload -Recurse -Force
    Remove-Item -LiteralPath $sourceArchiveZip -Force
}
