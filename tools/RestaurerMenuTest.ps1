$ErrorActionPreference = "Stop"

$gameRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
if ((Split-Path -Leaf $gameRoot) -ne "Hidden and Dangerous 2 - Test Menu Personnalise") {
    throw "Ce script ne peut restaurer que la copie de test Menu Personnalise."
}

$originalExecutable = Join-Path $gameRoot "HD2_SabreSquadron.original.exe"
$activeExecutable = Join-Path $gameRoot "HD2_SabreSquadron.exe"
if (-not (Test-Path -LiteralPath $originalExecutable -PathType Leaf)) {
    throw "Sauvegarde de l'executable original absente."
}
Copy-Item -LiteralPath $originalExecutable -Destination $activeExecutable -Force

$backupRoot = Join-Path $gameRoot "STATIC_MENU_BACKUP"
$managedPath = Join-Path $gameRoot "STATIC_MENU_MANAGED_FILES.json"
if (Test-Path -LiteralPath $managedPath -PathType Leaf) {
    $managed = Get-Content -LiteralPath $managedPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $managed.files) {
        if (-not $item.created) { continue }
        $relative = [string]$item.relative
        $active = [IO.Path]::GetFullPath((Join-Path $gameRoot $relative))
        if (-not $active.StartsWith($gameRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) {
            throw "Chemin de restauration non sûr : $relative"
        }
        if (-not (Test-Path -LiteralPath $active -PathType Leaf)) { continue }
        $currentHash = (Get-FileHash -LiteralPath $active -Algorithm SHA256).Hash
        if ($currentHash -eq [string]$item.sha256) {
            Remove-Item -LiteralPath $active -Force
        } else {
            Write-Warning "Fichier personnalisé conservé car il a été modifié : $relative"
        }
    }
}
if (Test-Path -LiteralPath $backupRoot -PathType Container) {
    foreach ($saved in Get-ChildItem -LiteralPath $backupRoot -Recurse -File) {
        $relative = [IO.Path]::GetRelativePath($backupRoot, $saved.FullName)
        $destination = Join-Path $gameRoot $relative
        $destinationDirectory = Split-Path -Parent $destination
        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
        }
        Copy-Item -LiteralPath $saved.FullName -Destination $destination -Force
    }
}

foreach ($relative in @(
    "Models\singleplayer.4ds",
    "GameData\Gamedata02.gdt",
    "GameData\Gamedata03.gdt",
    "GameData\Gamedata04.gdt",
    "GameData\Gamedata05.gdt"
)) {
    $saved = Join-Path $backupRoot $relative
    $active = Join-Path $gameRoot $relative
    if (-not (Test-Path -LiteralPath $saved -PathType Leaf) -and
        (Test-Path -LiteralPath $active -PathType Leaf)) {
        Remove-Item -LiteralPath $active -Force
    }
}

Write-Host "La copie de test a retrouve son executable, son menu, ses textes et ses fichiers precedents."
