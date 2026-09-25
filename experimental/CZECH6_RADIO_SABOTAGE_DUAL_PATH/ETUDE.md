# Czech 6 — sabotage radio avant ou après alarme

État du 25 septembre 2026 : paire de scripts reconstruite, **identique octet par
octet aux deux versions Base**, laboratoire désactivé, validation moteur en attente.

## Le sens exact de la branche historique

Le Patch récompense le premier sabotage indépendamment de l'alarme. La Base ne
bloquait pas l'accès jusqu'à une alarme : c'est l'inverse pour la récompense.
L'opérateur G11 émettait le signal 1 vers le câble lors de son alarme; le câble
retenait cet état et supprimait la récompense d'un sabotage effectué ensuite.

| Ordre | Patch, témoin | Paire Base, variante |
|---|---|---|
| Sabotage avant alarme | Câble cassé, signal objectif 11, musique 36, signal G11 2. | Identique. |
| Alarme puis sabotage | Même récompense que sans alarme. | Câble cassé, sans objectif 11, sans musique 36 ni signal G11 2. |
| Utilisation répétée | Ignorée par `firstuse`. | Ignorée par le même verrou. |

La variante conserve donc volontairement une ancienne condition plus exigeante
sur l'objectif optionnel. Elle n'introduit aucun objectif supplémentaire et ne
modifie pas le gestionnaire d'objectifs. Ce n'est pas un correctif obligatoire de
la release : le Patch reste le défaut.

## Pourquoi les deux scripts sont inséparables

`C5_obj02.scr` doit retrouver la variable `alarmed`, la branche conditionnelle et
son récepteur 1. `C5_G11.scr` doit retrouver l'émission correspondante dans son
`OnAlarm`. Restaurer seulement le câble laisserait `alarmed` à zéro; restaurer
seulement l'opérateur enverrait un signal sans récepteur. Le signal 1 que G40
adresse à **G11** est une autre chaîne, non réparée par cette variante.

Le profil `czech6-radio-before-alarm` utilise désormais `additional_changes` pour
contenir les deux modifications dans un laboratoire indivisible. Une sortie
isolée `.scr.disabled` est refusée pour ce profil. Tous les scripts de la paire
doivent réussir leurs empreintes, leurs ancrages, leur liaison et leur contrôle
de propriétaire avant qu'un laboratoire soit construit; le vérificateur refuse
aussi une paire amputée.

## Propriétaires et provenance

Le registre lie `1cable_ok` à `C5_obj02.scr` et `C5_G11` à `C5_G11.scr`.
G11 est sérialisé dans les acteurs. Les deux câbles ne sont pas des humains ni
des frames typées de `scene2.bin` : le lecteur 4DS décode intégralement les
**1001 nœuds** de la scène et retrouve `1cable_ok` (997) et `2cable_broken` (998),
deux objets visuels racines, à la même position :
`(82,483116 ; 18,496912 ; -66,837051)`. Leur nom n'est pas accepté par simple
recherche de sous-chaîne. `C5_objective` est également retrouvé dans `scene2.bin`.

Les six empreintes d'entrée sont dans le [catalogue](../reconstruction-variants.json).
Les sorties ont été comparées directement à `Scripts.dta`, sans exporter de
scripts commerciaux dans Git :

| Fichier | Octets | SHA-256 de la sortie, identique à la Base |
|---|---:|---|
| `C5_obj02.scr` | 1156 | `9d72a651971131ccf4ba40335ce0040d2c47a1ebd390b30c22665473a84db3dc` |
| `C5_G11.scr` | 2415 | `30ec6bfa42feaea3efdc9a5389bcb2a34b158195c46f63109464c0c9d0026359` |

Le laboratoire conserve les 109 fichiers de Czech 6 et les 95 scripts accessibles;
exactement ces deux scripts diffèrent du témoin Patch. Les changements du Patch
dans les autres scripts, notamment le conducteur ISU, restent inchangés.

## Essais requis

Tester les deux ordres ci-dessus, les utilisations répétées, l'alarme et le sabotage
quasi simultanés, la mort de G11 avant/après son émission, puis la sauvegarde et
reprise autour de chaque frontière. Vérifier les deux états visuels du câble,
le comportement de l'opérateur, les renforts, l'objectif optionnel et la fin de
mission. En Carnage, contrôler l'affectation alternative du gestionnaire
d'objectifs. Aucun résultat en jeu n'est encore revendiqué.

Les deux fichiers sont **OFFICIELS** comme versions Base; leur assemblage avec
le reste du Patch dans un nouveau laboratoire est **EXPÉRIMENTAL**. Ne pas
combiner cette paire avec un autre changement de G11, du câble ou de l'objectif
avant les comparaisons isolées. Retrait : retirer uniquement la copie de test.
