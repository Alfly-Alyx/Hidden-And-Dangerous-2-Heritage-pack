# Dépendances embarquées

## Hidden & Dangerous 2 Widescreen Fix

Le futur exécutable embarque une seule archive binaire tierce :
`installer/assets/HiddenandDangerous2.WidescreenFix.zip`.

Elle provient de la
[release H&D2 officielle de ThirteenAG](https://github.com/ThirteenAG/WidescreenFixesPack/releases/tag/hd2).
L'asset de cette release a été mis à jour le 16 mai 2020. La copie conservée
dans le Heritage Pack a été téléchargée de nouveau puis comparée bit à bit le
15 septembre 2026 :

- taille : `1 306 660` octets ;
- SHA-256 :
  `8B8315B88420FCFED9891F2D39886F6384BDA1B32CDD299AC27D728391E65A9F` ;
- résultat : identique à l'asset GitHub officiel.

L'archive contient exactement six fichiers installables :

- `d3d8.dll` ;
- `Maps/2e_camra.tga` ;
- `Maps/2e_scope.tga` ;
- `Maps/e_zamer.tga` ;
- `scripts/HiddenandDangerous2.WidescreenFix.asi` ;
- `scripts/HiddenandDangerous2.WidescreenFix.ini`.

L'installateur refuse un nom supplémentaire, un fichier manquant, une
empreinte interne différente ou une empreinte d'archive différente. Chaque
cible passe ensuite par le confinement au dossier du jeu, la sauvegarde
réversible et l'enregistrement de son empreinte finale.

## Licence

Le dépôt
[ThirteenAG/WidescreenFixesPack](https://github.com/ThirteenAG/WidescreenFixesPack)
publie une licence MIT, Copyright © 2018 ThirteenAG. Cette licence autorise la
redistribution à condition de conserver la notice de copyright et le texte de
licence.

`WidescreenInstaller` installe donc le texte MIT complet sous
`scripts/HiddenandDangerous2.WidescreenFix.LICENSE.txt` et suit ce fichier
dans le journal de restauration. La notice est supprimée avec les autres
changements lors d'une restauration complète si elle n'existait pas auparavant.

## Compatibilité multijoueur

Deux rapports publics de 2018 signalaient qu'une ancienne version du correctif
pouvait provoquer « CD-Key in use » en multijoueur. Le mainteneur a d'abord
fourni `InsertKey = 0` comme contournement, puis une version qui n'insère plus
de clé factice lorsqu'une vraie clé existe. Le testeur a confirmé la correction
et ThirteenAG a indiqué l'avoir republiée sur GitHub le 11 mai 2018. Le second
ticket a ensuite été fermé comme doublon résolu.

La copie embarquée est l'asset officiel mis à jour en 2020, donc postérieur à
cette correction. Ce constat ne remplace pas un essai dans H&D2 : la
publication finale exigera encore de rejoindre un serveur avec le correctif
actif et de consigner la capture ou le journal dans le registre d'exécution.

Sources :

- [release H&D2](https://github.com/ThirteenAG/WidescreenFixesPack/releases/tag/hd2) ;
- [licence MIT officielle](https://github.com/ThirteenAG/WidescreenFixesPack/blob/master/license) ;
- [ticket multijoueur n°450 et confirmation du correctif](https://github.com/ThirteenAG/WidescreenFixesPack/issues/450) ;
- [ticket n°467 fermé comme cas déjà traité](https://github.com/ThirteenAG/WidescreenFixesPack/issues/467).
