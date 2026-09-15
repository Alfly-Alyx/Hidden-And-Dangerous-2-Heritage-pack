# Étude expérimentale — ancienne variante multi-avions d'Africa1_Obj

État : architecture très incomplète, 14 septembre 2026. Aucun prototype,
binding ou actif n'est ajouté ; toute reprise jouable serait une création
moderne explicitement étiquetée.

La carte n'ayant qu'un registre multijoueur, une proposition solo distincte
est désormais décrite dans
[`VARIANTE_SOLO_RECONSTRUCTION.md`](VARIANTE_SOLO_RECONSTRUCTION.md). Elle ne
modifie ni la mission multijoueur à un avion ni le présent projet multi-avions.

## Verdict

La mission effective ne contient qu'un avion destructible :
`la_macchi01 -> AF1_mp_letadlo01.scr`. À sa mort, ce script produit l'explosion,
neutralise `w_explosive_13` et valide directement l'objectif 2.

`AF1_mp_letadla_counter.scr` et `AF1_mp_letadlo02.scr` sont tous deux non
reliés, sans acteur homonyme disponible. Les frames indispensables au second
avion et au compteur ont disparu. Il ne subsiste donc pas une fonctionnalité à
réactiver, mais les fragments de plusieurs conceptions successives.

## Registre et actifs

| Élément | État effectif |
| --- | --- |
| `dummy_letadlo_organizer` | présent et lié à `AF1_mp_letadlo_organizer.scr` |
| `la_macchi01` | présent et lié à `AF1_mp_letadlo01.scr` |
| `w_explosive_13` | présent |
| `la_macchi02` | absent |
| `dummy_let02` | absent |
| `dummy_letadla_counter` | absent |
| `w_explosive14` | absent |

Le registre compte huit bindings et ne lie ni le compteur ni le script avion
02. La couche Patch conserve les deux scripts avion, avec
`SetActorState(exp, 3)` à la place de `FRM_SetOn(exp, false)`, mais ne rétablit
aucun actif ni binding. Le résultat de progression reste une validation directe
de l'objectif 2 à la mort de chaque avion.

## Trois architectures incompatibles

### Release : un avion, succès direct

`AF1_mp_letadlo01.scr` est autosuffisant et ne contacte aucun compteur. La mort
du seul avion termine immédiatement l'objectif 2.

### Organisateur dormant : déplacement aléatoire d'un seul avion

`AF1_mp_letadlo_organizer.scr` ne crée pas de second avion. Il référence
`la_macchi01` et conserve seulement, en commentaires, un choix aléatoire qui
aurait téléporté cet avion près de `dummy_let02`. Cette frame est absente. Le
script actif se limite désormais à initialiser les objectifs 2 et 3.

### Compteur ancien : six valeurs sans propriétaires

`AF1_mp_letadla_counter.scr` attend un signal 1, puis teste les valeurs de jeu
10 à 15. Si l'une d'elles est vraie, il quitte ; si elles sont toutes nulles,
il valide l'objectif 2. Aucun script du dossier n'écrit ces six valeurs et ni
le script avion 01 ni le script 02 n'envoie le signal attendu au compteur.

Avec les valeurs par défaut, un premier signal 1 pourrait donc valider
immédiatement l'objectif. Le sens exact des six drapeaux — avions vivants,
charges actives ou autre état — n'est pas reconstructible à partir de ce lot.

## Application du principe additif

La branche release à un avion doit rester disponible et inchangée. Une variante
multi-avions pourrait être proposée comme mode exclusif distinct, mais elle
devrait créer ou fournir :

1. au moins un second avion et son modèle de collision ;
2. une seconde charge compatible avec le traitement Patch ;
3. un point de placement remplaçant `dummy_let02` ;
4. un agrégateur moderne avec état sauvegardé explicite ;
5. des scripts avion qui notifient cet agrégateur sans valider directement
   l'objectif 2.

Cette branche remplacerait, seulement lorsque l'option est choisie, la règle de
succès direct des avions. Elle ne doit jamais coexister avec cette validation,
sous peine de réussite au premier appareil détruit.

## Porte de prototype

Aucune maquette `.scr.disabled` n'est produite : quatre frames manquent, les six
valeurs n'ont aucun écrivain et le signal d'agrégation n'a aucun émetteur. Une
création moderne ne devient testable qu'après définition des actifs, du nombre
d'avions, de la persistance et de la condition de succès. Elle devra couvrir
destructions simultanées, respawn éventuel, sauvegarde/reprise et réplication.

## Sources internes

- registre effectif `missions/africa1_obj/mpscripts.dta`
- scripts Base `AF1_mp_letadla_counter.scr` et
  `AF1_mp_letadlo_organizer.scr`
- scripts Base/Patch `AF1_mp_letadlo01.scr` et `AF1_mp_letadlo02.scr`
- `scene2.bin`, `actors.bin` et `sounds.bin` d'Africa1_Obj
