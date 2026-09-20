param(
    [Parameter(Mandatory = $true)][string]$ManagerPath,
    [Parameter(Mandatory = $true)][string]$TestGame,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$workspace = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$gameRoot = (Resolve-Path -LiteralPath $TestGame).ProviderPath.TrimEnd('\')
$manager = (Resolve-Path -LiteralPath $ManagerPath).ProviderPath
$output = [IO.Path]::GetFullPath($OutputDirectory)
$fixture = Join-Path $workspace 'tests\fixtures\import-user-mission\Operation Test Joueur'
$missionName = 'Operation Test Joueur'
$library = Join-Path $gameRoot 'CustomMissions'
$package = Join-Path $library $missionName
$installedMission = Join-Path $gameRoot ('Missions\' + $missionName)
$catalogue = Join-Path $gameRoot 'GameData\Gamedata04.gdt'
$reportPath = Join-Path $gameRoot 'CUSTOM_MISSIONS_INSTALL.json'

function Assert-Within([string]$Path, [string]$Parent) {
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($Parent.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Chemin hors du dossier autorisé : $full"
    }
}
function Assert-NoLinks([string]$Path) {
    $itemPath = [IO.Path]::GetFullPath($Path)
    while ($itemPath) {
        if ((Test-Path -LiteralPath $itemPath) -and
            ((Get-Item -LiteralPath $itemPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Lien ou jonction interdit : $itemPath"
        }
        $itemPath = Split-Path -Parent $itemPath
    }
}
function Assert-GameStopped {
    if (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^HD2($|_)' }) {
        throw 'Fermez H&D2 avant de lancer ou poursuivre ce test.'
    }
}
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
function Catalogue-ContainsFixture {
    [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($catalogue)).Contains($missionName)
}

# Require an explicitly named test copy; never operate on the original install.
if ((Split-Path -Leaf $gameRoot) -notmatch '(?i)test' -or
    $gameRoot.Equals('D:\Games\Hidden and Dangerous 2', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'TestGame doit désigner une copie dont le nom contient Test, pas le jeu original.'
}
Assert-Within $output $workspace
Assert-Within $package $library
Assert-Within $installedMission $gameRoot
foreach ($path in @($gameRoot, $manager, $output, $library, $fixture, $installedMission)) { Assert-NoLinks $path }
Assert-GameStopped
if ((Test-Path -LiteralPath $output) -and (Get-ChildItem -LiteralPath $output -Force)) {
    throw 'OutputDirectory doit être neuf ou vide pour conserver tous les rapports précédents.'
}
if (-not (Test-Path -LiteralPath $manager -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $gameRoot 'HD2_SabreSquadron.exe') -PathType Leaf)) {
    throw 'Gestionnaire ou copie de jeu absent.'
}
$baselineReport = Read-Json $reportPath
$baselinePackages = @(Get-ChildItem -LiteralPath $library -Directory | Where-Object {
    -not $_.Name.StartsWith('_') -and ((Test-Path -LiteralPath (Join-Path $_.FullName 'mission.json')) -or
        (Test-Path -LiteralPath (Join-Path $_.FullName 'tree.klz')))
})
if ($baselinePackages.Count -eq 0 -or [int]$baselineReport.missions -ne $baselinePackages.Count) {
    throw 'Une bibliothèque de référence non vide et déjà intégrée est nécessaire.'
}
if ((Test-Path -LiteralPath $package) -or
    (Test-Path -LiteralPath $installedMission -PathType Leaf) -or
    ((Test-Path -LiteralPath $installedMission -PathType Container) -and
        (Get-ChildItem -LiteralPath $installedMission -Force)) -or (Catalogue-ContainsFixture)) {
    throw 'La mission fixture existe déjà : aucun fichier ne sera remplacé.'
}
foreach ($entry in $baselinePackages) {
    $manifestPath = Join-Path $entry.FullName 'mission.json'
    if (Test-Path -LiteralPath $manifestPath) {
        $manifest = Read-Json $manifestPath
        if ($manifest.missionDirectory -eq $missionName) { throw 'Nom fixture déjà présent dans la bibliothèque.' }
    }
}
New-Item -ItemType Directory -Path $output -Force | Out-Null
$commands = [Collections.Generic.List[object]]::new()
$stats = [ordered]@{
    status = 'RUNNING'; fixture = 'NONJOUABLE : test de copie et de catalogue uniquement, aucun lancement du jeu'
    workflow = 'Dépôt brut dans CustomMissions, sans mission.json et sans import manuel'
    manager = $manager; manager_sha256 = (Hash $manager); test_game = $gameRoot
    baseline_missions = [int]$baselineReport.missions; imported_missions = $null
    restored_missions = $null; archive = $null; commands = $commands
    registry_note = 'Une allocation historique dans .catalogue-ids.json peut subsister après retrait.'
}
function Invoke-Manager([string]$Label, [string[]]$Arguments) {
    Assert-GameStopped
    $stdout = Join-Path $output ($Label + '.stdout.log')
    $stderr = Join-Path $output ($Label + '.stderr.log')
    # Windows argv quoting: double backslashes preceding quotes or the closing quote.
    $quoted = @($Arguments | ForEach-Object {
        '"' + [regex]::Replace([regex]::Replace($_, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
    }) -join ' '
    $process = Start-Process -FilePath $manager -ArgumentList $quoted -WorkingDirectory $gameRoot `
        -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $commands.Add([ordered]@{ step = $Label; arguments = $Arguments; exit_code = $process.ExitCode })
    if ($process.ExitCode -ne 0) { throw "Échec $Label ($($process.ExitCode)), voir $stderr" }
}

$baselineFiles = @{}
foreach ($entry in $baselinePackages) {
    foreach ($file in Get-ChildItem -LiteralPath $entry.FullName -File -Recurse -Force) {
        Assert-NoLinks $file.FullName
        $baselineFiles[$file.FullName] = Hash $file.FullName
        $payloadPrefix = (Join-Path $entry.FullName 'payload').TrimEnd('\') + '\'
        if ($file.FullName.StartsWith($payloadPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            $deployed = Join-Path $gameRoot $file.FullName.Substring($payloadPrefix.Length)
            Assert-Within $deployed $gameRoot
            if (Test-Path -LiteralPath $deployed -PathType Leaf) { $baselineFiles[$deployed] = Hash $deployed }
        } elseif (-not (Test-Path -LiteralPath (Join-Path $entry.FullName 'mission.json'))) {
            $deployed = Join-Path $gameRoot ('Missions\' + $entry.Name + '\' +
                $file.FullName.Substring($entry.FullName.Length + 1))
            Assert-Within $deployed $gameRoot
            if (Test-Path -LiteralPath $deployed -PathType Leaf) { $baselineFiles[$deployed] = Hash $deployed }
        }
    }
}
foreach ($path in @($reportPath, (Join-Path $library '.catalogue-ids.json'),
    (Join-Path $gameRoot 'STATIC_MENU_MANAGED_FILES.json'))) {
    if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination (Join-Path $output ('before-' + (Split-Path -Leaf $path))) }
}
$fixtureCopied = $false
$failure = $null
try {
    Invoke-Manager '01-check-baseline' @('--check', $library)
    Invoke-Manager '02-self-test-safety' @('--self-test-safety', (Join-Path $output 'safety'))
    Assert-GameStopped
    if (Test-Path -LiteralPath $package) { throw 'Le dossier fixture a été créé pendant le test : copie refusée.' }
    $fixtureCopied = $true
    Copy-Item -LiteralPath $fixture -Destination $package -Recurse
    if (Test-Path -LiteralPath (Join-Path $package 'mission.json')) { throw 'La fixture brute contient un manifeste inattendu.' }
    Invoke-Manager '03-check-raw-folder' @('--check', $library)
    Invoke-Manager '04-integrate-raw-folder' @('--integrate', $library, $gameRoot, $gameRoot)
    $importedReport = Read-Json $reportPath
    $stats.imported_missions = [int]$importedReport.missions
    Copy-Item -LiteralPath $reportPath -Destination (Join-Path $output 'after-import-report.json')
    if ($stats.imported_missions -ne $stats.baseline_missions + 1) { throw 'Augmentation attendue du compteur de missions : +1.' }
    foreach ($file in Get-ChildItem -LiteralPath $fixture -File -Recurse) {
        $relative = $file.FullName.Substring($fixture.Length + 1)
        $expectedHash = Hash $file.FullName
        foreach ($copy in @((Join-Path $package $relative), (Join-Path $installedMission $relative))) {
            if ((Hash $copy) -ne $expectedHash) { throw "Contenu de la fixture différent : $copy" }
        }
    }
    $stats.fixture_tree_sha256 = Hash (Join-Path $installedMission 'tree.klz')
    if (-not (Catalogue-ContainsFixture)) { throw 'Mission absente du catalogue utilisateur Gamedata04.gdt.' }
    $stats.catalogue_contains_fixture = $true
}
catch { $failure = $_.Exception.Message }
finally {
    try {
        if ($fixtureCopied -and (Test-Path -LiteralPath $package)) {
            Assert-GameStopped
            Assert-NoLinks $package
            $resolvedPackage = (Resolve-Path -LiteralPath $package).ProviderPath
            Assert-Within $resolvedPackage $library
            $archive = Join-Path $output 'archive'
            Assert-Within $archive $output
            New-Item -ItemType Directory -Path $archive | Out-Null
            $stats.archive = Join-Path $archive $missionName
            Move-Item -LiteralPath $resolvedPackage -Destination $stats.archive
            Invoke-Manager '05-reintegrate-baseline' @('--integrate', $library, $gameRoot, $gameRoot)
            Invoke-Manager '06-check-restored' @('--check', $library)
            $stats.restored_missions = [int](Read-Json $reportPath).missions
            Copy-Item -LiteralPath $reportPath -Destination (Join-Path $output 'after-restore-report.json')
            if ($stats.restored_missions -ne $stats.baseline_missions -or (Catalogue-ContainsFixture)) {
                throw 'Le catalogue de référence reste différent de la baseline.'
            }
            if ((Test-Path -LiteralPath $installedMission) -and
                (Get-ChildItem -LiteralPath $installedMission -File -Recurse -Force)) {
                throw 'Des fichiers de la fixture restent installés.'
            }
        }
        foreach ($path in $baselineFiles.Keys) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Hash $path) -ne $baselineFiles[$path]) {
                throw "Fichier préexistant modifié ou absent : $path"
            }
        }
        $stats.preexisting_files_verified = $baselineFiles.Count
    }
    catch { $failure = (@($failure, ('Nettoyage : ' + $_.Exception.Message)) | Where-Object { $_ }) -join '; ' }
    $stats.status = if ($failure) { 'FAILED' } else { 'PASSED' }
    $stats.error = $failure
    $stats | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'summary.json') -Encoding UTF8
}
if ($failure) { throw $failure }
Write-Output ('Validation réussie, baseline rétablie. Rapport : ' + (Join-Path $output 'summary.json'))
