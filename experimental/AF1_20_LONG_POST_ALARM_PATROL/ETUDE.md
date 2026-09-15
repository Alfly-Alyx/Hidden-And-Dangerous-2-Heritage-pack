# Étude expérimentale — longue patrouille post-alarme d'AF1_20

État : **branche exclusive incomplète**, 15 septembre 2026. La rotation courte
release reste sélectionnée ; aucun fichier commercial n'est modifié/compilé.

## Verdict

`OnAlarmDone()` restaure les alarmes, la vue, l'optimisation, l'arme et la
marche, puis joue deux rotations de deux secondes. Une ancienne boucle commentée
vise `AF1_20_01..08` et appelle quatre fois `LOOKAROUND`.

Les checkpoints `_02..08` existent dans Base et Patch ; `_01` est absent. De
plus, aucun `Label LOOKAROUND` n'existe dans `AF1_20.scr`. Décommenter le bloc
échouerait donc même après création du point. Le placement et le contenu exact
des pauses sont deux lacunes séparées.

## Profils

- `SHORT_RELEASE` : rotations `%%turnleft/%%turnright`, comportement actuel ;
- `LONG_PATROL` : boucle 01–08, seulement avec point 01 et sous-routine de pause
  modernes, tous deux documentés et validés.

[`VARIANT_SELECTOR.scr.disabled`](VARIANT_SELECTOR.scr.disabled) garde les deux
corps exclusifs et sélectionne la release. La conversation initiale sous
`ACTIVATE`, ses trois animations aléatoires, les rayons, signaux, alarmes,
`AF1_pobocnik` et `AF1_20_alert` sont hors périmètre.

## Point 01 et pause modernes

Les positions commerciales `_02..08` et les candidats anonymes ambigus sont
documentés dans `experimental/AFRICA1_AF1_20_MISSING_LOOP_POINT/PROPOSITION.md`.
Deux candidats près du segment `_08/_02` sont à moins de 0,01 unité d'écart de
distance : aucun renommage automatique n'est justifiable.

[`AF1_20_01.plan.disabled`](AF1_20_01.plan.disabled) exige soit une source
historique, soit un placement moderne explicite. La sous-routine moderne
`LOOKAROUND_MODERN` proposée reprend uniquement les deux animations release et
leurs délais ; elle n'est pas présentée comme le code perdu.

## Validation

1. Tracer la sortie d'alarme release et la conversation initiale.
2. Créer `_01` dans une copie par l'éditeur, avec liens `_08↔_01↔_02` vérifiés.
3. Tester la sous-routine moderne isolément, interruption d'alarme pendant
   chaque animation comprise.
4. Faire dix tours, puis déclencher chaque type d'alarme sur chacun des huit
   segments ; aucune seconde boucle ne doit survivre à l'interruption.
5. Tester signal 21, rayons 150/50, mort, obstacle joueur et sauvegarde/reprise.
6. Revenir à `SHORT_RELEASE` et confirmer la conversation et les alarmes
   strictement identiques.

## Retour arrière

Restaurer ensemble `AF1_20.scr` et `check2.bin` commerciaux. Aucun changement
de la conversation, des alarmes ou du binding n'est requis.

## Sources internes

- scripts Base/Patch `AFRICA1/AF1_20.scr` ;
- Base/Patch `MISSIONS/AFRICA1/check2.bin` ;
- étude `experimental/AFRICA1_AF1_20_MISSING_LOOP_POINT/`.
