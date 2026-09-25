# Variantes reproductibles

État vérifié le **25 septembre 2026** sur la branche
`codex/reconstruction-phase-1` : vingt et un profils, soit vingt-quatre scripts dérivés,
ont été construits et
comparés aux sources commerciales. **Aucun n'est installé ni validé en jeu.**

Le [catalogue machine](../reconstruction-variants.json) contient uniquement les
empreintes, les prérequis et les modifications minimales. Les scripts commerciaux
complets restent dans l'installation légitime et dans `.analysis/`, ignoré par
Git. Le [générateur](../../tools/build_reconstruction_variant.py) les lit sans
modifier les archives.

## Résultat de la série

| Profil | Modification | Octets générés | Étude |
|---|---|---:|---|
| `arctic4-guard3-alarm-post` | Un déplacement réactivé à l'alarme. | 2506 | [Garde 3](../ARCTIC4_STATIC_GUARD3_ALARM_POST_ADDITIVE/ETUDE.md) |
| `czech2-ger12-lie` | Posture couchée avant l'animation de mort existante. | 380 | [Ger12](../CZECH2_GER12_DEATH_STAGING/ETUDE.md) |
| `sicily1-it40-open-doors` | Deux changements d'état après les déverrouillages existants. | 2464 | [Portes](../SICILY1_IT40_DUAL_DOOR_BEHAVIOR/ETUDE.md) |
| `africa1-officer21-cutscene-move` | Déplacement au point existant pendant la cinématique 10. | 3369 | [Officier](../AFRICA1_OFFICER_21_CUTSCENE_MOVE/ETUDE.md) |
| `czech6-isu-base-route` | Route de trois points à 12; sortie Patch conservée. | 2144 | [ISU](../CZECH6_ISU_DUAL_ROUTE/PROPOSITION.md) |
| `libye3-german15-move-to-alarm` | Déplacement vers l'alarme avant les réglages de combat. | 1342 | [German15](../LIBYE3_GERMAN15_ALARM_DUAL_BEHAVIOR/ETUDE.md) |
| `africa1-af126-safe-idle` | Sortie moderne de la boucle vide après alarme, sans route ajoutée. | 1750 | [Garde 26](../AFRICA1_AF1_26_INCOMPLETE_START_LOOP/ETUDE.md) |
| `czech3-nosic2-long-smoke` | Rotation historique et pause 42 s à la place des 5 s, sans cumul. | 8358 | [Porteur](../CZECH3_NOSIC2_SMOKE_IDLE_VARIANT/ETUDE.md) |
| `arctic4-gunner1-flak-exit` | Sortie moderne du véhicule avant le retour au poste. | 1635 | [Flak](../ARCTIC4_AMBIENT_ANIMATIONS_AND_FLAK_EXIT/PROPOSITION.md) |
| `arctic4-guard2-cold-fallback` | Activité Cold moderne dans la branche aléatoire 3. | 3674 | [Ambiance](../ARCTIC4_AMBIENT_ANIMATIONS_AND_FLAK_EXIT/PROPOSITION.md) |
| `arctic4-guard6-cold-fallback` | Activité Cold moderne après la bouteille, délais conservés. | 1493 | [Ambiance](../ARCTIC4_AMBIENT_ANIMATIONS_AND_FLAK_EXIT/PROPOSITION.md) |
| `sicily2-three-cleared-wave` | Au moins trois états 0 déclenchent la vague; aucune charge modifiée. | 3228 | [Déminage](../SICILY2_CHARGES_DUAL_STATE_WAVE/ETUDE.md) |
| `czech4-pianist-signal5` | Réception moderne de l'alerte, fermeture audio/animation, proximités désarmées. | 3224 | [Pianiste](../CZECH4_MISSING_SIGNAL_HANDLERS/PROPOSITION.md) |
| `czech6-radio-before-alarm` | Paire Base : récompense du sabotage seulement avant l'alarme. | 1156 + 2415 | [Radio](../CZECH6_RADIO_SABOTAGE_DUAL_PATH/ETUDE.md) |
| `arctic4-guard3-sit-smoke` | Assise/cigarette génériques et sorties protégées, sans animation incertaine. | 3049 | [Assise](../ARCTIC4_STATIC_GUARD3_SIT_SMOKE/ETUDE.md) |
| `normandy-inner-guards-proximity` | Paire N24/N25 : détecteur 30 m activé, routes commerciales inchangées. | 1857 + 1915 | [Gardes](../NORMANDY1_LEGACY_ACTIVATORS/ETUDE.md) |
| `burgundy3-direct-explosion-sound` | Paire destruction/son : signal moderne 11 sur la branche directe seulement. | 3348 + 1239 | [Dépôt](../BURGUNDY3_DEPOT_EXPLOSION_SOUND/ETUDE.md) |
| `libye3-panzer-driver-alarm-gate` | Masque historique des alarmes du conducteur jusqu'à l'arrêt, trajet inchangé. | 1121 | [Panzer](../LIBYE3_PANZER_DRIVER_ALARM_GATE/ETUDE.md) |
| `africa5-storage01-alarm-filter` | Filtre historique des pas; script seul, laboratoire bloqué. | 1733 | [Magasin](../AFRICA5_STORAGE_ALARM_FILTER_VARIANTS/ETUDE.md) |
| `africa5-storage02-alarm-filter` | Filtre historique pas/cadavre; script seul, laboratoire bloqué. | 2536 | [Magasin](../AFRICA5_STORAGE_ALARM_FILTER_VARIANTS/ETUDE.md) |
| `africa5-storage03-alarm-filter` | Même filtre, réactivation commerciale distincte; laboratoire bloqué. | 2682 | [Magasin](../AFRICA5_STORAGE_ALARM_FILTER_VARIANTS/ETUDE.md) |

Le choix est **exclusif avant chargement** : une copie laboratoire emploiera soit
les scripts commerciaux, soit leurs variantes pour les mêmes propriétaires. Aucun
signal de sélection, objectif, compteur ou état de sauvegarde n'est ajouté.
Burgundy 3 ajoute toutefois un signal de comportement 11, explicitement moderne
et limité au récepteur sonore; ce n'est pas un sélecteur de variante.
Ne pas empiler ces profils avec une autre modification du même script. La
fabrication d'un fichier seule n'est pas la création d'une mission laboratoire
complète. Dix-huit profils disposent de
[copies A/B inertes](LABORATOIRES_DESACTIVES.md), contrôlées hors jeu. Les trois
profils Africa 5 sont reconstruits comme scripts seulement : leur laboratoire
est refusé car `af4_runway01_detector.scr` est référencé mais absent de la
source commerciale. Le contrôle n'est pas contourné.

## Reproduction

Depuis la racine du dépôt, sans lancer le jeu :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_reconstruction_variants.py
.\.venv\Scripts\python.exe tools\build_reconstruction_variant.py --list
.\.venv\Scripts\python.exe tools\build_reconstruction_variant.py --game "D:\Games\Hidden and Dangerous 2" --check-all
.\.venv\Scripts\python.exe tools\build_reconstruction_variant.py --game "D:\Games\Hidden and Dangerous 2" --profile czech2-ger12-lie --build
```

Les contrôles sont en lecture seule par défaut. `--build` exige un seul profil;
la sortie doit se terminer par `.scr.disabled` et rester sous `.analysis/`.
Un fichier existant est refusé, jamais écrasé. `--output` permet de choisir un
nouveau nom dans cet espace. Aucune option n'installe le résultat dans le jeu.

Exceptions volontaires à l'export d'un seul script : `czech6-radio-before-alarm`,
`normandy-inner-guards-proximity` et `burgundy3-direct-explosion-sound`
contiennent chacun deux changements inséparables. Leur contrôle simple
fonctionne, mais `--build` dans le générateur de scripts est refusé. Employer
le générateur de laboratoires pour ces paires; aucun composant n'est proposé
isolément.

Les vérifications couvrent les archives effectives Base/Patch/Sabre, les tailles
et SHA-256 de **71 entrées commerciales distinctes**, la liaison unique du propriétaire,
sa présence sérialisée, les prérequis nommés et l'unicité de chaque modification.
Une entrée correspondante de `PatchX01.dta` est refusée plutôt que de deviner sa
priorité. Les fins de ligne et l'encodage commercial restent inchangés en dehors
des modifications explicites, y compris lorsque le script mélange CRLF et LF.

### Installation déjà modifiée

Le contrôle par défaut refuse les surcharges libres pertinentes. Sur cette
machine, `Missions/africa1/Scripts.dta` fait 4663 octets, SHA-256
`fba2f1a04084c6cbe22f064aebe43721c044a8e0765649d20fec7b99a6788b6c`, contre
4622 octets dans l'archive. La liaison AF1_21 reste présente, mais cela ne prouve
pas la compatibilité de toute la mission modifiée.

Pour reconstruire **explicitement la seule référence commerciale** :

```powershell
.\.venv\Scripts\python.exe tools\build_reconstruction_variant.py --game "D:\Games\Hidden and Dangerous 2" --archives-only --check-all
.\.venv\Scripts\python.exe tools\build_reconstruction_variant.py --game "D:\Games\Hidden and Dangerous 2" --archives-only --profile africa1-officer21-cutscene-move --build
```

Cette option n'efface ni ne remplace la surcharge. Le rapport enregistre son
empreinte sous `excluded_loose_overrides` et conserve
`installed_game_compatibility: not_tested`. Les six contrôles réussissent contre
les archives dans la première série; les deux profils Africa 1 doivent continuer
à refuser la surcharge en contrôle strict.

## Empreintes des sorties vérifiées

| Profil | SHA-256 |
|---|---|
| Arctic 4 | `6e1a366e75794249aa437b3577b50c45c32376409ddde197f9b57a306c17817c` |
| Czech 2 | `837c589b309fb8e1d6d48196c64ab370cb988fbe88e61e12f52b12b8fa0e4164` |
| Sicily 1 | `2c72cb89285b4d7cb7d8a4e79448f30554ce4e645f84aac4aa86412d746d1342` |
| Africa 1 | `92e3656a2cc5f73be16a2e1069d79b0e87a404d459f4875c41534ebd96498024` |
| Czech 6 | `19b0274ca5efce004f0933b9ef74d25d9020b1055728b749d9a94673abebfac7` |
| Libye 3 | `12bc58e7220307830df876f682735b1af80fcfb9e8a840bc65b1323a6699ae29` |
| Africa 1, garde 26 | `b3bde2cafffa5965d277d81c3f28dbf5dd0e624b5b09f21c9648162a2c03a57e` |
| Czech 3, porteur 2 | `4a314845ed46d07e243ad1b3b3890798fab87b2d4b28736b152d25bb82412c30` |
| Arctic 4, sortie Flak | `a194663f7d19402bfa200370a30966daefc7e4b433834a6a21e32835beab4b37` |
| Arctic 4, froid garde 2 | `c0e66c88797c17af1663bf8da69f033245e86670742009a7fb63bf1009d43f04` |
| Arctic 4, froid garde 6 | `368463f3e57880f0e41b18a65c2cd6a541996882020e4c6dde9018f5e3e86118` |
| Sicily 2, vague après déminage | `0f0414e6432b26f2030ffb10f40713db4e51ee3ddf7acb5b84fb1b93e72caf37` |
| Czech 4, pianiste | `d2c32f0046563682a5d9299d6eaa67d97f6b5791584908838ec0a6eaf51633e6` |
| Czech 6, câble Base | `9d72a651971131ccf4ba40335ce0040d2c47a1ebd390b30c22665473a84db3dc` |
| Czech 6, opérateur Base | `30ec6bfa42feaea3efdc9a5389bcb2a34b158195c46f63109464c0c9d0026359` |
| Arctic 4, garde 3 assis | `df4e8fee9961535e4d254162715754ca16dd11609dcd62b07b487b8392d95470` |
| Normandy 1, N24 | `d8c31825aa45b46c0ded16a2a19cd4ad58de9badc3915bdffd5281f397be6ed0` |
| Normandy 1, N25 | `f89dcd7e860f8986cf1793280131e89cf1fa2350b477f6a5f472bcbc3b566252` |
| Burgundy 3, destruction | `f764069924bdc930c04cc8b6b299c4813dbd966a2e7c04f393b11c6d099dab8d` |
| Burgundy 3, son | `e5b83bd4a6e590c11eb0d5126aadfcb72d2d28acb11fc4f5e02ff2aec835e294` |
| Libye 3, conducteur du Panzer | `7e3ddec85b59630239f97f1edfcc28d250e457c04f92a5c7564c97a2cd6ac21c` |
| Africa 5, magasin 01 | `702a6dcbea0f0d823cc5fc1fdb4ba694fbea4627609bd0a33b200aa070586e6a` |
| Africa 5, magasin 02 | `7cdfd0cba404299588deaaf2414a7fb06c4c724556bba0a321331d7b648b2ec9` |
| Africa 5, magasin 03 | `68051d380d7512b700aa08e30fb0b39a5b490f7270664042e17d45de597ef5b2` |

Les 47 tests de variantes utilisent des données inventées et ne nécessitent pas
de jeu. Ils couvrent notamment les refus de source modifiée, liaison dupliquée,
ressource absente, remplacement ambigu, surcharge inattendue, sortie active,
écriture dans le jeu et écrasement d'un fichier. Quatorze autres tests couvrent
les groupes de scripts indivisibles et les propriétaires 4DS typés. Les vingt-quatre
diff réels ont aussi
été inspectés. Ce ne sont ni une compilation du langage du jeu ni des essais
de comportement de l'IA.

## Travail restant avant activation

Les dix-huit copies laboratoire sont générées, intégralement désactivées.
Résoudre d'abord la dépendance manquante pour les trois profils Africa 5.
Résoudre ensuite leur
chargement réel et leur espace de scripts dans une installation de test isolée,
puis exécuter les scénarios des études et la
[barrière de validation](VALIDATION.md). Les vingt et un profils restent `pending` pour
l'exécution; aucun résultat manuel n'a été converti artificiellement en succès.
