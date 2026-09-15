param(
    [string]$Bibliotheque = (Join-Path $PSScriptRoot "custom-missions\library"),
    [string]$JeuOriginal = "D:\Games\Hidden and Dangerous 2",
    [string]$JeuTest = "D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise",
    [switch]$VerifierSeulement
)

$ErrorActionPreference = "Stop"
$outil = Join-Path $PSScriptRoot "tools\custom_mission_tool.py"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python est introuvable. Installez Python 3 ou lancez la préparation depuis l'environnement du projet."
}

if ($VerifierSeulement) {
    & python $outil check $Bibliotheque
} else {
    & python $outil integrate $Bibliotheque --original-game $JeuOriginal --test-game $JeuTest
}
if ($LASTEXITCODE -ne 0) {
    throw "La préparation des missions personnalisées a échoué."
}

Write-Host "Aucun jeu n'a été lancé."
