# Fiche de migration stable — reprise du polissage dans Burgundy 2

État : **migré vers stable**, 14 septembre 2026. Le cas concerne uniquement la
mission solo Burgundy 2. Cette fiche conserve la preuve et le protocole de
régression ; elle ne représente plus un travail expérimental restant.

## Verdict

L'intention du protocole est fortement attestée : `ge_motorka.scr` envoie 2
avant le dialogue avec le commentaire `nelesti` (« ne polis pas »), puis 3
après le dialogue avec le commentaire `lesti` (« polis »). Dans
`ge_dilna.scr`, le premier `Whenever` arrête effectivement l'animation, tandis
que le second est commenté « animation de polissage » mais écoute par erreur le
signal 2 et ne contient plus l'appel d'animation.

Le delta minimal a été promu dans l'installateur principal :

1. faire écouter le signal 3 au second `Whenever` ;
2. y rétablir l'appel exact à `%%lestisamopal` déjà utilisé par l'initialisation ;
3. ne pas réémettre `HUMAN_ACTIVITY_Sit(sit)` tant qu'un test ne démontre pas
   que l'arrêt de l'animation a aussi annulé l'activité assise.

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Intention 2 = arrêt | 4/4 | émetteur, commentaire et corps du récepteur concordent |
| Intention 3 = reprise | 4/4 | émetteur et commentaire du second handler concordent |
| Animation à reprendre | 4/4 | identifiant et paramètres conservés dans le même script |
| Interaction avec l'activité assise | résolue par delta minimal | aucune seconde activité assise n'est émise |

## Preuves officielles

### Séquence de dialogue

Dans la branche solo de `ge_motorka.scr`, lorsque le joueur est à moins de
12 unités et que la conversation n'a pas encore eu lieu :

```text
SendSignal(ge_dilna, 2);  // nelesti
... dialogue ...
SendSignal(ge_dilna, 3);  // lesti
```

Le signal 2 précède la première réplique de `ge_dilna`; le signal 3 suit la
dernière. Les deux commentaires décrivent une paire arrêt/reprise.

### État du polisseur

Le signal 1 d'activation de `ge_dilna.scr` :

```text
HUMAN_Suspend(0);
suspend=0;
SetAlarmType(503,1);
HUMAN_ACTIVITY_Sit(sit);
HUMAN_SetAnim("%%lestisamopal", 500,500,1);
```

Le handler `kec` sur signal 2 exécute seulement
`HUMAN_SetAnim("", 300, 300, 0)`. Il ne retire pas l'activité assise, ne déplace
pas l'acteur et ne change pas ses abonnements d'alarme.

Le handler `lesti` suivant écoute lui aussi le signal 2. Son corps ne contient
plus que le commentaire `//animace lesteni qeru` puis `goto end`. Corriger le
numéro sans restaurer l'appel d'animation ne produirait donc aucune reprise.

## Variantes

Les quatre seuls fichiers homonymes retrouvés dans les couches extraites sont
les copies solo et coopératives de `ge_motorka.scr` et `ge_dilna.scr` sous
Sabre ; aucune copie Base ou Patch supplémentaire n'existe. La version
coopérative ne constitue pas
une sauvegarde du comportement perdu : elle retire les deux signaux autour du
dialogue, ne place plus `ge_dilna` sur `ge_dilna_sit` et utilise une animation
`%%nudazed1` sans polissage. Elle représente une mise en scène différente.

L'identifiant `%%lestisamopal` n'apparaît que dans le script solo conservé. La
paire « signal 2 puis signal 3 vers le même acteur » autour de ce dialogue est
elle aussi unique dans le dossier Burgundy2. Il n'existe donc aucun second
handler historique à recopier, mais la ligne d'initialisation du même acteur
fournit l'action exacte.

## Delta migré vers stable

Le lot stable applique au script solo :

```diff
-Whenever lesti(_SignalReceived(2))
+Whenever lesti(_SignalReceived(3))
 {
 //animace lesteni qeru
+HUMAN_SetAnim("%%lestisamopal", 500,500,1);
 goto end;
 }
```

La correction 2 → 3 est classée **OFFICIELLE PAR CONTRAT** : le signal 3 et le
commentaire correspondant sont présents dans l'émetteur. L'appel d'animation
est la **RESTAURATION MINIMALE** retenue : sa chaîne et ses paramètres
proviennent du même script. Aucun appel à `HUMAN_ACTIVITY_Sit(sit)` n'est ajouté.

### Pourquoi ne pas répéter immédiatement `HUMAN_ACTIVITY_Sit(sit)`

Le signal 2 efface uniquement l'animation personnalisée. Rien dans la séquence
de dialogue ne déplace `ge_dilna` ou n'appelle une autre activité. Rejouer
l'activité assise pourrait réinitialiser sa pose ou sa position au moment de la
dernière réplique. Le plus petit delta consiste donc à reprendre l'animation.

La variante qui rejouerait `HUMAN_ACTIVITY_Sit(sit)` est abandonnée : elle
ajouterait un effet que le signal 3 ne demande pas et pourrait réinitialiser la
pose ou la position après la dernière réplique.

## Alarmes et courses critiques

`OnAlarm()` désactive les Whenevers et les signaux, mémorise le type d'alarme et
arrête l'animation dans les branches de menace. Il peut aussi armer l'acteur,
le déplacer vers `ge_dilna1`, l'envoyer au véhicule ou terminer son script.
`OnDeath()` désactive également les entrées et termine le script.

Le handler de reprise ne doit donc :

- ni réactiver les Whenevers désactivés par l'alarme ;
- ni réabonner les types d'alarme ;
- ni remettre l'acteur assis après un déplacement de combat ;
- ni relancer l'animation après sa mort ou la fin du script.

Le moteur doit ignorer le signal 3 si `DisableWhenevers(1)` est déjà effectif.
La simultanéité entre alarme et dernière réplique relève désormais du contrôle
de régression stable, pas d'une nouvelle variante expérimentale.

## Contrôle de régression stable

1. Activer la scène et confirmer le polissage initial en position assise.
2. Déclencher le dialogue : le signal 2 doit arrêter le polissage avant la
   première réplique.
3. Attendre la dernière réplique : le signal 3 doit reprendre exactement une
   boucle `%%lestisamopal`, sans saut de position.
4. Repasser près des acteurs après la conversation : aucun second dialogue ni
   empilement d'animation.
5. Déclencher chaque famille d'alarme avant le dialogue, pendant le dialogue et
   entre la dernière réplique et le signal 3.
6. Tester la mort de chacun des deux interlocuteurs pendant l'échange.
7. Tester les branches solo/Lone Wolf et les sorties en BMW déjà présentes.
8. Sauvegarder/reprendre avant activation, pendant le dialogue et après reprise.

Acceptation : la reprise n'a lieu qu'après la conversation normale, l'alarme
garde toujours priorité et aucune animation ne redémarre sur un acteur déplacé,
armé, mort ou dont le script est terminé.

Cette liste ne maintient aucun chantier expérimental : une anomalie observée
doit être traitée comme régression du raccord stable, sans réintroduire la
variante assise abandonnée.

## Sources internes

- `.analysis/scripts/sabre/Scripts/burgundy2/ge_motorka.scr`
- `.analysis/scripts/sabre/Scripts/burgundy2/ge_dilna.scr`
- variantes de mise en scène dans
  `.analysis/scripts/sabre/Scripts/co_burgundy2/`
