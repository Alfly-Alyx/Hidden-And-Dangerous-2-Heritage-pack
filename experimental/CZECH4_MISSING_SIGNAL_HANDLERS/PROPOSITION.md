# Proposition expérimentale — gestionnaires manquants de Czech 4

État : étude non intégrée, révisée le 14 septembre 2026. Cette proposition ne
modifie aucun script commercial. Elle distingue une reconstruction autonome
testable pour le pianiste, un signal de sniper probablement redondant et deux
trajectoires Plazzars qui ne doivent pas être inventées.

La mission additive coordonnée `Czech4 [Prototype — vestiges]` est étudiée dans
`../CZECH4_VESTIGES_VARIANT/ETUDE.md`. Elle reprend le compteur orphelin, les
pelotons 07–09 et le chien sans modifier les conclusions ci-dessous.

## Règle de preuve

- **OFFICIEL** : ligne ou comportement présent dans la mission commerciale.
- **INFÉRENCE** : raccord soutenu par plusieurs scripts voisins.
- **CRÉATION MODERNE** : comportement absent qu'un prototype ajouterait.

## Synthèse

| ID | Intention | Base comportementale | Verdict |
| --- | ---: | ---: | --- |
| `CZ4-PLATOON04-S5` | 4/4 | 3/4 | reconstruction autonome désactivée, à tester |
| `CZ4-SNIPER01-S1` | 2/4 | 3/4 | probablement redondant ; aucun delta |
| `CZ4-PLAZZARS02-S4` | 4/4 | 1/4 | intention attestée, comportement manquant |
| `CZ4-PLAZZARS03-S4` | 4/4 | 1/4 | intention attestée, comportement manquant |
| `CZ4-COUNTER01-S10` | 2/4 | 1/4 | prototype de contre-attaque très incomplet |

## Pianiste — signal 5

### Preuves officielles

`CZ4_APumperz_01.scr` résout `CZ4_Platoon_01` à `06`. Son `OnAlarm()` envoie le
signal 5 aux six soldats. Son `OnDeath()` répète exactement la même diffusion.
Le pianiste `CZ4_Platoon_04` est donc visé deux fois explicitement par une
chaîne commerciale.

Cinq des six scripts de peloton possèdent `OnSignal(5)`. Malgré leurs routes et
postures propres, leur intersection est stable :

```text
HUMAN_Suspend(false);
HUMAN_SetOptimized(1);
SetAlarmType(1023, true);
```

Les scripts 01, 02, 03, 05 et 06 exécutent tous ces trois appels. Ils ajoutent
ensuite un checkpoint, une posture, un délai ou une boucle spécifique. Aucun de
ces ajouts ne peut être copié au pianiste : aucun checkpoint de combat propre à
`CZ4_Platoon_04` n'est conservé dans son script.

Le script du pianiste contient déjà toute sa réaction à un événement moteur
d'alarme. `OnAlarm()` :

- arrête l'animation `%%piano` ;
- coupe les deux frames sonores `l_4piano_` et `S_piano_far` ;
- remet l'acteur debout, le tourne vers le joueur et passe l'IA en agressif ;
- conserve les mises à jour de la valeur de jeu 15 selon le type d'alarme ;
- termine ensuite le script.

Sa mort coupe également les deux sons. Mais le signal 5 ne vient pas seulement
de `OnAlarm()` : `CZ4_APumperz_01.OnDeath()` l'envoie aussi. Dans ce second cas,
aucun événement moteur d'alarme actif n'est garanti chez le pianiste. Un simple
réveil et réabonnement peut donc le laisser jouer, avec ses sons actifs.

Une autre course existe avant les seuils de 40 et 30 unités. Si le signal 5 est
reçu avant que le joueur approche, les Whenevers `AKTIVACE` et `AKTIVACE2`
restent armés et pourraient relancer ultérieurement le piano ou son alarme. La
reconstruction doit neutraliser ces deux entrées en plus de fermer l'état
audio/animation courant.

### Reconstruction expérimentale autonome

Le prototype désactivé `PROTOTYPE_CZ4_PLATOON04_SIGNAL5.scr.disabled` assemble
deux blocs officiels sans inventer de déplacement :

- l'intersection des cinq frères (`Suspend(false)`, optimisation 1 et alarmes
  1023) ;
- la fermeture d'état déjà utilisée dans le `OnAlarm()` du pianiste : arrêt de
  l'animation, extinction répétée des deux sons, station debout, rotation vers
  le joueur, agressivité et arrêt du mouvement.

Il désarme en outre `AKTIVACE` et `AKTIVACE2`. Ces deux lignes sont une
**GARDE MODERNE** : elles ne sont pas retrouvées dans un ancien handler, mais
empêchent un signal précoce de laisser redémarrer l'état piano. Le prototype
n'utilise ni `_GetAlarmType()`, ni les écritures de valeur 15 du `OnAlarm()` :
un signal de mort ne transporte pas le type d'événement nécessaire à ce choix.
Il n'invente enfin ni checkpoint, ni rôle de sniper.

Classification : **RECONSTRUCTION EXPÉRIMENTALE, fidélité 3/4**. La transition
d'état est entièrement composée d'opérations officielles du même groupe et du
même acteur ; l'ordre exact de l'ancien handler et les deux gardes ne sont pas
prouvés.

### Porte de test

Avant le delta, déclencher l'alarme de `CZ4_APumperz_01` alors que le pianiste
joue et vérifier s'il réagit déjà malgré l'absence de handler. Après le delta :

1. vérifier la réception du signal 5 après alarme et après mort du Pumperz ;
2. confirmer l'arrêt unique de `%%piano` et des deux sons ;
3. vérifier qu'aucune route inexistante n'est demandée ;
4. tester le signal avant l'activation par proximité à 40 et 30 unités ;
5. tester alarme avant signal, signal avant alarme et événements simultanés ;
6. tuer le pianiste pendant le son ou après l'alarme ;
7. sauvegarder/reprendre avant activation, pendant le piano et après le signal.

Critère d'arrêt : tout redémarrage de `%%piano`, maintien d'un son, double
réaction d'alarme ou écriture inattendue de la valeur 15 invalide le prototype.

## Sniper 01 — signal 1 probablement redondant

`CZ4_Detector_01.scr` envoie le signal 1 à six acteurs lorsque le joueur entre
à moins de 10 unités. Cinq destinataires possèdent une réception explicite.
`CZ4_Sniper_01.scr` n'en possède aucune, mais son propre Whenever actif dès
l'initialisation le sort de suspension à moins de 60 unités. Ses types d'alarme
sont déjà activés avant cette suspension.

Dans un parcours continu, atteindre le volume de 10 unités implique donc
d'avoir franchi auparavant le seuil de 60 : ajouter un handler 1 ne change pas
l'état nominal. Le signal peut être une diffusion uniforme conservée pour la
commodité du détecteur, ou le vestige d'un ancien réveil plus tardif.

**Verdict : probablement redondant, aucun delta.** Tester seulement les cas
limites — téléportation ou apparition directement dans le volume de 10,
sauvegarde/reprise à l'intérieur, désactivation/réactivation éventuelle du
Whenever — avant de rouvrir le dossier. Même si un cas limite échoue, il ne
donne pas le corps historique d'un handler.

### Degré de preuve, lacunes et risque

- émission vers le sniper : **OFFICIEL 4/4** ;
- équivalence fonctionnelle avec son réveil à 60 unités : **4/4** dans un
  parcours spatial continu ;
- existence historique d'une action supplémentaire : **0/4** ;
- utilité actuelle d'un handler : **1/4**.

Il manque une variante du sniper recevant 1 et toute preuve d'un état autre que
le réveil. Un alias moderne vers `HUMAN_Suspend(false)` serait généralement un
no-op, mais pourrait changer les cas de téléportation, de reprise dans le volume
ou d'ordre d'initialisation. Une démonstration isolée n'est donc nécessaire que
si la baseline montre que le seuil 60 n'est pas exécuté dans l'un de ces cas ;
elle ne devrait alors tester que le réveil, sans route ni changement d'alarme.

## Plazzars 02 et 03 — signal 4

### Matrice officielle

Trois détecteurs adressent le même trio :

| Émetteur | Portée | Signal | Récepteurs |
| --- | ---: | ---: | --- |
| `CZ4_Detector_03` | 10 | 3 | Plazzars 01, 02, 03 |
| `CZ4_Detector_04` | 20 | 4 | Plazzars 01, 02, 03 |
| `CZ4_Detector_15` | 15 | 7 | Plazzars 01, 02, 03 |

Les trois Plazzars gèrent 3, 7 et 16. Seul `CZ4_Plazzars_01` gère 4. Ce handler
le réveille, choisit marche ou course selon la valeur de jeu 15, réactive les
types d'alarme et le déplace vers `cor3`.

`CZ4_Plazzars_02` et `03` ont chacun une route complète pour 3 et 7. Pour 02,
elle se termine par `RRR4`; pour 03, par `RRR5`. Dans chacun de ces deux
scripts, les routes 3 et 7 sont presque identiques. Cette répétition ne fournit
pas la route du signal 4 : chez Plazzars 01, les signaux 3, 4 et 7 conduisent à
trois réactions différentes (`Susp9_2`, `cor3`, `Sn`).

Le token `cor3` apparaît aussi chez `CZ4_Corners_01`, mais aucune source ne
montre que les Plazzars 02 ou 03 devaient partager ce checkpoint. Les couches
Patch et Sabre auditées ne conservent aucune variante de ces scripts.

### Classification

**OFFICIEL.** Les deux émissions manquantes sont certaines : le détecteur 04
nomme explicitement les trois destinataires.

**INFÉRENCE forte.** Les acteurs 02 et 03 devaient probablement être réveillés
et rejoindre une position adaptée à l'approche par la zone du détecteur 04.

**COMPORTEMENT MANQUANT.** Les checkpoints, leur ordre, les postures, les délais
et la position finale ne sont pas conservés. Copier `cor3`, réutiliser la route
3/7 ou ne faire qu'un réveil modifierait la géométrie tactique sans preuve.

Aucun delta n'est proposé pour `CZ4_Plazzars_02.scr` ou
`CZ4_Plazzars_03.scr`. Les deux cas restent **« intention attestée,
comportement manquant »**.

### Conditions de réouverture

Rechercher en priorité une ancienne scène ou un ancien script contenant :

- un `OnSignal(4)` propre à 02 ou 03 ;
- des checkpoints dédiés au corridor du détecteur 04 ;
- une documentation reliant le détecteur à une position de défense ;
- une variante de mission où les trois branches 3/4/7 sont complètes.

Un test en jeu peut établir que les deux acteurs restent suspendus, mais il ne
peut pas restituer à lui seul leurs trajectoires historiques.

## Compteur orphelin `CZ4_Counter_01`

### Fragment officiel

`CZ4_Counter_01.scr` déclare quatre cibles, initialise `Platoon_counter` à 0,
puis incrémente cet entier à chaque signal 10. Son intention finale est lisible :
au-delà de deux notifications, envoyer le signal 7 à `CZ4_Platoon_06`, `_07`,
`_08` et `_09`.

```text
OnSignal(10)
{
  Platoon_counter = Platoon_counter + 1;
}

If (Platoon_counter > 2)
{
  SendSignal(CZ4_Platoon_06, 7);
  SendSignal(CZ4_Platoon_07, 7);
  SendSignal(CZ4_Platoon_08, 7);
  SendSignal(CZ4_Platoon_09, 7);
}
```

Ce fragment ressemble à un déclencheur de renforts ou de contre-attaque après
trois événements, probablement des morts. La nature des trois événements n'est
toutefois décrite par aucun commentaire ni émetteur survivant.

### Ruptures des deux côtés

**Amont manquant.** Aucun acteur propriétaire `CZ4_Counter_01` n'est relié dans
le registre effectif et aucune émission de signal 10 ne vise cette frame. La
mission emploie le numéro 10 ailleurs, mais vers `CZ4_Vata_*`, `CZ4_Chatter_*`
ou des soldats `R_Cz4_*`; un numéro de signal n'a pas de sens global et ces
émissions ne sont pas des sources pour le compteur.

**Aval manquant.** Parmi les quatre noms ciblés, seul `CZ4_Platoon_06` subsiste
dans la chaîne effective étudiée. Aucun script `CZ4_Platoon_07.scr`, `_08.scr`
ou `_09.scr` n'a été retrouvé dans le corpus commercial extrait, et les trois
acteurs correspondants sont absents du registre effectif. Le handler 7 éventuel
de ces trois groupes est donc également inconnu.

**Contrôle mal placé.** Le test `If (Platoon_counter > 2)` se trouve au niveau
principal, après le gestionnaire, et non dans `OnSignal(10)`. Le flux initialise
le compteur à 0, évalue immédiatement la condition comme fausse, puis ne montre
aucune boucle qui la réévaluerait après les incréments futurs. Même avec un
propriétaire et trois émetteurs, le script survivant ne démontre pas un
déclenchement fonctionnel au troisième signal.

### Surface réelle d'une reconstruction

Ce cas ne peut pas être présenté comme une réactivation simple. Il faudrait au
minimum créer ou retrouver :

1. l'acteur compteur et sa liaison au script ;
2. au moins trois événements émetteurs et leur condition exacte ;
3. les acteurs, scripts, positions et équipements de Platoon 07, 08 et 09 ;
4. leurs gestionnaires du signal 7 et leurs trajectoires ;
5. une correction structurelle déplaçant le test de seuil dans le handler ou
   dans une boucle démontrée ;
6. une protection contre les signaux supplémentaires et les doubles envois.

Même une version moderne limitée à Platoon 06 changerait le groupe de quatre
attesté par le script et ne restituerait pas la scène. Inventer trois émetteurs
de mort à partir d'acteurs choisis arbitrairement fixerait une sémantique que la
source ne donne pas.

**Verdict : prototype de renforts/contre-attaque très incomplet, fidélité 1/4,
aucun delta exécutable proposé.** La seule donnée ferme est la forme « trois
signaux 10, puis quatre signaux 7 » ; tous les propriétaires et comportements
qui lui donnent un sens sont absents ou partiels.

### Conditions de réouverture

Priorité à une ancienne scène ou liste de bindings contenant le porteur du
compteur, puis à des scripts d'acteurs envoyant explicitement le signal 10 à ce
porteur. Il faudrait ensuite retrouver au moins les scripts et transforms de
Platoon 07–09. Le seul déplacement du test dans `OnSignal(10)` ne suffit pas.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_APumperz_01.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Platoon_01.scr` à
  `CZ4_Platoon_06.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Detector_03.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Detector_01.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Sniper_01.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Detector_04.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Detector_15.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Plazzars_01.scr` à
  `CZ4_Plazzars_03.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Corners_01.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Counter_01.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH4/CZ4_Platoon_06.scr`
