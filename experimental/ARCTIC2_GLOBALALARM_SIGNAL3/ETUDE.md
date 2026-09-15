# Étude expérimentale — signal 3 du contrôleur d'alarme Arctic 2

État : intention attestée, comportement manquant. Étude statique du
14 septembre 2026. Aucun script commercial, binding ou fichier de mission
n'est modifié par cette fiche.

## Règle de preuve

- **OFFICIEL** : contenu présent dans une archive commerciale auditée.
- **INFÉRENCE** : interprétation compatible avec les scripts, mais non prouvée.
- **CRÉATION MODERNE** : comportement qu'il faudrait inventer pour rendre le
  signal observable.

## Verdict

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Intention d'envoyer un décès | 4/4 | les sept patrouilleurs émettent le même signal dans `OnDeath` |
| Conservation du récepteur | 0/4 | aucun `OnSignal(3)` dans le contrôleur |
| Faisabilité technique d'un handler | 4/4 | ajout syntaxiquement réduit |
| Fidélité d'une réaction proposée | 0/4 | ni seuil, ni effet, ni état associé ne sont conservés |

**Décision : ne proposer aucun delta.** La répétition prouve que les décès
devaient être notifiés à `dummy_GlobalAlarm`; elle ne prouve pas ce que ce
dernier devait faire. Le cas est classé **« intention attestée, comportement
manquant »**.

## Chaîne officielle conservée

Les sept scripts `R_Arc1B_W1.scr` à `R_Arc1B_W7.scr` résolvent tous la frame
`alarm` vers `dummy_GlobalAlarm`. Chacun possède exactement un `OnDeath()` et
exactement un :

```text
SendSignal(alarm, 3);
```

Ce résultat vaut pour W1, W2, W3, W4, W5, W6 et W7. L'ordre, les rondes et les
réactions d'alarme diffèrent entre patrouilleurs, mais leur contrat de décès est
uniforme.

`R_Arc1B_GlobalAlarm.scr` ne conserve que deux entrées :

- le signal 1 réveille les sept groupes de renforts, informe `dummy_diary` et,
  si l'alarme est éteinte, s'envoie le signal 2 ;
- le signal 2 bascule l'état `aktual`, les sirènes et les feux. À l'allumage il
  écrit la valeur de jeu 5 à 666 puis déclenche le signal 1 ; à l'extinction il
  écrit 99 et remet `aktual` à 0.

Le contrôleur ne déclare qu'un entier, `aktual`. Il n'a ni compteur de morts,
ni tableau d'états W1–W7, ni `OnSignal(3)`, ni commentaire décrivant ce signal.

Les canaux 1 et 2 ont déjà des producteurs sémantiquement précis chez les W :
pendant `OnAlarm`, plusieurs gardes peuvent rejoindre un bouton puis envoyer 2 ;
dans `OnAlarmDone`, les sept envoient 1 pour propager l'alarme lorsque le type
d'événement le justifie. Le signal 3 réservé à `OnDeath` est donc un troisième
événement distinct. L'aliaser vers 1 ou 2 fusionnerait des causes que les scripts
commerciaux ont volontairement numérotées séparément.

## Archives, variantes et scripts voisins

**OFFICIEL.** Une seule copie commerciale des huit scripts concernés a été
retrouvée, dans la couche Base d'Arctic 2. La couche Patch ne contient pas de
dossier Arctic 2 et les scripts Sabre audités ne fournissent pas de variante de
cette mission. Les contrôleurs d'alarme globale de Burgundy 1 et Sicily 1
pilotent leurs propres valeurs, sirènes et renforts, sans protocole de décès
équivalent au triplet 1/2/3 d'Arctic 2.

Le CMP public 2.6.5 contient une conversion `co_arctic2`, mais elle ne restaure
pas le récepteur : son `r_arc1b_globalalarm.scr` ne gère encore que 1 et 2.
Elle supprime l'envoi 3 du `OnDeath` de W1 à W6 et le conserve seulement chez
W7, toujours sans effet. Ce nettoyage partiel montre comment la conversion
traite le vestige ; il ne révèle ni seuil ni conséquence d'origine.

**OFFICIEL.** Les scripts de compteurs trouvés ailleurs montrent plusieurs
techniques incompatibles entre elles : incrément par signal jusqu'à un seuil,
lecture périodique de l'état d'acteurs, ou drapeaux individuels empêchant le
double comptage. Leurs seuils et leurs effets sont propres à leurs missions.
Ils prouvent que le moteur permet un compteur, pas qu'Arctic 2 en utilisait un.

**OFFICIEL.** L'objectif optionnel de discrétion lit la valeur de jeu 5 au
retour en surface. Cette valeur est initialisée à 0, passe à 666 lorsque
l'alarme globale s'allume et à 99 lorsqu'elle a déjà sonné puis est coupée. Le
signal 3 n'apparaît pas dans cette logique d'objectif. `dummy_diary` ne reçoit
que le signal 1 et choisit entre les textes « silence » et « aggressive ».

## Pourquoi les raccords évidents sont rejetés

### Transformer le signal 3 en signal 1

**CRÉATION MODERNE.** Cela déclencherait dès le premier décès tous les renforts,
le journal et, si nécessaire, l'alarme sonore. Aucun script ne relie le premier
patrouilleur mort à cette réaction. Cette solution transformerait une
notification inconnue en alarme générale certaine.

### Transformer le signal 3 en signal 2

**CRÉATION MODERNE, incohérente.** Le signal 2 est un interrupteur : chaque
décès pourrait alternativement allumer puis éteindre les sirènes. L'effet
dépendrait donc de la parité et de l'ordre des morts, sans compteur ni garde.

### Compter jusqu'à sept puis déclencher l'alarme

**INFÉRENCE faible.** Sept émetteurs rendent un compteur plausible, mais le
seuil n'est pas démontré. La réaction pourrait survenir au premier décès, après
plusieurs décès, à la disparition de tous les patrouilleurs, ou ne servir qu'à
un objectif ou à un diagnostic. Même au seuil sept, aucun effet aval n'est
attesté : signal 1, signal 2, journal, objectif ou autre frame.

### Incrémenter silencieusement un compteur

**CRÉATION MODERNE sans bénéfice démontré.** Ajouter un état qui n'est jamais
lu ne restitue aucun comportement. Ajouter ensuite un lecteur ou une condition
serait une seconde invention.

## Porte de réouverture

Une reconstruction ne devient recevable que si au moins une source apporte à
la fois le déclencheur et l'effet, par exemple :

- une autre version de `R_Arc1B_GlobalAlarm.scr` contenant `OnSignal(3)` ;
- un commentaire ou document de mission donnant le seuil et la conséquence ;
- un contrôleur frère avec les mêmes W1–W7, la même variable `aktual` et le
  même protocole 1/2/3 ;
- une référence d'objectif, de journal ou de valeur de jeu qui consomme
  explicitement le nombre de morts de ces sept patrouilleurs.

Un simple compteur générique d'une autre mission ne suffit pas.

## Protocole de constat dynamique ultérieur

Sans reconstruction, instrumenter une copie laboratoire et consigner, pour les
sept patrouilleurs tués dans plusieurs ordres :

1. l'émission unique du signal 3 à chaque décès ;
2. l'état `aktual`, la valeur de jeu 5, les sirènes et les feux ;
3. les signaux 1 reçus par les renforts et `dummy_diary` ;
4. l'état de l'objectif optionnel de discrétion ;
5. le comportement avant et après une alarme déjà active ou déjà coupée ;
6. une sauvegarde/reprise entre deux décès.

Le but de ce test est de confirmer l'absence de réaction scriptée et de détecter
une éventuelle sémantique moteur non visible dans les sources, pas de choisir un
seuil qui « semble bien fonctionner ».

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC2/R_Arc1B_GlobalAlarm.scr`
- `.analysis/scripts/base/SCRIPTS/ARCTIC2/R_Arc1B_W1.scr` à
  `R_Arc1B_W7.scr`
- `.analysis/scripts/base/SCRIPTS/ARCTIC2/R_Arc1B_objective3.scr`
- `.analysis/scripts/base/SCRIPTS/ARCTIC2/R_Arc1B_Diary.scr`
- contrôleurs d'alarme globale de Burgundy 1 et Sicily 1 dans la couche Sabre
- compteurs de morts et d'acteurs des couches Base, Patch et Sabre, consultés
  uniquement comme contre-exemples de seuils propres à chaque mission
- CMP public 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`,
  `Scripts/co_arctic2/`
