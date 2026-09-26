# Tables d'éditeur : limites exactes des fiches

Contrôle effectué le **26 septembre 2026**, en lecture seule. Le nouveau
`tools/item_editor_table.py` décode les **755 lignes** des deux tables
commerciales possédées : aucun record binaire n'est publié.

## Format retenu

L'en-tête de 24 octets porte la signature `0x14448408`, la version 7, deux
valeurs conservées opaques (la dernière vaut zéro), le nombre de colonnes et
la taille des données. Chaque descripteur de colonne occupe douze octets :
identifiant 16 bits, offset 32 bits, nombre de lignes 16 bits, pas de ligne
16 bits, type 16 bits. Tous sont little-endian.

Les types rencontrés sont 3 (booléen sur un octet), 4/18 (entier sur quatre
octets, distinction conservée), 5 (flottant), 6/7 (chaîne terminée par zéro
sur huit/seize octets). Les suffixes après le premier zéro sont opaques : un
ancien nom dans cette zone n'est pas une référence actuelle.

| Table | Colonnes | Début des données | Lignes | Pas | Taille totale |
|---|---:|---:|---:|---:|---:|
| `others.DTA::TABLES/item_shoot.tbl` | 26 | 336 | 255 | 135 | 34761 |
| `SabreSquadron.dta::Tables/item_base_items.tbl` | 22 | 288 | 500 | 133 | 66788 |

Le lecteur refuse formes mixtes, trous/chevauchements, identifiants répétés,
types inconnus, nombres non finis, chaînes invalides et octets surnuméraires.
Il ne donne pas de noms fonctionnels inventés aux colonnes numériques.

## Corrections des anciennes fenêtres de recherche

Les premières recherches utilisaient des fenêtres de texte empreintées. Elles
attestaient des fragments, **mais ne délimitaient pas toutes une fiche**.
Les outils exigent maintenant une coïncidence exacte avec le parseur complet.
Bornes de fin exclusives :

| Preuve | Ancienne fenêtre | Ligne/slot exact |
|---|---|---|
| Benelli, tir, ligne 9 | 1547–1682 | **1551–1686**, 135 octets |
| Boussole, table d'éditeur, ligne 9 | 1485–1620 | **1485–1618**, 133 octets |
| FG42, tir, ligne 27 | 3977–4112 | **3981–4116** |
| MG34 portative, tir, ligne 32 | 4652–4787 | **4656–4791** |
| Flammenwerfer, éditeur, ligne 44 | 6075–6210 | **6140–6273** |
| Flak TMP, éditeur, ligne 45 | 6210–6345 | **6273–6406** |
| Munition allemande 207, Base/Sabre | 101600 / 103616 | **101628 / 103644**, 508 octets |
| Munition britannique 208, Base/Sabre | 102108 / 104124 | **102136 / 104152**, 508 octets |

Les six preuves de munitions FG42/MG34/char et les quatre autres lignes de tir
MG15/MG81 sont également recalées et empreintées. Les 18 preuves de l'audit des
armes orphelines et les preuves lance-flammes repassent avec ces limites.

La ligne Benelli vaut désormais SHA-256
`ce461707bb7551abdb45e165222582201dc90c292d2ff781f684540e38e47fef`.
L'ancien « record_type = 1 » provenait du dernier entier de la ligne précédente :
ce n'est **pas un en-tête de record**. La ligne de boussole vaut
`ee8cb099a336049848d8e7c0ce05103e4b77d7ef7c716be117c1eca765abfd5f`.
Les anciens rapports privés restent des traces historiques ; leurs empreintes
de fenêtres ne remplacent plus les preuves de ligne actuelles.

Le banc privé **BenelliFPV_v5** a été reconstruit avec la preuve corrigée.
La géométrie FPV, les deux alias et l'inspecteur sont inchangés ; seul le
manifeste de provenance évolue. Aucun fichier de jeu n'a été modifié.

## Portée et reproduction

Les traces Benelli/FG42/MG34 restent présentes. La boussole et les casques
occupent toujours leurs slots protégés. Le booléen de la ligne Flammenwerfer 44
est nul, et le slot natif 44 est vide ; Flak TMP est toujours l'objet 45.
Les chaînes visibles FPV/monde de cette dernière ligne sont vides, malgré leurs
anciens suffixes. Ce constat ne permet pas de réactiver les armes manquantes.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_item_editor_table.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_weapon_evidence_boundaries.py
.\.venv\Scripts\python.exe tools/orphan_weapon_evidence_audit.py 'D:\Games\Hidden and Dangerous 2'
.\.venv\Scripts\python.exe tools/flamethrower_evidence_audit.py 'D:\Games\Hidden and Dangerous 2'
```

Onze tests synthétiques couvrent le format, les propriétaires et les refus des
anciennes fenêtres décalées. Les paramètres de tir, la conversion des tables
d'éditeur en descripteurs vivants et leurs effets restent des travaux distincts.
