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
