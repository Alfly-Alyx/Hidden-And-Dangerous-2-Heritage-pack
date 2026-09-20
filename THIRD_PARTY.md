# Remerciements et dépendances tierces

## HD2unpacker

Le lecteur DTA de `tools/dta_archive.py` et `installer/DtaArchive.cs` suit la documentation publique du format ISD0/ISD1 et l’implémentation GPL-3.0 de [M3tox/HD2unpacker](https://github.com/M3tox/HD2unpacker).

Le code de ce dépôt est distribué sous GPL-3.0-or-later.

## OpenSpy et pont GameSpy EnctypeX

Le Heritage Pack interroge le service réseau du [projet OpenSpy](https://github.com/openspy)
comme seconde source de serveurs H&D2. Il ne contient ni `openspy-client`, maintenu
par [anzz1](https://github.com/anzz1/openspy-client), ni un binaire provenant des
dépôts OpenSpy.

La fusion des deux listes est réalisée par un pont local propre au Heritage Pack.
Son implémentation compatible du chiffrement GameSpy EnctypeX est adaptée du fichier
`enctypex_decoder.c` publié par **Luigi Auriemma** sous GPL-2.0-or-later. Le port et
le reste du pont sont distribués avec le Heritage Pack sous GPL-3.0-or-later.

Le service OpenSpy et le service communautaire H&D2 restent des services extérieurs :
ils ne sont ni copiés ni exploités par le dépôt.

## Coop Map Package

L’installateur sait télécharger la [Hidden & Dangerous 2 Coop Map Package](https://github.com/ehylla93/had2-cmp/). Il vérifie la dernière révision officielle ; la version de référence 2.6.5 correspond au commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`.

L’archive CMP n’est pas stockée dans ce dépôt ni incorporée à l’exécutable. Elle est obtenue depuis sa source publique à la demande de l’utilisateur. La version de référence est verrouillée par taille et SHA-256 ; une révision officielle plus récente est contrôlée, identifiée par son commit et reçoit une empreinte SHA-256 enregistrée avant installation.

Aucun fichier de licence explicite n’a été trouvé dans l’archive CMP examinée. Cette absence est une raison supplémentaire de ne pas la republier dans l’exécutable.

## Hidden and Dangerous 2 Widescreen Fix

La version officielle `HiddenandDangerous2.WidescreenFix` de [ThirteenAG](https://github.com/ThirteenAG/WidescreenFixesPack/tree/master/source/HiddenandDangerous2.WidescreenFix) est embarquée afin de corriger le format d’image, le champ de vision, le HUD et les viseurs aux résolutions modernes. L’archive intégrée provient de la release `hd2`, publiée le 16 mai 2020, et est verrouillée par SHA-256 (`8B8315B88420FCFED9891F2D39886F6384BDA1B32CDD299AC27D728391E65A9F`).

Ce composant est distribué sous licence MIT, Copyright (c) 2018 ThirteenAG. Le texte complet de la licence est installé à côté du composant.

## Hidden & Dangerous 2

Aucun fichier de l’installation commerciale de Hidden & Dangerous 2 ou Sabre Squadron n’est stocké dans ce dépôt. Les restaurations sont calculées à partir de l’installation que possède déjà l’utilisateur.

Les noms, marques, cartes, scripts et ressources du jeu restent la propriété de leurs ayants droit respectifs. Ce projet communautaire n’est pas affilié à 2K, Take-Two ou Illusion Softworks/2K Czech.

## Sources documentaires

Les liens historiques et techniques sont regroupés dans les rapports du dossier `docs`, notamment :

- RpR Clan pour le jeu en ligne et les mods ;
- les interviews et tests GameSpot de 2003–2004 ;
- Hidden-and-Dangerous.net pour les archives communautaires ;
- les guides GameFAQs et H&D2 Wiki pour recouper le comportement publié des missions.
