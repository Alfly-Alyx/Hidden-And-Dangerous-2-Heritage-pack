# Proposition expérimentale — signaux d'alerte incomplets d'Africa 2

État : étude non intégrée, révisée le 14 septembre 2026. Deux gestionnaires
minimaux d'alerte et une reconstruction isolée du signal 2 d'AF2_06 sont
proposés pour essai dans une copie de mission. Aucun fichier actif n'est changé.

## Synthèse

| Candidat | Intention | Base locale | Verdict |
| --- | ---: | ---: | --- |
| `AF2_02` reçoit 5 | 4/4 | 4/4 | redirection minimale vers `ALERT` |
| `AF2_05` reçoit 20 | 4/4 | 4/4 | `goto ALERT` reproduit exactement les pairs |
| `AF2_05` reçoit 2 | 4/4 | 1/4 | intention attestée, corps absent |
| `AF2_06` reçoit 2 | 4/4 | 3/4 | branche `PLANECRASH` testable, désactivée |
| `AF2_activator` reçoit 1 d'AF2_13 | 4/4 | 3/4 | ancien fan-out probable, redondant aujourd'hui |

## Deux diffusions officielles

`AF2_activator.scr` reçoit le signal 5 lorsque le guetteur AF2_13 a repéré le
joueur et alerté les ennemis. Il le redistribue à AF2_01, 02, 04, 05 et 06. La
ligne destinée à AF2_03 existe mais est commentée.

Les destinataires 01, 04, 05 et 06 possèdent chacun un `OnSignal(5)` qui
interrompt l'activité, efface l'animation, passe en course accroupie et rejoint
son checkpoint `<acteur>_alert`. AF2_02 possède bien `AF2_02_alert` dans un
label `ALERT` complet, mais aucun handler 5.

`AF2_dummy_alert01.scr` diffuse le signal 20 au même ensemble 01, 02, 04, 05,
06, avec AF2_03 de nouveau commenté. Les scripts 01, 02, 04 et 06 traitent tous
ce signal par :

```text
OnSignal(20){
  goto ALERT;
}
```

Seul AF2_05 ne possède pas ce handler, alors que son label `ALERT` est complet
et rejoint `AF2_05_alert`.

La matrice des soldats effectivement adressés est donc symétrique :

| Soldat | Reçoit 5 de l'activateur | Reçoit 20 du collectif | Handler 5 | Handler 20 |
| --- | --- | --- | --- | --- |
| AF2_01 | oui | oui | oui | oui |
| AF2_02 | oui | oui | **manquant** | oui |
| AF2_03 | non, ligne commentée | non, ligne commentée | présent mais hors chaîne | présent mais hors chaîne |
| AF2_04 | oui | oui | oui | oui |
| AF2_05 | oui | oui | oui | **manquant** |
| AF2_06 | oui | oui | oui | oui |

## Archives et variantes

La comparaison complète donne les scripts concernés identiques entre la couche
Base et le Patch 1.12. AF2_02 n'y gère pas le signal 5 et AF2_05 n'y gère pas le
signal 20 ; les deux émetteurs conservent leurs envois. Un futur override doit
néanmoins viser la couche effective sans remplacer d'autres scripts de mission.

Les variantes Sabre `Libye2` et `Co_Libye2` redessinent cette rencontre autour
des signaux 1/2 et d'une fusillade mise en scène. Elles ne conservent ni les
émetteurs 5/20 ni les labels `ALERT` de la branche de base et ne peuvent pas
servir de corps historiques pour ces handlers.

## AF2_13 → activateur : signal 1 avant le signal 5

### Ordre exact

Lors de sa première alarme, AF2_13 attend trois secondes, court vers
`AF2_13_01`, envoie 1 à `af2_activator`, rejoint `AF2_13_02`, puis envoie 5.
La variable `alarmcnt` rend cette séquence unique.

L'activateur possède deux sorties déjà conservées :

- son Whenever joueur à 320 unités diffuse 1 à AF2_01, 02, 04, 05 et 06 ;
- son `OnSignal(5)` diffuse 5 au même ensemble.

La symétrie rend très probable l'ancien contrat « recevoir 1 puis redistribuer
1 », avant l'alerte 5. Le corps du fan-out existe donc localement, mais pas son
ancienne entrée `OnSignal(1)`.

### Pourquoi il est redondant dans la version actuelle

AF2_13 ne quitte normalement sa suspension qu'à moins de 300 unités. Le volume
de l'activateur est déjà actif à 320. Dans une approche continue, les cinq
soldats ont donc reçu 1 avant qu'AF2_13 puisse courir vers son premier
checkpoint et envoyer son propre signal 1.

Ajouter aujourd'hui un handler qui recopie le fan-out provoquerait une seconde
activation. Ce n'est pas nécessairement idempotent : AF2_01 repartirait vers
`ACTION` et renverrait 2 à AF2_05/06, tandis que les autres scripts pourraient
interrompre ou recommencer leur activité.

**Classement : vestige très probable d'une ancienne variante d'activation,
aucun delta.** Intention/fan-out : 4/4. Corps exact du handler : 0/4. Besoin
fonctionnel dans le parcours nominal : 1/4.

Les variantes Sabre remplacent entièrement cette topologie : leur AF2_13 est un
renfort réveillé par AF2_15_A1 et ne référence plus l'activateur. Elles ne
permettent pas de restaurer l'ancienne entrée.

### Données manquantes et protocole de test

Il manque une copie où le volume 320 est absent ou initialement désactivé, ainsi
qu'une preuve que le signal 1 devait appeler le fan-out plutôt qu'armer ce
volume. Pour trancher sans modification stable :

1. tracer le fan-out 1 du volume 320 et vérifier qu'il précède toujours
   l'activation d'AF2_13 à 300 ;
2. provoquer une alarme d'AF2_13 depuis plus de 320 unités, si le moteur le
   permet lorsqu'il est suspendu ;
3. envoyer 1 directement à l'activateur et confirmer le no-op actuel ;
4. dans une copie laboratoire seulement, mesurer les effets d'un second
   signal 1 sur chaque soldat, surtout la répétition d'`ACTION` chez AF2_01 ;
5. tester téléportation, apparition dans les volumes et sauvegarde/reprise entre
   320, 300, `AF2_13_01` et `_02`.

Une lacune hors parcours continu ne suffit pas à intégrer le handler : il faut
d'abord prouver que ce cas était supporté par l'architecture historique.

## Candidat 1 — AF2_02, signal 5

### Delta le plus petit

```diff
 OnSignal(20){
   goto ALERT;
 }

+OnSignal(5){
+  goto ALERT;
+}
```

Classification : **RECONSTRUCTION MINIMALE À FORTE FIDÉLITÉ**. Le signal émis,
le destinataire, le checkpoint et le comportement `ALERT` sont officiels. Le
saut n'invente aucune route : il réutilise une transition déjà appelée dans
AF2_02 par son signal 20 et par la branche d'alarme de type 256.

Le prototype ne doit pas recopier le corps des handlers 5 voisins. Toute la
mise en état nécessaire est déjà centralisée dans le label `ALERT` d'AF2_02 ;
la proposition ajoute seulement l'entrée qui manque.

## Candidat 2 — AF2_05, signal 20

Ajouter près des autres handlers :

```diff
+OnSignal(20){
+  goto ALERT;
+}

 OnDeath(){
   ...
 }
```

Classification : **RECONSTRUCTION À FORTE FIDÉLITÉ**. La forme est identique à
celle de quatre autres destinataires du même émetteur, et le label local existe
déjà. Aucun checkpoint ni comportement nouveau n'est créé.

Ici encore, ne pas dupliquer le corps du label. La seule création est la
redirection du signal 20 vers la logique officielle déjà présente.

## Signaux 2 — inspection et disparition du Junkers

Deux émetteurs Base/Patch adressent ensemble AF2_05 et AF2_06 :

- `AF2_01`, au début du label `ACTION`, juste avant de courir inspecter le
  véhicule suspect ;
- `AF2_hidejunkers`, lorsqu'il termine la particule, masque `HoriciJunkers` et
  imprime `NOW HIDING JUNKERS`.

Le numéro et la paire de destinataires sont donc répétés de part et d'autre du
même événement visuel. Ils ne ressemblent pas à une alerte générique : la
mission possède déjà les canaux 5 et 20 pour rejoindre `ALERT`.

### AF2_06 : branche locale suffisante pour un prototype

AF2_06 possède un label `PLANECRASH` qui n'est appelé que lors de son premier
`OnAlarm()`. Il sort l'acteur de suspension, passe en course zombie, parcourt
`AF2_06_02` à `_05`, rend AF2_07 à AF2_11 agressifs, revient vers l'épave puis
termine en posture défensive. La variable `cnt` empêche déjà cette scène de se
répéter lors des alarmes suivantes.

`PROTOTYPE_AF2_06_SIGNAL2.scr.disabled` ajoute une entrée gardée : si `cnt` vaut
0, elle le passe à 1 puis rejoint `PLANECRASH`; sinon elle revient à `END`.
Cette garde traite sans duplication les deux émissions possibles. Le label, le
compteur, les checkpoints et tous les effets sont **OFFICIELS** ; seule la
liaison du signal 2 à ce label est une **INFÉRENCE**. Fidélité proposée : 3/4.

### AF2_05 : corps toujours manquant

AF2_05 ne possède ni référence au Junkers, ni label de crash, ni checkpoint
inutilisé correspondant. Ses seules destinations sont l'inspection des caisses
et l'alerte de combat. Le faire sauter vers `ACTIVATE`, `ACTIVITY` ou `ALERT`
choisirait arbitrairement entre surveillance, reprise de ronde et combat.

**Aucun handler 2 n'est proposé pour AF2_05.** La symétrie des émetteurs prouve
qu'une réaction existait, pas que les deux soldats exécutaient le même corps.

La branche Sabre emploie bien le signal 2 chez ses AF2_05/06, mais pour une
fusillade scénarisée entre AF2_B01 et AF2_B02, avec d'autres routes et cibles.
Elle confirme que le protocole a été redessiné et ne constitue pas une variante
historique compatible avec Base/Patch.

## Protocole de test

### Baseline

Consigner séparément :

- signal 5 reçu de l'activateur après alerte d'AF2_13 ;
- signal 1 envoyé par AF2_13 au checkpoint `_01` et fan-out 1 déjà produit par
  la proximité 320 ;
- signal 20 reçu de `dummy_alert01` après alerte collective ;
- état suspendu, optimisation, posture, portée de vue et checkpoint des six
  soldats ;
- émission unique ou répétée par chaque contrôleur.

### Matrice AF2_02

1. Signal 5 avant le signal 1 d'activation locale.
2. Signal 5 pendant chaque segment de la patrouille.
3. Signal 20 avant puis après le signal 5.
4. Alarme de type 256 avant ou après le signal 5.
5. Mort avant réception et signaux répétés.

Acceptation : AF2_02 rejoint une seule fois `AF2_02_alert`, ne reprend pas sa
patrouille, reste réactif et n'exécute aucun checkpoint étranger.

### Matrice AF2_05

1. Signal 20 avant activation, pendant l'inspection des caisses et après son
   propre signal 5.
2. Alarmes 2, 16 et 256 avant/après la diffusion collective.
3. Signaux 20 répétés et mort anticipée.

Acceptation : AF2_05 rejoint le même état `ALERT` que ses pairs, sans boucle
`ALARMDONELOOP` concurrente ni double mouvement.

### Matrice AF2_06, signal 2

1. Signal d'AF2_01 avant l'activation locale d'AF2_06.
2. Disparition du Junkers avant puis après ce premier signal.
3. Alarme initiale avant, pendant et après `PLANECRASH`.
4. Vérifier une seule traversée des checkpoints et une seule bascule agressive
   d'AF2_07 à AF2_11.
5. Sauvegarder/reprendre avec `cnt` à 0 puis à 1.

Acceptation : la première cause seulement joue `PLANECRASH`; la seconde est
inerte, les canaux 5/20 restent capables de rejoindre `ALERT`, et aucune scène
n'est lancée après la mort de l'acteur.

### Commun

Tester une nouvelle mission et une sauvegarde/reprise autour de chaque signal,
dans tous les modes supportés. Les lignes vers AF2_03 restent commentées et les
signaux 2 vers AF2_05/06 restent inchangés.

## Réversibilité

Chaque candidat reste indépendant et désactivé. Une réversion retire uniquement
le handler testé ; aucun émetteur, checkpoint, acteur, valeur de jeu ou ordre de
mission n'est modifié. Le signal 1 de l'activateur n'a pas de prototype et ne
doit pas être ajouté avec les autres candidats.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_activator.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_13.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_dummy_alert01.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_hidejunkers.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_01.scr` à `AF2_06.scr`
- équivalents de la couche Patch
- variantes non équivalentes `Libye2` et `Co_Libye2` de la couche Sabre
