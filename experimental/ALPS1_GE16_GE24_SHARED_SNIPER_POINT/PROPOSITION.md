# Alps 1 — point ge16_sniper partagé par GE16 et GE24

État : **GE16 testable ; GE24 séparé et non reconstruit**, 14 septembre 2026.
Aucun script actif n’est remplacé.

## Verdict

GE16 et GE24 conservent chacun un HUMAN_Move("ge16_sniper") commenté pendant
leur réaction d’alarme. Seul GE16 conserve aussi HUMAN_SetSniper(1,1). Le
checkpoint commercial existe, mais sa géométrie montre qu’il appartient à GE16 :

| Élément | Position (x, y, z) | Distance à ge16_sniper |
| --- | --- | ---: |
| ge16_sniper | 208.277405, 3.530415, 19.420326 | 0 |
| acteur GE16 | 209.041656, 3.581576, 20.390566 | env. 1.24 |
| acteur GE24 | 282.850769, 9.485687, 39.547092 | env. 77 |

Envoyer GE24 vers ce point commun provoquerait une longue migration vers la
zone de GE16. La ressemblance des commentaires ne suffit donc pas à imposer une
restauration commune.

## Branches indépendantes

### GE16 — prototype à faible spéculation

PROTOTYPE_GE16_SNIPER.scr.disabled remet le déplacement et le mode sniper dans
l’ordre exact des lignes commentées. Il ne change ni le filtre d’événements
2/16/256, ni le verrou a, ni les alarmes.

### GE24 — aucune copie du comportement GE16

La branche GE24 reste release. Une éventuelle création moderne doit employer un
nouveau nom, par exemple ge24_reaction_test, choisi et validé près de la position
commerciale de GE24. Elle ne doit pas appeler HUMAN_SetSniper : aucun tel vestige
n’existe dans GE24.

Placer ce nouveau point exactement au spawn de GE24 serait vérifiable, mais
probablement un déplacement sans effet. Une destination utile exige donc un
choix en éditeur fondé sur la visibilité et la collision ; aucune coordonnée
n’est inventée ici.

## Tests GE16

1. Déclencher séparément les événements 2, 16 et 256.
2. Vérifier le trajet très court jusqu’à ge16_sniper et l’entrée en mode sniper.
3. Répéter les alarmes : le verrou a doit empêcher une réinitialisation.
4. Tester OnAlarmDone, mort, sauvegarde avant et après la prise de poste.
5. Vérifier que GE24 ne bouge jamais pendant ce test.

Retour arrière : restaurer uniquement ge_16.scr commercial. Aucun check2 n’est
ajouté pour cette branche.

## Tests d’une future création GE24

L’essai doit être emballé séparément de GE16, porter un nom de point distinct,
ne déplacer aucun checkpoint commercial et documenter explicitement son statut
moderne. Tester le trajet de 77 unités évité, la ligne de tir, la couverture et
les alarmes avant toute diffusion.

