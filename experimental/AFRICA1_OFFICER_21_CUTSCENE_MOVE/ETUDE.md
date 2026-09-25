# Africa 1 — déplacement de l'officier dans la cinématique 10

État : **prototype commercial reproductible désactivé**, 25 septembre 2026.
La compatibilité avec la mission Heritage installée reste à étudier.

## Position exacte du vestige

Le script effectif est `Patch.dta::scripts/africa1/af1_21.scr`, 3371 octets.
Il est lié au seul acteur `AF1_21`, position
`(6.329951, 0.543395, 71.905884)` dans les acteurs Patch.

Contrairement au raccourci de l'inventaire initial, le déplacement commenté
`HUMAN_Move("AF1_21_01")` se trouve **pendant `OnCutscene(10)`**, après le
démarrage de la caméra, de la voix et un délai de 2100 ms. Il n'est pas exécuté
avant le lancement de la cinématique. `AF1_21_01` existe dans le `check2.bin`
Patch; `camera_officer` existe dans `scene2.bin`, à
`(5.238705, 1.966853, 75.309525)`.

Le profil `africa1-officer21-cutscene-move` retire seulement les deux caractères
`//`. Il ne déplace pas l'appel et ne modifie ni le dialogue, ni
`OnCutsceneDone(10)`, ni les objectifs 1/2, ni les valeurs sauvegardées 21/55.
L'appel historique est **OFFICIEL**; son bon cadrage et sa synchronisation dans
la géométrie finale sont encore une **INFÉRENCE**.

## Sélection et conflit local

Une future mission laboratoire choisira exclusivement le script commercial ou
ce profil avant chargement. Aucune modification de l'introduction 3 ni des
scripts player01..04 n'est incluse : leur composition est une autre étude.

Le [générateur](../RECONSTRUCTION_BACKLOG/VARIANTES_REPRODUCTIBLES.md) vérifie
cinq ressources et produit 3369 octets. Son contrôle strict refuse actuellement
`Missions/africa1/Scripts.dta` libre : le registre installé diffère de l'archive.
L'option explicite `--archives-only` a servi à vérifier et construire la copie
de référence, sans toucher à ce registre. Son empreinte est consignée dans la
procédure commune; la présence de la liaison AF1_21 seule ne suffit pas à
certifier la compatibilité avec tous les ajouts Heritage.

## Essais encore nécessaires

Mesurer la durée du déplacement et le cadrage; tester un joueur devant le
chemin, loin de l'officier et dans chaque orientation d'approche. Vérifier la
voix, l'animation `%%af1_ital1`, le retour de caméra, l'arme et les sous-titres.
Interrompre par alarme/mort et fin de cinématique; vérifier objectifs et valeurs
sauvegardées une seule fois. Sauvegarder/reprendre avant et pendant la scène.

Le déplacement pourrait bloquer la suite d'une animation déjà synchronisée :
ne pas compenser en modifiant les délais sans nouvelle mesure. Retrait par
retour à la copie commerciale sur partie laboratoire neuve. Aucun test en jeu
ni changement de l'installation n'a été effectué pour ce profil.
