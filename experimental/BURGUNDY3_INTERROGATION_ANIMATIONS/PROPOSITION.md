# Proposition expérimentale — phases visuelles du dialogue Burgundy 3

État : reconstruction visuelle non intégrée, 14 septembre 2026. Les variantes
solo et coopérative sont étudiées ensemble, mais conserveraient chacune leur
propre override. Aucun objectif ni script actif n'est modifié.

## Classification

**Dialogue officiel actif, commandes visuelles orphelines.**
`bur3_rozhovor.scr` joue bien les dix-neuf répliques 59990001 à 59990019 entre
`bur03_20` et `bur03_sas02`. Il diffuse aussi huit signaux, mais aucun des deux
scripts participants ne contient de `OnSignal`.

La parole n'est donc pas du contenu dormant. La perte concerne uniquement la
chorégraphie synchronisée que suggèrent les signaux 10 à 17. Les corps exacts
des huit handlers ne sont conservés dans aucune variante.

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Texte, voix et ordre | 4/4 | séquence complète et active dans les deux variantes |
| Contrat des huit signaux | 4/4 | mêmes destinataires et même ordre solo/coop |
| Découpage en quatre phases | 3/4 | structure régulière par paires consécutives |
| Animations exactes | 1/4 | aucun récepteur historique retrouvé |
| Modèle gestuel générique | 3/4 | handlers voisins 10/11/12 dans la même mission |

## Séquence officielle

Les signaux forment quatre paires, chacune distribuée entre le prisonnier SAS
et l'interrogateur allemand :

| Phase | Signal SAS | Moment | Signal allemand | Moment |
| ---: | ---: | --- | ---: | --- |
| 1 | 10 | avant les répliques allemandes 1–5 | 11 | avant la réponse SAS 6 |
| 2 | 12 | avant les répliques allemandes 7–9 | 13 | avant les réponses SAS 10–12 |
| 3 | 14 | avant les répliques allemandes 13–14 | 15 | avant la réponse SAS 15 |
| 4 | 16 | avant les répliques allemandes 16–18 | 17 | avant la réponse SAS 19 |

Cette alternance montre des transitions de posture ou de réaction plutôt que le
protocole ordinaire « début de parole / arrêt ». Chaque acteur reçoit en effet
un nouveau numéro au moment où il devient auditeur de l'autre.

## Solo et coopération

Les deux variantes conservent exactement les mêmes répliques et la même suite
10–17. Leur environnement d'exécution diffère :

- en solo, le déclencheur est à 3 unités après un délai de 5 secondes, les
  sous-titres sont explicitement activés et le watcher de mort inclut aussi
  `bur03_21` ;
- en coopération, le déclencheur est à 7 unités, la conversation peut recevoir
  un signal 1 d'interruption de `bur3_20`, et le watcher de mort termine le
  script ;
- `bur3_20` et `bur3_sas02` ont des rayons d'activation et des responsabilités
  d'objectif différents entre solo et coop.

Les handlers visuels proposés doivent être identiques dans leur intention mais
ajoutés séparément aux quatre scripts participants. Copier tout le fichier solo
sur la coop, ou l'inverse, détruirait des comportements de mission valides.

## Modèle Sabre comparable

Dans Burgundy 3, `bur3_06.scr`, `bur3_22.scr` et `bur3_23.scr` fournissent le
modèle de conversation le plus proche :

- signal 10 : choix d'une animation parmi `%%rozhovor2`, `%%rozhovor3` et
  `%%rozhovor4` ;
- signal 11 : effacement de l'animation ;
- signal 12 : retour vers `ACTIVITY`.

Les dialogues `bur3_rozhovor02.scr` et `bur3_rozhovor03.scr` utilisent ce
protocole classique. Aucun script Sabre ne reproduit toutefois la séquence en
quatre paires 10/11, 12/13, 14/15 et 16/17.

Ce modèle atteste le vocabulaire gestuel et les fondus à 100 ms, pas la table
exacte du dialogue d'interrogatoire.

## Contraintes propres aux deux acteurs

### `bur3_20`

L'Allemand est debout, suspendu avant activation et ne possède aucune animation
d'activité particulière. Son label `ACTIVITY` aboutit à `END` en solo ; en coop
il boucle sur lui-même et ne doit donc jamais servir de destination à un nouveau
handler. Ses alarmes peuvent le déplacer vers `20_saskill`, attaquer le
prisonnier puis terminer le script.

Les trois animations génériques de conversation sont compatibles avec sa
posture, mais leur ordre par phase est une reconstruction.

### `bur3_sas02`

Le prisonnier est activé avec l'animation assise officielle
`%%kucasedi.i3d`. Ses scripts pilotent aussi la survie et les objectifs de
prisonniers. Aucune animation de conversation assise distincte n'est utilisée
ailleurs dans Burgundy 3.

Appliquer `%%rozhovor2/3/4`, prévues pour des acteurs debout dans les analogues,
pourrait casser sa pose ou sa position. Le premier prototype doit donc seulement
réaffirmer sa pose assise aux quatre transitions.

## Handlers expérimentaux proposés

### Prototype A — sécurité et synchronisation

Pour `bur3_20`, utiliser trois gestes officiels puis revenir à la pose moteur :

```text
OnSignal(11) { HUMAN_SetAnim("%%rozhovor2", 100, 100, true); goto END; }
OnSignal(13) { HUMAN_SetAnim("%%rozhovor3", 100, 100, true); goto END; }
OnSignal(15) { HUMAN_SetAnim("%%rozhovor4", 100, 100, true); goto END; }
OnSignal(17) { HUMAN_SetAnim("",             100, 100, false); goto END; }
```

Pour `bur3_sas02`, préserver la seule posture assise attestée :

```text
OnSignal(10) { HUMAN_SetAnim("%%kucasedi.i3d", 100, 100, true); goto END; }
OnSignal(12) { HUMAN_SetAnim("%%kucasedi.i3d", 100, 100, true); goto END; }
OnSignal(14) { HUMAN_SetAnim("%%kucasedi.i3d", 100, 100, true); goto END; }
OnSignal(16) { HUMAN_SetAnim("%%kucasedi.i3d", 100, 100, true); goto END; }
```

Ce prototype rend les huit commandes observables et donne quatre états visuels
à l'Allemand sans déplacer les acteurs. Il ne prétend pas restaurer les gestes
originaux du SAS. L'ordre `rozhovor2/3/4` est une **INFÉRENCE VISUELLE**.

### Prototype B — quatre poses réellement distinctes

N'essayer une chorégraphie plus riche qu'après avoir inventorié les animations
compatibles avec le squelette assis de `bur3_sas02`. Chaque paire doit alors
être considérée comme une phase complète : pose du SAS au début, puis réaction
de l'Allemand avant la réponse suivante.

Les candidats doivent provenir d'assets réellement chargés par Burgundy 3 et
être testés isolément. Une animation debout générique ne doit jamais être
assignée au prisonnier uniquement pour rendre les phases différentes.

## Ce que les handlers ne doivent pas faire

- ne modifier aucun statut ou signal d'objectif ;
- ne changer ni les dix-neuf appels de voix, ni leur ordre, ni leurs portées ;
- ne déplacer, tourner ou désuspendre les acteurs ;
- ne réactiver aucun acteur après `OnAlarm` ou `OnDeath` ;
- ne remplacer aucune logique solo par sa variante coopérative ;
- ne corriger dans ce lot ni le rayon de déclenchement, ni la répétabilité du
  `Whenever` de conversation.

## Protocole de test

1. Enregistrer une baseline vidéo solo et coop : positions, poses, voix et ordre
   exact des huit signaux.
2. Tester chaque animation candidate sur une copie isolée de chaque acteur,
   avant de raccorder le dialogue complet.
3. Vérifier les quatre phases et le fondu à chaque transition, sans glissement
   de position du prisonnier.
4. Déclencher une alarme pendant chacune des quatre phases ; l'alarme et la
   protection des objectifs doivent toujours avoir priorité.
5. Tuer `bur03_20`, `bur03_sas02` et, en solo, `bur03_21` à différents moments ;
   aucune animation ou voix ne doit continuer.
6. En coop, déclencher le signal 1 d'interruption de la conversation pendant
   chaque phase.
7. Sortir puis revenir dans le rayon après la réplique 19 afin de vérifier que
   les handlers n'aggravent pas une éventuelle répétition du dialogue.
8. Sauvegarder/reprendre avant le déclenchement, pendant chaque phase et après
   la dernière réponse, dans les modes qui l'autorisent.

Acceptation : les dix-neuf voix et tous les objectifs restent inchangés, les
transitions sont visuellement stables, le SAS demeure assis et toute alarme,
mort ou interruption coupe proprement la scène.

## Verdict

Les huit signaux attestent quatre phases visuelles perdues, mais aucune table
d'animations exacte n'a survécu. Le prototype A est une reconstruction prudente
fondée sur les animations officielles de la mission : gestes génériques pour
l'Allemand, maintien de la pose assise pour le SAS. Il doit rester expérimental
et être validé séparément en solo et en coopération.

## Sources internes

### Réalisation solo du 26 septembre 2026

`burgundy3-interrogation-visual-phases` reconstruit atomiquement les trois
scripts solo à partir de Sabre, avec neuf sources épinglées. Ce profil **MODERNE**
n'est pas le [profil coop séparé](COOPERATION.md) : le registre coop et les quatre scripts
participants ne sont pas interchangeables.

| Script | Source → variante, octets | SHA-256 source |
|---|---:|---|
| `bur3_20.scr` | 1554 → 3162 | `8dad418c41e59e7c486cff2c8f8526c7051e6f049a5d99b6dc94dec893920f45` |
| `bur3_sas02.scr` | 1757 → 3151 | `6c96d54090d36bd357be0e0de7d95e5534027885eed5f509128fd274d7dab5a9` |
| `bur3_rozhovor.scr` | 3824 → 3918 | `dbd0af922abbab3d7a75cb3aeaba22f2cd7886b10ec278440f61ee4fbff7f3a7` |

Chaque récepteur garde une phase locale et n'accepte que l'étape suivante quand
les deux acteurs sont vivants. Les signaux du SAS réaffirment seulement son
assise commerciale; le garde emploie `rozhovor2`, `rozhovor3`, `rozhovor4`, puis
efface son animation. Les trois scripts voisins attestant ces gestes sont
conservés comme preuves, sans être modifiés.

Les nouveaux signaux visuels sont désactivés avant l'alarme/mort du garde,
avant les objectifs de mort du SAS et avant ses voix de libération à quatre
mètres. Ainsi les récepteurs ajoutés ne doivent pas détourner ces séquences.
Le contrôleur emploie le signal **moderne 99** après la réplique 19 et au début
du watcher de mort pour fermer les récepteurs; ce numéro est absent des scripts
commerciaux de cette mission. Il efface un geste du garde encore en cours mais
ne relève pas le SAS de sa pose commerciale. Aucun nouveau signal d'objectif.

Les dix-neuf appels de voix, les huit émissions historiques, les rayons, les
délais et la progression demeurent inchangés. Le profil ne corrige pas la
répétabilité éventuelle de la conversation commerciale. La priorité réelle des
handlers, les signaux retardés, la sauvegarde et la pose assise sont à vérifier
en moteur, pas déduits des tests du générateur.

- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_rozhovor.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_20.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_sas02.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy3/bur3_rozhovor.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy3/bur3_20.scr`
- `.analysis/scripts/sabre/Scripts/Co_Burgundy3/bur3_sas02.scr`
- `bur3_rozhovor02.scr`, `bur3_rozhovor03.scr`, `bur3_06.scr`, `bur3_22.scr`
  et `bur3_23.scr` comme analogues locaux
