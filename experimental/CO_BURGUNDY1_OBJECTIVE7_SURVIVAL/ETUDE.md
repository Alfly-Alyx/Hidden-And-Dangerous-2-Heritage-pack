# Étude expérimentale — survie et copie Carnage de Co_Burgundy1

État : **sémantique proposée, implantation bloquée, aucun prototype
`.scr.disabled`**, 14 septembre 2026. Aucun script actif, registre de mission ou
fichier de jeu n'est modifié.

## Verdict

L'objectif 7 n'est pas un simple handler oublié à décommenter. Son intention et
son point de validation sont exceptionnellement bien conservés, mais la
condition solo `_IsTeamMemberDead()` n'a aucun précédent actif dans les scripts
coop Sabre et ne définit ni le respawn ni les changements de participants.

La sémantique coop proposée est la suivante :

> Tout joueur qui devient membre actif de l'équipe alliée entre dans la cohorte
> évaluée. Sa première mort pendant qu'il appartient à cette équipe rend la
> réussite de l'objectif 7 définitivement impossible pour la tentative. Un
> respawn, une reconnexion ou le départ ultérieur de ce joueur n'efface pas la
> perte. Une déconnexion vivante n'est pas une mort et ne fait pas échouer
> l'objectif. Les spectateurs qui ne rejoignent jamais l'équipe sont exclus.

Au contact final avec le maquisard, le script ne doit attribuer la réussite que
si aucune mort admissible n'a été enregistrée. Comme le solo ne marque pas
explicitement l'objectif en échec lors d'une perte, une reconstruction fidèle
conserverait ce comportement : drapeau interne irréversible, puis absence de
réussite à la fin, sans inventer un message d'échec anticipé.

Cette règle est cohérente et exploitable par un futur mécanisme serveur, mais
les sources disponibles ne permettent pas encore de l'implémenter de manière
fiable. Le blocage est donc technique, pas narratif.

## Preuve directe conservée

### Solo

`Burgundy1/bur1_maquisend.scr` effectue le test lorsque le joueur rejoint le
maquisard en fin de mission :

```text
// neni lone a nikdo nechcipl
if((!_IsTeamMemberDead()) AND (_SPGetGameType() != 2))
{
    SUBTITLES_SetText(57999804);
    Delay(2000);
    SetObjectiveStatus(7, 1);
}
```

Le commentaire signifie « pas Lone Wolf et personne n'est mort ». Le test est
placé avant la cinématique et avant la réussite de l'objectif 4 de contact. Il
ne demande pas que toute l'équipe soit dans la zone : le déclencheur est un
simple `_PlayerInRange(15)`.

Le catalogue solo analysé déclare huit objectifs dans cet ordre :

| Slot | Texte |
| ---: | ---: |
| 1 | `15560` |
| 2 | `15561` |
| 3 | `15562` |
| 4 | `15563` |
| 5 | `15566` |
| 6 | `15567` |
| 7 | `15565` — « All members of the unit must survive » |
| 8 | `15564` |

Le numéro de slot, le texte `15565`, le sous-titre de réussite `57999804`, la
condition solo et le moment d'attribution sont donc tous attestés.

### Coop

`Co_Burgundy1/bur1_maquis01.scr` conserve le même bloc au même endroit, avec
deux différences de contexte : la portée du déclencheur est de 5 unités et les
cinq lignes de survie sont toutes commentées. La réussite de l'objectif 4 reste
active juste après. Ce vestige prouve que l'objectif 7 a été envisagé dans cette
conversion coop, puis volontairement neutralisé ou laissé inachevé.

La carte `Co_Burgundy1` de `mpmaplist.txt` ne déclare que `15560`, `15561`,
`15562` et `15563`. La copie de carte du Coop Map Package confirme ces quatre
entrées. L'objectif 7 n'a donc pas non plus de ligne d'interface coop.

`bu1_spawn3.scr` active en outre `zone3` avec `MP_EnableSpawnZone` lorsqu'un
membre de l'équipe approche. Comme pour Co_Libye2, la réapparition est une
mécanique concrète de la carte, pas une hypothèse extérieure.

## Comparaison avec Co_Libye2

Les deux cas ont le même blocage fondamental :

| Élément | Co_Burgundy1, objectif 7 | Co_Libye2, objectif 4 |
| --- | --- | --- |
| intention | texte et bloc coop commenté | initialisation coop commentée |
| logique solo | `_IsTeamMemberDead()` au contact final | `_IsTeamMemberDead()` à l'extraction |
| feedback conservé | `57999804` dans le bloc | handler de signal 4, `53999802` |
| objectif déclaré en coop | non, seulement quatre slots | non, seulement deux slots |
| respawn local | `MP_EnableSpawnZone("zone3", 1)` | zones 2 à 5 activables |
| primitive de mort coop active | aucune | aucune |

Burgundy1 apporte une preuve historique plus forte du raccord exact : le corps
coop commenté est déjà présent et vise explicitement le slot 7. Il n'apporte
toutefois aucune preuve supplémentaire sur la vérité réseau de
`_IsTeamMemberDead()`.

L'inventaire Sabre complet ne contient cette fonction que dans des scripts solo
et dans le bloc commenté de Co_Burgundy1. Aucun `OnPlayerDeath`, `OnRespawn`,
`OnConnect`, `OnDisconnect` ou équivalent n'a été trouvé. Les `OnDeath()` coop
observés appartiennent à des scripts de PNJ ou véhicules fixes ; ils ne
fournissent pas un événement pour les avatars multijoueurs.

L'étude sœur détaille ce constat et les primitives coop disponibles :
`experimental/CO_LIBYE2_OBJECTIVE4_SURVIVAL/ETUDE.md`.

## Contrat précis pour les cas réseau

### Mort et respawn

- toute mort réelle en jeu compte, quelle qu'en soit la cause : ennemi,
  environnement, suicide ou tir ami ;
- la première mort pose un drapeau global de tentative, par exemple
  `casualty_seen = 1` ;
- ce drapeau ne revient jamais à zéro pendant la manche ;
- le respawn change l'état de l'avatar, pas le résultat historique de
  l'objectif ;
- avec `allowrespawn=0`, la même mort produit le même échec logique.

### Déconnexion et reconnexion

- une déconnexion alors que le joueur est vivant est neutre : elle ne doit ni
  créer une mort fictive ni empêcher les joueurs restants de finir ;
- une mort déjà observée reste comptée si le joueur se déconnecte pendant son
  attente de respawn ;
- une reconnexion ne réinitialise jamais le drapeau collectif ;
- si le moteur supprime le joueur mort avant d'émettre un événement de mort
  observable, le script ne peut pas distinguer un abandon vivant d'une fuite
  après décès : c'est un cas bloquant, pas une raison de choisir arbitrairement.

### Arrivée tardive, spectateur et changement d'équipe

- un joueur arrivé tardivement entre dans la cohorte lors de sa première
  apparition active côté allié ; seules ses morts postérieures comptent ;
- un spectateur pur est exclu ;
- une mort survenue alors que le joueur appartient à l'équipe alliée compte,
  même s'il change ensuite d'équipe ;
- le départ d'un joueur vivant retire seulement ses futures obligations, sans
  changer l'historique collectif.

Cette cohorte dynamique est préférable à une photographie des joueurs au
chargement : elle couvre les arrivées tardives sans considérer une simple
déconnexion comme une mort. Elle doit néanmoins être validée comme décision de
design, car aucun script commercial ne la formule.

## Pourquoi aucun prototype de survie n'est fourni

### Décommenter le bloc

Rejet : cela ne mémorise aucune mort et suppose que `_IsTeamMemberDead()` voit
les clients distants, les joueurs en attente et les avatars recréés. Après un
respawn, le test pourrait attribuer un faux succès.

### Polling avec drapeau irréversible

```text
Whenever casualty(_IsTeamMemberDead())
{
    casualty_seen = 1;
    SetWhenever(casualty, false);
}
```

Rejet provisoire : le stockage est adapté, mais le déclencheur n'est pas
attesté en coop. Une mort plus courte que la cadence d'évaluation, une
évaluation locale côté client ou une suppression immédiate de l'avatar suffirait
à rendre le résultat faux.

### Remplacer par `_MP_AllTeamMembersAreInRange`

Rejet : cette primitive mesure une présence spatiale actuelle. Elle ne prouve
aucune survie historique, confond déconnexion et absence, et modifierait le
contrat final du maquisard, actuellement déclenché par un seul joueur proche.

### Considérer toute déconnexion comme une mort

Rejet : aucun texte ni script ne soutient cette règle. Elle pénaliserait les
problèmes réseau et rendrait l'objectif dépendant d'un événement qui n'est pas
létal.

Sans événement joueur serveur ou preuve expérimentale de la persistance de
`_IsTeamMemberDead()`, tout `.scr.disabled` donnerait une fausse impression de
complétude.

## Point critique distinct : `bur1_obj_carnage.scr` copié vers la coop

La source principale actuelle contient une opération différente de l'objectif
de survie : `CrossMissionScriptInstaller` recopie le script solo
`Scripts/Burgundy1/bur1_obj_carnage.scr` vers
`Scripts/Co_Burgundy1/bur1_obj_carnage.scr`. Cette copie répond à une liaison
commerciale réelle : dans le registre coop, l'acteur `F_sloup03` demande ce
fichier, absent du dossier coop livré.

La provenance du fichier est donc officielle. L'affirmation « objectif Carnage
restauré » ne l'est pas encore, car deux contrats restent incomplets.

### Garde de type de partie

Le script initialise et réussit l'objectif 8 uniquement si
`_SPGetGameType()` vaut 3 ou 7 :

```text
if((game_type == 3) OR (game_type == 7))
{
    SetObjectiveStatus(8, 0);
}
else
{
    SetWhenever(alldead, false);
}
```

Les scripts commerciaux étiquettent systématiquement 3/7 comme **Carnage**.
`Co_Burgundy1`, lui, n'apparaît que dans la section
`<GAMESTYLE type="cooperative">` du `mpmaplist`; aucune entrée ne l'expose dans
un style Carnage séparé. D'autres scripts hérités de Co_Brest désactivent même
des acteurs lorsque le type vaut 3/7. Ce comportement est cohérent avec un mode
distinct du parcours coop normal, sans suffire à prouver ce que renvoie le moteur
dans `Co_Burgundy1`.

L'audit statique ne prouve cependant pas la valeur numérique retournée par le
moteur dans une session Cooperative. La conclusion exacte est donc :

- si la coop ordinaire ne renvoie ni 3 ni 7, la copie ne fait qu'initialiser la
  valeur 58 à zéro puis désarme son compteur ; elle est fonctionnellement inerte ;
- si une variante de lancement de Co_Burgundy1 peut renvoyer 3 ou 7, le compteur
  devient actif et participe aussi au déblocage de l'objectif 4 via les valeurs
  51, 52 et 58, mais son interface reste invalide tant que le slot 8 manque.

Il faut donc journaliser `_SPGetGameType()` sur serveur, hôte et client dans une
session Cooperative réelle avant de qualifier cette copie de restauration.

### Slot 8 absent du catalogue

Le catalogue commercial coop ne contient que quatre objectifs. Après la
restauration déterministe de `15566` et `15567`, il en contientrait six.
`15565` (survie) est le slot solo 7 et `15564` (éliminer tous les ennemis) le slot
solo 8 ; tous deux sont absents.

Un `SetObjectiveStatus(8, ...)` ne crée pas le huitième libellé. Aucun élément
inspecté ne prouve qu'un index hors catalogue est affichable ou même sûr. Ajouter
seulement `15564` comme septième entrée ne répare pas le script, qui continuerait
d'écrire dans 8. Ajouter aussi `15565` uniquement comme remplissage introduirait
un objectif de survie que l'étude vient précisément de classer bloqué.

Une éventuelle adaptation coop devrait donc choisir explicitement entre :

- conserver les slots solo 7/8, ce qui exige de résoudre d'abord la survie ;
- compacter `15564` au slot coop 7 et réécrire **toutes** les références Carnage
  8 vers 7, comme une adaptation numérotée et non comme une copie exacte ;
- ne pas installer le script si le type 3/7 est impossible en Cooperative.

### Verdict sur la source principale actuelle

**Classification : copie technique officielle, chaîne d'objectif incomplète et
encore expérimentale.** La validation actuelle prouve le fichier source, ses
marqueurs et sa liaison ; elle ne prouve ni l'activation du garde 3/7 en coop, ni
la validité du slot 8 hors catalogue. Les messages de l'installateur qui annoncent
un « objectif Carnage restauré » sont donc trop affirmatifs et devront être
révisés dans une tâche stable distincte si les tests confirment ce diagnostic.
La présente étude ne modifie pas `installer/`.

## Cas distinct : objectifs de discrétion 5 et 6

Les objectifs 5 et 6 ne doivent pas être regroupés avec l'objectif 7. Leur
restauration ne demande aucune définition nouvelle de joueur, de mort ou de
respawn.

`bu1_objective_05.scr` repose uniquement sur des preuves de monde déjà
conservées :

- la valeur globale 70 reste à 0 tant qu'aucune alarme n'a été déclenchée ;
- l'objectif 5 réussit si un joueur entre dans `dummy_boxik` avant l'alarme ;
- l'objectif 6 réussit si les trois explosifs sont armés avant l'alarme ;
- le premier passage de la valeur 70 à 1 désactive définitivement les deux
  tests de réussite ;
- les sous-titres `57999801` et `57999802` sont déjà présents.

Le fichier coop est identique au fichier solo à une seule ligne près : dans la
branche `obj6done`, le solo appelle `SetObjectiveStatus(6, 1)` et la coop appelle
par erreur `SetObjectiveStatus(5, 1)`. La correction vers 6 est donc une
restauration exacte, pas une création comportementale.

Le catalogue solo donne aussi les libellés sans invention : `15566` au slot 5
et `15567` au slot 6. Une restauration autonome peut ajouter ces deux entrées à
la suite des quatre objectifs coop, puis corriger cette unique cible numérique.
Elle ne doit pas attendre l'objectif 7 et ne doit pas embarquer automatiquement
l'objectif 8 (`15564`).

| Critère | Objectifs 5/6 | Objectif 7 |
| --- | --- | --- |
| conditions | monde, alarme, volume, explosifs | historique des joueurs |
| corps coop | complet ; une cible numérique erronée | commenté |
| corps solo homologue | identique sauf `5` → `6` | utilisable seulement sans respawn |
| textes de carte | `15566`, `15567` attestés | `15565` attesté |
| création de sémantique | aucune | cohorte et événements réseau à définir |
| décision | restaurable séparément | prototype bloqué |

## Protocole pour lever le blocage de l'objectif 7

Dans une copie laboratoire uniquement :

1. tracer `_IsTeamMemberDead()` côté serveur, hôte et client avant la mort,
   pendant l'attente de respawn et après la réapparition ;
2. répéter avec `allowrespawn 0` puis 1, plusieurs `respawntime`, mort de l'hôte
   et mort d'un client ;
3. vérifier si un `Whenever` voit toujours au moins une évaluation vraie pour
   une mort suivie d'un respawn immédiat ;
4. tester déconnexion vivante, déconnexion après mort, reconnexion et arrivée
   tardive ;
5. confirmer qu'un spectateur et un joueur d'une autre équipe n'affectent pas
   le résultat ;
6. vérifier que la réussite reste attribuée au contact de `bur1_maquis01` sans
   exiger le regroupement complet ;
7. déclarer temporairement les slots 5, 6 et 7 dans cet ordre, puis contrôler
   l'affichage et la réplication de `15565` et `57999804` ;
8. sauvegarder/reprendre avant une mort, après une mort et juste avant le contact
   final.

Pour la copie Carnage, relever en plus `_SPGetGameType()`, l'état du
`Whenever alldead`, les valeurs 51/52/58 et le comportement des appels aux slots
7/8 avant puis après ajout des seuls objectifs 5/6. Aucun essai ne doit utiliser
un slot non déclaré sans instrumentation de l'interface et de la fin de mission.

Critère de promotion : une source ou un test doit démontrer un événement de mort
autoritaire et non ambigu pour tous les membres actifs, ou prouver que
`_IsTeamMemberDead()` fournit un signal suffisamment persistant et global. La
politique de cohorte ci-dessus devra ensuite être acceptée explicitement.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_maquisend.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_maquis01.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bu1_objective_05.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bu1_objective_05.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_globalalarm.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_globalalarm.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bu1_spawn3.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_obj_carnage.scr`
- `.analysis/metadata/sabre/GameData/mpmaplist.txt`
- `.analysis/objective-audit.json`
- `output/audit/full-game-audit.json`
- `installer/CrossMissionScriptInstaller.cs` (lecture seule ; non modifié)
- `experimental/CO_LIBYE2_OBJECTIVE4_SURVIVAL/ETUDE.md`

## Source externe primaire

- [Lisez-moi officiel de Hidden & Dangerous 2: Sabre Squadron, copie
  archivée](https://hidden-and-dangerous.net/junk/ss_readme.htm) — commandes
  serveur `allowrespawn`, `respawntime` et `spawnprotection`.
