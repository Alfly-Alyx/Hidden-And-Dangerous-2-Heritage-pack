# Matrice des scripts commerciaux survivants

Ces fichiers existent dans `Scripts.dta` mais sont non liés. La colonne
« adaptation » reste bloquée par les identités/placements d'acteurs et la chaîne
d'activation. Correction du 25 septembre : les checkpoints cités et les deux
regards existent; leurs noms ne prouvent pas la navigation.

| ID | Rayon | Ronde officielle attendue | Regard | Particularité | Adaptation actuelle |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 140 | `T1_1 -> T1_2 -> T1_3` | `dummy_see1` présent | trois segments | bloquée |
| 2 | 140 | `T2_1 -> T2_2` | `dummy_see2` présent | — | bloquée |
| 6 | 125 | `T6_1 -> T6_2` | `dummy_see2` présent | — | bloquée |
| 7 | 140 | `T7_1 -> T7_2` | `dummy_see1` présent | réactions cutscene 1 | bloquée |
| 10 | 125 | `T10_1 -> T10_2` | `dummy_see2` présent | point-virgule dans le prédicat de proximité, à examiner | bloquée |
| 12 | 140 | `T12_1 -> T12_2`, détour `t12_3` | `dummy_see1` présent | fume parfois ; handler bouteille commenté, absent de l'analyse active | bloquée |
| 13 | 125 | `T13_1 -> T13_2` | `dummy_see2` présent | — | bloquée |
| 16 | 140 | `T16_1 -> T16_2` | `dummy_see1` présent | — | bloquée |
| 17 | 125 | `T17_1 -> T17_2` | `dummy_see2` présent | neutralisation en modes 3/7; prédicat de proximité à examiner | bloquée |

Invariant commun attesté : suspension initiale, mode défensif/garde, arme au
bras, handlers d'activité (trois actifs seulement pour 12), retour au segment courant, transmission du
signal 10 à `objectives` sur alarme puis reprise par `OnAlarmDone()`.

Ne pas « nettoyer » les particularités ou fautes de syntaxe historiques dans
une copie présentée comme officielle. Une version corrigée doit porter un nom
`*_modern.scr` et documenter chaque différence.
