# Deux ensembles extérieurs originaux modernes

**MODERNE, 26 septembre 2026 ; statique, muet, désactivé, non validé en jeu.**
Les deux ensembles visuels sont fabriqués. Ils ne constituent pas encore des
armes, une tenue animée ni une simulation de lance-flammes.

| Création | Pièces / nœuds | Triangles des deux LOD | Fichier natif |
|---|---:|---:|---:|
| [Flammenwerfer 35](modern-flmwr35-world.json) | 21 / 27 | 1504 / 856 | 244661 octets |
| [Portable No. 2](modern-flmthr2-world.json) | 19 / 25 | 1464 / 848 | 239502 octets |

Chacun possède cinq matériaux unis et cinq repères modernes. Le premier utilise
une silhouette dorsale à deux volumes verticaux ; le second un volume annulaire
et une silhouette de pièce tenue distincte. Ces proportions, couleurs, surfaces
et placements sont des choix artistiques pour le jeu, pas des dimensions
historiques ni un plan de construction. Aucun mécanisme interne n'est représenté.

Le modèle contient ensemble le sac, la pièce tenue et le tuyau décoratif dans
une pose de présentation. Il faudra les séparer et les rattacher correctement
pour une tenue par un personnage ; les repères ne réalisent pas cette liaison.
Les tuyaux ne se déforment pas. Ni pression, combustible, flamme, collision,
dégât, bruit, objet d'inventaire ou numéro de munition ne sont liés.

## Fabrication et contrôles

Le générateur existant accepte maintenant un tube décoratif suivant un chemin
plan. Son repère sans torsion utilise la normale explicite du plan. Une boucle
fermée partage la couture ; un chemin ouvert possède deux bouchons. Les points
répétés, virages trop serrés, rayons excessifs pour les virages, chemins non
plans et nombres non finis sont refusés. Ce contrôle n'est pas une preuve
universelle d'absence d'auto-intersection : les recettes livrées sont aussi
inspectées visuellement.

Huit tests nouveaux couvrent coutures, bouchons, orientation, caractéristique
d'Euler, deux niveaux de détail, refus, empreintes et export désactivé. Deux
lecteurs indépendants relisent les sorties 4DS v41 ; les planches de profil,
dessus et vue oblique ont été inspectées. Aucun fichier commercial n'est ouvert
par ces recettes. Les modèles Benelli, FG42 et MG34 conservent leurs empreintes.

```powershell
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/FLAMMENWERFER_35_AND_NO2/modern-flmwr35-world.json --output-name Flmwr35World_nouveau
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/FLAMMENWERFER_35_AND_NO2/modern-flmthr2-world.json --output-name Flmthr2World_nouveau
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_modern_flamethrower_assets.py
```

Les sorties sont confinées à un dossier neuf sous `.analysis/modern-assets/`,
ignoré par Git : modèle `.4ds.disabled`, OBJ, MTL, planche PNG et manifeste.
Omettre `--output-name` pour contrôler uniquement en mémoire. Les recettes et
le générateur suffisent à reproduire les résultats, sans publier de ressource
extraite du jeu.

Empreintes des lots `Flmwr35World_v1` et `Flmthr2World_v1` :

- modèle allemand : `a4b0aa9811cf0f69b1fe678813d933aeec2c4d230ec1a6822952e3ce9f21d3c6` ;
- recette allemande normalisée : `cef0da3dbecb4e0bf0862c398cb6631c43f97674b223d2d5ae2944a9a099124d` ;
- modèle britannique : `2d2bbb39e6c2774c56c713047c073d8b95e803591cfa692e6cb7739de1943a3b` ;
- recette britannique normalisée : `3442db7afd8f2ee06bf9babed672ec0985eed12e01c70e0ac5e07d79ba412f3f`.

## Travail restant

Construire les modèles FPV, les rattachements dorsaux et les animations ;
réaliser le cycle visuel et sonore ; établir une entrée additive, puis les
comportements et leur sauvegarde. Le banc d'effet 25 reste séparé. Il ne valide
aucune mécanique à lui seul. Préserver Flak TMP, les slots réutilisés et les
munitions 207/208. Essais d'échelle, éclairage, LOD, visibilité et tenue en moteur
encore nécessaires : aucun n'est annoncé réussi.
