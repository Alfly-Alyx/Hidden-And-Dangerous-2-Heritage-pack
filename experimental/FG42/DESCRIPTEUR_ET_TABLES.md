# FG42 — assemblage moderne et tables privées réversibles

**27 septembre 2026. Préparation désactivée, pas une arme jouable.**
Le constructeur `tools/build_fg42_descriptor_lab.py` réunit désormais fiche
Weapon, munition, modèles, neuf animations de mains, sons modernes, icône et
textes. Il ne lance rien et n'écrit jamais dans l'installation personnelle.

## Sources historiques et décisions modernes

La ligne officielle 27 de `item_shoot.tbl` reste inchangée, empreinte
`3c1c1186dbee311e4239297a3d1b460165fc59300c706d6b1f3492e21a3bdfb5`.
Dans le **nouveau descripteur uniquement**, ses deux références symboliques
`FG42_F/R` sont remplacées explicitement par les références des sons originaux
`MOD_FG42_F/R`. Ce choix moderne ne résout pas les anciens symboles : aucun
fichier sonore historique disparu n'est déclaré retrouvé. Les autres champs
de la ligne restent identiques.

La fiche générale FG42 d'origine n'étant pas retrouvée, les attributs de catégorie
sont adoptés **individuellement** depuis le MP44 Sabre, slot 26, empreinte
`e097423c6e8efa6e9565459ad44238a6ceb36df3fc487b6f21cd020501b44291`.
Poids de jeu 5,136, membres bruts de catégorie et action secondaire sont donc des
**réglages modernes provisoires**, pas des caractéristiques physiques restituées.
Aucun descripteur donneur complet ni son apparence ne sont copiés. Les octets
opaques du nouveau record sont mis à zéro selon une politique moderne explicite.

| Élément | Association de cette préparation seulement |
|---|---|
| Objet / groupe FPV | 362 / 462 ; non réservés globalement |
| Nom interne / texte | `MODERN_FG42` / 21502, marqueur MODERNE dans huit langues |
| Munition historique | 196, `AMMO FG 42`, quantité initiale 20 dans Sabre et PatchX01 |
| Tir moderne | banque 2, indice 55, `MOD_FG42_F.wav` |
| Recharge moderne | banque 3, indice 85, `MOD_FG42_R.wav` |
| Extérieur / FPV | `PROTOTYPE_FG42` / `PROTOTYPE_FG4FPV` |
| Icône originale | `MOD_FG42_ICON.bmp`, 64 × 32, palette originale 256 couleurs |

L'ancien slot **27 reste le casque `G HELM SS`**. La munition 196 reste
octet pour octet inchangée, SHA-256
`5b7e3b38eb13ae12de1d49207e0c926368c8307a99a0bdb859d10001f476c263`.
La lecture native isolée initialise bien 20 ; elle ne prouve pas un rechargement
complet ou le fonctionnement du chargeur en jeu.

## Contenus et contrôles

Le descripteur de **508 octets**, SHA-256
`c2cfe643abe0ed991a98b19f4c25f624a36c3c339af5d5f4a27d8dc5e9f929f0`,
est relu par les routines natives isolées. Treize liaisons d'états FPV et les
arguments natifs des deux références sonores concordent. L'action secondaire
conserve mode 5 et scalaire 0,8726646304 radian : quatre demandes d'état,
visée/dévisée 11/12 contrôlées ; caméra et opération de visée complète non exécutées.

Le modèle FPV conserve exactement ses octets sous un alias raccourci à la limite
du descripteur. Les clips viennent de la **banque de mains v7** ; aucun modèle
commercial de main n'est exporté. Chaque variante effectue **39 demandes de
ressources et neuf chargements/relocalisations d'animations** en émulation bornée.
Cela n'exécute ni scène, ni copie de modèle, ni skin final de l'arme équipée.

L'icône est rendue depuis le seul modèle moderne, avec profondeur et suréchantillonnage.
Le BMP indexé non compressé fait **3 126 octets**, SHA-256
`fa66bc9dbcf01aa96685e0fb44216b5d40490e6d7d11c365e4d4abccc7538d07`.
La palette originale comporte un cube de couleurs et quarante nuances grises.
Le fond encodé est opaque `(26, 26, 26)` ; aucun comportement de transparence
du moteur n'est supposé. Aucun bitmap ni palette commercial réutilisé.

Les huit textes reprennent intégralement les contenus installés. Les trois
libellés modernes du catalogue sont ajoutés après vérification de **quinze
tables**, sans toucher à la plage des missions 22000–65000. Le FG42 utilise 21502.
La [définition sonore moderne](../RECONSTRUCTION_BACKLOG/SONS_MODERNES.md)
comprend les quatre sons FG42/ZK-383 afin de conserver sa transaction entière ;
seuls les deux sons FG42 sont raccordés à cet objet. Les 539 anciennes entrées
et le bloc de recherche symbolique restent inchangés.

## Trois laboratoires complets

Sous `.analysis/item-table-labs/`, **31 fichiers par préparation**, dont
29 contenus `.disabled`, un manifeste et l'avertissement privé :

- `FG42_Tables_PatchX_H_v2` : sources PatchX01, mains H ;
- `FG42_Tables_Sabre_R_v2` : sources Sabre, mains R ;
- `FG42_Tables_Current_H_v2` : instantanés personnels des tables, mains H.

Les trois versions v1 restent conservées ; v2 corrige seulement la palette de
l'icône, sans modifier les descripteurs, sons, tables ou animations.
Les variantes H et R sont **mutuellement exclusives**, pas deux armes installées.

Chaque préparation vérifie **273 descripteurs**, les **500 emplacements**,
la table FPV complète et le retrait exact en mémoire. **272 objets et 277 groupes
FPV antérieurs restent intacts**. Le cas personnel conserve les **dix objets et
six groupes déjà modifiés** ; le retrait retrouve les instantanés personnels,
pas les archives d'origine. La capacité d'objets reste 252 000 octets, avec
504 octets de réserve consommés. Aucun fichier actif n'est déployé.

La définition sonore se retire séparément, octet pour octet. Les autres
surcharges de ressources ne sont pas fusionnées ; aucune liberté globale
d'identifiant ou compatibilité de sauvegarde complète n'est prétendue.

## Reproduction et reste à implémenter

```powershell
$env:PYTHONPATH = 'D:\Projets\GITHUB\H&D2\.research\binary-patch-deps'
.\.venv\Scripts\python.exe tools/build_fg42_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank .analysis/modern-assets/FG42_HandFPV_v7 --hand H --item-layer PatchX01.dta --preserve-central-overrides --output-name FG42_Nouveau
```

Un nom neuf est obligatoire ; le constructeur ne remplace pas une sortie existante.
Les ressources commerciales dérivées restent privées et exclues de Git.
**Quinze tests inventés** couvrent l'assemblage et les tables ; quatre autres
couvrent le générateur d'icône. Les collisions, sources modifiées, reçus natifs
incomplets et retraits après modification sont refusés.

Restent notamment : raccordement du correcteur de poignets au client, copie
de modèle en scène, cadrage, gestes réels de recharge, événements et écoute,
chargeur sonore complet, affichage de l'icône, attache tiers, IA, équilibre,
sauvegardes et réseau. **Le projet n'est pas encore au stade “tests seulement”.**
