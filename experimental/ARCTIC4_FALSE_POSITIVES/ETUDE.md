# Arctic 4 — deux faux positifs fermés

État : **fermeture statique vérifiée**, 25 septembre 2026. Aucun script modifié.

## Hunters : l'émetteur du signal 13 existe déjà

Les scripts des trois Hunters conservent un commentaire demandant l'envoi du
signal 13, mais le registre lie déjà `dummy_Hunters_activator` à
`R_Arc3_Hunters_activator.scr`. Son détecteur de joueur à 70 m envoie 13 aux
trois acteurs. `Hunter_1`, `Hunter_2` et `Hunter_3` ont chacun leur liaison et
un `OnSignal(13)` qui les réveille. Ajouter un deuxième émetteur ne restaure
donc rien et pourrait relancer une activité.

Cette fermeture concerne seulement le prétendu **signal manquant**. Elle ne
certifie pas toutes les routes, la manipulation des caisses ou les conditions
de combat des Hunters.

## Sub-gunners : l'activité de jumelles a remplacé l'ancien montage

`sub_gunner_1` et `sub_gunner_2` ont leurs liaisons. Les anciens appels d'objet
99 et d'animation `%%dalekohled` ne doivent pas être réactivés : les scripts
utilisent déjà `HUMAN_ACTIVITY_Binoculars()` et des sorties
`HUMAN_ACTIVITY_BinocularsEnd()`, notamment à l'alarme. Superposer les anciens
appels pourrait doubler l'objet tenu ou l'animation.

Cette fermeture ne clôt pas l'étude séparée de sortie du FlaK dans
[ARCTIC4_AMBIENT_ANIMATIONS_AND_FLAK_EXIT](../ARCTIC4_AMBIENT_ANIMATIONS_AND_FLAK_EXIT/PROPOSITION.md).

## Empreintes des preuves

Le registre `missions.dta::missions/arctic4/scripts.dta` possède l'empreinte
`618dbf08b27f3d58ffe5b67b6f515da3f3c17672a8d42ffa1e0f6f2396d64d57`.
Les scripts suivants viennent de `Scripts.dta::scripts/arctic4/`, sans
substitution Patch/Sabre pour ces fichiers :

| Script | Octets | SHA-256 |
|---|---:|---|
| `r_arc3_hunters_activator.scr` | 233 | `5abce583057f99e4745ac332452cb39f93bb038110670119643bc81007d88054` |
| `r_arc3_hunter_1.scr` | 2923 | `5d456c1ff45ba0dadbf72c2e8b702f008a24c8a16e3f31dd83139ff7c50f691c` |
| `r_arc3_hunter_2.scr` | 3024 | `5969b8be7337b0605b77ec2fbbcdd304b71efa33c015b2a24810f33aa01d0bf6` |
| `r_arc3_hunter_3.scr` | 1446 | `3fd424565e5f35947af0641578c99e6ae8fbe44b06ce04be0258e1324da32af8` |
| `r_arc3_sub_gunner_1.scr` | 1599 | `190c926ac786b09904f2c9270e5be7b32790c2df4e8eaffe3ea8e384b7bb78fa` |
| `r_arc3_sub_gunner_2.scr` | 2073 | `e0a3d5da4249d90ebd005a228fe5b29e322f31ce76ad11a254dd2d471f3f2e12` |

Reproduction : `tools/script_binding_audit.py` pour les liaisons, puis lecture
des scripts effectifs dans Base/Patch/Sabre. Les conclusions sont fondées sur
le code commercial, pas sur un nouveau test en jeu.
