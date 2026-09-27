# Repère des modèles modernes en vue subjective

**27 septembre 2026.** Correction de fabrication, pas une validation en jeu.
Les anciens modèles et leurs banques restent inchangés pour la reproduction.

## Pourquoi la conversion est nécessaire

Les recettes modernes ont été dessinées avec **+Y vers l'avant, +Z vers le haut**.
Dans le modèle FPV commercial Benelli examiné, la bouche `blsdum` est située vers
**+Z** par rapport à `fpv_weapon` : positions mondiales locales au modèle
environ `(0,09550; -0,09019; 0,87773)` contre
`(0,09491; -0,15960; 0,09559)` pour la racine. Ces positions sont des preuves
de géométrie ; elles ne donnent pas le cadrage des armes modernes.

Le nouveau choix d'auteur est **+X à droite, +Y en haut, +Z vers l'avant**.
L'échange `(x,y,z) → (x,z,y)` a un déterminant négatif : ce n'est pas une simple
rotation. `modern_fpv_axes.py` transforme donc ensemble les positions, normales,
rotations natives, échelles, inverse binds, boîtes d'os et boîtes de dummies.
L'ordre des sommets des triangles est inversé. UV, matériaux, indices d'os,
poids, noms et parentés restent conservés. Une seconde conversion restitue
**chaque octet du modèle original**.

Les quaternions natifs XYZW deviennent `(-x,-z,-y,w)` sans renormalisation.
Les matrices sont conjuguées par la permutation des axes. Les équipements
conservent leurs durées et leurs clés ; les anciennes banques de mains ne
peuvent pas être réutilisées telles quelles.

## Mains recalculées, jamais réfléchies

Les deux maillages et squelettes commerciaux de mains sont lus sous empreintes
exactes, seulement en mémoire. Aucune réflexion n'est appliquée à ces sources.
De nouvelles orientations de prise, directions de coude et flexions des doigts
sont calculées sur leurs longueurs et positions de repos inchangées.

La recette de prise utilise `S × R × D`, avec `D = diag(1,-1,1)` dans le repère
de repos de la paume. Le résultat est une rotation propre, vérifiée comme telle.
Il s'agit d'une **décision moderne d'animation**, pas d'une animation d'origine
retrouvée. Les pouces restent à la pose de repos et le contact fin des doigts
n'est pas qualifié. Aucun étirement du bras ou déplacement local d'os n'est permis.

## Sorties privées et aperçus

`build_equipment_fpv_view_bank.py` produit deux modèles et 36 clips privés
désactivés. Les alias `PROTOTYPE_F35VH…`, `PROTOTYPE_F35VR…`, `PROTOTYPE_F2VH…`
et `PROTOTYPE_F2VR…` sont distincts des anciens et restent limités à 19 caractères.
Le marqueur des clips reste `DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL`.

Empreintes SHA-256 des modèles corrigés, incluant les boîtes des dummies :

- F35 : `ce64ec2e8f1bafe6bf8e0e3dd808d89164ef4b802ddcc4f7ca00a2f0d709829e`.
- No. 2 : `80aba0ce1189b41755e954a14e850a773b5f58ed405a3492167513f04c72531e`.

Les banques `F35_CorrectedFPV_v1` et `F2_CorrectedFPV_v1`, sous
`.analysis/modern-assets/`, contiennent **46 fichiers chacune** : modèle,
18 clips, 24 vues individuelles, deux planches et manifeste. Aucun modèle de
mains ni texture commerciale n'est exporté. Les aperçus privés lisent la géométrie
moderne et les poses depuis les fichiers sérialisés. Les quatre planches des
deux variantes et les vues géométriques au repos sont inspectées.

La caméra de ces aperçus est volontairement explicite : perspective de diagnostic,
champ horizontal 90°, image 960 × 600, plan proche 0,03. Les triangles traversant
le plan proche sont découpés ; la profondeur interpolée utilise `1/z`.
**Ce ne sont pas des captures du jeu.** Le cadrage et la visibilité des pièces
proches restent à ajuster ; le calcul des matrices natives est étudié séparément
dans [Projection de caméra](../RECONSTRUCTION_BACKLOG/PROJECTION_CAMERA_NATIVE.md).

Les associations de ressources disposent de l'option explicite `--view-axes`.
Elles ne remplacent pas les anciennes banques. Les variantes d'un même cas
utilisent toujours le même groupe expérimental et sont donc mutuellement
exclusives ; aucun identifiant global n'est réservé.

Les quatre laboratoires privés `F35H_CorrectedFPVResources_v1`,
`F35R_CorrectedFPVResources_v1`, `F2H_CorrectedFPVResources_v1` et
`F2R_CorrectedFPVResources_v1` vérifient **156 demandes de ressources** et
**36 lectures/relocalisations d'animations**. Leurs modèles et clips sont
comparés octet pour octet aux banques inspectées ; chaque laboratoire contient
12 fichiers, manifeste compris. Les tables centrales ne sont pas émises.

## Contrôles et limites

Les tests synthétiques vérifient la réversibilité binaire, les normales et les
faces des deux LOD, les inverse binds et boîtes, les matrices aux clés et entre
clés, les orientations propres des paumes et **1 140 cibles de poignets**
accessibles avec des longueurs de bras synthétiques explicitement distinctes
des mains commerciales. Les entrées et variantes non prévues sont refusées.

Le contrôle dense `fpv_view_native_audit.py` reconstruit les banques, compare
leurs octets aux fichiers privés enregistrés, puis exécute les sous-systèmes
natifs isolés. Le rapport `.analysis/fpv-view-native-20260927.json` est terminé :
**36 lectures natives, 36 séquences denses et huit enchaînements**, soit
**2 668 instants observés**, 2 757 378 sommets de mains et 2 305 152 sommets de
tuyau. Les deux LOD sont évalués 5 336 fois ; les limites utilisent 170 752
transformations de coins. Temps, poses, skin et limites correspondent à leurs
références ; erreur maximale de palette `2,683e-7`, sans dépassement des boîtes
ni des sphères. Les 4 632 cibles de poignets des clips seuls restent sous
`1,690e-7` aux clés et `0,000162827` entre clés.

**Défaut restant mesuré, non qualifié comme réussi :** les 704 observations de
poignets pendant les changements de clips atteignent un écart de **0,040576**
unité de modèle, environ 4 cm à l'échelle d'auteur. Le mélange des rotations
d'os ne conserve pas exactement la contrainte de prise. Les huit scénarios
artificiels couvrent des ordres directs/inversés, pas uniquement les transitions
accessibles en jeu. Leur bonne exécution native ne valide donc pas le contact
visuel ; les transitions et contraintes de mains restent du travail d'implémentation.

Le [correcteur de contact après mélange](CONTACT_MAINS_ET_TRANSITIONS.md)
localise désormais ce défaut et le ramène sous `1,696e-7` dans les 704
observations, avec contrôle des palettes natives. Il s'agit d'un calcul
d'auteur hors jeu, **pas d'un raccordement au client**. Le même dossier mesure
les intersections des doigts et explique pourquoi la première proposition
d'opposition des pouces n'est pas retenue comme solution validée.

La découverte des os, le chargement des animations,
le temps/les poses, les palettes, le skin et les limites utilisent des
émulateurs distincts ; ce n'est pas un chargement de scène complet.

Il reste l'intégration au modèle chargé, le cadrage réel, les prises fines et
transitions visuelles, l'attache dorsale, les événements et le comportement
fonctionnel. Les gestes Rel/Jammed restent des présentations sans action de jeu.

```powershell
.\.venv\Scripts\python.exe tools/build_equipment_fpv_view_bank.py --case F35 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --previews --output-name F35_Vue_nouvelle
.\.venv\Scripts\python.exe tools/build_equipment_fpv_resource_lab.py --case F35 --hand H --view-axes --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name F35_Vue_Ressources_nouvelles
.\.venv\Scripts\python.exe tools/fpv_view_native_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/fpv-view-nouveau.json
```
