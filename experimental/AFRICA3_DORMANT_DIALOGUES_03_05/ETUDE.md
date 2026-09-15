# Étude expérimentale — dialogues dormants 03 à 05 d'Africa 3

État : analyse statique et prototype borné désactivé, 14 septembre 2026. Aucun
script de mission n'est activé. Base et Patch contiennent le même code utile
pour les éléments étudiés ; leurs différences de fichiers se limitent aux fins
de ligne.

Cette étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
les patrouilles et le synchroniseur release restent actifs ; une conversation
dormante ne peut être ajoutée qu'avec une condition exclusive et un mutex audio.

## Classification

**Contenu officiel dormant, raccords de déclenchement et d'animation
incomplets.** Le registre lie encore les trois dummies à des scripts de
conversation complets :

| Dummy | Script | Participants | Garde interne |
| --- | --- | --- | ---: |
| `dummy_rozhovor_03` | `AF3a_rozhovor_03.scr` | AF3a_28 / AF3a_29 | valeur 32 |
| `dummy_rozhovor_04` | `AF3a_rozhovor_04.scr` | AF3a_05 / AF3a_06 | valeur 31 |
| `dummy_rozhovor_05` | `AF3a_rozhovor_05.scr` | AF3a_02 / AF3a_03 | valeur 31 |

Les textes, voix, alternances et traitements `OnSignal(1)`/`OnSignal(2)` sont
officiels. Aucun émetteur scripté du signal 1 vers ces trois dummies n'est
toutefois conservé. Seul `dummy_rozhovor_02` possède un activator officiel.

Réveiller les dummies ne suffit pas : les dialogues diffusent les signaux 10
et 11 à leurs acteurs, alors que ceux-ci ne possèdent pas tous les handlers
correspondants. Pour le dialogue 05, le signal 10 a même déjà une autre
sémantique active chez AF3a_03.

## Modèle officiel : dialogue 02

`AF3a_rozhovor_02_activator.scr` attend simultanément :

```text
_PlayerInRange(70)
_FrameInRange(AF3a_14) < 5
```

Il envoie alors le signal 1 à `dummy_rozhovor_02`. Ce modèle prouve la forme
générale d'un déclenchement positionnel, mais pas les rayons, l'ancre ni le
moment prévus pour les dialogues 03 à 05.

AF3a_14 et AF3a_15 sont les seuls acteurs Africa 3 qui incluent
`_inc_rozhovor.scr`. Cet include définit :

| Signal | Effet officiel |
| ---: | --- |
| 10 | arrêt de l'activité, choix aléatoire d'une animation de parole, puis `END` |
| 11 | arrêt et effacement de l'animation, puis `END` |
| 12 | arrêt, effacement et retour vers `ACTIVITY` |
| 13 | arrêt, effacement et branchement vers `ALERT` |

Le dialogue 02 envoie 12 aux deux acteurs à sa fin et dans son traitement
d'interruption. Ces restitutions sont absentes des dialogues 03 à 05.

## Apport de CMP 2.6.5 : une piste pour le dialogue 04 seulement

Le commit CMP examiné (`793d979748b27a9924fccc30fa0fba6edb7cd70f`)
ajoute `AF3a_rozhovor_04_activator.scr`, mais son unique `Whenever
PIR (_PlayerInRange(10))` et son `SendSignal(dummy_rozhovor, 1)` sont entièrement
commentés. Surtout, cet activator n'est pas lié dans
`Missions/co_africa3/mpscripts.dta`. Le fichier est donc une proposition CMP
inerte, pas un déclencheur jouable ni une preuve commerciale du rayon 10.

CMP marque aussi `AF3a_rozhovor_04.scr` comme `DISABLED`. Cette variante retire
la garde commerciale sur la valeur 31 et ajoute des signaux 12 aux deux acteurs
après la dernière réplique, mais pas dans `OnSignal(2)`. Ces changements sont
des choix CMP : ils ne permettent pas d'attribuer au jeu commercial le rayon,
la suppression de garde ou le protocole de restitution.

Aucun activator équivalent n'est ajouté pour 03 ou 05. La présence de cette
ébauche ciblée fait donc de **04 le premier essai borné**, sous l'étiquette
**CMP/MODERNE**. Elle n'élève pas 03 ou 05 au même niveau de confiance.

## Audit par conversation

### Dialogue 03 — AF3a_28 / AF3a_29

Le script contient l'intégralité de la longue conversation et alterne 10/11
entre AF3a_28 et AF3a_29. Il refuse de commencer lorsque la valeur 32 est nulle.
Son signal 2 coupe les deux voix et les sous-titres.

- AF3a_28 ne traite ni 10 ni 11 et possède seulement `ACTIVATE` et `END` ;
- AF3a_29 ne traite ni 10 ni 11 et possède les mêmes labels ;
- AF3a_29 et AF3a_30 envoient déjà le signal 2 au dummy 03 en cas de mort ou
  d'alarme, ce qui atteste au moins une partie du raccord d'interruption ;
- la valeur 32 est remise à zéro par AF3a_29/30 lors de ces événements.

L'include complet ne peut pas être copié : les labels `ACTIVITY` et `ALERT`
n'existent pas. Une adaptation limitée aux handlers 10 et 11 est en revanche
structurellement possible. À l'interruption, le dialogue devrait aussi envoyer
au minimum 11 aux deux acteurs afin qu'une animation de parole en boucle ne
subsiste pas.

Cette paire est la reconstruction la plus isolable, mais le point et le moment
du déclenchement restent inconnus.

### Dialogue 04 — AF3a_05 / AF3a_06

La conversation commerciale attend la valeur 31 et utilise 10/11 pour chaque
réplique. AF3a_05 et AF3a_06 ne traitent actuellement que leurs signaux de
patrouille et d'alerte 1, 2 et 20.

- les deux possèdent un label `ACTIVITY` ;
- seul AF3a_06 possède un label `ALERT` ;
- le synchroniseur officiel AF3a_05/06 produit déjà deux petits échanges via
  les signaux 1 et 2 lorsqu'ils sont proches et que le joueur est à 20 unités ;
- aucun acteur ne référence `dummy_rozhovor_04`, donc aucun abort scripté vers
  son signal 2 n'est conservé ;
- le dialogue commercial ne leur envoie pas le signal 12 à sa fin ; seule la
  variante CMP désactivée ajoute cette restitution en fin normale.

Une copie aveugle de l'include échouerait pour AF3a_05 à cause du label
`ALERT` manquant. Le sous-ensemble officiel 10/11/12 peut être adapté aux deux
acteurs, puis le dialogue peut envoyer 12 à sa fin et lors d'un abort. Cette
solution doit encore démontrer qu'elle ne concurrence ni le synchroniseur, ni
les patrouilles, ni une alarme.

Le premier prototype ne fait volontairement **aucune** de ces adaptations. Il
ne contient qu'un activator monostable inspiré de l'ébauche CMP, réintroduit la
garde 31 comme sécurité moderne et expose un signal 2 de laboratoire pour
transmettre l'abort officiel au dummy. Les signaux 10/11 restent sans effet :
cela suffit à tester voix, sous-titres, concurrence et interruption avant de
toucher aux scripts acteurs.

### Dialogue 05 — AF3a_02 / AF3a_03

AF3a_02 ne traite pas 10/11, mais possède un label `ACTIVITY` : un sous-ensemble
10/11/12 est techniquement adaptable. AF3a_03 est le cas bloquant :

- son `OnSignal(10)` officiel déclenche déjà une réaction tactique à AF3a_02,
  avec déplacement d'inspection ;
- il n'a pas de handler 11 ;
- il n'a ni label `ACTIVITY` ni label `ALERT` ;
- aucun acteur ne référence `dummy_rozhovor_05`, donc aucun abort scripté n'est
  conservé ;
- le dialogue ne rend pas les acteurs à leur activité par signal 12.

Le signal 10 envoyé par la conversation déclencherait donc la patrouille
tactique d'AF3a_03 au lieu d'une animation de parole. Ajouter un second
`OnSignal(10)` est invalide ou ambigu ; remplacer le handler existant casserait
une interaction active. Cette conversation ne possède pas encore de delta
minimal défendable.

Deux identifiants de voix présentent en outre un défaut indépendant : les
commentaires annoncent `07991601` et `07991604`, tandis que le code appelle
`079915601` et `079915604`. Leur correction appartient à la tâche principale :
elle est explicitement hors périmètre de ce lot et n'est ni corrigée ni
dupliquée ici.

## Reconstruction en deux parties

### Partie A — activators positionnels et temporels

Pour 03 et 05, un activator expérimental devrait reproduire le principe du
dialogue 02 sans en copier arbitrairement les constantes. Pour chaque
conversation, il faudrait relever en jeu :

1. la position du dummy et le passage naturel du joueur ;
2. la proximité simultanée des deux participants avec leur point de dialogue ;
3. leur état de patrouille, d'alarme, de mort et de script ;
4. la valeur 31 ou 32 avant l'émission ;
5. les autres conversations ou synchroniseurs susceptibles de parler en même
   temps.

Le signal 1 ne doit jamais être envoyé avant que la garde interne soit vraie :
les trois scripts exécutent `EndScript()` si leur valeur est nulle, ce qui peut
condamner définitivement une conversation déclenchée trop tôt.

Pour 04 seulement, CMP fournit le candidat de test `_PlayerInRange(10)`. Le
prototype [`PROTOTYPE_CMP_MODERNE_CONVERSATION04_ACTIVATOR.scr.disabled`](PROTOTYPE_CMP_MODERNE_CONVERSATION04_ACTIVATOR.scr.disabled)
conserve ce rayon comme **hypothèse CMP**, ajoute la garde 31 et désarme son
Whenever avant d'envoyer le signal 1. Il n'est référencé par aucun registre.

Les dialogues 04 et 05 partagent la valeur 31 sans mutex propre. Leur activator
doit donc aussi empêcher deux conversations simultanées utilisant les
sous-titres globaux. Le rayon 70 et la distance 5 du modèle officiel sont des
valeurs de départ à tester, pas des constantes historiques prouvées pour ces
trois dummies.

### Partie B — protocole participant adapté par paire

- **Dialogue 04, phase 0 :** tester d'abord le seul activator CMP/MODERNE
  désactivé, sans modifier 05/06 ni la conversation commerciale.
- **Dialogue 04, phase ultérieure :** seulement après validation de la phase 0,
  envisager 10/11/12 chez 05/06, puis vérifier la reprise exacte des activités,
  le synchroniseur et les alarmes. Le retour 12 de CMP est un précédent moderne,
  pas une restitution commerciale prouvée.
- **Dialogue 03 :** conserver comme piste secondaire le sous-ensemble 10/11
  chez 28/29, avec nettoyage 11 sur abort ; ne pas ajouter 12/13 ni inventer de
  labels tant que l'activator reste inconnu.
- **Dialogue 05 :** suspendre la reconstruction animée jusqu'à attribution d'un
  protocole distinct pour AF3a_03 et d'une route de reprise correcte. Une
  version sans animation pour AF3a_03 serait une dégradation testable, pas une
  restauration fidèle.

Le signal 13 ne doit être ajouté qu'aux acteurs disposant réellement d'un label
`ALERT` et seulement si un émetteur en a besoin. Aucun des trois dialogues ne
l'émet actuellement.

## Protocole de test

1. Baseline : confirmer qu'aucun des dummies 03–05 ne reçoit le signal 1 au
   cours d'une partie normale ; ne pas activer 03 ni 05 dans ce lot.
2. Pour 04, journaliser valeur 31, distance joueur, état de 05/06 et signaux
   1/2/10/11/12 ; confirmer une émission unique à dix mètres.
3. Essayer valeur 31 nulle, éloignement puis retour, mort préalable d'un acteur
   et synchroniseur déjà en cours. Aucun départ prématuré ou double ne doit se
   produire.
4. Provoquer une alarme pendant plusieurs locuteurs. En phase 0, l'absence de
   raccord automatique vers le signal 2 est une lacune attendue à mesurer : si
   les voix ou sous-titres continuent, le prototype échoue son critère
   d'intégration et ne doit pas être activé.
5. Injecter séparément le signal 2 dans l'activator de laboratoire pour vérifier
   uniquement que l'abort commercial coupe voix et sous-titres. Ce test manuel
   ne prouve pas qu'une alarme réelle possède son émetteur.
6. Vérifier les deux échanges courts du synchroniseur avant, pendant et après
   la longue conversation ; aucune superposition de voix n'est acceptable.
7. Répéter après sauvegarde/reprise avant activation, pendant une réplique et
   après la fin. Les identifiants erronés de 05 restent hors de ce lot.

Acceptation : une conversation ne part qu'une fois, jamais pendant l'alarme ou
une autre conversation ; chaque acteur reprend exactement son état préalable ;
aucune route tactique, voix ou animation ne reste bloquée.

## Verdict

Les trois conversations sont du contenu officiel dormant, mais elles ne sont
pas trois restaurations équivalentes. CMP justifie de prototyper **04 en
premier**, seulement comme expérience désactivée CMP/MODERNE ; son activator
n'est ni actif ni lié et son interruption par alarme reste non résolue. Le 03
demeure une piste moins précise faute d'activator ; le 05 reste bloqué par la
collision active du signal 10 chez AF3a_03. Aucun raccord ne doit être intégré
au stable sans validation dynamique complète.

## Sources internes

- registre officiel d'Africa 3 pour `dummy_rozhovor_03/04/05`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_rozhovor_02_activator.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_rozhovor_02.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_rozhovor_03.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_rozhovor_04.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_rozhovor_05.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/_inc_rozhovor.scr`
- scripts participants `AF3a_02`, `03`, `05`, `06`, `28` et `29`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_0506synchronize.scr`
- CMP 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f` :
  `Scripts/co_africa3/AF3a_rozhovor_04_activator.scr`,
  `AF3a_rozhovor_04.scr`, scripts 05/06 et
  `Missions/co_africa3/mpscripts.dta`
