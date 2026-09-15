# Étude expérimentale — objectifs solo omis de Brest et Sicily en coopération

État : **classification terminée, aucun objectif à recopier directement**, 14
septembre 2026. Aucun script actif, catalogue commercial ou installateur n'est
modifié ; aucun prototype n'est produit.

## Synthèse

| Mission | Texte solo omis | Fonction | Classe | Verdict coop |
| --- | ---: | --- | --- | --- |
| Brest | `15502` | éliminer tous les ennemis | objectif Carnage | ne pas ajouter au mode Cooperative |
| Brest | `15505` | toute l'unité doit survivre | survie sans historique réseau | bloqué par mort/respawn/déconnexion |
| Sicily1 | `15543` | quitter la zone | étape de sortie solo | variante réseau à concevoir, pas restauration |
| Sicily1 | `15544` | éliminer tous les ennemis | objectif Carnage | ne pas ajouter au mode Cooperative |
| Sicily2 | `15558` | rejoindre les autres SAS | étape narrative solo raccourcie en coop | scénario remplacé |
| Sicily2 | `15552` | éliminer tous les ennemis | objectif Carnage | ne pas ajouter au mode Cooperative |
| Sicily2 | `15555` | toute l'unité doit survivre | survie sans historique réseau | bloqué par mort/respawn/déconnexion |
| Sicily2 | `15551` | pont détruit / détruire le pont | indicateur solo d'échec critique | ne jamais l'ajouter face à `15557` |

Les omissions ne forment donc pas un lot de huit restaurations. Trois sont des
objectifs propres au mode Carnage, deux sont des étapes de scénario solo sans
contrat réseau conservé, deux demandent une vraie mémoire de mort multijoueur,
et la dernière est un état d'échec désormais absorbé par le scénario coop.

## Méthode de numérotation

Les numéros de `SetObjectiveStatus` sont locaux à la liste d'objectifs de la
carte. Un texte conservé ne récupère pas automatiquement son index solo.

- Brest solo : `15500`, `15506`, `15503`, `15501`, `15504`, `15502`, `15505`.
- Co_Brest commercial : `15500`, `15506`, `15503`, `15501`.
- Sicily1 solo : `15540`, `15541`, `15542`, `15543`, puis `15545` à `15548`,
  enfin `15544`.
- Co_Sicily1 : `15540`, `15541`, `15542`, puis `15545` à `15548`. Les objectifs
  solo 5 à 8 deviennent explicitement coop 4 à 7.
- Sicily2 solo : `15558`, `15550`, `15553`, `15554`, `15552`, `15555`,
  `15556`, `15557`, `15551`.
- Co_Sicily2 : `15550`, `15553`, `15554`, `15556`, `15557`, renumérotés 1 à 5.

Dans Brest, `15504` est également absent du catalogue commercial coop, mais il
n'appartient pas au présent lot « restant » : son acteur, ses deux charges et son
script complet permettent une restauration déterministe déjà traitée ailleurs.
Son futur index coop 5 ne rend pas les anciens index 6/7 directement valides.

## Brest

### 15502 — objectif Carnage, pas objectif coop manquant

Le contrôleur normal `objectyves.scr` connaît dans ses commentaires l'objectif
6 mais ne l'initialise ni ne le valide. La logique existe dans le contrôleur
séparé `objectyves_carn.scr` :

```text
SetObjectiveStatus(6, 0);
Whenever DET(_GetCountOfCarnageEnemies()==0)
{
    ...
    SetObjectiveStatus(6, 1);
}
```

Ce compteur fait aussi partie de la condition qui autorise l'objectif de retour
en Carnage. `Co_Brest` est déclaré sous le `GAMESTYLE cooperative` et son
contrôleur ne contient ni état `detx`, ni compteur Carnage, ni objectif 6.

**Classification : objectif de mode.** Ajouter `15502` au bloc coop changerait
le scénario et pourrait retarder indéfiniment la sortie avec un ensemble
d'ennemis qui n'a pas été calibré comme population Carnage. Aucune restauration
n'est recommandée.

### 15505 — survie

Le solo ne mémorise pas les morts pendant la partie. À la sortie, son contrôleur
normal n'évalue `_IsTeamMemberDead()` que si `plnum > 1`, puis réussit l'objectif
7 si la fonction vaut faux. Le contrôleur Carnage fait un test final apparenté.
`Co_Brest` retire ce bloc et ne déclare pas le texte.

La seule sémantique coop défendable est celle déjà retenue pour Co_Libye2 et les
deux Burgundy : une mort d'un allié actif disqualifie définitivement l'objectif,
un respawn ou une reconnexion ne l'efface pas, une déconnexion vivante est
neutre et les spectateurs sont exclus. Aucun événement serveur fiable conservé
ne permet actuellement de maintenir cet historique.

**Classification : création réseau bloquée.** Ne pas tester seulement l'état
vivant à l'extraction ; cela récompenserait une équipe ayant respawné.

## Sicily1

### 15543 — quitter la zone

Dans le solo, la destruction des trois canons initialise l'objectif 4 puis arme
`vypadni`. En Carnage, ce départ attend en plus que le compteur d'ennemis tombe
à zéro. `_AllPlayersInRange(35)` lance ensuite la cinématique de sortie et valide
l'objectif 4.

Le contrôleur coop retire entièrement ce sas de fin et initialise directement
sept objectifs : les trois canons puis les quatre sabotages facultatifs. Il ne
conserve ni objectif de sortie, ni logique `vypadni`, et assume explicitement le
décalage solo 5–8 vers coop 4–7.

**Classification : étape solo sans équivalent réseau.** Une extraction coop
serait faisable techniquement, mais il faudrait définir le volume, le moment
d'activation, la présence de tous les joueurs, le traitement des morts,
respawns, spectateurs et déconnexions, puis le déclenchement de fin de mission.
Ce contrat n'est pas conservé ; aucun prototype minimal n'est proposé.

### 15544 — éliminer tous les ennemis

`Sic1_KRVEPROLITI.scr` n'assigne `Sic1_OBJ_KRVAK.scr` que lorsque
`_SPGetGameType()` vaut 3 ou 7. Le script attribué initialise et valide l'objectif
9 avec `_GetCountOfCarnageEnemies()`. La logique de sortie solo possède les mêmes
gardes 3/7.

**Classification : objectif Carnage.** Son absence de Co_Sicily1 est normale et
ne doit pas être compensée par un objectif coop 8 ou 9.

## Sicily2

### 15558 — rejoindre les autres SAS

Dans le solo, l'objectif 1 est le seul actif au départ. La conversation du
médecin réussit cet objectif, initialise les objectifs 2 à 4 et peut échouer le
premier si le médecin meurt avant le briefing.

La coop conserve le médecin et une version courte de la scène, mais son
`Sic2_SAS_1_doktor_dabing.scr` ne change plus aucun objectif : le signal 1 joue
une seule réplique puis rend le médecin à son activité, et sa mort ne porte plus
d'échec. Le contrôleur coop initialise dès le départ les cinq tâches du pont et
active `zone1`.

**Classification : scénario remplacé/raccourci.** Le support narratif subsiste,
mais le sas objectif a été supprimé consciemment. Le rétablir exigerait de
réintroduire l'ordre d'activation, un interlocuteur autoritaire et les cas où
plusieurs joueurs arrivent, ignorent la scène ou perdent le médecin. Ce n'est
pas une ligne `SetObjectiveStatus` manquante.

### 15552 — éliminer tous les ennemis

`Sic2_KRVEPROLITI.scr` assigne `Sic2_OBJ_KRVAK.scr` uniquement pour les types 3
et 7. Ce dernier initialise l'objectif solo 5 et le réussit quand
`_GetCountOfCarnageEnemies()` atteint zéro. Aucun homologue n'existe dans le
dossier coop.

**Classification : objectif Carnage.** Ne pas l'insérer dans la séquence coop.

### 15555 — survie

Le contrôleur solo n'évalue l'objectif 6 qu'à la fin de la défense :

```text
IF (!_IsTeamMemberDead()) { SetObjectiveStatus(6, 1); }
```

Le contrôleur coop omet ce test et active une zone de respawn. Comme pour Brest,
un état instantané ne dit pas si un joueur est mort puis revenu. La cohorte et
les règles mort/respawn/déconnexion doivent rester identiques aux études de
survie précédentes.

**Classification : création réseau bloquée.** Aucun `.scr.disabled` n'est
produit sans source de mort autoritaire et persistante.

### 15551 face à 15557 — conflit apparent, échec déjà absorbé

Le commentaire du contrôleur solo est sans ambiguïté : l'objectif 9 est
`MOST znicen (jen fail)`, « pont détruit, seulement en échec ». Le signal 2 des
éléments du pont exécute `SetObjectiveStatus(9, 3)` et termine la chaîne. Ce n'est
pas un ordre de détruire le pont qu'il faudrait rendre réalisable.

Dans la coop, le même signal 2 échoue directement les cinq objectifs déclarés.
À la fin normale, l'objectif coop 5 `15557` réussit si la section `M5` est encore
présente, sinon il échoue. Le scénario réseau a donc transformé l'ancien témoin
négatif en deux mécanismes plus explicites : échec global à la destruction et
objectif positif « pont intact ».

**Classification : fonction remplacée et conflit de scénario.** Ajouter
`15551` serait au mieux un doublon d'échec, au pire une consigne contradictoire
avec `15557`. Il ne doit jamais être proposé comme objectif coop supplémentaire.

## Porte de décision commune

Avant toute variante de sortie ou de survie, un test hôte/client doit journaliser
identité du joueur, appartenance à l'équipe, mort, respawn, spectateur,
connexion/déconnexion, changement de zone et fin de mission. Sans ce journal,
les objectifs 15505/15555 restent bloqués et 15543 reste une création de règles.

Les objectifs Carnage ne doivent être envisagés que dans une carte explicitement
exposée sous ce mode, avec population d'ennemis et catalogue propres. Ils ne sont
pas des bonus à greffer sur le `GAMESTYLE cooperative`.

## Sources internes

- `.analysis/objective-audit.json`
- `.analysis/metadata/sabre/GameData/Gamedata01.gdt`
- `.analysis/metadata/sabre/GameData/mpmaplist.txt`
- contrôleurs `objectyves.scr` et `objectyves_carn.scr` de Brest/Co_Brest
- `Sic1_objectives.scr`, `Sic1_KRVEPROLITI.scr`, `Sic1_OBJ_KRVAK.scr`
- `Sic2_OBJECTIVES.scr`, `Sic2_KRVEPROLITI.scr`, `Sic2_OBJ_KRVAK.scr`
- copies solo/coop de `Sic2_SAS_1_doktor_dabing.scr`
- études de survie sous `experimental/CO_LIBYE2_OBJECTIVE4_SURVIVAL/` et
  `experimental/CO_BURGUNDY1_OBJECTIVE7_SURVIVAL/`
