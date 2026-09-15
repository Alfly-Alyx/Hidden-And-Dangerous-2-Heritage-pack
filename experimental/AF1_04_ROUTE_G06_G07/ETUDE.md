# Étude expérimentale — prolongement g06/g07 de la ronde AF1_04

État : **bloqué par deux placements manquants**, 15 septembre 2026. Ce dossier
prolonge `AFRICA1_AF1_04_MISSING_PATROL_POINTS` sans modifier la mission.

## Verdict

L'acteur `AF1_04`, son binding et sa logique complète sont intacts. Sa boucle
active suit `AF1_04_g01` à `g05`; deux lignes commentées ajoutent ensuite `g06`
et `g07` avant le retour à `g01`. Base et Patch contiennent les cinq premiers
points et `AF1_04_alert`, mais aucun checkpoint `AF1_04_g06/g07`.

L'ordre historique est attesté ; les deux transformations et leurs liens de
navigation ne le sont pas. Une interpolation entre g05 et g01 serait une
création moderne et ne doit pas être présentée comme restauration.

## Profils exclusifs

| Profil | Route | Statut |
| --- | --- | --- |
| `RELEASE_G01_G05` | g01→g02→g03→g04→g05→g01 | référence sélectionnée |
| `LONG_G01_G07` | même route puis g06→g07→g01 | interdit tant que les deux points ne sont pas créés et validés |

Le fragment
[`PROTOTYPE_LONG_ROUTE.scr.disabled`](PROTOTYPE_LONG_ROUTE.scr.disabled)
remplace uniquement `GUARD_LOOP` dans une copie expérimentale. Il ne modifie ni
la suspension/activation, ni `OnSignal(20)`, ni `OnAlarm`, ni `OnAlarmDone`, ni
la mort, ni le point `AF1_04_alert`.

## Placement progressif

[`CHECKPOINTS_G06_G07.plan.disabled`](CHECKPOINTS_G06_G07.plan.disabled) laisse
les coordonnées à `TBD`. Une source historique peut les débloquer. À défaut,
un level designer peut choisir deux points modernes après inspection du terrain,
mais doit documenter position, quaternion, rayon, voisinage, pente, visibilité
et justification tactique.

Les cinq positions commerciales et l'analyse du graphe sont consignées dans
`experimental/AFRICA1_AF1_04_MISSING_PATROL_POINTS/PROPOSITION.md`. Le plus
court chemin g05→g01 repasse par g02 ; il ne révèle donc pas les deux points.

## Validation

1. Baseline : dix boucles g01–g05, alarmes sur chaque segment et retour.
2. Créer g06/g07 dans une copie de `check2.bin` avec l'éditeur, jamais par
   modification manuelle des index/tailles.
3. Vérifier g05→g06→g07→g01 dans les deux sens et sous blocage joueur.
4. Tester dix longues rondes, alarme, signal 20, mort et sauvegarde sur chaque
   nouveau segment.
5. Comparer vue, temps de parcours, couverture et progression à la release.

Critères d'arrêt : point sous terrain, route impossible, détour vers g02,
alarme retardée, référence de checkpoint non résolue ou placement non attribué.

## Retour arrière

Sélectionner `RELEASE_G01_G05`, remettre `AF1_04.scr` et `check2.bin`
commerciaux comme une paire, puis supprimer les deux points de la copie.

## Sources internes

- scripts Base/Patch `AFRICA1/AF1_04.scr` ;
- Base/Patch `MISSIONS/AFRICA1/check2.bin`, `actors.bin`, `scripts.dta` ;
- étude antérieure `experimental/AFRICA1_AF1_04_MISSING_PATROL_POINTS/`.
