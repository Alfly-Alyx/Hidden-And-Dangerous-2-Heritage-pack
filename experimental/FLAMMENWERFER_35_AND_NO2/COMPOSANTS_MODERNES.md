# Composants modernes séparés : pièce tenue, sac et tuyau

**MODERNE, 27 septembre 2026. Six modèles statiques indépendants, désactivés.**
Les deux [ensembles de présentation](MODELES_MODERNES.md) sont désormais
décomposés sans supprimer de pièce ni modifier leurs géométries originales.
Ce travail prépare les attaches et mouvements séparés ; il ne les réalise
pas encore dans le squelette d'un personnage.

Les recettes [allemande](modern-flmwr35-components.json) et
[britannique](modern-flmthr2-components.json) attribuent chaque maillage et
chaque repère source à un seul composant. Les modèles sources sont épinglés
et restent inchangés. Aucun fichier du jeu n'est lu par ce générateur.

| Ensemble | Composant | Pièces | Triangles LOD haut / bas | Taille 4DS |
|---|---|---:|---:|---:|
| Flammenwerfer 35 | Pièce tenue | 9 | 432 / 240 | 70 770 octets |
| Flammenwerfer 35 | Sac dorsal | 11 | 880 / 520 | 145 067 octets |
| Flammenwerfer 35 | Tuyau statique | 1 | 192 / 96 | 30 297 octets |
| Portable No. 2 | Pièce tenue | 10 | 372 / 228 | 63 561 octets |
| Portable No. 2 | Sac dorsal | 8 | 900 / 524 | 147 115 octets |
| Portable No. 2 | Tuyau statique | 1 | 192 / 96 | 30 296 octets |

## Repères locaux et conservation

La pièce tenue est recentrée sur son repère moderne de main droite ; le sac
sur son repère dorsal ; le tuyau sur sa première extrémité. Ces repères sont
des choix visuels, **pas des noms d'os natifs ni une calibration FPV**.
Les origines dans l'ensemble de présentation sont enregistrées pour permettre
sa recomposition hors moteur.

Le recentrage modifie uniquement la position locale de chaque nœud conservé.
Les octets de sommets, normales, indices, matériaux et deux LOD sont identiques
aux sources. Le générateur compare les blocs après neutralisation de ces
douze octets de position. Il recalcule les limites du composant et vérifie
la hiérarchie plate relue.

Trois repères modernes sont ajoutés : départ/arrivée du tuyau et arrivée sur
le sac. Les deux raccords au repos sont comparés en coordonnées de présentation.
L'erreur maximale de recomposition est inférieure à **1,72 × 10⁻⁸** et celle
des raccords à **2,94 × 10⁻⁸**, dans les unités métriques des recettes.
**Aucune liaison en mouvement n'est créée.**

Les noms de fichiers `PROTOTYPE_F35_Held`, `PROTOTYPE_F35_Pack`,
`PROTOTYPE_F35_Hose` et leurs variantes `F2` respectent les 19 caractères
des alias natifs. Les racines et propriétés conservent la provenance moderne.

## Contrôles et reproduction

Douze tests nouveaux contrôlent les empreintes des six sorties, la partition
complète, les deux LOD, la conservation binaire, les origines, les raccords,
une deuxième lecture de géométrie, les refus et l'absence d'écrasement.
Les six planches de trois vues ont été inspectées. Elles montrent les pièces
séparées, pas une tenue par le joueur.

```powershell
.\.venv\Scripts\python.exe tools/build_modern_equipment_components.py --case F35 --output-name F35_Components_nouveau
.\.venv\Scripts\python.exe tools/build_modern_equipment_components.py --case F2 --output-name F2_Components_nouveau
```

Omettre le nom de sortie pour vérifier uniquement en mémoire. Les lots privés
`F35_Components_v1` et `F2_Components_v1` sont sous `.analysis/modern-assets/`.
Chacun contient trois modèles `.4ds.disabled`, trois OBJ/MTL, trois planches
PNG et un manifeste avec empreintes. Aucun Item, effet ou installation.

## Suites de réalisation

Les [mouvements des pièces tenues](ANIMATIONS_PIECES_TENUES.md) sont maintenant
créés : dix-huit séquences de présentation, sans mécanique fonctionnelle.
Créer les mouvements des mains, définir les attaches joueur/IA et les
transformations FPV, puis réaliser une solution de tuyau
déformable. Le tuyau de présentation est isolé précisément pour ne pas
l'annoncer solidaire de deux composants mobiles indépendants. Les événements,
sons, effet, comportement, entrée additive et sauvegardes restent distincts.
Il ne reste donc pas seulement des tests pour ces deux armes.
