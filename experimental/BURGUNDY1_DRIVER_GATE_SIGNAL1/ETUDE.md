# Étude expérimentale — signal 1 de la barrière vers `bu1_driver01`

État : vestige probable d'une synchronisation remplacée, 14 septembre 2026.
Aucun prototype, script actif, binding ou installateur n'est modifié ; aucune
compilation n'est effectuée.

## Verdict

Dans Burgundy1 et Co_Burgundy1, `bur1_04.scr` ouvre la barrière puis envoie le
signal 1 à l'acteur `bu1_driver01`. Le script lié `bur1_driver01.scr` ne possède
aucun handler de signal. Son réveil initial vient d'un Whenever joueur à 200 m
en solo et 160 m en coop.

Le signal est bien placé comme une ancienne impulsion de synchronisation, mais
la progression conservée utilise désormais la valeur de jeu 61 pour libérer la
seconde moitié du trajet. Ajouter `OnSignal(1) { goto PATH02; }` doublerait ou
court-circuiterait ce mécanisme. Classement : **ancienne commande probablement
supplantée, aucun correctif actuel**.

| Aspect | Preuve | Motif |
| --- | ---: | --- |
| émission après ouverture de la barrière | 4/4 | identique en solo et coop |
| ancienne intention de synchroniser le camion | 3/4 | retour direct garde → conducteur |
| corps historique du handler | 0/4 | aucune variante ne le conserve |
| nécessité d'un handler dans le flux actuel | 1/4 | `SaveGameValue(61)` conduit déjà à `PATH02` |

## Ordre réel des deux phases

Le Whenever de proximité ne correspond pas au signal de la barrière. Il lance
la **première** phase :

1. entrée joueur à 200 m (solo) ou 160 m (coop) ;
2. `ACTIVATE`, puis chute directe dans `PATH01` ;
3. réveil, embarquement dans `La_OpelE_02` et conduite jusqu'à `path01_04` ;
4. envoi du signal 1 à `bu1_04` ;
5. retour du conducteur au label `END`, camion arrêté à la fin de la phase.

Le garde exécute alors :

1. marche vers `03_01` et orientation vers la barrière ;
2. signal 1 à `la_zavora_.zavora`, qui ouvre la barrière et joint `j1/j2` ;
3. signal 1 orphelin au conducteur ;
4. attente de 20 secondes ;
5. écriture de la valeur 61.

La proximité a donc déjà servi longtemps avant le signal orphelin. Le recopier
vers `ACTIVATE` ou `PATH01` ferait rembarquer un conducteur déjà dans son camion
et répéterait les quatre premiers checkpoints.

## Progression persistante qui remplace le signal

### Solo

`bur1_04` écrit 61=1 après les 20 secondes. Le contrôleur
`bur1_rozhovor_ubrany.scr` détecte cette valeur, joue les six répliques entre le
conducteur et le garde, puis écrit 61=2. Le Whenever `endr` du conducteur reçoit
alors cet état et rejoint `PATH02`.

Un handler 1 allant directement à `PATH02` ferait partir le camion dès
l'ouverture, avant le délai et avant la conversation. Il pourrait aussi laisser
les voix jouer à distance ou pendant le trajet.

### Coop

`bur1_04` écrit directement 61=2 après les 20 secondes. Le dialogue conserve
encore son attente de 61=1, mais celle-ci est contournée. Le conducteur rejoint
donc `PATH02` après le délai sans avoir besoin du signal 1.

Cette différence est cohérente avec une suppression du dialogue en coop et non
avec un handler manquant commun aux deux versions.

## Interprétation historique

Le modèle le plus vraisemblable est une migration d'un déclenchement fugace vers
un état sauvegardable : une ancienne version faisait peut-être reprendre le
camion par signal après l'ouverture, puis les auteurs ont introduit la valeur 61
pour attendre le dialogue solo et fournir un délai direct en coop. L'émission
est restée dans `bur1_04`, tandis que la réception a disparu.

La valeur persistante explique mieux la sauvegarde/reprise qu'un signal : une
impulsion reçue juste avant une sauvegarde ne peut pas nécessairement être
rejouée, alors que 61=1/2 permet aux deux Whenevers de retrouver la phase.

Il manque toutefois une ancienne copie du conducteur, un commentaire du signal
et un registre de version montrant la migration. L'interprétation reste donc une
inférence, pas une restauration attestée.

## Risques d'une démonstration `OnSignal(1)`

- `goto PATH01` : double embarquement, répétition du trajet et nouvel envoi au
  garde ;
- `goto PATH02` : départ anticipé, dialogue solo court-circuité et délai coop
  supprimé ;
- simple `HUMAN_Suspend(false)` : no-op après `PATH01`, sans bénéfice mesurable ;
- signaux répétés : nouvelle entrée de trajet alors que `endr` peut se déclencher
  simultanément sur 61=2 ;
- reprise de sauvegarde : collision entre instruction restaurée, signal non
  persistant et Whenever fondé sur la valeur 61.

**Aucune démonstration isolée n'est créée à ce stade.** Elle n'apporterait rien
que la lecture statique ne montre déjà et introduirait précisément les courses
à éviter.

## Protocole d'observation

1. Tracer les distances au conducteur et confirmer l'unique déclenchement à
   200/160 m.
2. Relever l'ordre de `path01_01` à `_04`, du signal vers le garde, de
   l'ouverture et du signal retour 1.
3. Confirmer que le conducteur reste à `_04` pendant les 20 secondes.
4. En solo, vérifier la séquence 61=0 → 1 → dialogue → 2 → `PATH02`.
5. En coop, vérifier 61=0 → 2 après 20 secondes → `PATH02`, sans dialogue.
6. Sauvegarder/reprendre avant la proximité, sur `_04`, pendant le délai,
   pendant le dialogue solo et juste après 61=2.
7. Provoquer alarme ou mort du conducteur à chaque phase et vérifier que le
   Whenever `endr` ne rembarque pas un acteur invalide.
8. Tracer séparément l'état de la barrière : le garde lui envoie 0 après le
   délai, alors que `zavora.scr` ne déclare que 1 et 2. Cette anomalie adjacente
   ne doit pas être confondue avec le signal du conducteur.

Critère de réouverture : si, sans modification, 61 atteint bien 2 mais le camion
ne rejoint pas `PATH02` dans une nouvelle partie ou après reprise, diagnostiquer
d'abord le Whenever `endr` et la restauration de valeur. Un handler 1 ne devient
recevable que si une source ancienne en fournit le corps et son interaction avec
61.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_04.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_driver01.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/bur1_rozhovor_ubrany.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy1/zavora.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_04.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_driver01.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/bur1_rozhovor_ubrany.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy1/zavora.scr`
- `.analysis/signal-graph-current.json` et `.md`
