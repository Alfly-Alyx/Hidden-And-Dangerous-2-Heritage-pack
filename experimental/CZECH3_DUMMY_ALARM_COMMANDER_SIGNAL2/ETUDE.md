# Étude expérimentale — délai d'alarme Czech 3 et signal 2 du commandant

État : reconstruction désactivée, 14 septembre 2026. Aucun fichier commercial
n'est modifié et le prototype n'est ni lié à la mission, ni compilé.

## Verdict

`R_cz3_dummy_alarm.scr` attend 60 secondes après son signal 1 puis adresse le
signal 2 au commandant. Le commentaire annonce une alarme si l'escouade ne sort
pas à temps. `R_cz3_commander.scr` ne conserve pourtant aucun gestionnaire de
signal.

Les archives locale, coopérative et leurs révisions publiques conservent toutes
la même rupture. Aucun corps exact de `OnSignal(2)` n'a été retrouvé. Le
prototype fourni est donc une **reconstruction expérimentale 2/4**, fondée sur
la branche d'alarme officielle du même commandant, et non une restauration.

## Chaîne officielle

Le dummy ne fait que :

```text
OnSignal(1)
{
  Delay(60000);
  SendSignal(commander, 2);
}
```

La source scriptée du signal 1 vers ce dummy n'apparaît pas dans le corpus ; un
déclencheur de scène reste possible. Le signal 2, son délai et son destinataire
sont néanmoins explicites.

Le commandant commence suspendu, avec seulement les alarmes 2, 16 et 256
actives après son masque final. Son `OnAlarm()` contient déjà une réaction
complète pour ces trois événements : arrêt de `%%ctuneco`, réveil, arme en main,
déplacement vers `commander1`, tirs sur `c3wn_vil4` à `c3wn_vil7`, rechargement,
mode sniper puis remise en attente. Cette salve est la seule transition locale
capable de rendre vraie l'intention « il y aura une alarme » après le délai.

## Recherche de variantes

- la copie Base est unique dans les couches commerciales extraites ;
- les sauvegardes inspectées ne contiennent qu'un état générique de commandant,
  sans source de script récupérable ;
- la variante `Czech3bco` du paquet coopératif et ses révisions 2021, 2022 et
  actuelle conservent le dummy et le commandant sans handler 2 ;
- la variante `co_czech3` remanie des commentaires et l'état global d'alarme,
  mais ne fournit toujours pas ce handler.

Sources publiques : [Czech3bco — commandant](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Czech3bco/R_cz3_commander.scr),
[Czech3bco — dummy d'alarme](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Czech3bco/R_cz3_dummy_alarm.scr),
[variante co_czech3](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/co_czech3/r_cz3_commander.scr).

## Reconstruction proposée

`PROTOTYPE_ONSIGNAL2.scr.disabled` transpose directement la branche officielle
2/16/256 dans une entrée de signal. Il ne lit pas `_GetAlarmType()` : un signal
n'apporte pas l'événement moteur requis. Il conserve la garde à 7 unités, les
quatre cibles, la variable `a`, les masques d'alarme et le retour au label
`end`.

Deux raccords plus courts sont rejetés :

- convertir 2 en un signal d'alarme générique n'a aucun précédent actif local ;
- activer le type 128 « script » puis appeler une alarme dépend d'une sémantique
  insuffisamment documentée et la branche officielle du commandant exclut 128.

Le prototype duplique donc du code, mais limite l'hypothèse au choix de la
branche. L'ordre original et l'éventuelle garde contre les répétitions restent
inconnus.

## Porte de test

1. Identifier ce qui déclenche le dummy et vérifier que le délai part une seule
   fois.
2. Tester le signal avant et après le réveil de proximité à 70 unités.
3. Tester joueur à moins et à plus de 7 unités au terme des 60 secondes.
4. Vérifier la salve, le rechargement, le sniper et le réarmement de 274.
5. Envoyer le signal deux fois et refuser toute double salve non maîtrisée.
6. Sauvegarder/reprendre avant le signal, pendant le délai et pendant la salve.

Le prototype doit rester désactivé si le déclencheur amont ne peut pas être
établi ou si la salve modifie la progression de l'objectif.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/CZECH3/R_cz3_dummy_alarm.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH3/R_cz3_commander.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH3/R_Cz3_reinforcement.scr`
- sauvegardes de `.analysis/unlock-profiles/`, consultées en lecture seule
