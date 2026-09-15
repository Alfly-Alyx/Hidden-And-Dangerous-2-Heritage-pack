# Ardens1_Obj Base — éléments à créer ou valider

État au 14 septembre 2026. Seuls `ETUDE.md`, ce fichier et
`VARIANTE_SOLO_RECONSTRUCTION.md` sont créés dans le lot. Tout élément de jeu
ci-dessous reste futur et spéculatif.

| Élément | Source possible | Statut actuel |
| --- | --- | --- |
| scène roster Base | `Missions.dta` | attestée, non modifiée |
| 12 ressources de l'entrée Base | inventaire `Missions.dta` | extraction technique complète |
| scripts d'initialisation | Base/Sabre identiques | attestés, insuffisants |
| `dummy_obj1/2/3` | `actors.bin` Base | attestés, aucun script propriétaire |
| trois validateurs de canons | OnDeath moderne ou adaptation Sabre | choix spéculatif |
| trois bindings de canons | nouveau `mpscripts.dta` | à créer |
| volumes d'action/spawn | reconstruction ou adaptation mesurée | absents en Base |
| charges et dummies | branche Sabre | absents en Base ; ajout spéculatif |
| sons de sabotage | inventaire Base/Sabre à comparer | à valider |
| textes et fin de manche | ressources de langue/règles réseau | à valider |
| métadonnées de l'entrée | nom demandé et nouvel identifiant | modernes |
| Jeep `la_JeepW_` | `actors.bin` Base | attestée, rôle non piloté |
| règles des six véhicules | tests multijoueur | à créer/documenter |

Le troisième Sherman, le second Tiger et la Jeep sont des actifs Base
attestés, pas des créations. Leur placement n'atteste toutefois ni leur
équilibrage, ni leur respawn, ni leur rôle dans les objectifs. La présence de
`dummy_obj1/2/3` n'autorise pas davantage à leur inventer un propriétaire : le
seul binding officiel reste `dummy_obj -> Ardens1_obj.scr`.
