# Étude expérimentale — compteur de pertes d'AF3b_organizer

État : analyse statique, 14 septembre 2026. Aucun handler comportemental n'est
proposé et aucun script actif n'est modifié.

## Classification

**Intention de comptage attestée, finalité manquante, architecture probablement
supplantée.** `AF3b_organizer.scr` déclare `INTEGER deadcnt = 0`, tandis qu'un
large ensemble d'ennemis envoie encore le signal 1 à `dummy_organizer`.
L'organisateur ne traite pourtant aucun signal et ne relit jamais `deadcnt`.

Le trou ne permet pas de conclure si un seuil devait provoquer une retraite,
arrêter l'invasion, valider un objectif ou ajuster la difficulté. Ces effets
sont mutuellement différents et plusieurs possèdent déjà des contrôleurs
concurrents dans la mission.

| Élément | Niveau | Motif |
| --- | ---: | --- |
| Producteurs du signal 1 | 4/4 | appels officiels nombreux dans Base et Patch |
| Variable `deadcnt` | 4/4 | déclaration officielle explicite |
| Incrément attendu | 3/4 | déduction directe du couple compteur/signaux de mort |
| Seuil | 0/4 | aucune constante ou comparaison conservée |
| Action au seuil | 0/4 | aucune destination ou branche attestée |

## Recherche de variante complète

Les sources suivantes ont été parcourues : couches Base et Patch, scripts
Sabre, autres extractions et archives locales indexées, registre de mission et
recherche publique sur les identifiants exacts `AF3b_organizer.scr`,
`dummy_organizer` et `AF3b_retreat`.

Aucune troisième copie ni ancienne version complète n'a été retrouvée. Base et
Patch contiennent le même organisateur pour cette partie : `deadcnt` est
initialisé puis abandonné. Le registre lie bien `dummy_organizer` au script, ce
qui exclut un simple acteur non enregistré.

## Inventaire exact des émissions

Le corpus Base contient 40 occurrences textuelles correspondant à
`SendSignal(organizer, 1)` :

- 39 appels actifs ;
- 38 scripts acteurs distincts ;
- une occurrence supplémentaire active dans `AF3b_11.scr` ;
- une occurrence commentée dans `AF3b_tankista01.scr`.

Les 38 émetteurs distincts sont :

- les soldats `AF3b_01` à `AF3b_33` ;
- `AF3b_dustojnik01` ;
- les équipages `AF3b_tankista02`, `03`, `05` et `06`.

`AF3b_tankista01` conserve un envoi commenté et `AF3b_tankista04` n'en possède
pas. Le périmètre du compteur n'est donc pas identique au nombre total d'acteurs
ou de véhicules de l'invasion.

### Double chemin d'AF3b_11

AF3b_11 envoie une première fois le signal dans `OnDeath()`. Il l'envoie aussi
dans `DESTROY_FORMATION`, branche accessible pendant qu'il est encore vivant
lorsqu'il dissout sa formation. Une mort ultérieure peut donc produire un
second signal pour le même acteur.

Ce détail interdit de prendre 39 comme nombre de morts attendu. Un ancien
handler pouvait filtrer ce doublon, compter des événements plutôt que des
acteurs, ou considérer la dissolution de formation comme une perte tactique.
Le code conservé ne permet pas de trancher.

## Séparation avec la stratégie radio

La variable `odvysilali` choisit les signaux et les délais de l'invasion selon
que les Allemands ont été avertis. La ligne qui la forçait à 1 neutralisait
cette branche, mais ce défaut stratégique est distinct et déjà traité dans le
lot stable.

Cette étude ne retire, ne réintroduit et ne documente aucun delta sur
`odvysilali`. Toute observation dynamique du compteur devra simplement utiliser
la version effective de la stratégie radio afin de comparer les deux parcours
averti/non averti.

## Contrôleurs concurrents déjà présents

### Déroulement de l'invasion

L'organisateur attend l'utilisation de la radio, active `S_invaze`, puis
réveille les véhicules et groupes en quatre séquences séparées par des délais.
Il désactive enfin le son 40 secondes après la dernière activation.

Un handler de mort peut arriver avant la radio, pendant les délais ou après la
fin de la séquence. S'il utilise `goto`, `EndScript()` ou modifie le son, il peut
interrompre la pile principale et empêcher des groupes ultérieurs d'apparaître.

### Objectifs

`AF3b_obj.scr` valide déjà la destruction des ennemis en mode normal lorsque
`_GetNumLiveEnemies() == 0`. Il accepte aussi les signaux 1 et 2 pour rejoindre
directement la branche de fin d'objectif.

`AF3b_debug.scr`, malgré son nom, est encore enregistré dans la mission. Il
surveille un compteur moteur et envoie le signal 1 à l'objectif lorsqu'il reste
moins de cinq ennemis dans sa condition de retrait. Ce mécanisme ressemble à
une version plus récente ou plus globale de la finalité que `deadcnt` aurait pu
porter.

Ajouter une seconde validation depuis l'organisateur peut donc terminer la
mission trop tôt, doubler textes et statuts ou diverger selon le mode de jeu.

### Capture de la base

`AF3b_enemiesinrange.scr` recompte séparément les soldats vivants situés à moins
de 30 unités. Il active et désactive `AF3b_capture_activator` autour des seuils
supérieur à 10 et inférieur à 6. Un compteur brut de morts ne représente pas la
même chose que la présence ennemie dans la base.

### Retraite par signal 22

Les soldats `AF3b_01` à `AF3b_33` possèdent largement un `OnSignal(22)` marqué
`RETREAT SECTION`, qui les fait courir vers `AF3b_retreat`. Aucun émetteur du
signal 22 n'est conservé dans les scripts Africa 4.

Cette symétrie rend une retraite au seuil plausible, mais non démontrée :

- aucun seuil de `deadcnt` n'existe ;
- l'organisateur ne référence pas uniformément les 33 soldats comme
  destinataires ;
- les équipages et l'officier comptés n'ont pas nécessairement la même route ;
- la retraite laisserait des ennemis vivants et interagirait avec les compteurs
  d'objectif et de capture.

## Reconstructions possibles

### A — instrumentation sans effet de jeu

Seul premier prototype défendable :

```text
OnSignal(1)
{
  deadcnt = deadcnt + 1;
  PrintfNumber("AF3b deadcnt: ", deadcnt);
  goto END;
}
```

Ce handler confirme la livraison des événements mais n'active aucun mécanisme.
Il doit rester dans un override de diagnostic et ne constitue pas une
restauration distribuable. Il révélera notamment le double comptage potentiel
d'AF3b_11 et l'ordre des morts par rapport aux vagues.

### B — retraite des survivants

À un seuil encore inconnu, le compteur aurait pu diffuser le signal 22 aux
survivants. Cette hypothèse explique les nombreux handlers de retraite sans
émetteur, mais nécessiterait de reconstruire : seuil, liste exacte, exclusions
d'équipages, condition radio, synchronisation avec les vagues et validation
d'objectif.

**Aucun delta ne doit être écrit** tant que ces paramètres ne sont pas prouvés
dynamiquement ou par une source historique.

### C — fin ou accélération de l'invasion

Le compteur aurait pu arrêter `S_invaze`, raccourcir les délais ou empêcher
l'activation de groupes devenus inutiles. Cette lecture est risquée : une mort
précoce pourrait sauter une partie de la séquence, et le label inutilisé
`ZVETSIT` ne modifie ni seuil ni groupe ; il ne fournit donc pas de corps de
remplacement.

### D — validation d'objectif

Un signal vers `MINARET22` est techniquement possible, mais redonderait
`AF3b_obj.scr` et `AF3b_debug.scr`. Sans seuil officiel, ce serait une nouvelle
règle de victoire plutôt qu'une restauration.

### E — équilibrage dynamique

`deadcnt` aurait pu ajuster `zpozdeni` ou le nombre de renforts. Aucun calcul ne
relie pourtant les deux variables. Cette option aurait l'impact le plus large
sur la difficulté et doit rester une hypothèse documentaire.

## Risques structurels

- un signal n'est pas nécessairement une mort unique à cause d'AF3b_11 ;
- certaines morts surviennent avant le démarrage de l'invasion ;
- tous les émetteurs ne font pas partie des mêmes vagues ;
- certains équipages sont exclus ou commentés ;
- un handler asynchrone peut détourner le flot principal de l'organisateur ;
- les seuils moteur existants comptent les ennemis vivants, pas les événements
  reçus ;
- la sérialisation de `deadcnt` après sauvegarde/reprise n'est pas démontrée ;
- les modes carnage et normal n'utilisent pas les mêmes mécanismes de fin.

## Protocole d'investigation

1. Ajouter uniquement le handler d'instrumentation dans un paquet de test.
2. Journaliser chaque émission avec l'identité de l'acteur, la valeur
   `deadcnt`, `_GetNumLiveEnemies()`, `_GetCountOfCarnageEnemies()`, l'étape de
   vague, l'état de la radio et les objectifs.
3. Tester les morts avant utilisation de la radio, pendant chaque délai, après
   la dernière vague et après extinction de `S_invaze`.
4. Provoquer `DESTROY_FORMATION` chez AF3b_11, puis sa mort, afin de quantifier
   le doublon.
5. Comparer les parcours radio averti et non averti désormais fonctionnels.
6. Observer le seuil inférieur à cinq du contrôleur debug et tous les acteurs
   recevant encore le signal 22.
7. Tester les modes normal et carnage, puis sauvegarde/reprise à plusieurs
   valeurs du compteur.
8. Ne prototyper une action qu'après avoir relié un seuil reproductible à un
   comportement visiblement absent.

## Verdict

Le signal 1 et `deadcnt` prouvent qu'un comptage avait été prévu, mais aucun
élément ne permet de choisir sa finalité. La retraite 22 est l'hypothèse la plus
suggestive, tandis que les contrôleurs moteur d'objectif et de capture indiquent
qu'une ancienne architecture a pu être remplacée. Le seul ajout actuellement
justifiable est une instrumentation expérimentale sans effet de jeu. Aucun
correctif stable ni reconstruction comportementale n'est proposé.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_organizer.scr`
- `.analysis/scripts/patch/SCRIPTS/AFRICA4/AF3b_organizer.scr`
- `AF3b_01.scr` à `AF3b_33.scr`
- `AF3b_dustojnik01.scr`
- `AF3b_tankista01.scr` à `AF3b_tankista06.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_obj.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_debug.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_enemiesinrange.scr`
- `.analysis/africa4/base/MISSIONS/AFRICA4/scripts.dta`
