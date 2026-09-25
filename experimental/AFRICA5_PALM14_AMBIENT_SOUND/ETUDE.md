# Africa 5 — palmier sonore 14

État : script et porteur retrouvés, position de la source sonore inconnue,
26 septembre 2026. Aucun son créé ni binding ajouté.

## Chaîne partielle officielle

`V_Af4_snd_palma14.scr` existe dans Patch.dta : 180 octets, SHA-256
`b07c00f7698aeb55b48946b74ad6514ce8496e1a0d4e28967425824d78d5f5d2`.
Il attend `_RandomInt(7000)+9000`, active `S_vrzplm14`, puis recommence. Le
dummy `v_dummy_palma_14` existe dans scene2.bin, sans liaison à ce script;
celui-ci n'est pas atteint par les dépendances littérales de la mission.

Les treize premiers sons et le quinzième existent; `S_vrzplm14` est absent.
La recherche exacte dans les fichiers sounds.bin des couches missions, Patch
et Sabre consultées ne fournit aucune copie de ce nom. Aucun remplacement
n'est déduit d'un autre nom approchant.

## Correction importante : le dummy ne donne pas la position du son

Les quinze dummies sont regroupés dans une petite grille, loin des émetteurs.
Les deux voisins suffisent à invalider la règle « son à la position du dummy » :

| N° | Position du contrôleur | Position du son | Distance |
|---|---|---|---:|
| 13 | (174,300; −0,326; 134,137) | (51,896; 5,243; 113,890) | 124,192 unités |
| 14 | (174,446; −0,311; 132,440) | inconnue | — |
| 15 | (174,573; −0,294; 130,576) | (106,908; 5,243; 120,239) | 68,673 unités |

La grille évoque un rangement d'éditeur (**INFERENCE**), pas les emplacements
des palmiers. Les sources 13 et 15 ne sont pas voisines par leur seule
numérotation; une interpolation entre elles n'est pas une preuve historique.

Les paramètres sonores 13/15 sont identiques, hors nom et position : ils visent
`l_a4palm2.wav`, avec le même parent et le même secteur Primary sector. Cette
ressource est indexée dans Sounds.dta, taille 126508 octets. Le lecteur DPCM a
été complété et testé : décodage en mémoire mono PCM16, 22050 Hz, 63232 trames,
soit **2,867664 s**. SHA-256 du WAV décodé :
`76a6ee13c96d52599ef16c4ed19a87ff86630bab51e05217a7aadfe63b181a68`.
Aucune écoute, validation moteur ou export audio n'est prétendu. Les sons
existants sont conservés; cette preuve de ressource ne fournit pas sa position 14.

## Suite possible, explicitement moderne

Relever d'abord les véritables palmiers, les quatorze sources existantes et
leurs portées dans l'éditeur. Une nouvelle position devra désigner un palmier
non déjà couvert et être étiquetée MODERNE. Ensuite seulement : copier les
paramètres compatibles d'un son officiel, renommer la source 14 et créer une
liaison unique au dummy déjà présent, en un delta atomique son/registre.
Ne pas créer de seizième contrôleur ni déplacer les quinze existants.

Comparer témoin/variante : cadence, superposition audible, secteurs, sauvegarde
et retrait. Le laboratoire de mission reste aussi soumis à la dépendance
commerciale `af4_runway01_detector.scr` absente, distincte de ce problème.

## Sources binaires

Dans missions.dta : scene2.bin, 6973053 octets, SHA-256
`53b1e6eb9fcbb6a295ff6d8f0ec960db5ced3c92e77b25d5a1843f19ecb5ec8f`;
sounds.bin, 58067 octets, SHA-256
`2e59da4942cb1ec969d269fab371eaeaccf50487d7a451e48c100393eed5998b`.
Positions décodées dans les records 0x4010, champs 0x20, et comparées aux champs
0x2c identiques. Les contrôleurs sont de type 6, les sons de type 4; leurs
identités ne sont pas déduites d'une simple sous-chaîne binaire.
