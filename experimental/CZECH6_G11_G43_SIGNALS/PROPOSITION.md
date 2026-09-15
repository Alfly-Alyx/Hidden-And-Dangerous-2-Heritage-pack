# Proposition expérimentale — récepteurs G11/G43 de Czech 6

État : étude non intégrée, révisée le 14 septembre 2026. Cette proposition n'altère aucun
script commercial et ne doit pas rejoindre le lot stable sans test dynamique.

## Classification

**Intention plausible, corps récepteur manquant.** Les deux signaux émetteurs
sont officiels, leurs destinataires existent et le patron de réveil proposé est
attesté chez plusieurs gardes voisins. Aucun gestionnaire exact de G11 ou G43
n'est toutefois conservé. La reconstruction minimale reste hypothétique et ne
doit même pas être prototypée avant la baseline hors rayon décrite ci-dessous.

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Faisabilité technique | 3/4 | deux petits gestionnaires, mais sémantique d'alarme à tester |
| Fidélité de l'émission | 4/4 | deux `SendSignal(..., 1)` officiels dans G40 |
| Fidélité des récepteurs | 2/4 | patron voisin cohérent, contenu original inconnu |
| Risque | moyen | réveil redondant, cascade G11 et déplacement G43 possibles |

## Preuves officielles

### Émetteur G40

Dans `C5_G40.scr`, l'alarme interrompt la conversation avec G41, augmente la
portée de vue, passe G40 en course, puis exécute :

```text
SendSignal(g11, 1);
SendSignal(g43, 1);
```

G40 termine ensuite son script. Sa mort interrompt seulement la conversation et
n'envoie pas ces deux signaux. G41, l'autre interlocuteur, n'envoie pas non plus
de signaux à G11/G43 lors de son alarme. Ces asymétries doivent rester intactes.

### Récepteur G11

`C5_G11.scr` décrit un membre d'équipage du Panther, associé au siège
`C5_G11_sit01` et au câble `1cable_ok`.

- état initial : IA défensive, optimisation 2, acteur suspendu ;
- à moins de 50 unités : réveil, assise et animation `%%spojar` ;
- signal 2 : câble détruit, variable `destroyed = 1`, puis boucle sonore de
  réglage radio ;
- alarme : si le câble n'est pas détruit, signaux vers G14, G15, G16, G17, G19
  et G20, puis sortie du script ;
- aucun signal 1 n'est traité.

La couche Patch conserve cette absence de gestionnaire du signal 1. Elle retire
par ailleurs un `SendSignal(obj, 1)` du traitement d'alarme de G11 ; cette
correction distincte doit être préservée dans tout futur override.

### Récepteur G43

`C5_G43.scr` décrit le garde qui surveille l'opérateur radio.

- état initial : IA défensive, optimisation 2, acteur suspendu ;
- à moins de 50 unités : réveil et animation `%%cumvoda` ;
- alarme : arrêt de l'animation, course vers `C5_G43_01`, fin du script ;
- aucun `OnSignal` n'est présent.

### Analogues de réveil dans la même mission

Plusieurs gardes suspendus de Czech 6 possèdent un gestionnaire du signal 1
réduit à :

```text
HUMAN_Suspend(false);
GoTo end;
```

Ce patron existe notamment chez G21, G29, G32, G33, G34, G35, G36, G38, G39,
G44 et G45. D'autres gardes ajoutent un mode accroupi ou une route parce que leur
script et leurs checkpoints le demandent explicitement. Rien d'équivalent ne
prouve une route supplémentaire pour G11 ou G43.

## Hypothèses

### H1 — fonction des deux signaux

**INFÉRENCE plausible.** Comme G11 et G43 commencent suspendus et possèdent déjà
leur comportement d'alarme, le signal envoyé par G40 devait au minimum les
réveiller lorsqu'une alarme naît hors de leur rayon de proximité.

### H2 — réveil sans alarme forcée

**INFÉRENCE prudente.** Le signal n'est pas une preuve qu'il faut appeler ou
reproduire manuellement `OnAlarm`. Le moteur peut distribuer l'événement
d'alarme à un acteur dès son réveil, ou son IA défensive peut reprendre à partir
de l'état global. Le plus petit raccord cohérent est donc uniquement la levée de
suspension.

### H3 — aucun trajet ajouté

**INFÉRENCE forte.** G43 possède déjà `C5_G43_01` dans son traitement d'alarme.
G11 possède déjà toute sa cascade radio dans le sien. Ajouter ces actions au
gestionnaire du signal 1 risquerait de les exécuter deux fois si `OnAlarm` est
aussi reçu.

## Porte de décision obligatoire avant modification

Exécuter impérativement Czech 6 sans reconstruction, en déclenchant l'alarme de G40
alors que le joueur reste à plus de 50 unités de G11 et G43.

- Si G11 exécute déjà sa cascade et G43 rejoint déjà `C5_G43_01`, les signaux 1
  sont redondants : ne rien modifier.
- Si les deux restent suspendus mais réagissent lorsqu'on approche ensuite à
  moins de 50 unités, le réveil manquant est démontré : essayer le delta minimal.
- Si un seul garde reste inerte, prototyper uniquement son gestionnaire.
- Si le réveil seul ne déclenche pas la réaction attendue, arrêter l'essai et
  relever l'état moteur ; ne pas inventer automatiquement une alarme forcée.

## Delta expérimental conditionnel

Ne considérer les ajouts ci-dessous que si la baseline prouve que G11 ou G43
reste suspendu et inerte lorsque G40 déclenche l'alarme hors de son détecteur de
50 unités. Sans cette observation, il n'existe aucun delta recommandé.

### G11 — appliquer sur la version effective Patch

Ajouter, sans toucher au signal 2 ni au traitement d'alarme :

```diff
 OnSignal(2)  // received from C5_obj02
 {
   destroyed=1;
   ...
 }

+OnSignal(1)  // reconstruction minimale : probablement reçu de C5_G40
+{
+  HUMAN_Suspend(false);
+  GoTo end;
+}
```

### G43 — appliquer sur un override expérimental du script commercial

```diff
 Whenever player(_PlayerInRange(50))
 {
   HUMAN_Suspend(false);
   HUMAN_SetAnim("%%cumvoda", 200, 200, true);
   GoTo end;
 }

+OnSignal(1)  // reconstruction minimale : probablement reçu de C5_G40
+{
+  HUMAN_Suspend(false);
+  GoTo end;
+}
```

Les commentaires `reconstruction minimale` n'affirment pas qu'ils existaient
dans le code original. Le prototype réel doit rester dans ce dossier et porter
la même classification.

## Alternatives rejetées à ce stade

- `HUMAN_SetAlarm(true)` : aucun analogue direct n'est démontré pour cette
  chaîne et cela peut dupliquer l'événement moteur ;
- copier le corps de `OnAlarm` dans le signal 1 : risque de double cascade ou de
  double déplacement ;
- envoyer directement les signaux G14–G20 depuis G40 : contourne G11 et sa
  variable `destroyed` ;
- déplacer G43 directement dans le gestionnaire : son `OnAlarm` possède déjà la
  route officielle ;
- modifier le signal 2 ou restaurer le `SendSignal(obj, 1)` supprimé par le
  patch : hors périmètre et contraire à la couche effective ;
- ajouter les mêmes signaux à G41 ou au décès de G40 : aucune preuve officielle.

## Protocole de test

### Baseline et instrumentation

Consigner : émission des deux signaux par G40, état suspendu/actif de G11/G43,
entrée dans leurs traitements d'alarme, animation de G11, position de G43, état
du câble et signaux envoyés par G11 à G14–G20.

### Matrice G11

1. Alarme de G40 hors du rayon de 50 unités, câble intact.
2. Même scénario après réception préalable du signal 2.
3. Signal 2 reçu après le réveil par signal 1.
4. Joueur entrant ensuite dans le rayon de 50 unités.
5. G11 mort avant ou après le signal.

Acceptation : G11 est réveillé au plus une fois, le signal 2 garde sa boucle
sonore, `destroyed` continue de bloquer la cascade prévue et aucun signal
G14–G20 n'est doublé.

### Matrice G43

1. Alarme de G40 hors du rayon de 50 unités.
2. Proximité avant puis alarme.
3. Alarme avant puis proximité.
4. Types d'alarme 16, 256, 512 et autre type.
5. G43 mort avant ou après le signal.

Acceptation : le réveil ne lance aucune route inventée ; si l'événement d'alarme
est reçu, G43 utilise une seule fois son checkpoint officiel `C5_G43_01` et son
animation d'observation ne reste pas bloquée.

### Scénarios communs

- alarme provenant de G40 et alarme provenant uniquement de G41 ;
- interruption et fin normales de `C5_G40_G41_speech` ;
- passages répétés près des deux gardes ;
- sauvegarde/reprise avant l'alarme, après le signal et après le réveil ;
- modes solo et coopération pris en charge par la mission.

## Réversibilité et verdict

La réversion consiste à retirer uniquement les deux gestionnaires ajoutés. Elle
ne modifie aucun acteur, checkpoint, signal émetteur ni état d'objectif.

**Verdict.** Le réveil seul est une hypothèse raisonnable et le plus petit
prototype possible, mais il n'est pas encore une correction validée. Si le test
baseline montre que les acteurs reçoivent déjà correctement l'alarme malgré
leur suspension, classer les deux `SendSignal` comme redondants et abandonner la
reconstruction.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_G40.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_G11.scr`
- `.analysis/scripts/patch/SCRIPTS/CZECH6/C5_G11.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_G43.scr`
- scripts voisins `C5_G01.scr` à `C5_G45.scr`
