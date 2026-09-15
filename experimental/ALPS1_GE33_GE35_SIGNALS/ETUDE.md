# Étude expérimentale — signaux manquants de ge33/ge35 dans Alps 1

État : intention attestée, comportements manquants. Étude statique du
14 septembre 2026. Aucun handler n'est proposé à l'intégration, même
expérimentale, faute d'un corps analogue assez précis.

## Synthèse

| Récepteur | Signal | Émetteur(s) officiel(s) | Verdict |
| --- | ---: | --- | --- |
| `ge_33` | 3 | `signal_k_ohni`, `ge_34` lorsqu'il voit le joueur | intention attestée, comportement manquant |
| `ge_35` | 3 | `signal_k_ohni`, `signal_ke_strelnici` | intention attestée, comportement manquant |
| `ge_35` | 4 | `ge_36` sur alarme | intention attestée, comportement manquant |

Les trois chaînes ont un émetteur et un destinataire officiels. Elles n'ont
cependant ni handler conservé, ni commentaire donnant l'action exacte, ni
variante d'archive qui permette de la recopier.

## Chaîne du feu — signal 3

`signal_k_ohni.scr` reçoit son signal d'activation puis envoie le signal 3 à
`ge_33`, `ge_34` et `ge_35`, en même temps qu'un signal de coordination au
temporisateur du conducteur.

Seul `ge_34.scr` possède le récepteur 3. Son corps est entièrement propre à sa
mise en scène : il modifie un type d'alarme, téléporte le gobelet `hrnek` sur
`ge34poloz`, puis retourne au label `sedim`, qui déroule les animations assises
et les manipulations du gobelet.

Ce handler prouve que le signal 3 interrompait ou réorganisait les scènes près
du feu. Il ne fournit aucune action réutilisable pour ge33 ou ge35 : ceux-ci ne
possèdent ni le gobelet, ni `ge34poloz`, ni le label `sedim`.

## ge33 — deux émissions, aucune réaction conservée

`ge_33.scr` ne traite que le signal 1, qui le réveille et lance l'animation
`%%sedimtak`. Sa scène de proximité arrête cette animation, effectue une longue
ronde `ge33_01` à `ge33_07`, puis le replace assis. Son `OnAlarm()` désactive les
signaux, arrête l'animation, arme l'acteur et termine le script.

Le signal 3 lui est envoyé :

- par `signal_k_ohni`, avec les deux autres hommes de la scène du feu ;
- par `ge_34` dans `OnAlarm()` uniquement lorsque son type d'alarme vaut 32.

**INFÉRENCE forte.** ge33 devait abandonner sa scène assise ou réagir à une
alerte née chez ge34.

**COMPORTEMENT MANQUANT.** Rien n'indique s'il devait seulement arrêter son
animation, s'armer, rejoindre un checkpoint, reproduire son `OnAlarm()`, ou
continuer sa ronde dans un état modifié. Appeler `OnAlarm()` n'est pas une
option neutre : ce corps lit `_GetAlarmType()` et termine définitivement le
script.

## ge35 — deux signaux distincts vers une logique sensible

`ge_35.scr` commence suspendu avec les événements humains désactivés. Son signal
1 n'effectue pas de déplacement : il active les événements et ajuste les types
d'alarme. Son `OnAlarm()` compte les alertes 2 et 256 jusqu'à un seuil de trois,
ou huit dans les modes 3/7, tandis qu'une explosion 16 saute immédiatement vers
`hotovo`.

Le label `hotovo` a des effets majeurs : arrêt des signaux et événements,
arrêt des conversations, choix de cinématiques, signaux vers ge36/ge37 ou échec
d'objectif selon l'état du téléphone et d'autres valeurs de jeu.

Trois émissions restent sans récepteur :

- `signal_k_ohni` envoie 3 à ge35 ;
- `signal_ke_strelnici` envoie aussi 3 à ge35 ;
- `ge_36` envoie 4 à ge35 dès son propre `OnAlarm()`.

**INFÉRENCE plausible.** Ces signaux pouvaient avertir directement le
« bonzak » et raccourcir ou achever son compteur d'alarme.

**Risque critique.** Ajouter `goto hotovo` à 3 et 4 déclencherait potentiellement
une cinématique ou un échec sans respecter les seuils, y compris avant que le
signal 1 ait activé l'écoute. Incrémenter `b` ou `c` imposerait arbitrairement
une catégorie d'alarme. Activer seulement les événements pourrait au contraire
être insuffisant. Aucun de ces choix n'est prouvé.

## Analogues étudiés

Le même `signal_ke_strelnici` envoie 3 à `ge_30`, `ge_31` et `ge_32`. Leurs
handlers sont tous des réactions d'alarme, mais chacun contient sa route et sa
posture propres : `ge30_06`, `ge31_05` ou `ge32_03`, avec des combinaisons
différentes d'armes, de mode et de suspension. Ils confirment la famille
fonctionnelle « alerte », pas le corps de ge35.

`ge_34` fournit de son côté un analogue exact seulement pour sa propre scène du
gobelet. Les scripts homonymes trouvés dans Castle 1 appartiennent à une autre
mission et à d'autres trajets. Aucune seconde copie **commerciale** Patch ou
Sabre des scripts Alps 1 ciblés n'a été retrouvée.

Le CMP public 2.6.5 contient une conversion `co_alps1`, mais pas les corps
recherchés. Elle conserve `signal_k_ohni` et ses envois 3 vers ge33/ge34/ge35,
alors que ses trois récepteurs ne gèrent plus 3. Elle retire entièrement
`signal_ke_strelnici` et retire l'envoi 4 de ge36 vers ge35. Cette conversion
tolère ou élimine les no-op selon les besoins coop ; elle ne constitue donc pas
une source du comportement solo perdu.

## Reconstitution comportementale prudente — sans corps exécutable

La lecture complète des routes réduit l'enveloppe des comportements, sans
permettre un handler fidèle :

- **ge33 / signal 3** doit au minimum interrompre ou reconfigurer la scène
  assise. Cependant `signal_k_ohni` utilise 3 pour synchroniser la scène du feu,
  tandis que ge34 utilise le même numéro après avoir vu le joueur. Chez ge34,
  3 replace le gobelet puis retourne à `sedim`, et non au combat. Copier le
  `OnAlarm()` de ge33 armerait donc peut-être un acteur qui devait seulement se
  rasseoir ; copier son signal 1 relancerait peut-être une scène qui devait être
  interrompue.
- **ge35 / signal 3** arrive deux secondes après l'activation de la zone de tir
  et dix secondes après celle du feu. L'effet probable est une notification au
  « bonzak » avant les autres acteurs, mais le script ne dit pas si elle
  incrémentait `b`, `c` ou sautait à `hotovo`.
- **ge35 / signal 4** vient exclusivement du `OnAlarm()` de ge36, avant que ce
  conducteur ne poursuive sa propre fuite. Son numéro distinct indique une
  catégorie différente de la notification 3 ; il ne justifie donc ni un alias,
  ni un `goto hotovo` partagé.

Ces contraintes sont suffisamment fortes pour rejeter les copies naïves, mais
pas pour choisir un effet. Le résultat de la reconstruction est donc un
**contrat probable**, pas un prototype : 3 coordonne les scènes feu/stand et 4
relaie l'alarme du conducteur ; leurs mises à jour exactes ont disparu.

La recherche dans les archives commerciales n'a livré aucune autre version. La
conversion coopérative publique décrite plus haut est un remaniement et non une
copie historique ; elle ne change pas la porte de réouverture ci-dessous.

## Décisions de non-reconstruction

Aucun de ces ajouts ne doit être produit sans nouvelle source :

- copier le handler 3 de ge34 dans ge33/ge35 ;
- copier les routes de ge30–32 ;
- faire sauter ge35 directement vers `hotovo` ;
- transformer le signal 4 de ge36 en type d'alarme arbitraire ;
- recopier le corps de `OnAlarm()` dans un handler ;
- utiliser le seul réveil du signal 1 comme réponse universelle.

Les émissions sont conservées telles quelles. Les handlers 3/4 restent classés
**« intention attestée, comportement manquant »**. Tout handler créé sans
nouvelle source devra porter la mention **RECONSTRUCTION MODERNE**, même s'il
réutilise une primitive ou un checkpoint officiel.

## Porte de réouverture et tests de constat

Une ancienne version doit idéalement apporter un handler exact, ou au minimum
un commentaire reliant chaque signal à un label ou à un type d'alarme. Une
trace de scène/waypoints peut compléter cette preuve mais ne remplace pas le
contrat scripté.

En laboratoire, sans ajout de handler :

1. tracer les émissions de `signal_k_ohni`, `signal_ke_strelnici` et ge36 ;
2. relever l'état suspendu, l'animation, les événements et les compteurs de
   ge33/ge35 avant et après chaque signal ;
3. tester chaque ordre d'activation par signal 1 puis signal 3/4 ;
4. déclencher les alarmes 2, 16 et 256 avant/après les signaux ;
5. vérifier les cinématiques, le téléphone, l'objectif et les conversations ;
6. sauvegarder/reprendre à chaque transition.

Le test peut démontrer une rupture observable. Il ne doit pas être utilisé pour
choisir empiriquement une cinématique ou une route sans source.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/signal_k_ohni.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/signal_ke_strelnici.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_30.scr` à `ge_36.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/ridiccasovac.scr`
- CMP public 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`,
  `Scripts/co_alps1/`
