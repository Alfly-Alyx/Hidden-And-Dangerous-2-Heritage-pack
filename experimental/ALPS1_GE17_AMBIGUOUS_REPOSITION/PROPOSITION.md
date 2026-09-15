# Alps 1 — repositionnement ambigu de GE17

État : **variante réversible HUMAN_Move retenue**, 14 septembre 2026. Le
prototype est désactivé et ne modifie pas la séquence commerciale de release.

## Verdict

La séquence de GE17 conserve deux solutions commentées au même endroit :

- HUMAN_Move("ge17_03") ;
- FRM_TeleportNearCheckpoint(me, "ge17_03", "ge16_sniper").

Elles sont mutuellement exclusives. Le déplacement déterministe vers ge17_03
est retenu. Le téléport entre deux checkpoints introduit une position aléatoire
dans l’espace partagé de GE16, rend les collisions moins reproductibles et
n’exprime pas une destination exacte.

## Géométrie

- ge17_03 : 205.687698, 3.473050, 19.879480, rayon 1 ;
- ge16_sniper : 208.277405, 3.530415, 19.420326, rayon 3 ;
- distance entre les deux : environ 2.63 unités ;
- l’acteur GE17 démarre vers 207.064804, 3.505886, 21.702841.

Le mouvement est donc court, local et observable. Le checkpoint ge17_02 est à
environ 0.32 unité de ge17_03, ce qui impose tout de même un test visuel de la
transition.

## Delta proposé

PROTOTYPE_GE17_MOVE.scr.disabled remplace uniquement la ligne de déplacement
commentée par HUMAN_Move("ge17_03"). La ligne de téléport reste absente. Les
rotations, l’animation hledamkulomet, son délai de 15 secondes, ge17_04 et la
pose sedila1 restent dans leur ordre commercial.

## Test et retour arrière

1. Observer au moins dix cycles sans alarme, caméra proche des pieds et du MG.
2. Vérifier l’orientation après ge17_03 et avant hledamkulomet.
3. Déclencher chaque événement d’alarme avant, pendant et après le mouvement.
4. Tester reprise de sauvegarde pendant le trajet et pendant l’animation.
5. Contrôler que GE16 peut rejoindre ge16_sniper sans collision avec GE17.
6. Retour arrière : restaurer ge_17.scr commercial ; aucun point n’est ajouté.

La variante est rejetée si le mouvement provoque une oscillation entre ge17_02
et ge17_03, un chevauchement d’acteurs ou une interruption de la suite release.

