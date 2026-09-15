# Placement moderne et protocole de test

Ce document décrit un **candidat reproductible**, pas le transform historique
de `TUT_Talker_02`.

## Candidat A — axe de regard de Talker_01

Le quaternion commercial de `TUT_Talker_01` définit un axe horizontal. En
plaçant le nouvel acteur à 1,80 unité devant son axe local négatif Z, puis en le
tournant de 180 degrés autour de Y, on obtient :

| Champ | Valeur candidate |
| --- | --- |
| position | `(-56.764634, 1.144970, -4.152906)` |
| quaternion | `(0.938359, 0, -0.345661, 0)` |
| échelle | `(1, 1, 1)` |
| distance à Talker_01 | `1,80` |
| distance à `T_dummy_speech` | `1,78` |

La justification est géométrique : les deux personnages se font face, tous deux
restent près du porteur officiel et aucun déplacement du contrôleur n'est
nécessaire. La valeur 1,80, l'axe choisi et le quaternion retourné sont
**MODERNES**. L'éditeur doit confirmer la convention de l'axe avant ; si elle
est inversée, le candidat est rejeté au lieu d'être corrigé silencieusement.

Le voisinage statique contient notamment `T_dummy_OS` à 2,71 unités et
`l_tut_tbl_53` à 2,93 unités du candidat. Ces distances ne prouvent pas une
collision, mais imposent une inspection visuelle et un test de navigation.

## Préconditions

- travailler sur une copie nommée et sélectionnable du Tutorial ;
- conserver un exemplaire byte-identique de la mission release ;
- n'ajouter qu'un acteur, un item et deux bindings ;
- journaliser entrée/sortie des rayons, début/fin des voix, morts et statut de
  l'objectif 7 ;
- commencer avec `goodone = 1` inchangé.

## Séquence de validation

1. **Baseline release.** Parcourir normalement la zone, déclencher le dialogue
   de `ControlorOne`, tuer aucun instructeur, puis sauvegarder/reprendre.
2. **Présence.** Charger la copie et vérifier modèle, visage `e_f073`, sol,
   orientation, ligne de vue et absence de blocage du passage.
3. **Seuils.** Approcher le porteur par quatre directions ; confirmer le départ
   à sept unités et l'arrêt au-delà de dix.
4. **Ordre positif.** Entendre une seule fois 00990123, puis 00990130 et 31,
   sans 00990124 à 28 et sans seconde source sonore.
5. **Réentrée.** Sortir avant la fin, revenir immédiatement puis après dix
   secondes. Noter le comportement commercial avant toute décision de latch.
6. **Concurrence.** Déclencher le signal 20 de `ControlorOne` avant, pendant et
   après la conversation ; aucun morphing ni sous-titre ne doit se superposer.
7. **Morts.** Tester Talker_01 seul, Talker_02 seul, puis les deux, avant et
   pendant la scène ; l'objectif 7 ne doit recevoir qu'un échec cohérent.
8. **Sauvegarde.** Reprendre avant la portée, pendant chacune des trois voix,
   après interruption et après fin.
9. **Repli.** Désactiver la variante et confirmer le retour exact à la baseline
   release sans acteur, binding ni état sauvegardé résiduel.

## Critères d'arrêt

Rejeter le candidat si l'acteur flotte, traverse un décor, bloque un trajet,
tourne dos à Talker_01, se trouve hors ligne de vue, double un dialogue existant,
réarme en boucle sans contrôle ou modifie la progression Tutorial. Un autre
placement reste une nouvelle création moderne et reçoit sa propre mesure.
