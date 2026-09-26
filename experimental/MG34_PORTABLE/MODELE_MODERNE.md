# MG34 portative : extérieur original moderne

**MODERNE, généré le 26 septembre 2026, non validé en jeu.** Le modèle
extérieur/posé existe ; il ne constitue pas une arme jouable et n'utilise
aucune géométrie, texture ou logique du TANK MG34.

La [recette originale](modern-world-model.json) définit **33 pièces, cinq
matériaux et cinq repères**, soit 39 nœuds. Crosse, poignée, couvercle, enveloppe
du canon, tambour latéral et bipied sont une interprétation low-poly moderne.
Les ouvertures sombres sont des décors de surface : elles ne prétendent pas
reproduire un mécanisme interne ni une géométrie industrielle exacte.

Deux niveaux de détail : **1536 / 960 triangles**. Les surfaces sont fermées,
orientées et sans triangles dégénérés. Le tambour est orienté par une rotation
rigide précalculée ; il n'a aucune animation ou logique d'alimentation. Deux
lecteurs indépendants vérifient la structure et les sommets. Les trois vues
de la planche hors moteur ont été inspectées.

```powershell
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/MG34_PORTABLE/modern-world-model.json
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/MG34_PORTABLE/modern-world-model.json --output-name MG34World_nouveau
```

La génération ne lit aucune archive de jeu. Dans un dossier neuf sous
`.analysis/modern-assets/`, elle produit le `.4ds.disabled`, l'OBJ, le MTL,
une planche PNG et un manifeste. Le lot vérifié `MG34World_v1` porte :

- modèle : **260160 octets**, SHA-256
  `d45597f0c720991a468fe8064c5ee972efeb884dc1be6acef45bb06dfc924dac` ;
- recette normalisée :
  `0a3bf981df684d64448aafcf14448f0a193d46aeb2a8c2bd6d323c00f1387c26`.

Les huit tests nouveaux partagés avec le [FG42](../FG42/MODELE_MODERNE.md)
couvrent transformations, surfaces, LOD, génération stable et sorties inertes.
Ce contrôle n'est pas un essai moteur. Les repères ne sont pas des os FPV ;
les pieds ne font pas un bipied déployable et le tambour n'est pas un chargeur
fonctionnel. Aucun son ni projectile n'est créé.

Les [animations originales de pièces](../RECONSTRUCTION_BACKLOG/ANIMATIONS_MODERNES.md)
sont construites dans un banc distinct ; ce modèle extérieur statique et son
empreinte restent inchangés.

Le casque 32, la munition portative 201 et la munition de char 211 restent
intacts ; aucun ID n'est alloué. Restent le banc décoratif en moteur, la vue
FPV originale, les animations de personnage et la chaîne additive, avec essais de tenue,
dépôt/reprise, tir, IA, sauvegarde et réseau.
