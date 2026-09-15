# Matrice — deux propriétaires possibles

Les deux copies partent de Co_Libye3 et ne peuvent jamais être actives sous le
même nom de mission.

| Variante | Unique delta | Hypothèse testée |
| --- | --- | --- |
| `Co_Libye3 [Test A — Opel cargo sans carburant]` | `la_OpelAfK_ → Opel.scr` | camion de village ajouté comme décor immobilisé |
| `Co_Libye3 [Test B — Opel FlaK sans carburant]` | `la_OpelFAf_1 → Opel.scr` | batterie checkpoint volontairement indéplaçable |

## Baseline préalable

Avant tout binding, essayer d'entrer et de déplacer chaque véhicule : au début,
après mort du gunner, après défense du checkpoint et après activation du
village. Relever carburant visible, accès aux sièges, IA, collisions, objectifs
et sauvegarde/reprise.

## Test A

- confirmer que seul le cargo refuse de rouler ;
- faire exploser ou détruire `w_explosive_2` et les caisses voisines ;
- vérifier l'accès au village et toutes les fins avec le cargo intact/détruit ;
- confirmer que la FlaK reste identique à la baseline.

## Test B

- vérifier que le gunner embarque, tourne, vise et tire avec carburant nul ;
- tester les renforts 3/4, les trois gardes et le réveil par l'objectif 2 ;
- tuer le gunner puis essayer tous les sièges et la conduite ;
- confirmer que le cargo reste identique à la baseline.

## Critère discriminant

Une variante est rejetée si elle bloque une IA, un objectif, une route, une
interaction ou une sauvegarde. Si les deux sont fonctionnellement neutres, le
test ne tranche pas l'histoire : conserver A comme hypothèse prioritaire, sans
promouvoir aucun binding dans la mission commerciale.

