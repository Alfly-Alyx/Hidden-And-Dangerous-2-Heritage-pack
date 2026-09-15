# Proposition expérimentale — handlers d'activation manquants d'Africa 5

État : **`AF4_sklad04` retiré du périmètre expérimental après promotion
stable ; seul `AF4_43` reste à étudier**, 14 septembre 2026. Les scripts
directement concernés ont le même contenu normalisé dans Base et Patch ; les
octets diffèrent à cause des fins de ligne. Aucun script actif n'est modifié
par ce dossier.

## Classification générale actualisée

L'audit initial avait relevé deux sous-systèmes envoyant encore des signaux vers
des acteurs suspendus dont le label `ACTIVATE` subsiste, mais dont le
`OnSignal` correspondant avait disparu :

| Récepteur | Émetteur | Signal | Statut actuel |
| --- | --- | ---: | --- |
| `AF4_sklad04` | `AF4_sklad_activator` | 1 | **traité dans le lot stable ; hors créations expérimentales** |
| `AF4_43` | `AF4_44` et `AF4_49` en alarme | 5 | **expérimental ; comportement d'alarme non prouvé** |

Le signal 1 du magasin appartient à une activation groupée de sept hommes et
son corps exact a pu être établi par comparaison directe. Le signal 5 vise
probablement à propager une alerte avant que le joueur n'entre dans le
détecteur de proximité du garde 43, mais aucun corps exact n'est encore prouvé.

## Cas clos — mécanicien `AF4_sklad04`

### Preuves

`AF4_sklad_activator.scr` recherche `AF4_sklad01` à `AF4_sklad07` et leur
envoie le signal 1 lors de son `OnUse` s'ils sont vivants. Le code bascule la
porte puis diffuse les sept signaux sans condition sur le nouvel état : en
pratique, une fermeture ultérieure peut donc réémettre le signal.

Six des sept scripts traitent le signal 1 et rejoignent `ACTIVATE`. Seul
`AF4_sklad04.scr` n'a aucun `OnSignal`, alors qu'il conserve :

- un état initial suspendu et tous les types d'alarme désactivés ;
- un label `ACTIVATE` qui le réveille, optimise l'IA, impose garde/debout puis
  tombe dans `ACTIVITY` ;
- une activité `%%mechanik` ;
- un détecteur joueur à 20 unités, plus riche, qui active les alarmes, déplace
  l'acteur vers `AF4_sklad04_01`, le tourne et lance `!manipul1`.

Les voisins 02, 03, 05, 06 et 07 exécutent tous
`SetAlarmType(2, true)` dans leur handler 1 avant `goto ACTIVATE`. Le voisin 01
a déjà ses alarmes actives à l'initialisation et n'a pas besoin de cette ligne.
Les handlers 1 et leurs labels d'activation sont sémantiquement identiques entre
Base et Patch ; la seule variation de `AF4_sklad01` supprime un son joué une fois
et n'affecte pas cette comparaison.

La comparaison directe permet le raccord exact désormais retenu par le lot
stable :

```diff
+OnSignal(1)
+{
+  SetAlarmType(2, true);
+  goto ACTIVATE;
+}
```

`AF4_sklad04` n'est donc plus une création, une variante graduée ni un travail
spéculatif de ce dossier. Les anciens essais « réveil seul » sont retirés : ils
ne correspondent pas au corps commun démontré. Les validations de porte,
d'alarmes, de répétition et de sauvegarde relèvent désormais du lot stable.

## Cas B — garde `AF4_43`

### Preuves

`AF4_44.scr` et `AF4_49.scr` recherchent tous deux `AF4_43` et lui envoient le
signal 5 dès leur `OnAlarm`. Six scripts traitent par ailleurs ce signal :
`AF4_40`, `AF4_41`, `AF4_42`, `AF4_44`, `AF4_45` et `AF4_49`. Le groupe
40–42 se notifie mutuellement et rejoint ses routes d'alarme — les trois passent
même par l'acteur `AF4_42_ad`. Les acteurs 44 et 49 notifient 43, puis chacun
rejoint son propre `ALARMDONE` et sa propre route ; 45 possède encore une route
distincte. Ces handlers attestent qu'un signal 5 peut lancer une route de combat,
mais aucun ne fournit un corps exact pour 43 : son script ne contient ni label
`ALARMDONE`, ni destination de route à reprendre.

`AF4_43.scr` ne possède aucun `OnSignal`. Il commence suspendu, avec les alarmes
1023 actives, et son détecteur joueur à 15 unités rejoint `ACTIVATE`. Ce label :

- lève la suspension ;
- règle l'optimisation à 1 ;
- place l'acteur debout ;
- le tourne vers le joueur ;
- rejoint `END`.

Son `OnAlarm` contient déjà le véritable comportement d'alerte : réveil,
portée de vue 200, optimisation 0, lecture du type d'alarme, puis fin de script.
Le recopier dans un handler 5 risquerait de dupliquer l'événement moteur ou de
terminer le script sans type d'alarme valide.

### Prototype minimal

Après une baseline hors du rayon de 15 unités :

```diff
+OnSignal(5)
+{
+  goto ACTIVATE;
+}
```

Cette version restaure uniquement la propagation de réveil. Comme les alarmes
sont déjà actives chez 43, elle permet d'observer si le moteur lui distribue
ensuite l'état d'alarme global. Elle n'appelle pas artificiellement `OnAlarm` et
n'invente aucun déplacement.

Si le réveil seul laisse 43 actif mais indifférent au combat déjà déclenché,
arrêter l'essai et relever son état moteur. Une seconde reconstruction pourrait
reprendre certains réglages visuels du préambule d'alarme, mais elle ne doit pas
être écrite avant de savoir quel type d'alarme et quelle destination étaient
attendus.

### Tests

1. Déclencher séparément l'alarme de 44 puis celle de 49 alors que le joueur
   reste à plus de 15 unités de 43.
2. Vérifier si 43 se réveille déjà sans handler ; dans ce cas, classer les
   signaux 5 comme redondants et abandonner la reconstruction.
3. Avec le prototype, relever suspension, optimisation, posture, orientation,
   portée de vue et entrée éventuelle dans `OnAlarm`.
4. Répéter quand 43 a déjà été activé par proximité, puis dans l'ordre inverse.
5. Provoquer les deux alarmes presque simultanément ; le double signal ne doit
   pas relancer ou corrompre l'acteur.
6. Tester mort de 43, 44 ou 49 avant l'émission et sauvegarde/reprise autour du
   premier signal.

Acceptation : 43 est réveillé au plus une fois, sa proximité reste fonctionnelle
et aucune fausse alarme, route ou fin de script n'est ajoutée.

## Alternatives rejetées

- copier le détecteur de proximité complet dans l'un des handlers : il invente
  mouvements, alarmes et animations non attestés par le signal ;
- appeler ou reproduire directement `OnAlarm` : le type d'événement n'est pas
  porté par le signal ;
- recopier l'un des six handlers 5 chez 43 : le label `ALARMDONE` n'existe pas
  chez lui et les routes observées sont propres à deux groupes d'alerte ou à
  leurs checkpoints ;
- supprimer les signaux émetteurs parce que la proximité peut être suffisante :
  leur présence officielle atteste au minimum une intention de propagation ;
- intégrer le prototype `AF4_43` au stable avant sa baseline correspondante.

## Verdict

Le cas `AF4_sklad04` est résolu hors de ce dossier par le handler 1 commun au
groupe et ne figure plus dans la charge expérimentale. Pour `AF4_43`, le réveil
seul demeure le seul premier essai acceptable ; toute simulation d'alarme exige
des preuves supplémentaires. **Seul `AF4_43` reste expérimental.**

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_sklad_activator.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_sklad01.scr` à
  `AF4_sklad07.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_43.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_40.scr` à `AF4_45.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_49.scr`
- copies sémantiquement équivalentes directement concernées sous
  `.analysis/scripts/patch/SCRIPTS/AFRICA5/`
