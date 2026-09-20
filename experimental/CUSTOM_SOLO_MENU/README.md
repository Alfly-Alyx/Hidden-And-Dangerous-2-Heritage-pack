# GUI expérimentale des missions personnalisées

La branche `codex/experimental-gui` réunit désormais la GUI du jeu et
`HD2-Custom-Mission-Manager.exe` dans un même flux d'installation.

## Parcours installé

Le menu **Single Player Game** reçoit un bouton **Custom Missions** entre
**Single Mission - Carnage** et **Back**. Il ouvre un écran comportant trois
boutons :

1. missions utilisateur ;
2. missions multijoueur adaptées au solo ;
3. exploration libre / tests d'armes.

Chaque bouton ouvre un catalogue distinct. Les libellés du bouton principal,
des trois catégories, des titres de listes et des missions suivent la langue
active parmi les huit langues prises en charge par H&D2.

## Architecture

- `Gamedata02.gdt` contient les trois entrées de catégories ;
- `Gamedata03.gdt` contient les adaptations multijoueur ;
- `Gamedata04.gdt` contient les missions utilisateur ;
- `Gamedata05.gdt` contient les cartes d'exploration libre ;
- `Models/singleplayer.4ds` reçoit le bouton d'accès ;
- `Models/single mission 2.4ds` reçoit les trois boutons de catégories ;
- `Scripts/HD2.CustomMenu.asi` raccorde les contrôles au navigateur natif.

L'exécutable commercial n'est jamais réécrit. Le module ASI vérifie toutes les
signatures du client 1.12 avant de modifier en mémoire les routes du menu. Le
gestionnaire exige le chargeur ASI du correctif écran large (`d3d8.dll`).

## Installation et retour arrière

Le gestionnaire construit les quatre catalogues depuis le catalogue original
de `SabreSquadron.dta`, génère les scènes de menu depuis les modèles originaux,
installe les traductions et copie les missions placées dans `CustomMissions`.
L'ensemble est appliqué dans une transaction unique.

`STATIC_MENU_MANAGED_FILES.json` mémorise l'empreinte de chaque fichier créé ou
remplacé. Une mise à jour ou une restauration refuse d'écraser un fichier qui a
été retouché depuis l'installation.

## État de validation

Les tests hors ligne exécutent les adaptateurs x86 compilés et couvrent les
trois boutons, les listes, les retours, les offsets cumulés et la préservation
des menus officiels. Le gestionnaire reproduit bit pour bit les catalogues et
scènes générés par l'outil Python de référence. Une validation visuelle
complète dans le jeu reste obligatoire avant de qualifier cette branche de
version stable.
