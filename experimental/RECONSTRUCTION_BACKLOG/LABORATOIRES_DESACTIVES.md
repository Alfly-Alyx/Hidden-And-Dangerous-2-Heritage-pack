# Laboratoires A/B inertes

Le générateur `tools/build_reconstruction_lab.py` transforme chaque profil en
deux copies complètes de mission : témoin commercial et variante. Les sorties
restent sous `.analysis/`, hors jeu, non distribuables car dérivées des archives
commerciales. Elles ne sont **ni installées, ni lancées, ni validées en moteur**.

## Garanties et limites

- Chaque copie possède son identifiant et son dossier `H2Lab_…_B` ou `H2Lab_…_V`.
- Géométrie, collisions, acteurs, registre et scripts locaux sont copiés depuis
  les archives effectives. Seuls les scripts explicitement déclarés diffèrent
  dans la variante : un par profil, ou une paire indivisible (radio Czech 6,
  gardes Normandy 1, son Burgundy 3).
- Tous les fichiers de charge utile et les manifestes portent `.disabled`, y
  compris à l'intérieur du ZIP. Une extraction accidentelle ne crée pas de
  paquet scannable par le gestionnaire.
- Les scripts accessibles depuis le registre, `#include` et `ScriptAssign` sont
  contrôlés. Dépendance absente, nom dynamique, chemin externe ou chemin figé
  vers la mission originale : refus, pas de remappage deviné.
- Aucun objectif nouveau n'est introduit. Les nouveaux signaux de comportement
  doivent être explicitement documentés (11 vers le son du dépôt Burgundy 3).
  Le gestionnaire conserve
  intégralement les blocs d'objectifs du gabarit Base ou Sabre, dans leur ordre.
- Les ressources globales restent fournies par l'installation légitime. La
  fermeture statique des scripts ne prouve pas leur résolution par le moteur
  sous un nouveau nom de mission, ni l'absence de toute dépendance implicite.

La vérification ZIP contrôle l'intégrité et la cohérence internes, pas une
signature d'authenticité. L'origine commerciale est contrôlée lors de la
génération depuis les archives et les empreintes du catalogue de variantes.

## Commandes

Lecture seule par défaut; `--build` crée un fichier neuf, jamais un écrasement :

```powershell
.\.venv\Scripts\python.exe tools\build_reconstruction_lab.py --game "D:\Games\Hidden and Dangerous 2" --archives-only --profile czech2-ger12-lie
.\.venv\Scripts\python.exe tools\build_reconstruction_lab.py --game "D:\Games\Hidden and Dangerous 2" --archives-only --profile czech2-ger12-lie --build
.\.venv\Scripts\python.exe tools\build_reconstruction_lab.py --verify .analysis\laboratories\czech2-ger12-lie.lab.zip.disabled
```

`--archives-only` exclut explicitement les surcharges locales et enregistre leurs
empreintes pertinentes. Il ne valide pas leur compatibilité avec la variante.

Pour contrôler les catalogues avec le gestionnaire compilé :

```powershell
.\build-custom-mission-manager.ps1 -ConsoleOnly
$labBundles = @(Get-ChildItem -LiteralPath .analysis\laboratories\20260925 -Filter *.lab.zip.disabled | Select-Object -ExpandProperty FullName)
.\.venv\Scripts\python.exe tools\reconstruction_catalogue_audit.py --game "D:\Games\Hidden and Dangerous 2" @labBundles
```

Cet audit fabrique une bibliothèque temporaire de **faux contenus non jouables**
pour exercer le gestionnaire. Il n'extrait pas les missions du ZIP. Il compare
les objectifs hérités octet par octet, vérifie que les neuf missions Sabre sont
inchangées et génère en mémoire les fichiers du menu. Les faux paquets et le
catalogue temporaire sont ensuite retirés. Ce n'est pas un test du jeu.

## Mesures de la première série — 25 septembre 2026

| Mission | Fichiers copiés par branche | Scripts accessibles | Objectifs conservés par branche |
|---|---:|---:|---:|
| Arctic 4 | 115 | 100 | 9 |
| Czech 2 | 110 | 83 | 6 |
| Sicily 1 | 102 | 90 | 9 |
| Africa 1 | 156 | 114 | 10 |
| Czech 6 | 109 | 95 | 6 |
| Libye 3 | 85 | 73 | 6 |
| Czech 3 | 99 | 76 | 4 |
| Czech 4 | 124 | 105 | 4 |
| Sicily 2 | 131 | 117 | 9 |
| Normandy 1 | 183 | 157 | 8 |
| Burgundy 3 | 105 | 89 | 9 |

Les douze entrées témoin/variante de cette série ont passé l'audit de catalogue.
Le profil supplémentaire AF1_26 emploie les mêmes 156 sources Africa 1 et conserve
les dix objectifs; le contrôle a également réussi avec les quatorze entrées.
Les trois profils supplémentaires Arctic 4 et le profil Czech 3 portent ensuite
le total à **onze laboratoires, vingt-deux entrées contrôlées**. Le catalogue
combiné a l'empreinte `5107b3803e0dacdc93698c7cdbda7d0a8391f84a80afe44dd09b0b8a9c2cb234`.

Le pianiste de Czech 4 et la vague de Sicily 2 portent le total actuel à
**treize laboratoires et vingt-six entrées contrôlées**, catalogue combiné
`cbbfbc5691842db62c4f1954fb1811659e202d44b3169f1ad2cbcb02d72eea7e`.

La paire radio Czech 6 porte ensuite le total courant à **quatorze laboratoires,
vingt-huit entrées et quinze scripts modifiés**, catalogue
`b5b5964e92c1b0da06f95d588865576f995df725a5f78093b6461fd9eea01339`.
Son emballage contient obligatoirement les deux scripts Base; un fichier manquant
ou resté en version Patch est refusé. Les anciens ZIP à un seul script restent
lisibles par le vérificateur.

L'assise du garde 3 Arctic 4 porte le total à **quinze laboratoires, trente
entrées et seize scripts modifiés**, catalogue
`33939de79d993364b0c18e3093801b3d41e7f039bc308ef30515477b6b49152c`.
Ce profil reste exclusif de celui du poste d'alarme du même garde.

Les deux paires Normandy 1/Burgundy 3 portent le total à **dix-sept laboratoires,
trente-quatre entrées et vingt scripts modifiés**, catalogue
`9a9862e763d141f1c49fd302780a3c9fd8860dee363c621ac603c7ebcb273e28`.
Les neuf missions Sabre d'origine restent identiques, objectifs inclus.

Les **135 tests Python** couvrent 47 cas de variantes, 20 cas de laboratoires,
huit cas de conservation d'objectifs, quatre contrôles de lecture de catalogues,
quatorze modèles/contrats de charges, assise, proximité et son,
quatorze cas de groupes atomiques/4DS
et 28 tests d'émulation du menu.
Les auto-tests C# passent également. Le contrôle
de dépendances distingue maintenant une désaffectation explicite
`ScriptAssign(owner, "")` d'un nom dynamique; une concaténation de nom reste
refusée. Ces nombres ne comptent aucun essai moteur.
Restent obligatoires : installation dans une copie de test explicitement isolée,
apparition dans le menu, chargement, résolution locale des scripts, interruptions,
sauvegarde/reprise, objectifs et fin de mission comparés au témoin. Aucun retrait
de `.disabled` ni intégration au jeu courant n'est effectué par ces outils.
