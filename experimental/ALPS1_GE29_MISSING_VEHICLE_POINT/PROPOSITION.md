# Alps 1 — point véhicule opel_1_2 manquant de GE29

État : **reconstruction bloquée faute de point unique**, 14 septembre 2026.
La route release reste inchangée et aucun check2 n’est produit.

## Verdict

Dans la branche reçue par le signal 2, GE29 conduit vers opel_01, puis une ligne
commentée viserait opel_1_2 avant opel_02. La branche d’alarme par le signal 3
ne contient pas ce vestige et passe directement de opel_01 à opel_02.

Le nom opel_1_2 est absent du check2 véhicule. Sa position ne peut pas être
déduite précisément : le graphe commercial contient déjà deux nœuds distincts
entre opel_01 et opel_02.

| Nœud véhicule | Position (x, y, z) |
| --- | --- |
| opel_01 | 216.892746, 3.741755, 23.436855 |
| sans nom, index 45 | 222.291656, 3.758093, 29.209654 |
| hakl_09 | 228.176773, 3.373273, 33.655128 |
| opel_02 | 235.215851, 3.088827, 37.228111 |

Le chemin du graphe est exactement opel_01 -> index 45 -> hakl_09 -> opel_02.
L’index 45 est un candidat géométrique plausible, mais hakl_09 l’est aussi en
tant qu’étape existante ; un troisième point disparu peut encore avoir été
interpolé entre eux. Renommer l’un de ces nœuds perturberait ses autres usages.

## Branches à préserver

- **release signal 2** : opel_01 -> opel_02 -> opel_03 -> opel_04 -> opel_05 ;
- **release signal 3** : la même route avec ses vitesses propres ;
- **historique futur** : opel_1_2 seulement dans la branche signal 2, après
  preuve de sa position et test du graphe.

Le plan disabled interdit explicitement de toucher la branche d’alarme. Un
point moderne éventuel doit être créé sous un nouveau nom tant qu’aucune source
ne permet de l’appeler historiquement opel_1_2.

## Critères de déblocage et tests

Il faut une archive, une capture éditeur ou une attribution explicite de la
position. Ensuite : dupliquer un enregistrement véhicule compatible, régénérer
liens/coûts, tester vitesses 30/40/90, collisions avec hakl_09, dix parcours,
signal 3 concurrent, alarmes, sortie du véhicule, téléport final et sauvegarde.

Retour arrière atomique : restaurer check2 et ge_29.scr commerciaux. Aucun
script ne doit référencer opel_1_2 si le point n’est pas installé.

