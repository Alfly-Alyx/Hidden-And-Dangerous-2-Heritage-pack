# Czech4 [Prototype — vestiges]

État : **conception additive et prototype chien désactivé**, 14 septembre 2026.
Czech4 release et Czech4 Zone restent intacts.

## Périmètre

Cette mission distincte rassemble trois vestiges sans prétendre restaurer une
version historique complète :

1. le compteur `CZ4_Counter_01` et les pelotons 07 à 09 ;
2. le chien `CZ4_Dog01` rattaché à `CZ4_Runner_03` ;
3. le script vide `R_Cz4_hodiny.scr`, maintenu dormant.

Le dossier frère
`../CZECH4_MISSING_SIGNAL_HANDLERS/PROPOSITION.md` reste la référence pour les
handlers manquants d'acteurs existants, notamment le signal 5 du pianiste. Le
présent dossier ne remplace pas ses conclusions.

## Inventaire officiel

L'audit Czech4 compte 102 liaisons, 108 scripts et trois scripts orphelins :
`CZ4_Counter_01.scr`, `CZ4_Dog01.scr` et `R_Cz4_hodiny.scr`.

- `CZ4_Platoon_01` à `06` et `CZ4_Runner_03` existent et sont liés ;
- `CZ4_Platoon_07` à `09` et l'acteur du compteur sont absents ;
- les routes `p6_1` et `p6_2` survivent ;
- deux frames d'horloge, `d_hodiny_` et `d_hodiny_2`, survivent ;
- le script d'horloge est vide.

`CZ4_APumperz_01` envoie officiellement le signal 5 aux pelotons 01 à 06 à
l'alarme et à sa mort. Ce mécanisme release reste inchangé.

## Compteur et renforts 07–09

Le script orphelin du compteur nomme P06, P07, P08 et P09. Son signal 10
incrémente une variable, mais le test `counter > 2` est placé hors du handler :
il n'est évalué qu'à l'initialisation. Aucun émetteur de signal 10 ne subsiste,
et P06 ne traite pas le signal 7. L'intention d'une activation après trois
événements est visible ; sa source et son exécution ne le sont pas.

La reconstruction proposée est moderne : trois observateurs monostables
suivent la première mort de P01, P02 et P03 et envoient chacun un signal 10 au
nouveau compteur. Au troisième événement, le compteur envoie une seule fois le
signal 7 à P06–P09. Ces trois sources sont choisies pour être testables ; elles
ne sont pas présentées comme les sources originales.

Le signal 7 de P06 peut reprendre de façon idempotente son réveil release du
signal 5 et rejoindre sa garde `p6_1`/`p6_2`. Si P06 est déjà actif, cette
réception n'ajoute aucun contre-mouvement : inventer une nouvelle route serait
moins fidèle. P07–P09 exigent encore acteurs, transformations, équipements,
routes et scripts de mort ; aucun squelette exécutable ne masque ces lacunes.

Le contrôleur d'objectif `CZ4_OD` scanne actuellement 49 acteurs et termine au
seuil `> 48`. Une copie propre à la variante devra ajouter P07–P09 et porter le
seuil final à 52 morts (`> 51`). Le seuil tactique `> 35`, si conservé, doit
être réévalué explicitement plutôt que décalé sans preuve. Les morts ajoutées
ne doivent jamais être envoyées au contrôleur release.

Le plan détaillé se trouve dans `PLAN_COUNTER_PLATOON07_09.md`.

## Chien de Runner03

Le script orphelin officiel ne fait que définir `CZ4_Runner_03` comme maître et
passer le chien en mode agressif. L'acteur et son placement ont disparu.

`PROTOTYPE_CZ4_DOG01_CONTROLLER.scr.disabled` conserve ce noyau et ajoute, avec
l'étiquette `MODERNE`, des portées initiales, une réaction d'alarme et une
réaction unique à la mort du maître. Le placement proposé est à 2–4 mètres de
Runner03, orientation parallèle, après vérification des collisions et lignes
de vue. Les vocalisations restent celles de l'IA canine ; aucun frame sonore
non attesté n'est inventé.

Ce prototype ne devient testable qu'après ajout d'un acteur chien dans la copie
de mission. Il ne compte dans aucun objectif ennemi avant validation.

## Horloges

`R_Cz4_hodiny.scr` ne contient aucune instruction. Les deux frames de décor ne
prouvent ni animation, ni son, ni horaire. Elles restent dormantes. Une démo
spéculative pourra être créée ailleurs, mais ne fait pas partie de la mission
vestiges tant qu'un comportement comparable n'est pas établi.

## Tests d'acceptation

- comparer Czech4 release, Czech4 Zone et la nouvelle entrée dans trois
  lancements indépendants ;
- tester les six ordres de mort des trois sources, répétitions et morts
  simultanées ;
- confirmer un seul signal 7 et un seul ajustement du compteur d'objectif ;
- tester chien hors alarme, alarme, maître mort, joueur furtif, sauvegarde et
  reprise ;
- vérifier navigation, collisions, tir ami et absence de blocage de P06–P09 ;
- désactiver chaque vestige séparément et retrouver la baseline de la copie.

