# Proposition expérimentale — annulation du danger d'alarme dans Alps 2

État : étude révisée le 14 septembre 2026, sans prototype exécutable. Aucun
script commercial n'est modifié. La désactivation de `mamete` est évaluée comme
reconstruction minimale plausible, distincte d'une restauration attestée.

## Synthèse

| Cas | Intention | Base comportementale | Verdict |
| --- | ---: | ---: | --- |
| `AL2_alarm` / `_carn` reçoit 1 | 4/4 | 3/4 | reconstruction minimale plausible, non attestée |
| `AL2_alarm_carn` → `AL2_35` signal 2 | 1/4 | 0/4 | probablement résidu ; ne pas restaurer |
| `AL2_01_A1` → `AL2_01` signal 1 | 2/4 | 0/4 | branche incomplète et coupée ; ne pas restaurer |

## Cas principal — signal 1 vers `AL2_alarm`

### Preuve officielle de l'intention

Dans la version effective Patch de `AL2_01.scr`, le gestionnaire du signal 8
joue l'interaction de la porte secrète puis exécute :

```text
SendSignal(alarm, 1);  // zrus nebezpecie alarmu
```

Le commentaire signifie « annuler/supprimer le danger de l'alarme ». La frame
`alarm` est résolue vers `AL2_alarm`. Le même envoi et le même commentaire sont
présents dans la version Base.

Selon le mode de jeu, `setobjectives.scr` laisse `AL2_alarm.scr` actif ou
réassigne la frame à `AL2_alarm_carn.scr`. Les deux contrôleurs doivent donc
comprendre le même protocole d'annulation pour que le signal fonctionne dans
tous les modes concernés.

### État des deux contrôleurs

Les deux scripts ne gèrent que :

- le signal 5 dans le Whenever `mamete`, commenté « joueur découvert avant de
  prendre les documents » ; il envoie le signal d'échec critique 3 au
  contrôleur d'objectifs ;
- le signal 6 dans `alarmarchive`, qui lance l'alarme de l'archive et sa grande
  cascade d'acteurs.

Au début du traitement du signal 6, les deux variantes exécutent :

```text
SetWhenever(mamete, 0);
```

La variante carnage ajoute aussi la valeur de jeu 30 et diffère dans les
acteurs alertés, mais la désactivation de `mamete` est commune.

**INFÉRENCE forte.** Une fois la porte secrète ouverte et l'interaction validée,
le danger spécifique « découvert avant de prendre les documents » ne doit plus
rester armé. Désactiver `mamete` est l'effet conservé le plus proche du
commentaire, sans déclencher l'alarme, sans réveiller d'acteur et sans modifier
un objectif.

## Recherche de variante et retrait du delta

La variante coopérative publique `co_alps2` conserve les mêmes trois ruptures :

- `AL2_01_A1` reste désactivé et ne s'arme que par son propre signal 1 ;
- `AL2_01` ne reçoit toujours que 4, 6 et 8 ;
- `AL2_alarm` n'ajoute aucun signal 1, et `al2_35` ne reçoit que 1.

Les révisions publiques survivantes de 2021, 2022 et actuelle ne fournissent
aucun ancien corps. Sources : [AL2_01_A1](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/co_alps2/AL2_01_A1.scr),
[AL2_01](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/co_alps2/AL2_01.scr),
[AL2_alarm](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/co_alps2/AL2_alarm.scr),
[al2_35](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/co_alps2/al2_35.scr).

La désactivation de `mamete` reste l'interprétation la plus proche du
commentaire et réemploie une instruction officielle du signal 6. La plus petite
maquette concevable pour chacune des deux variantes serait :

```text
Whenever cancel_danger(_SignalReceived(1))
{
  SetWhenever(mamete, 0);
  GoTo end;
}
```

Il s'agit d'une **RECONSTRUCTION MINIMALE 3/4**, pas d'une restauration : le
signal, le commentaire, le watcher et l'instruction qui le désactive sont
officiels, mais aucune source ne prouve que l'ancien handler se limitait à ces
deux lignes. Aucun fichier `.scr.disabled` n'est créé tant qu'une observation
dynamique n'établit pas un défaut perceptible.

### Données manquantes et risques

- corps exact, nom du Whenever et ordre original des opérations ;
- éventuelle mise à jour d'un objectif, d'une valeur de jeu ou d'un son ;
- comportement lorsque l'échec par signal 5 a déjà été envoyé ;
- priorité si les signaux 1, 5 et 6 arrivent au même tick ;
- persistance de l'état de `mamete` après sauvegarde/reprise.

Le raccord ne doit ni annuler rétroactivement un échec, ni interrompre la
cascade du signal 6. S'il faut ajouter un second effet pour satisfaire le test,
la base comportementale retombe à 1/4 et la maquette doit être abandonnée.

## Non-restauration 1 — signal 2 vers AL2_35 en carnage

`AL2_alarm_carn.scr` contient simultanément :

```text
//al2_35 v carnage disabled
SendSignal(al2_35, 2);
```

`setobjectives.scr` ne remplace pas le script d'AL2_35 en carnage et commente
explicitement qu'il n'existe pas dans ce mode. Le script normal `al2_35.scr`
teste les modes 3/7, désactive ses signaux et se suspend. Il ne possède aucun
récepteur 2.

**Verdict.** L'envoi est probablement un résidu inoffensif vers un acteur
neutralisé. Ajouter un handler 2 contredirait le commentaire et réintroduirait
potentiellement un personnage que le mode carnage retire. Aucun delta.

## Non-restauration 2 — `AL2_01_A1` vers AL2_01

`AL2_01_A1.scr` définit un volume à trois unités qui envoie le signal 1 à
AL2_01, mais son Whenever spatial `player` est désactivé au démarrage. Il ne se
réactive qu'après réception d'un autre signal 1 par l'activateur. Le script
d'AL2_01 ne gère pour sa part que 4, 6 et 8.

La version Patch d'AL2_01 conserve cette absence. Aucun label ou commentaire ne
dit si son signal 1 devait lancer une conversation, une animation, une
vérification de documents ou autre chose. Réactiver le volume, ajouter un
réveil générique ou rediriger vers les modes 1/2 cumulerait plusieurs
hypothèses.

**Verdict.** Intention partielle, comportement manquant. Ne pas modifier
`AL2_01_A1.scr` ni ajouter de handler 1 à AL2_01 sans source supplémentaire.

## Protocole d'observation du cas principal

### Baseline

Tracer le signal 1 au moment exact de l'interaction avec la porte, les signaux 5
et 6 reçus par le contrôleur, l'état de `mamete`, les statuts d'objectifs, le son
`S_alarm_fake_ovl` et la valeur de jeu 30.

### Matrice sans modification

1. Être découvert avant l'ouverture de la porte : l'échec critique existant
   doit rester inchangé.
2. Ouvrir la porte puis provoquer la même détection et constater si le signal 5
   reste accepté par `mamete` dans le script original.
3. Recevoir le signal 5 juste avant, juste après et si possible au même tick que
   le signal 1.
4. Déclencher le signal 6 avant puis après l'ouverture de la porte.
5. Répéter l'interaction de porte et relever les signaux effectivement reçus.
6. Tester modes normal, 3 et 7 pour couvrir les deux scripts d'alarme.
7. Sauvegarder/reprendre avant la porte, après le signal 1 et après le signal 6.

### Décision

Le test peut confirmer l'absence d'effet, la fenêtre logique et une course entre
1, 5 et 6. Il ne peut pas restituer le corps historique. Garder `AL2_alarm`,
`AL2_alarm_carn`, `AL2_01_A1`, `AL2_01` et `AL2_35` inchangés jusqu'à découverte
d'une variante source.

## Sources internes

- `.analysis/scripts/patch/SCRIPTS/ALPS2/AL2_01.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/AL2_01.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/AL2_alarm.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/AL2_alarm_carn.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/setobjectives.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/AL2_01_A1.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS2/al2_35.scr`
