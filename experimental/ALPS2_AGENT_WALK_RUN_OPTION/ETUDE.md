# Alps 2 — allure optionnelle de l'agent

État : **marche release conservée, rattrapage dynamique désactivé**, 15
septembre 2026.

## Vestige et séquence active

Dans `AL2_agent.scr`, `//HUMAN_SETMODE_Run();` se trouve immédiatement avant
`SendSignal(obj,4)`, `HUMAN_SetWaitForPlayer(true,9,3,true)` et la longue route
d'escorte `AL2_ag_01 ... AL2_ag_08`. Le script ne contient pas de setter Walk
à cet endroit : l'allure courante est donc la valeur release implicite et ne
doit pas être écrasée globalement.

La route comporte sept contrôles de proximité sur des points `way1..way7`, une
ouverture de porte et une attente du joueur. Un `Run()` brut au début
accélérerait toute l'escorte, y compris les approches de porte et les boucles de
correction. Ce profil est rejeté comme remplacement.

## Option additive

`WALK_RELEASE` est toujours le défaut et ne change aucune ligne.

`DYNAMIC_CATCHUP_TEST` est un mock de gameplay : à des frontières de segments
déjà existantes, il autorise la course seulement si le joueur est proche ; si
le joueur est loin, il revient à la marche et laisse
`HUMAN_SetWaitForPlayer` faire son travail. Aucun waypoint n'est ajouté. Les
seuils et emplacements du mock sont des **CRÉATIONS**, pas des vestiges.

Le fragment `PROTOTYPE_DYNAMIC_MODE.scr.disabled` illustre le contrat sans être
compilable ni installable. Il ne doit être recopié qu'après validation de la
syntaxe conditionnelle dans une copie de mission.

## Tests

- chronométrer `WALK_RELEASE` comme référence ;
- tester joueur collé, à 5–10 m, très loin et bloqué derrière chaque porte ;
- tester coopération à plusieurs joueurs ;
- vérifier qu'aucune boucle `xw1..xw7` n'oscille entre marche et course ;
- revenir explicitement à Walk avant `AL2_ag_07_1`, le déverrouillage et
  `AL2_ag_08` ;
- tester alarme, mort, sauvegarde/rechargement et fin d'escorte ;
- rejeter l'option si elle fait courir l'agent loin du joueur ou modifie le
  timing des dialogues/objectifs.

La variante Carnage n'est pas incluse automatiquement : son script et ses
timings doivent être mesurés séparément avant d'adopter la même option.

## Profil complet du 26 septembre 2026

`alps2-agent-segment-pace` est désormais une recette complète **MODERNE** du
catalogue. Elle fabrique 5 828 octets à partir des 4 646 octets de
`Scripts.dta::scripts/alps2/al2_agent.scr`, SHA-256
`90ffa75ea923d2353c01505c6640715dd92b5b5c5755dd1831fcefd676b558d0`.
L'acteur `AL2_agent`, sa liaison, les huit points concernés et les sept frames
`way1..way7` sont vérifiés dans les sources épinglées.

Six choix d'allure sont insérés **avant**, et non à l'intérieur, des boucles de
reprise : `AL2_ag_01`, `al2_agx_002`, `al2_agx_04`, `AL2_ag_05`, `AL2_ag_05c`,
`AL2_ag_06x`. Au début du segment, joueur dans les sept unités : Run; sinon Walk.
La distance est un choix moderne. L'attente commerciale du joueur 9/3 reste
active et l'allure n'est pas recalculée continuellement pendant le mouvement.

Le retour Walk est explicite avant `AL2_ag_07_1`, donc avant la porte et la
boucle `AL2_ag_08`. Il est aussi rétabli avant `SetNPCTeamStatus(me, 1)` pour
ne pas transmettre l'allure expérimentale au contrôle joueur. Aucune route,
condition de reprise, voix, attente, alarme ou émission d'objectif n'est changée.
Le Run global commenté reste commenté. Variante issue du solo, pas un port coop.

Empreinte du script dérivé :
`a8709f5393233b7e285be49a4aa0dc75ef20edbbb90dc64c3b0d8b8f87019a65`.
Le profil est prêt pour préparation native; la fluidité, la distance réellement
évaluée, les portes et les interruptions restent des essais moteur `pending`.
