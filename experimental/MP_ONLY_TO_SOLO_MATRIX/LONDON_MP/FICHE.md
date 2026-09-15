# Prototype — reconstruction — Poland/London MP

Statut : **BLOQUÉ, tranche verticale entièrement créée**.

## Origine

- entrée commerciale : `Poland`, dossier `London_mp`, mode Deathmatch ;
- dix fichiers complets : `actors.bin`, `effects.bin`, `loader.4ds`, `map.4ds`,
  `scene.4ds`, `scene2.bin`, `sounds.bin`, `tree.klz`, `versions.dat`,
  `volumy.bin` ;
- aucun `check2.bin`, `items.dat`, registre ou script de mission ;
- 41 noms d'acteurs/frames : 32 points `mp_spawn01..32`, quatre échelles de
  canal et quelques frames de décor ; aucun PNJ de scénario.

Le nom interne London et le nom publié Poland ne suffisent pas à rattacher la
carte aux quatorze scripts `ENGLAND`. Cette relation reste une hypothèse.

## Wrapper

- **ORIGINE** : géométrie, collisions, volumes, sons et un seul spawn choisi
  après test parmi les 32 ;
- **DÉDUCTION** : utiliser un second spawn comme sortie afin de traverser la
  carte ;
- **CRÉATION** : équipe, quatre ennemis de test, objectif « atteindre la
  sortie », textes, échec et fin.

Aucun script England n'est branché dans la première tranche. Une comparaison
spatiale ultérieure doit précéder tout raccord.

## Manques et tests

Manquent briefing, routes, acteurs, items, objectifs et fin. Tester les 32
spawns pour sol/collision, choisir départ et sortie opposés, parcourir tous les
volumes, puis valider furtivité, sauvegarde et retour Deathmatch. Niveau de
création : **3/3**.

