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
New-Item -ItemType Directory -Force $build | Out-Null
$sources = @(Get-ChildItem -LiteralPath (Join-Path $projectRoot 'network-bridge') `
    -Filter '*.cs' | ForEach-Object FullName)
$output = Join-Path $build 'HD2-Master-Bridge.exe'
& $csc @(
    '/nologo', '/utf8output', '/checked+', '/warn:4', '/platform:anycpu',
    '/optimize+', '/target:exe', "/out:$output",
    '/reference:System.dll', '/reference:System.Core.dll',
    '/reference:System.ServiceProcess.dll'
) $sources
if ($LASTEXITCODE -ne 0) {
    throw "Network bridge build failed: $LASTEXITCODE"
}
& $output '--self-test'
if ($LASTEXITCODE -ne 0) {
    throw "Network bridge self-test failed: $LASTEXITCODE"
}
Get-FileHash -LiteralPath $output -Algorithm SHA256
