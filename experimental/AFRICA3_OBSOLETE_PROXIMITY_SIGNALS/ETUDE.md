# Étude expérimentale — faux positifs de signaux de proximité d'Africa 3

État : analyse statique, 14 septembre 2026. Aucun handler ni prototype n'est
ajouté. Ces arêtes du graphe sont classées **obsolètes ou remplacées**, pas
comme du contenu à restaurer.

## Verdict synthétique

| Émetteur | Signal sans handler | Mécanisme actif conservé | Verdict |
| --- | ---: | --- | --- |
| `AF3a_16_activator` | 1 vers AF3a_16 à 20 m | AF3a_16 démarre directement sur `START`/`ACTIVITY` | ancien réveil devenu inutile |
| `AF3a_25_detector` | 10 vers AF3a_25 à 8 m | AF3a_25 rejoint `ACTIVATE` par son propre Whenever joueur à 15 m | détecteur externe remplacé |
| `AF3a_doctor_activator` | 16 vers médecin et AF3a_19 à 20 m | proximité autonome à 40/30 m | activation externalisée obsolète |
| `AF3a_doktor_detector` | 16 vers patient et médecin à 2 m | patient autonome à 30 m ; médecin possède son échange autonome à 2 m | détecteur d'entrée remplacé |

## AF3a_16 : commentaire périmé, acteur déjà actif

`AF3a_16_activator.scr` se décrit comme le script qui « unsuspends » AF3a_16
et lui envoie le signal 1 lorsque le joueur entre à vingt mètres. AF3a_16 ne
possède pourtant aucun `OnSignal(1)`, n'appelle pas `HUMAN_Suspend(true)` dans
son initialisation et exécute directement `START`, puis sa boucle `ACTIVITY`.

Ajouter un handler 1 ne restaurerait donc aucune étape manquante : le soldat
est déjà réveillé. Le Patch ajoute seulement un label `END2` vide au script
acteur ; cela ne change pas ce constat.

## AF3a_25 : le réveil est déjà autonome

`AF3a_25_detector.scr` envoie le signal 10 à huit mètres. AF3a_25 n'a pas de
handler 10, mais il se suspend à l'initialisation puis possède son propre
`Whenever player (_PlayerInRange(15))`, qui rejoint `ACTIVATE`, le réveille et
le tourne vers le joueur.

Les rayons 8 et 15 ne prouvent pas une équivalence historique exacte. Ils
prouvent en revanche que le comportement requis — sortir AF3a_25 de suspension
à l'approche — dispose déjà d'une voie active. Ajouter `OnSignal(10)` créerait
un second déclencheur concurrent, sans effet nouveau attesté.

## Groupe médecin : quatre signaux 16 remplacés par des Whenevers

`AF3a_doctor_activator` envoie 16 au médecin et à l'opérateur radio AF3a_19 à
vingt mètres. `AF3a_doktor_detector` envoie 16 au patient et au médecin à deux
mètres. Aucun des trois récepteurs ne traite 16.

Leurs scripts actuels possèdent déjà leurs propres seuils :

- le médecin se réveille à quarante mètres et se resuspend hors de portée ; à
  deux mètres, son Whenever `blizko` joue l'échange avec le joueur puis reprend
  la séquence de soin ;
- AF3a_19 sort de suspension à trente mètres et possède une seconde réaction à
  dix mètres pour sa transmission radio ;
- le patient sort de suspension au moyen de son Whenever à trente mètres.

Le Patch renforce encore l'autonomie du médecin en le désuspendant lors de la
mort du patient, de l'alarme et au label `ACTIVITY`. Rien ne suggère qu'un
handler 16 supplémentaire soit encore requis.

## Confirmation CMP et règle d'audit

CMP 2.6.5 conserve les quatre émetteurs et leurs bindings, mais n'ajoute aucun
handler correspondant aux acteurs. Cette conservation mécanique ne transforme
pas les signaux en fonctionnalité manquante.

Règle retenue : lorsqu'un commentaire d'activator annonce un réveil, vérifier
d'abord l'état initial du récepteur et ses Whenevers autonomes. Si la transition
est déjà atteinte sans signal, classer l'arête comme **obsolète/remplacée**. Ne
pas créer de handler uniquement pour satisfaire le graphe statique.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_16_activator.scr`
- scripts Base/Patch `AF3a_16.scr`, `AF3a_25_detector.scr`, `AF3a_25.scr`
- scripts Base/Patch `AF3a_doctor_activator.scr`,
  `AF3a_doktor_detector.scr`, `AF3a_doktor.scr`, `AF3a_19.scr` et
  `AF3a_pacient02.scr`
- `.analysis/signal-graph-current.md` et `.analysis/signal-graph-current.json`
- CMP 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`
