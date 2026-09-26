# Essais des reconstructions expérimentales

Le [registre expérimental](reconstruction-runtime.json) est séparé du registre
du paquet stable `runtime-validation.json` et des conversions
`multiplayer-solo-runtime.json`. Il ne modifie aucun de leurs résultats.

Au 26 septembre 2026 : **27 profils, 165 contrôles, tous pending**. Aucun essai
moteur n'a été effectué par la création du registre ou son audit.

- 24 variantes de scripts : six contrôles chacune;
- trois comparaisons scène/registre coop : sept contrôles chacune, dont réseau;
- chaque profil pointe vers son étude et contient des étapes propres au
  comportement concerné, ses prérequis et l'empreinte de sa définition actuelle.

Les profils de scripts visent ici le solo; les comparaisons de scène visent la
coopération. Un résultat dans ce registre ne qualifie pas automatiquement les
autres modes, notamment Carnage ou une conversion coop vers solo.

## Avant un essai

Préparer une copie de jeu isolée et un déploiement réversible. Ne pas utiliser
directement l'installation personnelle. Les 20 laboratoires complets restent
désactivés; les quatre profils Africa 5 n'ont pas de mission complète tant que
le détecteur commercial de piste manque. Les trois comparaisons binaires ne
sont pas des paquets de mission activables. Le registre n'est pas une permission
d'ignorer ces prérequis, de créer une dépendance vide ou de forcer un déploiement.

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
  l'essai**, couvrant sa définition, les étapes et les scénarios communs;
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

```powershell
.\.venv\Scripts\python.exe tools\reconstruction_runtime_audit.py
.\.venv\Scripts\python.exe tools\reconstruction_runtime_audit.py --require-recorded-passes
.\.venv\Scripts\python.exe tools\runtime_validation_audit.py
```

La première commande vérifie seulement structure, couverture et preuves présentes.
Elle réussit avec 165 cas pending, sans annoncer une validation moteur.
La deuxième échoue tant que tous les résultats expérimentaux ne sont pas
enregistrés comme réussis avec leurs preuves. La troisième reste le contrôle
séparé des 56 essais stables et 21 candidates de conversion.

Même avec toutes les preuves enregistrées, **aucune activation n'est autorisée
automatiquement**. Il reste la relecture des preuves, la compatibilité avec le
paquet cible et les critères de promotion du
[registre maître](../experimental/RECONSTRUCTION_BACKLOG/VALIDATION.md).

Dix-huit tests synthétiques vérifient couverture, modes, signatures de recettes,
chemins, commentaires de blocage, dates, empreintes, résultats incomplets et
non-promotion automatique. La suite complète compte **240 tests réussis**;
ces tests utilisent des preuves inventées et ne comptent jamais comme essais du jeu.
