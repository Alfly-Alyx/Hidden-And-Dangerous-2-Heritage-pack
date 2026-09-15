# Africa 1 — points de patrouille manquants d’AF1_04

État : **reconstruction bloquée faute de géométrie unique**, 14 septembre 2026.
Aucun script actif, checkpoint, binding ou fichier stable n’est modifié.

## Verdict

Le script commercial contient une patrouille active de AF1_04_g01 à g05, puis
deux déplacements commentés vers g06 et g07. Le check2 commercial ne nomme que
g01 à g05 et AF1_04_alert. Les deux noms absents ne peuvent pas être reconstruits
par interpolation sans inventer leur emplacement.

Les lignes g06/g07 ne doivent donc pas être décommentées tant que deux points
n’ont pas été créés dans une copie de mission, reliés et validés en jeu.

## Preuves géométriques

| Point | Position commerciale (x, y, z) | Rayon |
| --- | --- | ---: |
| AF1_04_g01 | -131.291565, 18.418146, 34.075836 | 80 |
| AF1_04_g02 | -107.712952, 10.155030, 45.818047 | 80 |
| AF1_04_g03 | -92.866272, 6.334103, 107.342560 | 64 |
| AF1_04_g04 | -32.948528, 0.918266, 81.587204 | 8 |
| AF1_04_g05 | -96.619247, 4.266477, 51.495346 | 80 |

La route la plus courte du graphe entre g05 et g01 repasse par g02. Elle ne
révèle donc pas deux nœuds omis. La forme irrégulière du circuit, les rayons très
différents et l’absence des noms dans la table excluent une extrapolation fiable.

Base et Patch conservent exactement les mêmes deux lignes commentées. Ce doublon
atteste l’intention d’une patrouille plus longue, pas les coordonnées perdues.

## Limite d’autorité

Un point sans nom proche d’un segment n’est pas automatiquement g06 ou g07 :
le graphe sert plusieurs acteurs et les coûts n’encodent pas l’ordre historique.
Aucun candidat ne sera renommé, dupliqué ou injecté dans check2 sur cette seule
base.

Le fichier PLAN_RECONSTRUCTION_CHECK2.disabled fixe les conditions minimales
d’un futur essai. La branche release reste la référence et ne change pas.

## Validation exigée avant tout décommentaire

1. Retrouver une source historique, une capture éditeur ou deux positions
   explicitement attribuées à g06/g07.
2. Dupliquer les enregistrements complets de points dans une copie de check2 ;
   ne jamais modifier à la main les index ou la taille de section.
3. Recalculer liens et coûts dans l’éditeur et vérifier les deux sens du graphe.
4. Tester dix boucles, alarmes à chaque tronçon, OnAlarmDone, mort et reprise de
   sauvegarde.
5. Seulement après ces tests, créer une variante expérimentale du script qui
   réactive les deux lignes. Le retour arrière restaure check2 et AF1_04.scr
   commerciaux ensemble.

## Risques

- point sous le terrain ou derrière un obstacle ;
- détour ou boucle sur g02 causé par de mauvais liens ;
- rayon trop large qui masque l’erreur de placement ;
- blocage lors d’une alarme entre g05, g06, g07 et g01 ;
- sauvegarde incompatible si le script référence un nom absent.

