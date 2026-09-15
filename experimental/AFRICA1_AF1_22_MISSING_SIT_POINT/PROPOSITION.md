# Africa 1 — destination assise manquante d’AF1_22

État : **ancrage spatial démontré, reconstruction check2 à tester**, 14 septembre
2026. Le dummy commercial reste intact et la ligne de déplacement reste
commentée dans la mission stable.

## Verdict

AF1_22.scr conserve HUMAN_Move("dummy_22_sit") en commentaire à la fin de sa
boucle. Ce nom n’existe pas dans la table des checkpoints, mais le cadre
dummy_22_sit existe dans scene2 à la position :

**19.567675, 0.765765, 63.880829**.

Le checkpoint humain AF1_22_0 existe à :

**19.546448, 0.235948, 63.284740**, rayon 1.

La distance tridimensionnelle entre les deux ancrages est de 0.797796 unité.
C’est une correspondance locale forte et bien meilleure que les autres points
nommés. Elle rend un checkpoint expérimental démontrable, sans prétendre que
son enregistrement binaire historique a survécu.

## Reconstruction proposée

Dans une copie éditeur :

1. dupliquer l’enregistrement complet de AF1_22_0 comme point humain ;
2. conserver son type et son rayon, puis le renommer dummy_22_sit ;
3. placer sa position à celle du dummy scene2, sans déplacer ce dernier ;
4. régénérer les liens et coûts au lieu de modifier les index à la main ;
5. vérifier que la destination est accessible depuis AF1_22_letadlo et rejoint
   encore la boucle START.

Le plan disabled contient ensuite la ligne exacte à tester. Elle ne doit être
copiée qu’après validation du point dans l’éditeur.

## Ce qui est conservé

- la halte AF1_22_odpoc, l’activité Turk et le cycle de fumée de 120 secondes ;
- le déplacement AF1_22_letadlo et les rotations ;
- les handlers d’alarme et la destination AF1_22_ad ;
- le dummy scene2 original et AF1_22_0 ;
- tous les bindings commerciaux.

## Risques et test

- le point du dummy peut être décoratif et non navigable ;
- la hauteur du dummy peut nécessiter une projection terrain faite par l’éditeur ;
- copier les liens de AF1_22_0 sans recalcul provoquerait une route incohérente ;
- le personnage peut atteindre le point sans adopter une pose assise, car la
  ligne retrouvée n’appelle aucune activité Sit.

Tester dix boucles, l’approche depuis letadlo, la collision du décor, une alarme
pendant le trajet, OnAlarmDone, mort, sauvegarde/reprise à chaque étape. Le
retour arrière restaure le check2 commercial et laisse la ligne commentée.

