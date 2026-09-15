# Inventaire des armes et véhicules retirés

Premier balayage lexical des archives. Les nombres comptent des noms ou sous-chaînes et ne prouvent ni une liaison exacte à une mission ni une jouabilité complète.

| Élément | Correspondances lexicales | Modèles 4DS | Fichiers sous Scripts | Tables |
|---|---:|---:|---:|---:|
| flamethrower | 5 | 1 | 0 | 4 |
| garrote | 0 | 0 | 0 | 0 |
| zk383 | 0 | 0 | 0 | 0 |
| me323 | 6 | 2 | 0 | 0 |
| aichi | 3 | 2 | 0 | 0 |
| fa223 | 2 | 2 | 0 | 0 |
| la5 | 24 | 2 | 5 | 0 |
| ju52 | 24 | 12 | 4 | 0 |
| fw200 | 2 | 2 | 0 | 0 |
| li2 | 16 | 2 | 8 | 0 |
| dfs230 | 2 | 2 | 0 | 0 |

Lecture manuelle recoupée :

- usage exact dans une mission prouvé : Ju 52 uniquement, comme décor scénarisé dans Africa 1 ;
- modèles présents sans chaîne de mission exacte démontrée : La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS/DSF 230 ;
- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;
- les deux lance-flammes conservent icônes, munitions, sons et effet, mais pas une chaîne d’arme fonctionnelle ;
- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.
- la Benelli M4 conserve animations FPV, textures, icône, munition 179 et sons de tir/rechargement, mais son entrée Weapon a été remplacée par la boussole et son modèle extérieur manque ;
- le Vickers K appartient à la jeep SAS active : son modèle FPV, ses axes de tourelle et son ancrage `BARREL01_00` subsistent, et une mission CMP conserve la liaison exacte vers `w_vickerKFPV`; le canon de 17 mm est déjà employé dans `Ardens1_obj` ;
- FG 42 et MG 34 portative restent des vestiges de catalogue incomplets ; MG 15 et MG 81 ne sont attestés que comme armements montés.

Les modèles exacts La-5, `la_aici`, `LA_M323`, Li-2, `la_Fa 223`, Fw 200 et DFS 230 sont présents et articulés. Ce constat prouve des véhicules conservés comme ressources, pas leur pilotage : seul le Ju 52 possède une utilisation commerciale de scène directement reliée. Les scripts Li-2 repérés séparément sont des ambiances sonores et ne constituent pas une chaîne de vol.
