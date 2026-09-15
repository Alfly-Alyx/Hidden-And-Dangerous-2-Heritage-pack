# Alps2 — comportements retirés AL2_13 / AL2_14

État : **deux comportements modernes désactivés, acteurs encore à créer**, 14
septembre 2026. Alps2 release reste intacte et `AL2_13_A1` n'est pas lié.

## Correction de l'inventaire

Le registre effectif contient 115 bindings et 129 scripts. `AL2_13_A1.scr` est
orphelin, tandis que sa frame homonyme existe et est libre.

Contrairement à l'hypothèse initiale, aucun frame exact `AL2_13` ou `AL2_14`
n'existe dans les `actors.bin`, `scene2.bin` ou `sounds.bin` effectifs, y
compris après les overrides de `Patch.dta`. Les seules occurrences binaires de
`AL2_13` viennent du préfixe `AL2_13_A1` et du texte du script. Il manque donc :
acteurs, items, transforms, bindings **et** comportements.

Les commentaires `al2_13 neni` et `al2_14 neni` dans `AL2_alarm.scr` et sa
version Carnage confirment une suppression connue, pas deux bindings oubliés.

## Vestige officiel

`AL2_13_A1.scr` résout les deux noms disparus puis, lorsque le joueur entre à
moins de deux unités, leur envoie le signal 1. Son transform local
`(1.555, 0.015, -0.682)` doit rester associé à son parent ; ce n'est pas une
coordonnée monde exploitable isolément.

L'étude antérieure est conservée dans
[`ALPS2_TUTORIAL_COBREST`](../ALPS2_TUTORIAL_COBREST/FAISABILITE.md). Le présent
dossier approfondit seulement la variante additive et ses deux analogues.

## Analogues voisins

| Acteur | Rôle/script attesté | Armes/items | Routes |
| --- | --- | --- | --- |
| `AL2_12` | soldat entrant dans la salle, documents, signaux 1/2/3 | inventaire propre complexe | `AL2_12_01..04` |
| `AL2_15` | garde agressif de sortie, dialogue/interdiction | huit records d'item ; premier type 12 | `al2_15_01..04`, `nuda` |
| `AL2_16` | second garde défensif, fumeur | huit records ; premier type 17 | `al2_16_1..4`, `6` |
| `AL2_17` | renfort suspendu, réveillé par signal 1 | huit records ; premier type 12 | aucune |

`AL2_15_A1` réveille 15, 16 et 17 après l'alarme et conserve un commentaire
ancien « activator for AL2_13 », mais son code ne résout ni 13 ni 14. Cette
phrase soutient un rôle de gardes locaux ; elle ne fournit aucun checkpoint.

Les scripts 15 et 16 utilisent des points de regard, dialogues et routes
propres. Les copier intégralement produirait des collisions avec leurs acteurs
release. Le seul analogue sans route est le réveil minimal de 17.

## Variante proposée

Nom : `Alps2 [Prototype — gardes 13/14]`.

- **AL2_13 moderne** : acteur/item copié d'AL2_15, garde agressif local debout ;
- **AL2_14 moderne** : acteur/item copié d'AL2_16, garde défensif local qui se
  baisse après activation ;
- transforms : deux placements créés de part et d'autre du volume
  `AL2_13_A1`, après projection monde et test de navmesh ;
- aucun chemin : les acteurs gardent leur position et réagissent à l'alarme ;
- aucun objectif : ils suivent le traitement ennemi normal sans devenir une
  nouvelle condition de victoire.

Ces rôles sont des **DÉDUCTIONS**, pas les comportements perdus retrouvés. Les
prototypes désactivés matérialisent la décision minimale :
`PROTOTYPE_AL2_13_LOCAL_GUARD.scr.disabled` et
`PROTOTYPE_AL2_14_LOCAL_GUARD.scr.disabled`.

## Ordre d'implantation obligatoire

1. créer les deux acteurs, items, affiliations et transforms dans une copie ;
2. lier chacun à son prototype désactivé puis tester un signal manuel ;
3. valider mort, alarme, collision et sauvegarde ;
4. seulement ensuite copier la frame `AL2_13_A1` et lier son script officiel ;
5. rendre son déclenchement monostable dans la copie si le moteur le répète.

Le détecteur seul reste interdit. Les détails de création figurent dans
`ELEMENTS_A_CREER.md`.

