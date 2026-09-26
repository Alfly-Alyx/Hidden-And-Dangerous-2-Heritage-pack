# Benelli — ajout réversible dans des tables complètes désactivées

**27 septembre 2026.** Le constructeur original
`tools/build_benelli_table_lab.py` prépare désormais les deux tables complètes
dans un laboratoire privé. Aucun fichier de l'installation n'est modifié et
aucune arme n'est activée. Les sorties dérivées du jeu ne sont pas publiées.

## Opération réellement réalisée

`tools/item_table_additive.py` réalise une transaction **en mémoire**, sur une
paire de fichiers, puis son inverse :

1. Relire strictement la table de 500 emplacements et les groupes FPV natifs.
2. Refuser un slot occupé, un libellé/nom déjà référencé, une munition absente
   ou de mauvaise classe, un propriétaire FPV existant et une capacité différente.
3. Remplacer les quatre octets vides du candidat **359** par le descripteur
   moderne de 508 octets, sans modifier les autres records. Retirer exactement
   **504 octets 0xCD** de la réserve finale : la taille reste **252 000 octets**.
4. Ajouter le groupe **459** à la fin de la table FPV. Seule la taille de la
   racine est corrigée ; les 277 anciens groupes conservent leurs octets,
   leurs positions et leur ordre, dont les groupes 109 et 359.
5. Relire tous les objets présents avec les routines natives isolées :
   **273 descripteurs par variante**, dont les 272 commerciaux inchangés.
6. Retirer l'ajout et comparer les deux résultats aux sources : restitution
   **exacte octet pour octet**, y compris la réserve 0xCD et l'en-tête FPV.

Le reçu contient les tailles et empreintes avant/après, les propriétaires et
les limites d'insertion. Toute modification ultérieure d'une des deux tables
fait refuser le retrait de la paire entière. Le reçu n'est pas une signature
authentifiée ni une autorisation d'installation. La source n'est jamais
réécrite pour réaliser ces vérifications.

## Deux laboratoires privés construits

Les variantes sont séparées : les corrections MP 44/BAR de PatchX01 restent
dans cette variante et ne sont pas remplacées par les valeurs Sabre.

| Sortie désactivée | Taille | SHA-256 |
|---|---:|---|
| items.sav — Sabre | 252000 | `2cf638ec23598f107b79fc961a3e13c0ed5b5c8979dc981d7e0a271567ae6943` |
| items.sav — PatchX01 | 252000 | `89632736933ddc529d8012fbef29550fe7b5284b8e105cbbbcf134b36a443bfe` |
| FpvAnims.sav — commun aux deux | 127942 | `ee57e901bff1bfc4895c96f6504ac2c2bee5d54d605ba34c4e8b3b2352e07f65` |

Dans les deux tables d'objets : **273 présents, 227 vides**, 139 592 octets
sérialisés et 112 408 octets de réserve. La table FPV contient **278 groupes**.
La boussole 9, la munition 179 et tous les autres emplacements sont conservés.

Les dossiers `.analysis/item-table-labs/BenelliTables_Sabre_v1` et
`BenelliTables_PatchX01_v1` contiennent chacun **16 fichiers** : les deux
tables désactivées, le descripteur et son fragment FPV, les deux modèles,
les huit textes modernes, un manifeste et un avertissement. Toutes les
sorties binaires/textuelles ont été relues après écriture. Le libellé **21500**
et les modèles sont identiques au [descripteur v3](DESCRIPTEUR_MODERNE.md).

## Limites conservées

Cette étape termine la **construction binaire et son inverse** ; elle n'est
pas une transaction d'installation atomique sur disque. Elle ne fusionne pas
les surcharges personnelles, ne réserve pas globalement 359, ne migre pas les
sauvegardes et ne démontre pas le chargement complet en jeu. Le chargeur natif
global n'a pas été exécuté par cet outil : ses lecteurs de descripteurs le sont.

Un [oracle distinct de parcours natif](PARCOURS_NATIF_TABLE.md) vérifie désormais
également la boucle originale des 500 emplacements, avant/après ajout dans les
deux variantes. Il s'arrête toujours avant les appels système et ne valide
pas le chargement en jeu ni le chargeur FPV complet.

Restent la préparation d'un déploiement isolé et la gestion des surcharges,
les contrats de sauvegarde complète, les paramètres secondaires, les mains,
la caméra et les événements FPV. Les essais de rendu, de comportement et de
multijoueur restent ensuite obligatoires. **Ne pas copier ces tables dans le jeu.**

## Reproduction sans activation

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_table_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --item-layer PatchX01.dta --output-name BenelliTables_PatchX01_nouveau
```

Sans `--output-name`, la construction reste en mémoire. Un dossier existant,
lié, une source modifiée ou une couche Base/Patch est refusé. Le choix de la
couche est obligatoire ; les surcharges centrales libres sont seulement
signalées et empreintées avec `--archives-only`, jamais écrasées.

**Dix-huit tests synthétiques** supplémentaires couvrent les deux constructeurs,
les limites de capacité, la dernière insertion possible, les collisions,
l'intégrité du retrait, les changements ultérieurs et les sorties désactivées.
