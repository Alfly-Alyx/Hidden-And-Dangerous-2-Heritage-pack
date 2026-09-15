# Matrice de comparaison des postures

| ID | Script / emplacement | Release | Variante | Portée du risque |
| --- | --- | --- | --- | --- |
| GE04_CROUCH_SNIPER | ge04, après `ge04_sniper` | StandFast + sniper | Crouch + sniper | locale, tir/couverture |
| GE14_CROUCH_SIGNAL1 | ge14, signal 1 | mode hérité + TurnAt | Crouch + TurnAt | activation |
| GE19_CROUCH_ALARM | ge19, après `ge19_02` | Run/StandFast | Crouch | alarme/navigation |
| GE19_TURN_NEAR | ge19, pas joueur <4 | fin sans rotation | TurnAtNearestPlayer | locale, fin du script |
| GE31_RANGE_STANCE_PAIR | ge31, `ge31_02` | délai sans changement | Crouch, délai, Stand | stand de tir |
| GE07_INITIAL_WALK | ge07, initialisation | mode hérité | Walk | script entier |
| GE08_INITIAL_RUN | ge08, initialisation | mode hérité | Run | script entier |
| GE09_INITIAL_RUN | ge09, initialisation | mode hérité | Run | script entier |

## Verrous permanents

| Appels directs commentés | Remplacement actif | Décision |
| --- | --- | --- |
| ci01 14992836 | `ci01krik` | ne pas doubler |
| ci02 14992838 | `ci02krik` | ne pas doubler |
| ci03 14992840 | `ci03krik` | ne pas doubler |
| ge30 14992828 | `ge30krik` | ne pas doubler |
| ge36 14992831 | `ge36krik` | ne pas doubler |

Ci01 conserve par ailleurs un appel direct actif 14992837 dans une autre
branche ; il ne constitue pas une autorisation à réactiver 14992836.
