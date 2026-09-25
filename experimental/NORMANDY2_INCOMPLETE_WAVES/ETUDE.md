# Normandy 2 — vagues et mouvements inachevés

État : contrats et présence vérifiés, routes supplémentaires bloquées par la
géométrie, 26 septembre 2026. Aucun déplacement ni acteur ajouté.

## Première vague : cinq routes partielles, trois acteurs conservés

| Script | Acteur / liaison | Mouvements nommés conservés |
|---|---|---|
| Wave1_1 | présents | `W1man1_1` |
| Wave1_2 | absents | `W1man2_1` |
| Wave1_3 | présents | `W1manX_1`, `W1man3_2`, `W1manX_3`, `W1man3_4` |
| Wave1_4 | absents | `W1manX_1`, `W1man4_2`, `W1manX_3`, `W1man4_4` |
| Wave1_5 | présents | `W1manX_1`, `W1man5_2`, `W1manX_3` |

Les cinq commentaires proposent une suite « probablement dans le bâtiment »,
mais aucun nom ni emplacement pour cette suite. Tous les repères déjà nommés
sont présents. Ils se trouvent dans `DeAlarm`, atteint par `OnAlarmDone`, pas
dans l'activation initiale : le signal 1 réveille, avec des attentes distinctes
selon le soldat. Ajouter un trajet immédiatement à l'activation changerait aussi
ce contrat; ce n'est pas la simple complétion du commentaire.

## Deuxième vague : embarquement complet, suites à pied non renseignées

Wave2_1/2/3 ont acteurs et liaisons; Wave2_4/5 n'ont ni l'un ni l'autre. Les cinq
scripts possèdent chacun **deux** `HUMAN_Move("")` commentés et deux regards
sans argument commentés : après débarquement sur signal 2, puis après alarme.
Il ne s'agit donc pas seulement des deux soldats supprimés.

Le conducteur Wave2_1 conserve le parcours `Hakl_1..5` sur signal 10, avec
vitesses 12/20/27/22/17, suivi de `HUMAN_Drive("", 0)` : ce dernier est l'arrêt
commercial, **pas une route manquante**. Les cinq repères existent. Signal 1
embarque les soldats dans les sièges 0..4 prévus par leurs scripts; aucun siège
supplémentaire n'est introduit ici. La présence des cinq scripts ne prouve pas
la viabilité d'un nouvel équipage.

## Suite encadrée

Conserver les six acteurs commerciaux et leurs parcours comme témoin. Relever
dans l'éditeur les accès au bâtiment, les points après débarquement, les champs
de tir et les sorties possibles; distinguer les positions d'attente des routes
de repli. Chaque point supplémentaire sera MODERNE, jamais présenté comme une
coordonnée officielle retrouvée. Les quatre acteurs manquants restent dans
l'[étude dédiée](../NORMANDY2_REMOVED_DEFENDERS/ETUDE.md), avec leurs items,
affiliations, compteurs et nettoyage final.

Tester séparément activation, arrivée, véhicule bloqué, alarme pendant trajet,
retour d'alarme, mort avant/après débarquement, sauvegarde et fin. Ne pas relever
les seuils d'objectifs ni importer le coordinateur de défense pour ces essais.

## Traçabilité

L'[audit commun](../../tools/audit_normandy2_vestiges.py) vérifie les dix scripts,
les six acteurs et toutes les routes nommées; rapport sans écriture et empreinte
de chaque source. Les fichiers de mission effectifs viennent de Patch.dta :

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `scripts.dta` | 6587 | `660acc607e6ef1236f9c1c6cd0745f4ee484d9951a9a7cc55dd5ea32e4408b40` |
| `actors.bin` | 30115 | `44072df8ba4aac4a9828deb76d40de7c59286f69857f0403859a7d03a261d417` |
| `scene2.bin` | 5004207 | `b0456e29869f5f73aeea60ccd50ee57dbefc08a7124999747c481695ab6888a9` |
| `check2.bin` | 128206 | `5f506de1cb7dd6cd777de88f97a3f583867418227b09a4c536dc47f46839e50f` |

Une occurrence de nom ne prouve ni collision ni navigation. Aucun test moteur
n'est validé par cet audit.
