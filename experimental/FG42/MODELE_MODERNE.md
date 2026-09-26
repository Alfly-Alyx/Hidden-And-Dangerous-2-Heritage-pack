# FG42 : extérieur original moderne

**MODERNE, généré le 26 septembre 2026, non validé en jeu.** Le modèle statique
extérieur/posé est construit ; FPV, animations, mécanique et intégration restent
à réaliser. Ce n'est pas une ressource commerciale retrouvée.

La [recette originale](modern-world-model.json) comprend **25 pièces, cinq
matériaux unis et cinq repères**, soit 31 nœuds. Le chargeur latéral, la crosse,
le garde-main, les deux jambes du bipied et les organes visibles sont des
interprétations low-poly modernes. Leurs proportions ne sont ni une mesure
historique ni un plan technique. Aucun maillage, texture, son ou animation du
jeu n'est lu ou copié.

Les deux niveaux de détail comportent **876 / 564 triangles**. Les surfaces
sont fermées et orientées vers l'extérieur, sans faces dégénérées ; deux
lecteurs indépendants relisent la géométrie et le format 4DS v41. Les pièces
inclinées utilisent une rotation rigide précalculée, sans animation implicite.
Profil, vue oblique et dessus ont été inspectés hors moteur.

```powershell
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/FG42/modern-world-model.json
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/FG42/modern-world-model.json --output-name FG42World_nouveau
```

La première commande contrôle en mémoire. La seconde produit dans un dossier
neuf ignoré par Git le `.4ds.disabled`, l'OBJ, le MTL, une planche PNG et un
manifeste de provenance. Le lot contrôlé est `FG42World_v1` :

- modèle : **151395 octets**, SHA-256
  `111c3e8cb882bc67b53415097165f6ca8f63533af528ac554e6e16aa57091aba` ;
- recette normalisée :
  `b254c92c21375f661b4030ef37c612384a9e155ea8ad3f6134131c9f0aa5d2d4`.

Les repères de prise, chargeur, bouche et éjection ne sont liés à aucun moteur,
squelette, particule ou objet. Le bipied est un volume statique, pas une
fonction déployable. Aucun ItemID n'est réservé ; le casque 27 et la munition
196 ne sont pas modifiés. Le résultat demeure muet et désactivé.

Huit tests supplémentaires communs aux deux nouvelles armes couvrent rigidité,
topologie, deux LOD, empreintes stables, refus de données invalides et absence
de régression du modèle Benelli :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_modern_weapon_assets.py
```

Les [animations originales de pièces](../RECONSTRUCTION_BACKLOG/ANIMATIONS_MODERNES.md)
sont désormais construites dans un banc distinct ; ce modèle extérieur
statique et son empreinte restent inchangés.

Suites nécessaires : banc décoratif isolé, échelle/éclairage/LOD en moteur,
modèle FPV et animations de personnage, tenue en troisième personne, puis entrée
additive et comportements. Aucun de ces essais n'est déclaré réussi ici.
