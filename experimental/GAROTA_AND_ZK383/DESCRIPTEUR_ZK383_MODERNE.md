# ZK-383 — arme et chargeur de jeu modernes, préparation privée

**27 septembre 2026. Aucun comportement ZK-383 historique retrouvé.**
`tools/build_zk383_descriptor_lab.py` assemble maintenant deux nouveaux objets
de jeu, les modèles originaux, les clips privés de mains, deux icônes, les
sons modernes et les textes. Tout reste désactivé ; aucun jeu ou installateur
lancé, aucun fichier de l'installation personnelle modifié.

## Choix de conception explicites

La recette `modern-zk383-item.json` porte `MODERN_GAME_DESIGN`. Elle adopte des
valeurs de catégorie **individuelles** du MP40 Sabre, pas sa fiche complète,
sa géométrie ou ses sons. Les paramètres de tir sont un point de départ de
gameplay explicitement moderne ; ils ne constituent pas une restitution de
balistique, cadence, poids ou dégâts du ZK-383 réel. Leurs significations
physiques et leur équilibre restent non qualifiés.

Le MP40 original 18 et sa munition 187 demeurent intacts. La nouvelle arme
référence **sa propre munition moderne**, et non le chargeur MP40. Le choix
de quantité **30** est encodé dans la recette, pas présenté comme une donnée
récupérée d'une ancienne version du jeu.

| Élément | Nouvelle association dans cette préparation seulement |
|---|---|
| Arme / groupe FPV | 364 / 464, `MODERN_ZK383` |
| Munition / quantité | 365 / 30, `MODERN_ZK383_AMMO` ; aucun groupe FPV ajouté |
| Textes | 21503 arme ; 21504 chargeur ; marqueurs MODERN dans huit langues |
| Modèles extérieurs | `PROTOTYPE_ZK383` / `PROTOTYPE_ZK3MAG` |
| Modèle FPV | `PROTOTYPE_ZK3FPV`, simple alias raccourci, octets inchangés |
| Sons originaux | banque 2 indice 56 ; banque 3 indice 86 ; `MOD_ZK383_F/R.wav` |
| Icônes originales | `MOD_ZK383_ICON.bmp` / `MOD_ZK3MAG_ICON.bmp` |

Les emplacements 364/365 et le groupe 464 ne sont **pas réservés globalement**.
Le préparateur exige des emplacements vides dans les archives examinées, puis
dans les instantanés personnels utilisés. Toute collision est refusée.

## Descripteurs et modèles

Deux fiches natives de **508 octets** sont construites par des sérialiseurs
originaux, avec mise à zéro explicite des zones opaques, sans copier une fiche
donneuse complète :

- Weapon : `16aedf1940b124995325923c71f999c972d68064afd859f312f0d86d23c5f002` ;
- Ammunition : `3a7e271d37b3c103fe6a29eccf25ffb2c606ca099470b15f01a86f937c9e40ea`.

Les deux sont relues par les routines natives isolées. La liaison 364 → 365
initialise bien une quantité de **30**. Treize liaisons FPV et les deux arguments
sonores concordent. L'action secondaire adopte mode 5, scalaire 0,9599310756
radian, quatre demandes d'état et visée/dévisée 11/12 contrôlées ; ni scène,
caméra, opération complète de tir ou rechargement ne sont exécutées.

Le modèle d'arme moderne reste inchangé : **193 258 octets**, 33 pièces,
deux LOD 1 120/720 triangles. Le chargeur extérieur est une création moderne
séparée reprenant les deux pièces simples de la recette originale du projet,
recentrées et réorientées : **5 486 octets**, deux pièces, trois nœuds,
24/24 triangles, SHA-256
`021b5186b93245073c6cf56f81e3ce8a46e2e2e0b93184eed81f3c461b73b847`.
Ses trois vues hors moteur sont inspectées dans
`.analysis/modern-assets/ZK383_Magazine_v1/preview.png`. Aucun mécanisme physique
interne ni cartouche n'est représenté.

Les deux icônes sont rendues depuis ces seuls modèles, BMP 64 × 32, indexés
non compressés, **3 126 octets chacun**. Palette originale, fond opaque gris,
aucun bitmap commercial. Empreintes :

- arme : `f02fc24b4a6ff4d953aaeb41583f6dac8e0b6e3202e2053725e8c8765812bd29` ;
- chargeur : `43b070acdf7d90c29af2a01ff840fe7e01a2ec17e0a481c1468fff50c2697200`.

L'affichage natif, le fond et les proportions dans la grille d'inventaire
restent à qualifier. Le chargeur extérieur est volontairement simplifié,
sans présenter ce niveau de détail comme une ressource historique retrouvée.

## Mains, sons et textes

Les préparations utilisent la **candidate de mains v9 distincte**, avec index
rapproché de la détente. Ses 18 clips et 1 074 poses avaient passé les contrôles
numériques documentés dans [Mains rigides](../RECONSTRUCTION_BACKLOG/MAINS_ARMES_RIGIDES.md).
Sa posture visuelle et les gestes de recharge restent ouverts ; elle ne remplace
pas le profil par défaut v7. Chaque variante d'assemblage transmet **39 demandes
et neuf chargements/relocalisations d'animations** en émulation bornée.
Les mains H/R sont mutuellement exclusives ; aucun modèle commercial de main exporté.

Les quatre sons de la [banque moderne](../RECONSTRUCTION_BACKLOG/SONS_MODERNES.md)
restent ensemble pour conserver sa transaction entière. Seuls les deux sons
ZK-383 sont raccordés à cette arme. Ils n'ont pas encore été écoutés ; le chargeur
complet de définition, les événements et la lecture native restent ouverts.

Le catalogue prépare maintenant **cinq libellés** après vérification de quinze
tables et des références d'objets. Les huit sorties conservent tous les anciens
octets et se retirent exactement. Les numéros de missions 22000–65000 sont protégés.

## Ajout simultané et retrait exact

`item_ammo_additive.py` ajoute d'abord le nouvel objet Ammunition, puis la Weapon
et son seul groupe FPV. La capacité ne grandit pas : **1 008 octets de réserve**
sont consommés. Le retrait inverse ces opérations, avec contrôles d'empreintes
à chaque étape. Aucun groupe d'animation fictif n'est fabriqué pour la munition.
Les positions d'objet avant/après l'arme et les emplacements limites sont testés.

Trois laboratoires complets sous `.analysis/item-table-labs/`, **34 fichiers
chacun**, dont 32 contenus `.disabled`, manifeste et avertissement :

- `ZK383_Tables_PatchX_H_v1` ;
- `ZK383_Tables_Sabre_R_v1` ;
- `ZK383_Tables_Current_H_v1`.

Dans chacun, **274 descripteurs et 500 emplacements** sont contrôlés ; les
**272 objets et 277 groupes FPV antérieurs restent inchangés**. Le laboratoire
personnel conserve les **dix objets et six groupes modifiés**. Le retrait retrouve
l'instantané personnel exact. La définition sonore et les textes gardent leurs
propres preuves de retrait ; ce n'est pas encore une transaction de déploiement.

**23 tests inventés** couvrent les sérialiseurs, l'ajout double, les sources,
les refus natifs et l'assemblage. Les contrôles d'icône et de textes existants
s'appliquent également. Aucun binaire commercial n'est publié dans les tests.

```powershell
$env:PYTHONPATH = 'D:\Projets\GITHUB\H&D2\.research\binary-patch-deps'
.\.venv\Scripts\python.exe tools/build_zk383_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank .analysis/modern-assets/ZK383_HandFPV_v9 --hand H --item-layer PatchX01.dta --preserve-central-overrides --output-name ZK383_Nouveau
```

Nom neuf obligatoire, aucune sortie écrasée. Les dérivés commerciaux restent privés.
Reste notamment à implémenter/qualifier : raccordement en scène, cadrage, prise
visuelle et gestes, événements, écoute, comportement/équilibre, animations de
personnage, IA, sauvegardes et réseau. **La présence du paquet ne rend pas
l'arme jouable et ne réduit pas le projet entier aux seuls tests.**
