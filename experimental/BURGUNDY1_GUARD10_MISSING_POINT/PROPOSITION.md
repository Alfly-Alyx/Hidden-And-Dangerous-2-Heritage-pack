# Burgundy 1 — checkpoint 10_02 manquant de la garde 10

État : **candidat géométrique moderne, identité historique non prouvée**, 14
septembre 2026. La variante reste désactivée et exige un check2 de laboratoire.

## Verdict

bur1_10.scr fait parcourir 10_01, saute une ligne commentée vers 10_02, puis
rejoint 10_03, 10_04 et 10_05. Les copies solo et coop conservent le même
vestige. Le check2 solo contient 10_01/03/04/05 mais aucun nom 10_02.

| Point | Position commerciale (x, y, z) |
| --- | --- |
| 10_01 | 44.205269, 2.114846, -50.734760 |
| 10_03 | 37.018887, 0.445664, -27.410927 |
| 10_04 | 66.131203, 2.047197, -68.768417 |
| 10_05 | 16.624050, 1.424546, -59.137669 |

Le plus court chemin pondéré du graphe entre 10_01 et 10_03 traverse trois
points sans nom :

| Index d’analyse | Position (x, y, z) |
| ---: | --- |
| 4706 | 41.139858, 1.305692, -44.770451 |
| 4710 | 40.218849, 1.268423, -40.495117 |
| 4713 | 41.177238, 0.817047, -35.565758 |

L’index 4710 se trouve à environ 1.48 unité du milieu géométrique de 10_01 et
10_03. C’est le meilleur **repère moderne** pour un arrêt intermédiaire, mais
les trois nœuds appartiennent au même chemin et aucun indice ne prouve lequel
portait historiquement le nom 10_02.

## Reconstruction prudente

La restitution historique reste bloquée. Pour un test moderne explicite,
l’éditeur peut attribuer le nom 10_02 au point existant situé à
40.218849, 1.268423, -40.495117, sans déplacer le point ni modifier ses liens.
Il faut le retrouver par position, pas par index d’analyse, car un réenregistrement
peut renuméroter les records.

Cette opération ajoute seulement un nom à un nœud navigable existant. Elle est
moins risquée qu’un nouveau point dupliqué et conserve la route commerciale.
Le fichier PROTOTYPE_GUARD10_02.scr.disabled ne devient testable qu’après cette
étape et ne doit jamais être installé seul.

## Tests

1. Dans une copie, nommer le point par l’éditeur et régénérer proprement la
   table ; aucune modification binaire manuelle.
2. Vérifier les liens 10_01 -> candidat -> 10_03 dans les deux sens.
3. Comparer dix parcours release et dix parcours avec arrêt 10_02.
4. Déclencher alarme avant, pendant et après chaque mouvement ; le script doit
   conserver ses handlers et ne jamais rester suspendu.
5. Tester obstruction, mort et sauvegarde/reprise sur le candidat.
6. Refaire séparément en coop avant toute conclusion : le nom commun ne prouve
   pas une synchronisation réseau identique.

Retour arrière atomique : restaurer check2 et bur1_10.scr commerciaux ensemble.
Le résultat doit rester étiqueté MODERNE tant qu’une source historique ne relie
pas explicitement 10_02 à cette position.

