[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPath = Join-Path $projectRoot '.venv'
$lockPath = Join-Path $projectRoot 'requirements-tools.lock.txt'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python est introuvable dans PATH.'
}
if (-not (Test-Path -LiteralPath $lockPath)) {
    throw "Verrou de dépendances introuvable : $lockPath"
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw "La création de l'environnement Python a échoué : $LASTEXITCODE"
    }
}

& $venvPython -m pip install --require-virtualenv -r $lockPath
if ($LASTEXITCODE -ne 0) {
    throw "L'installation des dépendances a échoué : $LASTEXITCODE"
}

& $venvPython -c "import PIL, reportlab, unicorn; print('Environnement Python prêt.')"
if ($LASTEXITCODE -ne 0) {
    throw 'La vérification des dépendances Python a échoué.'
}

Write-Host "Interpréteur prêt : $venvPython"
