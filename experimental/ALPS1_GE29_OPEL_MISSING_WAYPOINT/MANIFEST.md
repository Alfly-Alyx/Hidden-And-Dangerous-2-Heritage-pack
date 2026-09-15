# Manifeste spéculatif — `opel_1_2`

## OFFICIEL

| Point | x | y | z | Rôle |
| --- | ---: | ---: | ---: | --- |
| `opel_01` | 216.892746 | 3.741755 | 23.436855 | voisin nommé amont |
| nœud anonyme 45 | 222.291656 | 3.758093 | 29.209654 | intermédiaire du graphe |
| `hakl_09` | 228.176773 | 3.373273 | 33.655128 | intermédiaire nommé |
| `opel_02` | 235.215851 | 3.088827 | 37.228111 | voisin nommé aval |

Graphe officiel : `opel_01 -> index 45 -> hakl_09 -> opel_02`.
Distance directe `opel_01/opel_02` : environ 22,94 unités.

## DÉRIVÉ GÉOMÉTRIQUEMENT

| Candidat | Formule | x | y | z | Usage |
| --- | --- | ---: | ---: | ---: | --- |
| A `TEST_opel_1_2_linear` | milieu `opel_01/opel_02` | 226.054299 | 3.415291 | 30.332483 | premier test |
| B `TEST_opel_1_2_curve_control` | milieu index45/`hakl_09` | 225.234215 | 3.565683 | 31.432391 | contrôle seulement |

## CRÉATION MODERNE REQUISE

Rayon, orientation, type exact de checkpoint véhicule, projection au sol,
liens, coûts, nom final et validation de navigation.

## ABSENT

Transform historique, parent, rayon, direction, liens et preuve qu'A ou B est
la position originale. Aucun fichier mission n'est fourni.
