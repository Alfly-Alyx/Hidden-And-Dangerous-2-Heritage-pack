[CmdletBinding()]
param()

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
$icon = Join-Path $projectRoot 'installer\assets\hd2-heritage-icon.ico'
New-Item -ItemType Directory -Force $build | Out-Null
$sources = @(
    (Join-Path $projectRoot 'diagnostic-monitor\Program.cs'),
    (Join-Path $projectRoot 'diagnostic-monitor\AssemblyInfo.cs')
)
$common = @(
    '/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu', '/optimize+',
    '/reference:System.dll', '/reference:System.Core.dll',
    '/reference:System.IO.Compression.dll', '/reference:System.IO.Compression.FileSystem.dll'
) + $sources

$consoleOut = Join-Path $build 'HD2-Heritage-Diagnostics.Console.exe'
& $csc (@('/target:exe', "/out:$consoleOut") + $common)
if ($LASTEXITCODE -ne 0) {
    throw "Diagnostic monitor validation build failed: $LASTEXITCODE"
}
& $consoleOut --self-test
if ($LASTEXITCODE -ne 0) {
    throw 'Diagnostic monitor self-tests failed.'
}

$finalOut = Join-Path $build 'HD2-Heritage-Diagnostics.exe'
& $csc (@('/target:winexe', "/win32icon:$icon", "/out:$finalOut") + $common)
if ($LASTEXITCODE -ne 0) {
    throw "Diagnostic monitor build failed: $LASTEXITCODE"
}
Get-FileHash -LiteralPath $finalOut -Algorithm SHA256
