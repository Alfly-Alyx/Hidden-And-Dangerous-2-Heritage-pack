# Essais des reconstructions expérimentales

Le [registre expérimental](reconstruction-runtime.json) est séparé du registre
du paquet stable `runtime-validation.json` et des conversions
`multiplayer-solo-runtime.json`. Il ne modifie aucun de leurs résultats.

Au 26 septembre 2026 : **49 profils, 298 contrôles, tous pending**. Aucun essai
moteur n'a été effectué par la création du registre ou son audit.

- 43 variantes de scripts solo et deux Carnage : six contrôles chacune;
- un triplet de scripts coop : sept contrôles, dont réseau;
- trois comparaisons scène/registre coop : sept contrôles chacune, dont réseau;
- chaque profil pointe vers son étude et contient des étapes propres au
  comportement concerné, ses prérequis et l'empreinte de sa définition actuelle.

Le mode solo, Carnage ou coopération est explicite dans chaque protocole. Les
registres de mission ne sont jamais fusionnés. Un résultat dans ce registre ne
qualifie pas automatiquement un autre mode ou une conversion coop vers solo.

## Avant un essai

La [voie d'essai native](ESSAIS_NATIFS.md) fournit désormais une copie indépendante,
des configurations sous les noms de mission d'origine et un déploiement
réversible, sans lancer de programme de jeu. Elle est distincte des laboratoires
renommés décrits ci-dessous et ne lève aucune validation moteur.

Préparer une copie de jeu isolée et un déploiement réversible. Ne pas utiliser
directement l'installation personnelle. Les 20 laboratoires complets restent
désactivés; les sept profils Africa 5 n'ont pas de mission complète tant que
le détecteur commercial de piste manque. Les trois comparaisons binaires ne
sont pas des paquets de mission activables. Le registre n'est pas une permission
d'ignorer ces prérequis, de créer une dépendance vide ou de forcer un déploiement.
Pour Africa 5 et Co-Burgundy 1, la voie native conserve exactement les absences
commerciales et impose l'observation réelle du témoin avant sa variante.

Lire l'étude du profil et ses exclusions : les deux variantes du garde 3
Arctic4 et les deux variantes d'explosion Burgundy3 doivent notamment rester
des expériences distinctes. Préserver les corrections Heritage déjà installées;
un témoin archives-only ne prouve pas la compatibilité avec leurs surcharges.

## Six familles communes, plus le réseau en coop

| Contrôle | Critère à démontrer |
|---|---|
| `baseline` | Témoin commercial chargé, mode et comportement de référence consignés. |
| `effect` | Changement attendu de l'étude reproduit, sans effet hors de son périmètre. |
| `interruption` | Alarmes, morts et autres interruptions pertinentes sans blocage ni duplication. |
| `save_load` | États cohérents avant, pendant et après sauvegarde/reprise. |
| `objectives` | Objectifs, compteurs et fin comparés au témoin; pas seulement exploration. |
| `rollback` | Retour vérifié au témoin, données et sauvegardes préservées. |
| `network` | Hôte/deux clients, distances et reconnexion sans cadence multipliée ni désynchronisation. |

Les trois étapes particulières de chaque profil complètent ces familles : seuils
15/16/30, masques 4/516, réarmement, voix et portes ne sont pas interchangeables.

## Enregistrer un résultat réel

Chaque contrôle possède `state` et `evidence` :

- `pending` : pas de résultat, `evidence` doit rester `null`;
- `blocked` : `evidence` contient seulement `notes`, avec l'obstacle précis;
- `passed` ou `failed` : dossier de preuve complet obligatoire.

Un dossier de preuve complet contient exactement :

- `tester` et `date` réelle au format `YYYY-MM-DD`, non future;
- `mode`, identique au mode du profil;
- `game_build_sha256`, `baseline_payload_sha256`, `variant_payload_sha256` :
  empreintes de l'exécutable testé et des deux ensembles de fichiers testés;
- `test_plan_sha256` : empreinte fournie par l'audit pour ce profil **avant
  l'essai**, couvrant sa définition, les étapes, les scénarios communs et le
  texte de l'étude liée (fins de ligne normalisées);
- `notes` : observations et résultat, avec les écarts constatés;
- `artifacts` : liste non vide d'objets `{ "path": "...", "sha256": "..." }`
  pointant vers de vraies captures ou journaux locaux.

Pour les ensembles de fichiers, conserver aussi le manifeste exact des chemins
et empreintes dans les preuves. L'audit vérifie le format de leurs empreintes,
pas leur correspondance physique avec une installation exécutée. Cette
correspondance et le contenu des captures nécessitent une relecture humaine.
Le témoin et la variante doivent avoir des empreintes distinctes.

Les fichiers de preuve doivent être sous `validation/evidence/reconstruction/`.
Ce dossier est ignoré par Git : captures, journaux et données personnelles ne
sont pas publiés automatiquement. Les chemins absolus, traversées `..`, liens
symboliques sortant du dossier, fichiers absents et empreintes différentes sont
refusés. Un clone sans les preuves locales ne peut pas vérifier les résultats
enregistrés; ne pas effacer une preuve ou la remplacer par un simple lien mort.

Toute modification de la définition génératrice invalide son empreinte dans le
registre. Toute modification du protocole invalide les preuves précédentes.
Mettre à jour les consignes et recommencer les essais concernés; ne pas réétiqueter
d'anciennes captures comme preuve d'une nouvelle variante.

## Commandes sans écriture ni lancement du jeu

### Identifier exactement le témoin et la variante

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_bundle_evidence.py .analysis\laboratories\20260925\czech2-ger12-lie.lab.zip.disabled --profile czech2-ger12-lie --game "D:\Games\Hidden and Dangerous 2" --archives-only
.\.venv\Scripts\python.exe tools\reconstruction_bundle_evidence.py .analysis\scene-patches\co-burgundy3-ambience.scene-patch.zip.disabled --profile co-burgundy3-ambience --game "D:\Games\Hidden and Dangerous 2" --archives-only
```

L'outil reconstruit la comparaison **en mémoire** depuis les sources actuelles
et compare chaque octet du contenu attendu au ZIP existant. Il ne se contente
pas de croire les empreintes du rapport inclus. Il conserve les refus de sources
modifiées et de surcharges; `--archives-only` consigne les exclusions.

Il produit les deux empreintes `baseline_payload_sha256` et
`variant_payload_sha256`, ainsi que leurs listes exactes de chemins, tailles et
SHA-256. Le condensat porte sur le JSON canonique `{ "files": [...] }`, tri des
fichiers par chemin, clés triées, séparateurs compacts et échappement ASCII.
Pour les laboratoires, les chemins incluent leurs espaces de mission distincts;
pour les comparaisons de scène, ils désignent seulement les deux fichiers de
mission concernés. Conserver ces listes avec les preuves du déploiement réel.

**20 laboratoires et trois comparaisons de scène ont été recontrôlés** avec cet
outil. Les sept profils Africa 5 restent hors de ce total : aucun ZIP complet
n'est inventé. L'ancienne comparaison Burgundy3 sans champ `profile` est reconnue
par la correspondance exacte des quatre contenus reconstruits, pas par son nom.

Ces empreintes ne couvrent ni l'installation entière, ni les fichiers de menu
produits lors d'un déploiement ultérieur : consigner séparément ces derniers.
Aucun résultat du registre n'est rempli automatiquement.

### Contrôler les registres

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_runtime_audit.py
.\.venv\Scripts\python.exe tools\reconstruction_runtime_audit.py --require-recorded-passes
.\.venv\Scripts\python.exe tools\runtime_validation_audit.py
```

La première commande vérifie seulement structure, couverture et preuves présentes.
Elle réussit avec 298 cas pending, sans annoncer une validation moteur.
La deuxième échoue tant que tous les résultats expérimentaux ne sont pas
enregistrés comme réussis avec leurs preuves. La troisième reste le contrôle
séparé des 56 essais stables et 21 candidates de conversion.

Même avec toutes les preuves enregistrées, **aucune activation n'est autorisée
automatiquement**. Il reste la relecture des preuves, la compatibilité avec le
paquet cible et les critères de promotion du
[registre maître](../experimental/RECONSTRUCTION_BACKLOG/VALIDATION.md).

Vingt tests synthétiques vérifient couverture, modes, signatures de recettes,
chemins, commentaires de blocage, dates, empreintes, résultats incomplets et
non-promotion automatique. Dix autres vérifient les contenus des ZIP, les sources
changées, leurs empreintes, noms ambigus et métadonnées d'activation refusées.
Avant l'ajout du préparateur ci-dessous, la suite comptait **252 tests réussis**;
ces tests utilisent des preuves inventées et ne comptent jamais comme essais du jeu.

## Préparer les fiches sans rien lancer

`tools/prepare_reconstruction_trials.py` rassemble les éléments nécessaires aux
essais ultérieurs dans un dossier documentaire local. Il ne déploie rien, ne
retire aucun suffixe `.disabled` et ne lance ni jeu, ni installateur, ni
gestionnaire. Cet outil documentaire ne construit pas la copie de jeu;
les [outils de préparation native](ESSAIS_NATIFS.md) prennent désormais cette étape en charge.

```powershell
.\.venv\Scripts\python.exe tools\prepare_reconstruction_trials.py --game "D:\Games\Hidden and Dangerous 2" --labs .analysis\laboratories\20260925 --scenes .analysis\scene-patches --archives-only --build --output .analysis\reconstruction-trials\preparation-20260926
```

Sans `--build` et sans `--output`, l'outil effectue les contrôles en lecture seule.
Pour vérifier ultérieurement un dossier existant, remplacer `--build` par
`--check-output` en conservant les autres arguments. Cette vérification refait
les comparaisons aux sources, puis compare chaque document; elle ne se contente
pas de relire les empreintes qu'il contient. Un changement d'exécutable, de ZIP,
d'étude, de protocole ou de source rend le dossier obsolète.

Le dossier contient un index, un relevé général et une fiche Markdown/JSON pour
chacun des 49 profils. Les fiches réunissent :

- l'étude, les prérequis et les étapes particulières;
- les six contrôles solo ou sept contrôles coop, sans résultat inventé;
- les empreintes du protocole, de l'exécutable source et du ZIP désactivé;
- les chemins, tailles et empreintes des fichiers témoins et variantes;
- les surcharges locales exclues et les profils modifiant le même script;
- le protocole de retour arrière à vérifier dans la future copie isolée.

Les 20 laboratoires et trois comparaisons de scène sont recontrôlés contre les
archives. Si un laboratoire manque, l'outil vérifie sa recette et essaie sa
fermeture avant de distinguer « ZIP non construit » et « dépendance absente ».
Les sept profils Africa 5 conservent leur obstacle explicite; aucun fichier
vide n'est fabriqué. Une erreur de source ou un ZIP ambigu/corrompu interrompt
la préparation au lieu d'être reclassé comme un simple prérequis.

Les sorties sont limitées à un **nouveau** sous-dossier direct de
`.analysis/reconstruction-trials/`. Aucun dossier existant n'est écrasé et les
liens de sortie sont refusés. Une écriture interrompue laisse son dossier partiel
pour inspection; il n'est pas réutilisé silencieusement. Les fichiers produits
ne contiennent que des métadonnées et des consignes, pas les contenus commerciaux.
Ils restent ignorés par Git, notamment parce qu'ils contiennent des chemins locaux.

Quatorze tests supplémentaires couvrent cette préparation. Sur ce poste,
**265 tests réussissent sur 266**, avec un test de création réelle de lien
symbolique non exécuté faute de privilège Windows. Ce résultat ne valide aucun
des 298 essais moteur, qui restent en attente.
