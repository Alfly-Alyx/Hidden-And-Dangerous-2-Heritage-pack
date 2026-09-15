# Étude expérimentale — détecteurs de retour de Normandy 2

État : analyse statique, 14 septembre 2026. Aucun delta de script n'est
proposé. Cette étude n'altère ni les scripts actifs, ni les archives du jeu.

Cette étude suit le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
la progression `R_N2_Waves` reste la branche release ; les détecteurs de retour
ne pourraient former qu'une branche optionnelle dotée d'un arbitre empêchant
les réveils doubles. Aucun arbitre attesté n'est encore disponible.

## Reclassement

**Architecture ancienne probablement remplacée ; aucune réactivation
minimale démontrée.** Les détecteurs 9 à 11 forment encore un découpage spatial
cohérent des groupes Blue, mais deux de leurs trois protocoles de sortie sont
incompatibles avec les récepteurs conservés. Surtout, `R_N2_Waves.scr` possède
déjà sa propre progression sur exactement les mêmes groupes actifs.

Le défaut ne peut donc pas être réduit à un lien de registre manquant. Toute
reconstruction devrait à la fois réparer le protocole des signaux 9 et 11 et
expliquer comment la branche de retour coexiste avec le contrôleur de vagues
sans réveil double.

| Élément | Destinataires actifs | Signal émis | Compatibilité Blue |
| --- | --- | ---: | --- |
| `R_N2_Detector_9` | Blue 1 à 6 | 9 | aucune réception correspondante |
| `R_N2_Detector_10` | Blue 7 à 11 et 13 | 10 | compatible avec le réveil conservé |
| `R_N2_Detector_11` | Blue 14, 15 et 17 | 11 | aucune réception correspondante |

Blue 12 et Blue 16 sont commentés à la fois dans les détecteurs concernés et
dans `R_N2_Waves.scr`. L'ensemble actif des trois détecteurs est ainsi le même
ensemble de quinze groupes que celui parcouru par le contrôleur de vagues.

## Preuves officielles

### Les trois détecteurs

Chaque détecteur commence désactivé et possède :

- une zone joueur (`_PlayerInRange`) qui diffuse son signal aux groupes Blue de
  son secteur ;
- un `OnSignal(10)`, commenté comme venant de l'objectif pour la route de
  retour, qui active cette zone.

Le découpage paraît volontaire : Detector 9 couvre les groupes 1–6, Detector
10 les groupes 7–11 et 13, puis Detector 11 les groupes 14, 15 et 17. En
revanche, les numéros émis sont respectivement 9, 10 et 11. Seul le secteur
central utilise le protocole réellement compris par les Blue.

`R_N2_OBJECTIVES.scr` recherche bien les frames `Detector_9`, `Detector_10` et
`Detector_11`. Toutefois, aucun `SendSignal` vers ces trois références n'est
présent dans ce script, et la recherche dans les scripts Normandy 2 ne révèle
aucun autre émetteur scripté qui les arme. Les commentaires des détecteurs
attestent donc une ancienne intention de route retour, pas une chaîne complète
dans le corpus conservé. Un déclencheur placé dans la mission reste possible et
devrait être contrôlé dynamiquement ; il n'est pas prouvé par les scripts.

### Contrat des dix-sept groupes Blue

Les dix-sept scripts `R_N2_Blue_*.scr` exposent la même matrice de signaux :

- le signal 10 est l'entrée de réveil ;
- les signaux 1 à 5 gèrent les réactions aux groupes alliés ;
- aucun ne traite le signal 9 ou le signal 11.

Les émissions de Detector 9 et Detector 11 sont donc sans récepteur dans le
code conservé. Il n'existe pas non plus de variante officielle contenant les
deux gestionnaires manquants.

### Contrôleur de vagues concurrent

`R_N2_Waves.scr` contient une séquence explicitement consacrée au réveil
progressif de la vague Blue. Elle active successivement ses Whenevers puis
envoie le signal 10 aux groupes Blue 1 à 11, 13 à 15 et 17 ; Blue 12 et Blue 16
y restent commentés.

Ce contrôleur recouvre donc exactement les quinze destinataires actifs des
trois détecteurs. Il fournit déjà un propriétaire fonctionnel du réveil, avec
son propre ordre et ses propres temporisations. Réactiver en parallèle les
détecteurs introduirait une seconde autorité sur le même état.

## Ce que les traces permettent — et ne permettent pas — de conclure

L'hypothèse la plus cohérente est que les trois détecteurs appartiennent à une
ancienne architecture de retour, ensuite remplacée ou supplantée par
`R_N2_Waves.scr`. Le signal correct conservé dans Detector 10 peut être un
reste partiellement migré ; il ne suffit pas à prouver que les deux autres
numéros sont de simples fautes de frappe.

Deux reconstructions techniques sont évidentes mais non historiques :

1. remplacer les émissions 9 et 11 par le signal 10 ;
2. ajouter aux groupes Blue des alias `OnSignal(9)` et `OnSignal(11)` vers leur
   réveil.

La première modifie le contrat des émetteurs ; la seconde modifie jusqu'à
dix-sept récepteurs et invente un protocole absent. Aucune ne règle le
chevauchement avec `R_N2_Waves.scr`. Même Detector 10, pourtant compatible, ne
doit pas être réactivé isolément : cela créerait une branche partielle et
asymétrique de l'ancienne logique.

## Conditions avant toute reconstruction

Une proposition exécutable ne devient recevable qu'après avoir établi les
quatre points suivants :

1. **Route distincte.** Prouver en jeu que les trois zones correspondent à un
   passage de retour réellement emprunté et identifier ce qui doit armer leurs
   `OnSignal(10)`.
2. **Ordonnancement.** Relever si `R_N2_Waves` a déjà réveillé chaque groupe au
   moment où le joueur traverse cette route.
3. **Propriété exclusive ou idempotence.** Choisir soit un contrôleur unique,
   soit une garde d'état démontrée qui rend une seconde émission inoffensive.
4. **Portée exacte.** Expliquer le maintien hors circuit de Blue 12 et Blue 16,
   ainsi que les effets en sauvegarde/reprise et dans les modes spéciaux qui
   réveillent aussi Blue 10.

Sans ces preuves, corriger seulement 9/11 en 10 peut accélérer ou dupliquer des
engagements, tandis que neutraliser `R_N2_Waves` modifierait toute la cadence de
combat de la mission.

## Protocole d'observation sans modification

1. Instrumenter les signaux reçus par Detector 9, 10 et 11 et par les quinze
   groupes Blue actifs.
2. Jouer la progression normale, puis la route de retour supposée, en notant
   l'ordre des réveils produits par `R_N2_Waves`.
3. Vérifier si un mécanisme de mission non visible dans les scripts arme les
   détecteurs.
4. Traverser séparément les trois zones avant et après le réveil de leurs
   groupes, sans changer les numéros de signal.
5. Répéter autour d'une sauvegarde/reprise et dans les modes où Blue 10 reçoit
   un réveil supplémentaire.

Le test doit d'abord démontrer une lacune perceptible propre à la route de
retour. L'incompatibilité statique des signaux 9 et 11 ne suffit pas, à elle
seule, à autoriser une correction.

## Décision

**Aucun delta expérimental à ce stade.** Ne pas corriger 9/11 en 10, ne pas
ajouter de gestionnaires 9/11 aux Blue, ne pas activer seulement Detector 10 et
ne pas désactiver le contrôleur de vagues. Une future proposition devra prouver
la route retour distincte et documenter explicitement la prévention des
doubles réveils.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Detector_9.scr`
- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Detector_10.scr`
- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Detector_11.scr`
- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Waves.scr`
- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_OBJECTIVES.scr`
- `.analysis/scripts/base/SCRIPTS/NORMANDY2/R_N2_Blue_1.scr` à
  `R_N2_Blue_17.scr`
