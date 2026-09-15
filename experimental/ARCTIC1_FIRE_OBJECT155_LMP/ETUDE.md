# Arctic 1 — `Object155` et lightmaps du feu

État : **OWNER_CREATION = BLOCKED**, 15 septembre 2026. Aucun nouveau porteur,
binding ou script actif n'est créé.

## Verdict

`R_Arc1A_ohen_LMP.scr` est libre et cible `Object155`, mais sa boucle change la
lightmap sans aucune attente active. Le registre ne lui donne aucun
propriétaire. `Object155` apparaît une seule fois dans `scene2.bin` sous la
forme d'un grand bloc `LMAP` ; ce record ne contient pas le champ transform
monde utilisé par les frames ordinaires. Sa position ne peut donc pas être
extraite de façon autonome avec le décodeur de frames employé pour la mission.

La recherche de `FRM_SetLightMap` et `_RandomInt` dans le corpus ne fournit
aucun autre contrôleur commercial de feu à lightmaps aléatoires. Les scripts de
lightmap comparables sont des bascules statiques, pas des précédents de cadence,
d'arrêt ou de propriété. Rien ne justifie encore la création d'un acteur.

## Corps dormant exact

Le script atteste seulement :

- cible `Object155` ;
- indices 0, 1 et 2 via `_RandomInt(3)` ;
- `wait = 100`, jamais consommé ;
- ancien calcul aléatoire 10–29 et `delay(wait)`, tous deux commentés ;
- boucle infinie sans signal de démarrage ni d'arrêt.

Le fichier brut ne doit jamais être lié : il produirait une boucle serrée.

## Réévaluation du dossier antérieur

Le dossier
[`ARCTIC1_CAMPFIRE_LIGHTMAP`](../ARCTIC1_CAMPFIRE_LIGHTMAP/ETUDE.md) avait créé
une maquette moderne à 150–300 ms et proposé un dummy séparé. Cette maquette est
désormais classée **historique, non promotable**. Sa cadence est inventée et le
dummy n'a ni position ni précédent commercial. Elle n'est pas copiée ici.

## Conditions de réouverture

[`OWNER_GATE.plan.disabled`](OWNER_GATE.plan.disabled) exige d'abord :

1. une inspection éditeur ou une requête moteur donnant le transform effectif
   de `Object155` et l'objet visuel auquel le LMAP appartient ;
2. une capture des états 0/1/2 confirmant qu'il s'agit bien du feu visé ;
3. un contrôleur comparable attestant cadence, durée et arrêt, ou une décision
   explicite de créer un effet moderne ;
4. un propriétaire existant et spatialement cohérent, ou un transform approuvé
   pour un nouveau dummy ;
5. une preuve qu'une unique boucle survit aux signaux répétés et s'arrête au
   reload/à la sortie de mission.

Sans ces cinq éléments, seule la baseline statique est autorisée.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_ohen_LMP.scr` ;
- `.analysis/arctic1-full/MISSIONS/ARCTIC1/scene2.bin` ;
- `.analysis/arctic1-full/MISSIONS/ARCTIC1/actors.bin` ;
- `.analysis/arctic1-full/MISSIONS/ARCTIC1/scripts.dta` ;
- recherche corpus des appels `FRM_SetLightMap`.
