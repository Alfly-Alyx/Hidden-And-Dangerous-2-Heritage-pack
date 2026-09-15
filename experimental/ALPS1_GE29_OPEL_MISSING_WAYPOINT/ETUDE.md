# Ge29 — reconstruction géométrique de `opel_1_2`

État : **manifeste spéculatif, aucun checkpoint installé**, 15 septembre 2026.
La route release reste active et rien n'est compilé.

## Constat

La branche signal 2 conduit l'Opel de `opel_01` à `opel_02`. Entre ces deux
appels subsiste `//HUMAN_Drive("opel_1_2",30);`. Le nom `opel_1_2` est absent de
`check2.bin`, `scene2.bin` et `actors.bin`. La branche signal 3 ne contient pas
ce vestige et doit rester strictement release.

Le graphe commercial entre les deux points nommés contient déjà un nœud anonyme
et `hakl_09`. Aucun de ces deux n'est renommé ou dupliqué.

## Construction géométrique

Deux coordonnées sont conservées dans [`MANIFEST.md`](MANIFEST.md) :

- candidat A, principal : milieu direct de `opel_01` et `opel_02`, calculé
  uniquement depuis les deux voisins nommés ;
- candidat B, contrôle de courbure : milieu du segment intérieur entre le nœud
  anonyme 45 et `hakl_09`.

Le candidat A reçoit seulement le nom de laboratoire
`TEST_opel_1_2_linear`. Il ne devient `opel_1_2` qu'après validation dans
l'éditeur : projection sur la chaussée, hauteur, direction, rayon, liens et
coûts de navigation. Le candidat B mesure si la route réelle impose une courbe ;
il n'est pas une seconde destination.

[`WAYPOINT_CONSTRUCTION.plan.disabled`](WAYPOINT_CONSTRUCTION.plan.disabled)
conserve la formule et interdit toute écriture mission. Une future copie de
ge29 pourrait insérer le point uniquement dans la branche signal 2, aux vitesses
commerciales 40 → 30 → 90.

## Tests après validation éditeur

1. Baseline signal 2 et signal 3, dix parcours chacun, trajectoire et vitesse.
2. Afficher A et B sans les relier ; mesurer route, pente, collision et écart au
   centre de chaussée.
3. Relier A seul sous nom `TEST_`, puis conduire à 30 entre opel01/opel02.
4. Tester véhicule occupé, alarmes, collision avec `hakl_09`, sortie, téléport
   `o1/o2`, sauvegarde/reprise et plusieurs joueurs.
5. Ne renommer en `opel_1_2` que si une preuve historique ultérieure confirme
   le placement ; sinon conserver le statut moderne ou abandonner.

Rejet : choix motivé seulement par le nom, renaming du nœud 45 ou de `hakl_09`,
modification de la branche signal 3, oscillation, sortie de route ou différence
réseau.

## Sources

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_29.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/check2.bin`,
  `scene2.bin`, `actors.bin` ;
- `experimental/ALPS1_GE29_MISSING_VEHICLE_POINT/`.
