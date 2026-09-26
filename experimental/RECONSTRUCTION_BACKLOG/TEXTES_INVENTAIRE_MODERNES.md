# Libellés d'inventaire modernes et réversibles

**27 septembre 2026.** Le catalogue original `modern-inventory-texts.json`
réserve **21500–21531 au projet** et prépare le premier libellé, **21500 :
Benelli M4 [MODERNE]** en français. Ce numéro de texte ne réserve pas le slot
d'objet 359 et ne prouve pas l'absence de collision avec tout mod externe.

## Collision future évitée

Une absence dans les textes installés n'est pas suffisante : le créateur de
missions réserve déjà **22000–65000**, y compris les valeurs non utilisées.
Le préparateur lit ses constantes actuelles et refuse un chevauchement avec
la nouvelle plage. Un test vérifie également les identifiants du menu personnalisé.

Avant construction, il vérifie les **quinze tables TEXTY/TEXTY_DD présentes**,
les identifiants de texte des objets commerciaux dans les quatre couches et
ceux de la table d'objets libre installée. La recherche conservatrice refuse
toute occurrence du nombre 21500 comme jeton numérique, même dans un commentaire.
Elle préfère un faux positif à une réaffectation silencieuse.

Ce contrôle n'est pas présenté comme un parseur universel de TEXTY : les fichiers
anciens contiennent du texte multiligne, des commentaires particuliers et quelques
doublons. Ceux-ci sont conservés. Les références indéfinies de tous les scripts,
les autres mods et les sauvegardes ne sont pas globalement qualifiés par ce lot.

## Huit langues, aucun ancien texte réécrit

Les ajouts portent un marqueur moderne visible :

| Langue installée | Nouveau libellé | Encodage de l'ajout |
|---|---|---|
| Czech | Benelli M4 [MODERNÍ] | cp1250 |
| english / EnglishUS | Benelli M4 [MODERN] | cp1252 |
| french | Benelli M4 [MODERNE] | cp1252 |
| german | Benelli M4 [MODERN] | cp1252 |
| italian / spanish | Benelli M4 [MODERNO] | cp1252 |
| japan | Benelli M4 [MODERN] | UTF-8, libellé ASCII |

Seul un commentaire et une ligne sont ajoutés à chaque `TEXTY_DD.txt`.
**Tous les octets initiaux restent inchangés**, y compris textes personnalisés,
retours de ligne, BOM, encodage et doublons préexistants. Les tailles/empreintes
des sources, ajouts et résultats sont consignées. Le retrait en mémoire retrouve
exactement les huit sources. Toute modification ultérieure du résultat fait
refuser ce retrait, afin de ne pas effacer de nouveaux changements.

La langue japonaise ne dispose ici que de `TEXTY_DD.txt`, pas du `TEXTY.txt` de
base. Cette limite est signalée ; le libellé ASCII est intentionnel, sans prétendre
avoir validé une police japonaise ou le comportement de repli du jeu.

## Laboratoires préparés, installation inchangée

- `.analysis/inventory-text-labs/BenelliText_v1` : huit fichiers `.disabled`
  et le manifeste, sans insertion d'arme.
- `.analysis/item-descriptor-labs/BenelliDescriptor_v3` : descripteur, fragment
  FPV, deux modèles, huit textes `.disabled`, manifeste et avertissements,
  **quatorze fichiers**. Seul le membre de texte du descripteur change par rapport
  à v2 ; les modèles, actions, munition et fragment FPV restent identiques.

Le nouveau descripteur de 508 octets a pour SHA-256
`6b03354261405a6e30c2225c65c23a7eed7349653828a4444ba3c10da90a251c`.
Le lecteur natif isolé conserve bien **21500** dans son membre 0x14 ; les contrôles
de munition et des treize états FPV réussissent encore. Cela ne valide pas le
chargeur complet de texte ni son affichage dans l'inventaire.

Les textes complets issus de l'installation restent privés, ignorés par Git.
Le dépôt ne reçoit que le catalogue moderne, les outils, la documentation et
les tests synthétiques. Aucun fichier personnel de jeu n'est modifié.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/build_modern_inventory_text_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name BenelliText_nouveau
.\.venv\Scripts\python.exe tools/build_benelli_descriptor_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --inventory-texts --output-name BenelliDescriptor_nouveau
```

Sans nom de sortie, la préparation est en mémoire. Sans `--inventory-texts`,
le constructeur de descripteur garde explicitement le texte non résolu des
versions antérieures. Il ne devine pas silencieusement la table à utiliser.

Douze tests nouveaux couvrent catalogue, plages réservées, encodages, collisions,
préservation et retrait. Trois tests supplémentaires vérifient le raccordement
au Benelli et ses refus. Restent les contrôles de rendu/polices en moteur et la
transaction additive sûre des tables, indépendamment des autres contrats d'arme.
