# Arctic 4 — réactions voisines aux chutes de glace Kra

État : **positions initiales mesurées, réactions supplémentaires non
démontrées**, révisé le 25 septembre 2026. Aucune réaction humaine n’est ajoutée
au script.

## Verdict

Les trois détecteurs commerciaux sont liés et actifs :

| Détecteur | Rayon joueur | Signaux attestés |
| --- | ---: | --- |
| dummy_Kra1_detektor | 40 | Kra_1, signal 1 |
| dummy_Kra2_detektor | 45 | Kra_2 et Static_Guard_5, signal 1 |
| dummy_Kra3_detektor | 25 | Kra_3, signal 1 |

Chacun conserve le commentaire indiquant qu’il faut aussi compléter les
personnages/animations autour. Ce commentaire prouve une intention de réactions
locales, mais ne nomme aucun destinataire ni signal.

Le seul contrat humain conservé est Static_Guard_5 pour Kra2. Son OnSignal(1)
tourne vers dummy_Kra2_detektor, attend huit secondes, affiche deux messages,
puis reprend sa boucle. L’animation « effrayée et figée » y est elle-même
marquée à compléter : aucun nom d’animation n’est attesté.

## Mesures des positions initiales

Les binaires complets sont désormais accessibles. L'outil
`tools/scene_frame_position_audit.py` résout les détecteurs dans le
`scene2.bin` effectif de `Patch.dta` et les soldats dans `actors.bin` de
`missions.dta`. Les 763 frames positionnées ont été contrôlées. Les distances
ci-dessous sont euclidiennes entre **positions
initiales**, pas des distances garanties au moment où le joueur déclenche la
chute. Le rayon de `_PlayerInRange` mesure le joueur par rapport au détecteur;
il ne définit pas à lui seul un rayon de réaction pour les soldats.

| Détecteur, position XYZ | Acteurs liés les plus proches, distance initiale |
| --- | --- |
| Kra1 `(-85.138313, 3.381779, -63.280319)` | Static_Guard_3 : 32,07 m; Static_Guard_2 : 47,37 m; Static_Guard_4 : 50,34 m. |
| Kra2 `(-67.625069, 2.938424, 28.357651)` | Static_Guard_5 : 18,45 m; Meteorolog : 24,28 m; Walking_Guard_1 : 38,96 m; Sniper_2 : 48,40 m. |
| Kra3 `(-166.762726, 2.718777, 36.131020)` | AntiSniper_1/2/3 : 37,07/37,69/38,24 m; aucun acteur nommé dans les 25 m initiaux. |

Les frames parents `Kra_1`, `_2` et `_3` affichent `(0, 0, 0)` dans ce
parseur, car leur transformation utile est portée par la hiérarchie de scène.
Elles ne servent donc **pas** de points de mesure. Les détecteurs et frames
d'effets proches servent d'ancres spatiales; un contrôle dans l'éditeur ou le
moteur reste nécessaire pour connaître le lieu physique exact de la chute.

Le registre commercial relie `Static_Guard_3`, `Static_Guard_5`, `Meteorolog`,
`Walking_Guard_1` et les trois AntiSnipers à leurs scripts respectifs. Le
script de `Static_Guard_3` consomme déjà le signal 1 pour la conversation avec
le garde 2 : le réutiliser pour Kra1 ferait entrer deux événements distincts
dans le même handler. `Meteorolog` transporte une caisse selon une longue
route et `Walking_Guard_1` patrouille; aucun des deux n'a de contrat Kra ni de
gestionnaire de signal 1. Leur seule proximité initiale ne permet pas de les
interrompre sans prévoir la reprise d'activité.

## Pourquoi aucune copie vers Kra1/Kra3

Kra1 possède un garde proche au départ, mais son signal 1 est réservé à une
conversation. Kra3 n'a aucun humain lié dans les 25 m initiaux. Aucune
animation de surprise et aucun chemin de reprise propre à Kra1/Kra3 n'ont été
retrouvés. Copier `OnSignal(1)` de Static_Guard_5 créerait une collision de
protocole pour le garde 3 et une réaction sans propriétaire prouvé pour Kra3.

## Proposition uniquement spéculative

Le fichier REACTION_MATRIX.plan.disabled conserve la matrice mesurée et les
portes restantes, pas un prototype de script. En éditeur et en moteur, il faut
capturer la position des acteurs **au moment de chaque chute**, puis inspecter
leurs activités avant de réserver un signal. Les candidats ne sont acceptés que
si :

- ils sont spatialement dans le rayon de l’événement, pas seulement du joueur ;
- leur script ne consomme pas déjà le signal choisi ;
- une animation compatible existe dans les assets commerciaux ;
- alarmes, mort et reprise de patrouille interrompent proprement la réaction.

Sans ces quatre preuves, la proposition reste une simple liste moderne. Aucun
Sendsignal supplémentaire ne doit être ajouté aux détecteurs.

## Provenance des mesures

- `Patch.dta::MISSIONS/ARCTIC4/scene2.bin` : 3 579 974 octets, SHA-256
  `df28fdab6a40d59d26abf696f0e45291310356f3fb637c54aa2e3f0f9f204e37`;
- `missions.dta::MISSIONS/ARCTIC4/actors.bin` : 16 359 octets, SHA-256
  `280aa09645a1610db10c2708263f4d1dc7b35694f99d48872388039c7f77fdfb`;
- `missions.dta::MISSIONS/ARCTIC4/Scripts.dta` : bindings contrôlés avec
  `tools/script_binding_audit.py`;
- scripts commerciaux Kra et gardes : `Scripts.dta::SCRIPTS/ARCTIC4/`.

## Tests futurs

Tester chaque Kra séparément, puis alarmes simultanées, acteur mort, joueur à la
limite du rayon, sauvegarde pendant animation, et répétition du détecteur. Pour
Kra2, vérifier d’abord le comportement commercial de Static_Guard_5 afin de ne
pas attribuer à une nouvelle animation un délai ou une reprise déjà défectueux.
