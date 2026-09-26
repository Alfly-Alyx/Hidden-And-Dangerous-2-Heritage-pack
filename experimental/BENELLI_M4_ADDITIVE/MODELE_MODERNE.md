# Benelli : modèle extérieur original, expérimental

État au 26 septembre 2026 : **MODERNE — généré et contrôlé hors moteur**.
Ce premier modèle statique n'est pas une arme jouable et ne termine pas les
phases B1–B4. Il ne reproduit aucun maillage, texture ou animation du jeu.

## Livrable reproductible

La [recette originale](modern-world-model.json) décrit 25 pièces visuelles,
six matériaux unis et quatre repères modernes. Le
[générateur](../../tools/build_modern_asset.py) produit :

- un modèle natif v41 `PROTOTYPE_HERITAGE_BenelliWorld.4ds.disabled`;
- un OBJ et son MTL pour inspection et retouche dans un modeleur;
- une planche de trois vues hors moteur;
- un manifeste d'empreintes avec provenance et limites explicites.

Les deux niveaux de détail comportent **1 264 et 728 triangles**. Un nœud racine
regroupe les pièces et les repères. Les proportions, l'origine approximative de
prise, l'orientation +Y/+Z, les couleurs et la portée de changement de détail
sont des choix artistiques modernes. Aucun matériau externe n'est nécessaire.
L'apparence low-poly doit encore être comparée aux personnages et aux armes dans
le jeu; la planche n'est pas une capture du moteur.

```powershell
.\.venv\Scripts\python.exe tools\build_modern_asset.py
.\.venv\Scripts\python.exe tools\build_modern_asset.py --output-name BenelliWorld_examen
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_modern_asset.py
```

Sans `--output-name`, seul le contrôle en mémoire est exécuté. La sortie est un
nouveau dossier sous `.analysis/modern-assets/`; aucun fichier existant n'est
écrasé. Les chemins liés sont refusés. Le générateur n'ouvre aucune archive du
jeu, ne crée aucun Item/Weapon et ne choisit aucun ID.

## Vérifications effectuées

- Deux lecteurs indépendants du dépôt relisent la structure et la géométrie.
- Les 30 nœuds, indices de faces, matériaux et deux LOD sont contrôlés.
- Chaque pièce est fermée, orientée vers l'extérieur et sans triangle dégénéré;
  normales finies/unitaires et bornes cohérentes entre niveaux.
- Treize tests automatisés couvrent aussi la génération répétable, les entrées
  invalides, les sorties désactivées et le refus d'écrasement.
- Planche visuelle inspectée : profil, vue oblique et dessus. Elle vérifie le
  modèle généré, pas les matériaux ni les ombres du jeu.

Le modèle vérifié mesure 207 614 octets, SHA-256
`6bc815610019739adc101d3e00319fa7819dd3d436b05e66d0521d258f291c8c`.
La recette normalisée porte l'empreinte
`a549b76865c1b37f6f610dee76f9f56974760901e185f140a2b2d244e9c21f0b`.
Les modèles binaires restent régénérables localement; la recette constitue la
source versionnée, pas un fichier extrait du jeu.

## Format et provenance technique

La structure v41 a été recoupée avec la documentation communautaire primaire
[4ds.bt de hdmaster, RoadTrain et pudingus](https://github.com/RoadTrain/mafia-formats/blob/master/4ds.bt)
et les [types LS3D](https://github.com/RoadTrain/mafia-formats/blob/master/ls3d.bt),
consultés le 26 septembre 2026. Le générateur est une implémentation originale
limitée aux objets statiques et repères; il ne reprend pas les templates.

Le contrôle local `models.dta::MODELS/w_garand.4ds`, 19 607 octets, SHA-256
`46b8b2b582c7fe6ea6228ba9f0d6a8639fcde502d7922c2d585f2b604fb47a3e`,
confirme les indices de matériau à partir de 1, le dernier LOD à portée zéro,
le quaternion identité et les drapeaux de nœuds employés. Aucun sommet ou
matériau de ce modèle n'est importé. La signification complète des drapeaux et
le rendu effectif doivent encore être vérifiés dans le moteur.

## Travail restant, distinct des contrôles de géométrie

1. Charger ce modèle comme décor dans un laboratoire isolé, contrôler face
   visible, échelle, éclairage et transition de détail. Aucun essai effectué.
2. Construire/adapter la vue FPV statique et son contrat de squelette : les
   quatre repères modernes ne sont **pas** les os des neuf animations officielles.
3. Développer ensuite la voie Item/Weapon additive, après rescan d'identifiants;
   conserver la boussole 9 inchangée. Le simple modèle ne réserve pas 359.
4. Qualifier tenue, dépôt, reprise, sons, mécanique, sauvegarde et réseau dans
   leurs essais séparés. Le fichier reste désactivé jusque-là.
