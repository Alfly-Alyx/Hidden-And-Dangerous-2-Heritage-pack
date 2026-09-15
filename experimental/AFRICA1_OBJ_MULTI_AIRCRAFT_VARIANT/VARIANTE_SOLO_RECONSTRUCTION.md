# Africa1_Obj — variante solo `RECONSTRUCTION`

État : conception non jouable, 14 septembre 2026. Nom de travail :
`Africa1_Obj [Reconstruction Solo]`. Cette entrée possède à terme son propre
répertoire et ne modifie jamais les registres `mpscripts.dta` ou `scripts.dta`
de la carte multijoueur officielle.

## Données officielles réutilisées

- la scène et ses placements commerciaux ;
- les cinq citernes et leurs charges `w_explosive_01–05` ;
- `dummy_cisterny_organizer` et le protocole des valeurs 1–5 : chaque citerne
  passe sa valeur à zéro à la destruction, puis l'organisateur réussit
  l'objectif 1 lorsqu'elles sont toutes nulles ;
- l'avion `la_macchi01`, sa charge `w_explosive_13` et son succès direct de
  l'objectif 2 à la mort ;
- les huit bindings multijoueur résolus comme référence de comportement ;
- les objectifs 1–3 initialisés par les scripts commerciaux.

La logique du second avion, des valeurs 10–15 et des frames manquantes n'est
pas classée comme donnée solo officielle.

## Logique solo créée

La reconstruction propose une mission de sabotage à un joueur :

1. insertion à un spawn solo distinct ;
2. destruction des cinq citernes, avec conservation du compteur commercial ;
3. destruction de `la_macchi01`, avec conservation de son explosion Patch ;
4. extraction vers une nouvelle zone seulement après réussite des objectifs 1
   et 2 ;
5. réussite de mission à l'entrée du joueur vivant dans cette zone.

L'objectif 3 devient donc un objectif d'extraction **MODERNE**. Son texte, sa
zone, son activation conditionnelle et l'appel de fin de mission sont à créer.
Il ne doit pas réutiliser une règle multijoueur opaque sous prétexte que le
numéro 3 est déjà initialisé.

La première version solo reste volontairement à un avion. La variante
multi-avions étudiée dans le dossier pourra devenir ensuite une option de
difficulté, mais seulement après création de ses actifs et de son agrégateur.

## Choix spéculatifs

| Choix | Proposition de départ | Pourquoi spéculatif |
| --- | --- | --- |
| ordre des sabotages | citernes et avion libres, extraction verrouillée | aucun ordre solo commercial |
| objectif 3 | extraction | la règle multijoueur exacte n'est pas conservée |
| renforts | une vague après le premier objectif réussi | aucun directeur solo attesté |
| sauvegarde | checkpoints après chaque objectif 1/2 | la carte MP n'en définit pas |
| multi-avions | difficulté optionnelle ultérieure | second avion et charge absents |
| briefing/textes | rédaction moderne | aucune campagne solo associée |

Les ennemis existants, leur quantité et leurs itinéraires ne deviennent pas
automatiquement une difficulté solo correcte. Toute modification d'IA sera
nommée et testée comme création.

## Éléments encore bloquants

- position sûre du spawn et de l'extraction, volumes et orientation ;
- texte localisé des trois objectifs et briefing ;
- appel exact de réussite/échec d'une mission solo dans ce mode ;
- comportement de l'objectif 3 commercial, s'il en existait un côté défense ;
- traitement de l'avion ou d'une citerne détruits avant l'initialisation ;
- équilibre munitions/explosifs et règles de sauvegarde ;
- propriétaire des éventuels renforts et de la musique de fin.

Ces lacunes n'annulent plus la variante : elles empêchent seulement de la
présenter comme jouable ou fidèle avant création explicite.

## Protocole de test

1. Vérifier que la carte multijoueur conserve huit bindings et ses règles
   actuelles avant/après présence de l'entrée solo.
2. Tester les cinq citernes dans tous les ordres, y compris destructions
   simultanées et destruction avant activation de l'objectif.
3. Tester l'avion avant/après les citernes et confirmer un seul succès de
   l'objectif 2.
4. Interdire l'extraction tant qu'un objectif principal manque ; l'autoriser
   une seule fois ensuite.
5. Tester mort, rechargement et sauvegarde après 0 à 5 citernes, puis avant et
   après l'avion.
6. Confirmer qu'aucune valeur 10–15 ni aucun script du second avion n'est lu
   dans la configuration solo initiale.
7. Vérifier retour au menu, texte de résultat et absence de dépendance réseau.

Acceptation : la mission solo se termine de façon déterministe, sans modifier
la trace de la carte multijoueur et sans présenter l'extraction créée comme une
route commerciale retrouvée.
