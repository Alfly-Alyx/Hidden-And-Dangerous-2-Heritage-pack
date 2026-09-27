# Tuyaux visuels déformables modernes

**MODERNE, 27 septembre 2026. Deux skins à deux LOD et dix-huit clips désactivés.**
Les [pièces tenues animées](ANIMATIONS_PIECES_TENUES.md) ont maintenant leurs
tuyaux synchronisés. Le raccord côté sac reste fixe ; le raccord côté pièce
tenue suit sa translation et sa rotation. Il s'agit d'une déformation visuelle
originale, **pas d'une simulation physique ni d'une attache au joueur**.

Les recettes [allemande](modern-flmwr35-hose-animation.json) et
[britannique](modern-flmthr2-hose-animation.json) épinglent chacune le modèle
tenu et sa banque. Les fichiers statiques précédents ne sont pas remplacés.
Le générateur ne lit aucune archive, géométrie ou animation commerciale.

## Construction native

Les sommets, normales, indices et matériaux des deux tuyaux originaux restent
conservés. Chaque modèle ajoute huit os modernes indépendants sous une racine
skin d'identité. Les deux LOD contiennent respectivement **576/288 sommets et
192/96 triangles**. Les os sont des repères d'influence du tuyau, pas des os
de main, de joueur ou de sac.

Les deux premières sections restent fixes ; les deux dernières suivent la
pièce tenue. Les quatre sections intermédiaires utilisent une progression
douce selon leur distance au repos. Chaque sommet appartient à un seul os,
avec indice natif un-basé et octet de mélange nul. Ce sont les mouvements
différents des sections voisines qui déforment les surfaces entre elles.

Tous les os ont le même pivot de repos : la prise droite de la pièce tenue.
Le dernier os peut donc reprendre exactement les rotations et translations
de cette pièce, au lieu d'approcher la trajectoire courbe du raccord par une
suite de positions linéaires. Les raccords sont vérifiés aussi entre les clés.

Neuf clips par modèle reprennent les durées et états visuels du lot tenu,
avec neuf pistes de transformations chacun. `Shot`/`AimShot` n'émettent rien ;
`Rel` reste un abaissement/retour, pas un rechargement fonctionnel.
Les couples tuyau/pièce tenue ne sont **pas encore chargés ensemble par le jeu**.

## Contrôles

Quatorze tests nouveaux couvrent les empreintes, la conservation des deux LOD,
les inverse-binds, les indices de peau, 1 122 poses à demi-trame, les raccords
entre séquences, la provenance, les refus et l'export sans écrasement.
Le lecteur historique reste limité par défaut à un LOD ; la lecture de deux
LOD exige une option explicite et vérifie les poids des deux niveaux, même
lorsqu'un seul est sélectionné. Les tests antérieurs restent applicables.

Deux planches d'assemblage, chacune avec six poses et trois vues, ont été
inspectées. Elles montrent un sac fixe et une pièce tenue mobile sans mains.
L'éclairage de ces aperçus n'est pas celui du jeu.

L'audit natif est terminé : **1 122 poses**, 11 220 calculs de nœud, 8 976 poses
d'os de tuyau et 2 244 déformations de LOD, soit **969 408 sommets évalués**.
Les 484 704 sommets des sections de raccord sont également comparés aux
composants fixes/mobiles. Résidus : pose et skin nuls, palette au plus
5,97 × 10⁻⁸, raccord fixe nul, raccord tenu au plus **1,99 × 10⁻⁸**.
Rapport privé : `.analysis/modern-equipment-hose-native-20260927.json`.

Les routines épinglées de pose, palette et skin sont exécutées en émulation
bornée séparée. La pose de départ est explicitement réinitialisée à chaque
échantillon ; ce n'est pas une scène persistante ni une validation des
transitions du jeu. Chargeur, callbacks, rendu, son et partie restent exclus.

La comparaison native respecte la particularité déjà établie de `SetRot` :
une rotation dont `abs(w)` atteint 1 en float32 donne une matrice d'identité,
même si de très petits x/y/z subsistent. Le contrôle du raccord compare donc
deux matrices natives, sans remplacer celle de la pièce tenue par une rotation
mathématique renormalisée. Un test protège cette distinction.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/build_modern_equipment_hose.py --case F35 --output-name F35_HoseMotion_nouveau
.\.venv\Scripts\python.exe tools/build_modern_equipment_hose.py --case F2 --output-name F2_HoseMotion_nouveau
.\.venv\Scripts\python.exe tools/equipment_hose_native_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/modern-equipment-hose-native_nouveau.json'
```

Omettre le nom de sortie pour compiler uniquement en mémoire. Les lots privés
`F35_HoseMotion_v1` et `F2_HoseMotion_v1` sont sous `.analysis/modern-assets/`.
Chacun contient 27 fichiers : rig, neuf couples natifs, six aperçus, planche et
manifeste. Tous les fichiers natifs sont `.disabled` ; aucun Item ni effet ajouté.

Empreintes :

- F35 : `acae0e6ded8dc4b74d3887d697ec5a5a6d47bc50d459d8d854853fc8b73c7715` ;
- F2 : `1451f7c7775c17e8a243674492955241aeee41d8bd05a30fc997e963ae0545ed`.

## Limites et réalisations restantes

Cette solution couvre les séquences modernes connues avec un sac fixe.
Elle n'est pas un solveur de positions arbitraires : ni longueur constante,
collision, gravité ou réaction au déplacement du sac. L'intégration des modèles
dans un ensemble chargé, les attaches joueur/IA, les mains et la caméra restent
nécessaires. Visibilité, éclairage, transitions et comportement moteur restent
à qualifier ; effets, sons, consommation, dégâts et sauvegardes à réaliser.
Il ne reste donc pas seulement des tests pour ces deux armes.
