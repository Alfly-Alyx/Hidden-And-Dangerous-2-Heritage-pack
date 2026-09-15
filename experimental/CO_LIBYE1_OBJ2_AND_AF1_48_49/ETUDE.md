# Étude expérimentale — ancien objectif 2 et dialogue AF1_48/49 de Co_Libye1

État : ancien objectif commercialement remplacé mais variante additive
définissable ; dialogue bloqué faute de synchronisation exacte, 14 septembre
2026. Aucun delta ni prototype n'est recommandé pour le paquet stable.

Cette étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
le remplacement commercial interdit l'écrasement de la release, mais pas une
branche distincte dont les identifiants et la progression sont isolés.

## Synthèse

| Vestige | Intention | Effet conservé | Verdict |
| --- | ---: | ---: | --- |
| `AF1_obj2_succ_sender` | 4/4 | condition et handler d'objectif conservés ; handlers de texte absents | objectif 2 remplacé ; coexistence possible seulement comme variante additive 7 |
| dialogue AF1_48/49 | 3/4 | douze voix et appels solo conservés ; second signal de départ et deux fins absents | aucun prototype avant synchronisation exacte |

## Ancienne validation de l'objectif 2

### Déclencheur officiel mais neutralisé

`AF1_obj2_succ_sender.scr` conserve une condition complète : NPC1 et NPC2
doivent chacun se trouver à moins de cinq unités du porteur du script, puis le
signal 3 est envoyé à la frame `objectives`.

Le fichier s'annule toutefois avant cette condition :

```text
// zruseno (pozastaveno)
SetWhenever(OBJw, false);
Endscript();
```

Le commentaire signifie « annulé/suspendu ». Cette neutralisation est
explicite et précède le Whenever ; ce n'est pas un simple oubli de binding.

### Récepteur historique encore lisible

Le contrôleur coopératif `AF1_objectives.scr` ne possède plus de handler 3
actif, mais conserve son ancien corps intégralement commenté :

```text
// OnSignal(3)  // posila to AF1_obj2_succ_sender
// {
//   SetObjectiveStatus(2, 1);
//   printf("OBJ - chranit ty dva - SPLNEN");
//   SendSignal(texty, 4);
//   GoTo end;
// }
```

Les commentaires de `AF1_texty.scr` associent l'identifiant 52999710 à la
réussite « les prisonniers libérés sont arrivés sains et saufs dans la zone de
sécurité ». Aucun `OnSignal(4)` actif ne l'affiche toutefois encore. Le résultat
historique du signal 3 est donc documenté — réussite de l'ancien objectif
d'escorte et message associé — mais la chaîne de texte doit elle aussi être
restaurée.

### Confirmation par le solo

Les contrôleurs solo `AF1_objective.scr` et `AF1_objective2.scr` possèdent un
`OnSignal(3)` actif, reçu respectivement de SAS1 ou de l'unité LRDG. Ils
valident l'objectif 2 après la remise des prisonniers, informent le journal et
affichent le texte de réussite. Leurs effets supplémentaires concernant les
membres d'équipe et le journal sont propres au solo ; ils confirment la
sémantique de remise en sécurité, pas un corps à copier en coopération.

## Pourquoi la branche ne doit pas être réactivée

Dans la version coopérative, l'objectif 2 a été explicitement remplacé :

```text
SetObjectiveStatus(2, 0); // oba musi prezit ZRUSEN ... NAHRAZEN sejmi vsechny dustojniky
```

Le commentaire indique que la règle « les deux doivent survivre » est annulée
et remplacée par « éliminer tous les officiers ». Le Whenever actif
`OficersDeath` attend la mort de AF1_20, AF1_49 et AF1_55, puis valide le même
objectif 2 et envoie le texte 3, correspondant à l'élimination des officiers.

Réactiver seulement le sender et le handler 3 permettrait donc aux prisonniers
d'arriver à la zone de sécurité et de valider prématurément un objectif qui
demande désormais autre chose. Les deux voies pourraient aussi envoyer deux
messages de réussite incompatibles pour le même numéro d'objectif.

**Interdiction de raccord : ne jamais réactiver le signal 3 sur l'objectif 2
coopératif actuel.** Son numéro désigne désormais l'élimination des officiers
et possède déjà sa condition de succès active.

Une véritable variante historique demanderait un basculement cohérent de tout
le contrat :

1. remplacer la description courante de l'objectif 2 ;
2. réactiver son activation après la libération des deux prisonniers ;
3. retirer ou réaffecter la condition de mort des trois officiers ;
4. réactiver le sender de zone ;
5. restaurer le handler 3 commenté et son texte 4 ;
6. vérifier l'échec si un prisonnier meurt en route.

Ce remplacement complet de l'objectif 2 est écarté. **Verdict commercial :
l'ancien objectif a bien été remplacé**, et les signaux neutralisés ne doivent
pas être qualifiés de simple oubli. Une variante additive, décrite ci-dessous,
peut conserver tous les objectifs coop courants, mais son armement et son chemin
d'échec sont des raccords modernes explicitement étiquetés.

## Variante additive proposée : objectif 7

### Deux branches conservées

| Branche | Condition de choix | Autorité de succès |
| --- | --- | --- |
| release | toujours active | objectif 2, mort des trois officiers |
| additive | option expérimentale déclarant l'objectif 7, puis libération des deux prisonniers | objectif 7, arrivée conjointe dans la zone sûre |

La désactivation de l'option additive doit restituer exactement les six
objectifs coop actuels. Lorsque l'option est active, les succès 2 et 7 restent
indépendants : aucun signal, texte ou état sauvegardé ne peut valider les deux.
Les tests doivent couvrir les deux ordres de résolution et leur quasi-
simultanéité afin de détecter toute double validation ou fin prématurée.

### Numéro et texte disponibles

Co_Libye1 occupe déjà les objectifs 1 à 6. Sa déclaration de carte utilise,
dans cet ordre, `15510`, `15518`, `15514`, `15515`, `15519` et `15509`, en
accord avec les six conditions actives du script : libérer les prisonniers,
tuer les officiers, détruire la radio, détruire les véhicules, photographier
les plans et éliminer le sniper.

La mission solo déclare `15510`, `15511`, `15512`, `15514`, `15515`, `15516`
et `15513`. Son contrôleur montre que son objectif 2 est précisément la remise
des prisonniers à l'unité alliée. `15511` est donc le libellé historique à
réutiliser ; ni `15518` ni l'objectif 2 coop ne doivent être détournés.

La déclaration expérimentale ajoute en septième position :

```xml
<OBJECTIVE allied_text="15511" axis_text="15511" value="03"/>
```

`AF1_texty.scr` coop conserve aussi les trois messages nécessaires dans ses
commentaires :

- `52999702` : nouvel objectif, protéger les prisonniers jusqu'à la zone sûre ;
- `52999706` : échec, les prisonniers ont été tués en chemin ;
- `52999710` : réussite, les prisonniers ont atteint la zone sûre.

Le dernier est mentionné par l'ancien `SendSignal(texty, 4)`, mais le handler 4
n'existe plus dans `AF1_texty.scr`. La chaîne historique n'est donc pas
entièrement exécutable sans restaurer également les récepteurs de texte.

Ces identifiants constituent une piste textuelle, pas encore une garantie que
toutes les langues coop les exposent correctement. À défaut de preuve dans les
ressources de chaque langue ciblée, une variante devra employer un nouveau
texte explicitement **MODERNE**, plutôt que réattribuer silencieusement un
libellé incertain.

### Contrat expérimental cohérent

La variante proposée ne touche pas au succès courant de l'objectif 2 et suit
ce cycle :

1. Ajouter l'objectif 7 au bloc de carte, sans l'activer au chargement.
2. Garder le test `OBJw` de `AF1_obj2_succ_sender` désactivé au départ, mais ne
   plus terminer le script pendant son initialisation.
3. Ajouter au sender un signal d'armement. Quand les deux prisonniers ont été
   libérés, le handler 1 de `AF1_objectives` active l'objectif 7, arme le sender
   et demande l'affichage de `52999702`.
4. Quand NPC1 et NPC2 sont tous deux à moins de cinq unités de la zone, le
   sender se désarme avant d'envoyer une seule fois le signal 3 à `objectives`.
5. Le handler 3 marque **l'objectif 7** accompli et déclenche `52999710`. Il ne
   modifie jamais l'objectif 2.
6. Le test de mort utilise `pom1obj`, déjà positionné après la libération :
   avant celle-ci, il garde l'échec actuel de l'objectif 1 ; après celle-ci, il
   marque l'objectif 7 en échec et affiche `52999706`, sans réécrire l'objectif
   1 déjà réussi.

Les signaux 13 et 14 de la frame `texty` ne sont employés nulle part dans les
scripts Co_Libye1 examinés. Ils peuvent servir, uniquement dans le prototype,
à afficher respectivement `52999702` et `52999706`; le signal 4 historique
reste réservé au succès `52999710`.

Le sender doit être explicitement monostable. Son ancien `goto TheEnd` ne
désactive pas à lui seul le Whenever : enlever seulement l'`EndScript()` de
l'initialisation risquerait donc d'émettre plusieurs succès tant que les deux
NPC restent dans la zone.

### Risques propres au nouvel objectif

- l'objectif 7 devient obligatoire s'il reprend la même valeur `03`; la fin de
  mission doit attendre sa résolution ;
- l'armement doit être répliqué pour tous les clients et survivre à une
  sauvegarde/reprise ;
- la mort simultanée d'un prisonnier et son entrée dans la zone crée une course
  succès/échec qui doit avoir une priorité explicite, idéalement l'échec ;
- le seuil de cinq unités est historique mais doit être validé avec la forme
  réelle de la zone et les collisions coop ;
- `pom1obj` devient fonctionnel : son état doit être sauvegardé correctement
  ou reconstruit après chargement.

## Conversation AF1_48 / AF1_49

### État solo

La version solo contient douze répliques actives, 52990033 à 52990044. Après la
dernière, le coordinateur envoie le signal 2 aux deux interlocuteurs. Ni
`AF1_48.scr` ni `AF1_49.scr` ne possède de récepteur 2.

Le démarrage solo est incomplet : le coordinateur attend deux signaux 1, mais
seul AF1_49 en envoie un explicitement. `AF1_48_A1.scr` adresse une seule fois
les deux acteurs ; comme les autres scripts réarment explicitement leurs
`Whenever` lorsqu'ils veulent retenter, aucune répétition automatique ne peut
être retenue comme second signal fiable. Le label `start` reste donc
inatteignable par la chaîne explicitement conservée.

Les états officiels avant et pendant le dialogue sont différents :

- AF1_48 est réveillé puis passe à l'activité `%%oprenejOzedL`, adossé au mur ;
- AF1_49 est assis sur `AF1_49_sit` avec `%%plzen`, puis lance le coordinateur ;
- leurs `OnAlarm()` arrêtent les animations, interrompent le coordinateur et
  terminent les scripts.

Le coordinateur utilise du morphing de parole, sans commande conservée qui
montre une nouvelle animation corporelle à la fin. Le signal 2 pouvait restaurer
les poses initiales, lancer de nouveaux gestes, suspendre les acteurs ou être
un ancien raccord devenu redondant.

### État coopératif

La version coop conserve les identifiants et la structure, mais toutes les
répliques sont commentées. Les deux signaux 2 finaux restent exécutables. Les
scripts acteurs sont eux-mêmes réduits : le label `activity` d'AF1_48 est vide,
et AF1_49 utilise `%%buchadostolu` avant d'appeler le coordinateur puis possède
également un label `activity` vide.

Les ressources anglaises inventoriées contiennent pourtant les douze fichiers
`Sounds/52990033.wav` à `52990044.wav` et les douze données de morphing
`Tables/Dabing/<id>.dat`. Les voix et leur synchronisation labiale sont donc
**OFFICIELLES** ; ce sont le déclenchement à deux participants et la transition
corporelle de fin qui manquent.

Ainsi, même si des handlers 2 étaient ajoutés, la conversation coop ne
fournirait aucun état final attesté à rejoindre. Réactiver les répliques,
inventer le second signal de départ et inventer deux fins cumulerait trois
changements indépendants.

### Ce que les dialogues voisins permettent d'inférer

Le couple AF1_33/34 emploie le protocole complet attendu : chaque acteur envoie
une fois le signal 1 au coordinateur, puis celui-ci leur renvoie 2 après la
dernière réplique ; leurs handlers 2 restaurent ensuite un comportement ambiant
défini. C'est le meilleur précédent local.

AF1_23/24 ne confirme pas cette symétrie : seul AF1_23 envoie 1 au
coordinateur, tandis qu'AF1_24 conserve bien son handler 2. Son dialogue
présente donc la même lacune de départ que 48/49. Il ne doit pas être compté
comme second exemple complet.

C'est une preuve forte du **protocole**, mais pas des animations finales de
AF1_48/49. Pour ce couple :

- le solo atteste `%%oprenejOzedL` pour la pose appuyée d'AF1_48 ;
- le solo place AF1_49 assis sur `AF1_49_sit` avec `%%plzen` avant le dialogue ;
- la coop remplace cette mise en scène par `%%buchadostolu` pour AF1_49 et ne
  déclare pas la frame de siège dans son script ;
- aucun des deux scripts solo ne révèle ce que le signal 2 devait faire.

### Pourquoi aucun prototype de dialogue n'est proposé

Une expérience audio minimale demanderait encore trois décisions non
attestées : l'endroit exact où AF1_48 doit envoyer son signal 1, la réaction de
48 au signal 2 et celle de 49 au même signal. Le précédent 33/34 suggère la
forme générale, mais ses mouvements et animations appartiennent à d'autres
acteurs et ne peuvent pas être copiés.

`%%oprenejOzedL` est attesté pour la pose solo d'AF1_48 avant le dialogue ; ce
n'est pas une preuve de sa pose après le dialogue. AF1_49 est assis sur
`AF1_49_sit` avec `%%plzen` en solo, alors que la coop ne référence plus le
siège et joue `%%buchadostolu` avant l'unique signal 1. Choisir l'une de ces
poses comme sortie serait une **CRÉATION MODERNE**.

Le simple décommentage des douze appels ne produirait rien tant que le compteur
reste à 1. Ajouter seulement le signal manquant jouerait les voix, puis
enverrait deux signaux 2 ignorés. Cette chaîne n'est pas une synchronisation
exacte et ne mérite pas de fichier `.scr.disabled`.

## Classification et porte de réouverture

Les signaux 2 prouvent une intention de transition après dialogue, mais aucune
animation finale n'est attestée dans les variantes examinées. Ne pas :

- rediriger automatiquement le signal 2 vers `activity` puisque ces labels
  sont vides en coop ;
- rejouer arbitrairement `%%oprenejOzedL`, `%%plzen` ou `%%buchadostolu` ;
- utiliser `HUMAN_Suspend(true)` sans preuve ;
- décommenter le dialogue coop sans traiter son statut de contenu supprimé.

Les voix peuvent être extraites ou écoutées comme constat grâce aux ressources
conservées. Une proposition jouable ne devient recevable qu'avec un second
signal 1 historiquement attribué et deux handlers 2 anciens, ou une autre source
fixant sans ambiguïté les états de fin. En l'état : **audio attesté,
synchronisation incomplète, aucun prototype**.

## Tests de constat ultérieurs

- confirmer que l'ancien sender est lié à une zone de remise et reste terminé
  dès l'initialisation ;
- confirmer que l'ajout de `15511` produit bien un septième objectif et ne
  renumérote pas les six entrées coop ;
- comparer l'objectif 2 courant avant/après mort des trois officiers, puis
  vérifier qu'il reste indépendant de l'objectif 7 ;
- libérer un seul puis les deux prisonniers, vérifier activation et armement ;
- tester arrivée normale, mort en route, mort dans la frame d'arrivée, double
  émission, sauvegarde/reprise et réplication hôte/client ;
- tester mort suivie de respawn, respawn dans ou hors de la zone, déconnexion
  puis reconnexion du porteur d'un prisonnier, migration ou perte de l'hôte si
  le moteur le permet ; aucune de ces transitions ne doit convertir un échec
  en succès ni produire une seconde résolution ;
- vérifier les messages `52999702`, `52999706` et `52999710` dans toutes les
  langues installées ;
- instrumenter le compteur solo et confirmer qu'il reste à 1 sans intervention ;
- rechercher un ancien signal 1 d'AF1_48 et d'anciens handlers 2 avant tout
  essai jouable ;
- si une nouvelle source apparaît, tracer les signaux 2 et vérifier les poses
  finales réellement conservées par le moteur ;
- tester alarmes et morts avant la synchronisation, pendant chaque réplique et
  juste avant les signaux de fin ;
- sauvegarder/reprendre avant libération, arrivée à la zone et dialogue.

Les deux chaînes doivent rester indépendantes. L'objectif d'escorte ne remplace
jamais l'objectif 2 courant, et une éventuelle recherche sur le dialogue ne doit
pas être rendue dépendante de la variante d'objectif 7.

## Sources internes

- `.analysis/scripts/sabre/Scripts/Co_Libye1/AF1_obj2_succ_sender.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye1/AF1_objectives.scr`
- `.analysis/scripts/sabre/Scripts/Co_Libye1/AF1_texty.scr`
- `.analysis/scripts/sabre/Scripts/Libye1/AF1_objective.scr`
- `.analysis/scripts/sabre/Scripts/Libye1/AF1_objective2.scr`
- `.analysis/metadata/sabre/GameData/mpmaplist.txt`
- `.analysis/langenglish-list.json`
- `output/audit/full-game-audit.json`
- versions solo et coop de `AF1_48.scr`, `AF1_49.scr` et
  `AF1_48_AF1_49_speech.scr`
- dialogues voisins AF1_23/24 et AF1_33/34, versions solo et coop
