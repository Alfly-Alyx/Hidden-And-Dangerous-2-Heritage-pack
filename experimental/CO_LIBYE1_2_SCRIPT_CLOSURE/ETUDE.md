# Co-Libye 1/2 — fermeture des scripts par registre

État : fermeture statique relue, registres distingués, 26 septembre 2026.
Aucun registre fusionné ni script ajouté.

## Les nombres de liaisons ne sont pas des populations simultanées

| Mission / registre | Paires | Scripts racines | Atteints | Disponibles |
|---|---:|---:|---:|---:|
| CoLibye1 / scripts.dta | 189 | 133 | 133 | 140 |
| CoLibye1 / mpscripts.dta | 196 | 140 | 140 | 140 |
| CoLibye2 / mpscripts.dta | 136 | 132 | 132 | 135 |
| CoLibye3 / scripts.dta | 148 | 148 | 148 | 149 |
| CoLibye3 / mpscripts.dta | 148 | 148 | 148 | 149 |

Aucune dépendance littérale manquante dans ces fermetures. Les 385 liaisons
précédemment annoncées pour CoLibye1 sont **189+196 dans deux registres**;
ce n'est pas un registre unique ni une exécution de 385 scripts. Les deux
registres CoLibye3 sont byte-identiques : 296 est leur somme, pas 296 liaisons
distinctes. L'autorité réelle du moteur selon le mode reste à observer; aucun
outil de reconstruction ne doit simplement concaténer ces fichiers.

Ce contrôle suit les inclusions et affectations littérales hors commentaires.
Il ne certifie ni navigation ni positions et ne ferme pas les dialogues ou
comportements incomplets par la seule présence des fichiers.

## Trois orphelins CoLibye2, pas trois Jeep

Les trois fichiers non atteints sont `AF2_Jeep1`, `AF2_Opelflak1` et
`AF2_Opelflak2`. Aucun n'a de liaison. Le premier envoie signal 2 à `AF2_obj`
sur mort, mais le script effectivement lié `AF2_objective` ne possède **aucun
gestionnaire OnSignal(2)**. Les deux OpelFlak ont un OnDeath vide; leur nom ne
suffit pas à inventer ce qui devrait s'y passer.

Le contrôleur d'objectifs scanne déjà les états de véhicules pour échec et
progression. Ajouter les bindings et un récepteur 2 pourrait doubler cette
chaîne. Le problème de l'objectif 4 survie est
[indépendant](../CO_LIBYE2_OBJECTIVE4_SURVIVAL/ETUDE.md). L'objectif 2 et les
gardes ajoutés de CoLibye1 sont dans leur
[étude propre](../CO_LIBYE1_OBJ2_AND_AF1_48_49/ETUDE.md).

## Empreintes SabreSquadron.dta

| Entrée abrégée | Octets | SHA-256 |
|---|---:|---|
| CoLibye1/scripts.dta | 6534 | `f7821d7f793f924bbfcce17a59ee87c5b230a9f403dcd7f632b488c381715a57` |
| CoLibye1/mpscripts.dta | 6846 | `131b2de1fb31ca7be8ccd2769535648b96f22b5c58cfe1f72cd9a79a0648c6fc` |
| CoLibye2/mpscripts.dta | 4454 | `cf0773e6ff8b4cccb75f01df99d8f0eb2bcd36d7d444c92ca212d7ad22cbf534` |
| CoLibye3, chacun des deux registres | 6358 | `8573d6cefc32af31fe68e8b3e6ddbbd587b18ca7d7ca44fc57d93e12a975e5e1` |
| CoLibye2/AF2_Jeep1.scr | 610 | `9a1f521071a64311de2c5ac5202ea8a83b79062cec73171f12053a1824dfe98a` |
| CoLibye2/AF2_Opelflak1.scr | 547 | `fc041350b323fd19d8c475a988a8773671fdfd93df2c391d7ccb6ccc1b0aaf1b` |
| CoLibye2/AF2_Opelflak2.scr | 547 | `a41c8af1a44843a055e31b28a8bec43662e7b3a5934790e52a0183ce4f18012c` |

Les quatre premières lignes désignent `missions/<mission>/...`; les trois
dernières `scripts/co_libye2/...`. La fermeture est reproductible avec
ArchiveSources, parse_bindings et transitive_scripts; le rapport global
mission_closure_audit additionne les registres, d'où la distinction explicite
dans ce tableau. Aucun essai moteur ni réseau n'est validé.
