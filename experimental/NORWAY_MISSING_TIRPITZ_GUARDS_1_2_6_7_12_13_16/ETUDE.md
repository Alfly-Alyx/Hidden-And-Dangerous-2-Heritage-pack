# Étude expérimentale — sept gardes Tirpitz absents de Norway

État : **implantation bloquée, scripts commerciaux retrouvés**, 15 septembre
2026. Aucun acteur, checkpoint, binding ou script de jeu n'est créé/compilé.

## Correction de l'hypothèse initiale

Les acteurs et bindings 1, 2, 6, 7, 12, 13 et 16 sont bien absents de
`actors.bin` et `scripts.dta`, dans Base comme dans Patch 1.12. En revanche, les
sept fichiers `R_Nor_Tirpic1/2/6/7/12/13/16.scr` subsistent dans la couche
commerciale Base et apparaissent comme scripts non liés dans l'audit effectif.

Il ne faut donc pas recréer leurs comportements à partir des neuf voisins : les
scripts propres constituent une preuve plus forte. Le chantier porte sur les
acteurs, leurs routes, leur équipement et l'intégration du sender.

## Inventaire exact

| ID | Acteur exact | Binding exact | Script commercial | Chemins requis |
| ---: | --- | --- | --- | --- |
| 1 | absent | absent | présent | `T1_1`, `T1_2`, `T1_3` absents |
| 2 | absent | absent | présent | `T2_1`, `T2_2` absents |
| 6 | absent | absent | présent | `T6_1`, `T6_2` absents |
| 7 | absent | absent | présent | `T7_1`, `T7_2` absents |
| 12 | absent | absent | présent | `T12_1`, `T12_2`, `T12_3` absents |
| 13 | absent | absent | présent | `T13_1`, `T13_2` absents |
| 16 | absent | absent | présent | `T16_1`, `T16_2` absents |

Les recherches sont exactes et terminées par zéro afin d'éviter le faux positif
`tirpic_guard_1` dans `tirpic_guard_11/14/15/18`.

`dummy_see2` existe, mais `dummy_see1` est absent des deux scènes inspectées.
Plusieurs scripts retrouvés ciblent donc eux aussi un point de regard perdu.

## Scripts retrouvés

[`SCRIPTS_SURVIVANTS.md`](SCRIPTS_SURVIVANTS.md) détaille les rayons, routes et
particularités. Ils attestent pour chaque garde : suspension initiale, ronde,
signaux 1 chapeau, 2 bouteille, 3 froid, 4 regard vers la mer, signalement de
l'alarme à `objectives` puis reprise.

Ces scripts ne sont pas pour autant prêts à l'emploi : les chemins sont absents,
la bouteille pointe vers une frame vide, le point de regard manque pour quatre
des sept et aucune identité/position d'acteur n'est conservée.

## Sender et probabilités

`R_Nor_action_Sender.scr` tire toujours :

- un signal avec `_RandomInt(12)+1`, écrêté à 4 ;
- un numéro avec `_RandomInt(18)+1` ;
- une attente de 7 à 17 secondes.

Ses branches actives ciblent 3, 4, 5, 8, 9, 11, 14, 15 et 18. Les sept branches
étudiées sont commentées. Le sender figure lui-même comme non lié dans l'audit,
donc son porteur doit être identifié ou créé dans une copie expérimentale avant
de conclure que les actions aléatoires tournent dans la release.

Le fragment
[`PROTOTYPE_SINGLE_SENDER_EXTENSION.scr.disabled`](PROTOTYPE_SINGLE_SENDER_EXTENSION.scr.disabled)
doit être fusionné dans **l'unique** sender de la variante. Il ne crée aucun
second tirage. Ainsi chaque garde existant conserve exactement sa probabilité
de sélection de 1/18 par cycle ; seules sept anciennes issues sans destinataire
deviennent actives. Les distributions des quatre signaux et du délai restent
inchangées.

## Placement : porte bloquante

Aucune coordonnée historique des acteurs ni de leurs 16 checkpoints n'a été
retrouvée. Les numéros des gardes voisins, leur proximité visuelle ou une zone
vide du navmesh ne suffisent pas à attribuer des positions historiques.

[`PLACEMENTS.plan.disabled`](PLACEMENTS.plan.disabled) laisse donc tous les
transforms à `TBD_SOURCE_OR_MODERN_EDITOR`. Deux voies seulement sont admises :

1. source attribuée donnant position/orientation et parcours ;
2. implantation moderne en éditeur, explicitement annoncée comme telle.

Sans l'une de ces voies, aucun acteur ne doit être ajouté.

## Intégration graduée

1. Réserver une copie de mission et mesurer les neuf gardes release, sender
   inclus ou absent.
2. Implanter un seul garde pilote, avec ses chemins et son point de regard,
   sans modifier aucun acteur 3/4/5/8/9/11/14/15/18.
3. Lier son script commercial propre ; ne dériver un script que pour renommer
   un checkpoint moderne, avec diff et source indiqués.
4. Tester ronde, quatre signaux, alarme, retour, décès, modes 3/7 et sauvegarde.
5. Ajouter les gardes un par un. Le sender complet n'est activé qu'après
   validation des sept.
6. Comparer les fréquences des neuf gardes existants sur un grand nombre de
   tirages : chacune doit rester 1/18 par cycle.

Critères d'arrêt : chemin manquant, acteur bloqué, double sender, modification
d'une probabilité existante, équipement inventé présenté comme officiel,
régression d'objectif ou divergence Base/Patch inexpliquée.

## Retour arrière

Retirer les sept nouveaux bindings, acteurs et chemins, puis restaurer le sender
commercial avec ses sept branches commentées. Les neuf gardes existants et
leurs fichiers ne sont jamais modifiés.

## Sources internes

- scripts Base `NORWAY/R_Nor_action_Sender.scr` et
  `R_Nor_Tirpic1/2/3/4/5/6/7/8/9/11/12/13/14/15/16/18.scr` ;
- Base/Patch `MISSIONS/NORWAY/actors.bin`, `scene2.bin`, `scripts.dta` ;
- `output/audit/script-bindings.json` et
  `.analysis/script-bindings-refresh.json`.
