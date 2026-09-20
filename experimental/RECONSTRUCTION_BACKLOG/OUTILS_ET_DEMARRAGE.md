# Outils et procédure de démarrage

Ce document prépare le poste de travail. Il ne demande aucune modification de
mission et ne rend aucun prototype actif.

## Prérequis

- Windows avec PowerShell 7 recommandé;
- Git;
- Python 3 avec le module `venv`;
- installation légitime de *Hidden & Dangerous 2: Sabre Squadron 1.12*;
- compilateur C# du .NET Framework 4 (`csc.exe`) pour construire l'installateur;
- accès réseau uniquement pour installer les dépendances Python et pour les
  audits réseau explicitement demandés.

État observé sur la machine de référence le 19 septembre 2026 : Git 2.52,
PowerShell 7.6.5, Python 3.14, les compilateurs .NET 32/64 bits présents et les
archives commerciales disponibles sous `D:\Games\Hidden and Dangerous 2`.
L'environnement isolé a été vérifié avec Pillow 12.3.0, ReportLab 5.0.1 et
Unicorn 2.1.4; 30 interfaces d'outils se chargent sans erreur.

## Installation isolée des outils Python

Depuis la racine du dépôt :

```powershell
.\tools\PreparerEnvironnement.ps1
```

Le script crée `.venv`, ignoré par Git, puis installe Pillow, ReportLab et
Unicorn avec les versions vérifiées de `requirements-tools.lock.txt`.
`requirements-tools.txt` conserve la liste minimale lisible. Le script ne
modifie ni le jeu ni les missions. Toutes les commandes ci-dessous peuvent
ensuite utiliser :

```powershell
.\.venv\Scripts\python.exe tools\NOM_OUTIL.py --help
```

## Outils d'archives et de recherche

| Outil | Usage |
|---|---|
| `tools/dta_archive.py` | Lister une archive DTA, filtrer par glob et extraire vers un dossier temporaire. |
| `tools/archive_content_search.py` | Rechercher un ou plusieurs termes dans plusieurs archives, avec filtres et sortie JSON. |
| `tools/full_game_audit.py` | Produire l'audit global JSON et Markdown d'une installation. |
| `tools/map_inventory_audit.py` | Inventorier les missions, cartes et conteneurs. |
| `tools/asset_presence_audit.py` | Vérifier la présence et les empreintes de ressources. |

Exemples sûrs et non destructifs :

```powershell
.\.venv\Scripts\python.exe tools\dta_archive.py "D:\Games\Hidden and Dangerous 2\missions.dta" --json
.\.venv\Scripts\python.exe tools\archive_content_search.py "D:\Games\Hidden and Dangerous 2\missions.dta" --term "R_Cz2_Ger12" --json
.\.venv\Scripts\python.exe tools\full_game_audit.py "D:\Games\Hidden and Dangerous 2" --json-output output\audit\full-game-audit.json --markdown-output docs\AUDIT_COMPLET_JEU.md
```

Toute extraction doit viser `.analysis/` ou un dossier temporaire, jamais un
dossier suivi par Git. `.analysis/` et `.research/` sont volontairement ignorés.

## Outils de scripts, scènes et signaux

| Outil | Usage |
|---|---|
| `tools/script_binding_audit.py` | Relier scripts, acteurs libres et bindings; filtrage par mission. |
| `tools/signal_graph_audit.py` | Cartographier émetteurs, récepteurs et signaux sans destinataire. |
| `tools/objective_audit.py` | Examiner déclarations, activations, validations et échecs d'objectifs. |
| `tools/scene_frame_position_audit.py` | Résoudre les positions de frames et chercher les voisins. |
| `tools/mission_closure_audit.py` | Vérifier les scripts libres et la fermeture structurelle d'une mission. |
| `tools/boundary_label_audit.py` | Auditer les drapeaux de zone et objets `border`. |
| `tools/tree_klz.py` | Lire et transformer les collisions avec conservation de structure. |

Commandes de départ :

```powershell
.\.venv\Scripts\python.exe tools\script_binding_audit.py "D:\Games\Hidden and Dangerous 2" --mission arctic1 --json
.\.venv\Scripts\python.exe tools\scene_frame_position_audit.py "D:\Games\Hidden and Dangerous 2" arctic2 --name S_radio --name m_radiog_ --nearest 10
.\.venv\Scripts\python.exe tools\signal_graph_audit.py "D:\Games\Hidden and Dangerous 2" --json-output output\audit\signal-graph.json --markdown-output docs\AUDIT_SIGNAUX.md
```

## Outils de ressources et prototypes

| Outil | Usage |
|---|---|
| `tools/item_id_collision_audit.py` | Vérifier qu'un ID d'objet additif est libre. |
| `tools/orphan_weapon_evidence_audit.py` | Consolider les traces d'armes orphelines. |
| `tools/flamethrower_evidence_audit.py` | Vérifier spécifiquement les lance-flammes. |
| `tools/aircraft_scenic_audit.py` | Auditer les avions utilisables comme décors. |
| `tools/model_wireframe.py` | Rendre une vue filaire de modèle; nécessite Pillow. |
| `tools/prototype_deployment_audit.py` | Contrôler les deux prototypes installés sans les confondre avec des missions solo validées. |

Avant toute attribution d'ID :

```powershell
.\.venv\Scripts\python.exe tools\item_id_collision_audit.py "D:\Games\Hidden and Dangerous 2" --candidate 359
```

Un résultat libre n'autorise pas automatiquement l'utilisation de l'ID : il
doit être rescanné juste avant intégration.

## Conversion multijoueur vers solo

La commande de référence est :

```powershell
.\.venv\Scripts\python.exe tools\multiplayer_solo_readiness_audit.py "D:\Games\Hidden and Dangerous 2" --runtime-results validation\multiplayer-solo-runtime.json --require-baseline
```

L'option `--require-proven` doit être ajoutée uniquement lorsqu'une conversion
est revendiquée comme validée. À ce jour, le registre contient 21 candidates et
zéro conversion validée.

## Contrôles du projet et préparation d'une livraison

| Outil | Usage |
|---|---|
| `tools/runtime_validation_audit.py` | Valider la structure des preuves d'exécution. |
| `tools/stable_candidate_coverage_audit.py` | Vérifier que chaque candidat stable a une disposition. |
| `tools/installer_wiring_audit.py` | Vérifier le câblage des options de l'installateur. |
| `tools/installer_composition_audit.py` | Vérifier la composition des modules. |
| `tools/release_readiness_audit.py` | Barrière finale combinant preuves, installateur, état Git, artefact et éventuellement jeu/réseau. |
| `tools/state_journal_audit.py` | Vérifier le journal de restauration. |
| `tools/embedded_dependency_audit.py` | Vérifier les ressources tierces embarquées. |

Contrôle de schéma, sans jeu et sans écriture :

```powershell
.\.venv\Scripts\python.exe tools\runtime_validation_audit.py
```

Barrière finale, à réserver à une vraie livraison :

```powershell
.\.venv\Scripts\python.exe tools\release_readiness_audit.py . --game "D:\Games\Hidden and Dangerous 2" --json-output output\audit\release-readiness.json
```

Cette barrière doit échouer tant que les validations manuelles sont en attente,
que l'arbre de travail n'est pas propre ou que l'installateur final n'est pas à
jour. Un échec pendant le développement est donc une information, pas une raison
de contourner les contrôles.

## Menu personnalisé, réseau et documents

- Menu/paquets : `custom_mission_packages.py`, `custom_mission_tool.py`,
  `custom_menu_candidate_audit.py`, `menu_gui_audit.py` et
  `build_static_custom_menu.py` (Unicorn requis pour l'émulation ciblée).
- Réseau : `network_master_audit.py`, `gamespy2_server_probe.py` et
  `network_runtime_preflight.py`. Ces outils accèdent au réseau et ne prouvent
  pas à eux seuls une connexion réussie dans le jeu.
- PDF : scripts sous `tools/pdf/` (ReportLab requis). Les quatre PDF finaux sont
  publiés comme fichiers séparés de la release et ne font pas partie du setup.

## Construction de l'installateur

```powershell
.\build.ps1 -ConsoleOnly
.\build.ps1
```

Le premier appel valide la compilation console; le second produit l'exécutable
Windows final. Le script utilise le compilateur .NET Framework, les sources C#
de `installer/`, l'icône et l'archive Widescreen. Ne pas lancer
la construction tant que le travail porte seulement sur une étude `.disabled`.

## Checklist avant la première modification

- [ ] Se placer sur `codex/experimental-reconstruction-inventory`.
- [ ] Vérifier que les travaux locaux non liés ne seront ni ajoutés ni écrasés.
- [ ] Exécuter `tools/PreparerEnvironnement.ps1`.
- [ ] Lire `README.md`, `MISSIONS.md`, `SYSTEMES_ET_ASSETS.md`, `VALIDATION.md`
      et `REFERENCES.md` dans ce dossier.
- [ ] Lire l'étude existante correspondante dans `experimental/<ID>/`.
- [ ] Capturer une baseline commerciale avant tout prototype.
- [ ] Classer chaque fait `OFFICIEL`, `INFERENCE` ou `MODERNE`.
- [ ] Garder le comportement commercial par défaut.
- [ ] Écrire d'abord sous `.disabled`; ne pas modifier l'installateur.
- [ ] Définir retrait, test et critères d'abandon avant activation.
