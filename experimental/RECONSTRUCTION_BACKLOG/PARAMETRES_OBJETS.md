# Correspondance des fiches générales d'objets

Contrôle du **27 septembre 2026** : `tools/item_base_projection.py` rapproche
les lignes de `item_base_items.tbl` des descripteurs Sabre et PatchX01, sans
modifier une table. Il vérifie **500 emplacements par couche**, dont 272
présents et 228 vides. Le marqueur d'existence concorde partout.

## Plages établies

Offsets relatifs au record présent de 508 octets. Une chaîne compare seulement
son préfixe visible et son zéro terminal, pas ses anciens octets de suffixe.

| Colonne d'éditeur | Offset du record | Représentation |
|---:|---:|---|
| 1 | 0 | présence, entier 32 bits |
| 2 | 88 | nom interne |
| 6 | 8 | nom du modèle FPV |
| 8 | 28 | nom de l'icône |
| 10 | 48 | nom du modèle extérieur |
| 11 | 68 | entier brut → membre natif 0x0c |
| 4 | 108 | identifiant du texte → 0x14 |
| 12 | 112 | poids float32 → 0x18 |
| 14 | 116 | entier brut → 0x1c |
| 44 | 120 | entier brut → 0x38 |
| 46 | 124 | entier brut → 0x3c |
| 48 | 128 | entier brut → 0x40 |
| 50 | 132 | entier brut → 0x44 |
| 16 | 136 | premier sélecteur d'action |
| 20 | 140 + taille du premier payload | second sélecteur |

Le bloc dérivé commence après les deux sélecteurs, leurs payloads et 32 octets
opaques. Son emplacement est calculé, jamais supposé constant :

- Classe native 1, Weapon : colonnes **5, 39, 40, 24** vers les membres
  **0x58, 0x5c, 0x60, 0x54**. Le dernier est la référence de munition déjà
  qualifiée par son consommateur.
- Classe 0, munition : colonne **26**, float32, vers **0x54**.
- Classe 2, objet générique : colonnes **5, 39, 40** vers **0x54, 0x58, 0x5c**.
  Les deux membres suivants restent opaques. Ils varient effectivement sur des
  vêtements et accessoires ; les remplacer tous par -1 serait incorrect.

La classe native est **fournie explicitement**, pas déduite des colonnes 5/11/14 :
ces combinaisons présentent des collisions entre classes. Les colonnes 18 et 22
restent des références de lignes d'action non résolues par cet outil. Pour quatre
armes ajoutées par Sabre, la ligne de tir ne porte plus le numéro de l'objet :
260→39, 261→38, 262→62, 263→63. Les lignes correspondantes de la table de tir Base
ont un nom vide ; elles ne permettent pas de reconstruire les paramètres Sabre.

## Exceptions conservées, pas corrigées

Dans **chaque couche**, 259 des 272 objets concordent sur toutes les plages
comparées. Les treize autres conservent les exceptions suivantes :

- Slots **38, 56, 57, 60, 61, 62, 63, 65, 66, 70, 71** : colonne 24 égale à zéro,
  référence native de munition égale à `0xffffffff`.
- Slots **207 et 208** : quantité d'éditeur égale à zéro, quantité native égale
  à **-1,0** (`0xbf800000`). Leur signification complète n'est pas inventée.

Le rapport vérifie à la fois la colonne, la classe et la valeur exacte de ces
exceptions. Il n'applique **aucune règle universelle zéro → -1**.

La table d'éditeur Sabre n'est pas exportée par-dessus Base/Patch : ces couches
présentent d'autres valeurs et même quatre différences de présence
(183/185/186/205). L'outil de projection n'annonce pas leur équivalence.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/item_base_projection.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output .analysis/projection-objets-nouveau.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_base_projection.py
```

Rapport privé contrôlé : `.analysis/item-base-projection-20260927.json`.
Neuf tests synthétiques couvrent les classes explicites, offsets variables,
sentinelles, octets opaques, champs invalides, références non résolues et absence
de mutation. Deux autres tests encadrent la lecture **explicitement demandée**
des tables d'éditeur version 5 ; le lecteur reste strictement en version 7 par
défaut. La table `item_balistic.tbl` version 5 est décodable, mais ses consommateurs
ne sont pas qualifiés par ce lot.
