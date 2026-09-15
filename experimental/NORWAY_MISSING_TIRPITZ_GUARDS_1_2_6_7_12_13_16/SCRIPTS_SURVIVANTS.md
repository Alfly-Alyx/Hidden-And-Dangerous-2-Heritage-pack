# Matrice des scripts commerciaux survivants

Ces fichiers existent dans `Scripts.dta` mais sont non liés. La colonne
« adaptation » ne devient nécessaire que si des checkpoints modernes reçoivent
des noms différents ; toute modification doit rester un script dérivé annoncé.

| ID | Rayon | Ronde officielle attendue | Regard | Particularité | Adaptation actuelle |
| ---: | ---: | --- | --- | --- | --- |
| 1 | 140 | `T1_1 -> T1_2 -> T1_3` | `dummy_see1` absent | trois segments | bloquée |
| 2 | 140 | `T2_1 -> T2_2` | `dummy_see2` présent | — | bloquée |
| 6 | 125 | `T6_1 -> T6_2` | `dummy_see2` présent | — | bloquée |
| 7 | 140 | `T7_1 -> T7_2` | `dummy_see1` absent | réactions cutscene 1 | bloquée |
| 12 | 140 | `T12_1 -> T12_2`, détour `T12_3` | `dummy_see1` absent | fume parfois ; handler bouteille commenté de façon ambiguë | bloquée |
| 13 | 125 | `T13_1 -> T13_2` | `dummy_see2` présent | — | bloquée |
| 16 | 140 | `T16_1 -> T16_2` | `dummy_see1` absent | — | bloquée |

Invariant commun attesté : suspension initiale, mode défensif/garde, arme au
bras, quatre handlers d'activité, retour au segment courant, transmission du
signal 10 à `objectives` sur alarme puis reprise par `OnAlarmDone()`.

Ne pas « nettoyer » les particularités ou fautes de syntaxe historiques dans
une copie présentée comme officielle. Une version corrigée doit porter un nom
`*_modern.scr` et documenter chaque différence.
