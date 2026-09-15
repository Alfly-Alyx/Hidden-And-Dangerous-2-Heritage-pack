# Czech 6 — double route de l’ISU-152

État : **divergence Base/1.12 prouvée, sélecteur de laboratoire désactivé**,
14 septembre 2026. Aucune mission n’a été compilée ou installée.

## Verdict

Le Patch 1.12 raccourcit et accélère effectivement la route de l’ISU. La Base
ne contient toutefois pas seulement les deux points cités : son trajet complet
est `C5_isu01` → `C5_tank11` → `C5_isu02`, tous à vitesse 12. Le Patch conserve
en commentaire une tentative `C5_isu01` à vitesse 30, mais la route effective va
directement à `C5_isu02` à vitesse 30.

La reconstruction la plus utile n’écrase donc pas le comportement 1.12. Elle
garde la route directe par défaut et ajoute un choix de laboratoire avant le
signal 2 : route Base exacte, ou route hybride qui réintroduit seulement
`C5_isu01` à la vitesse du Patch. Cela permet d’isoler séparément l’effet du
checkpoint, du détour `C5_tank11` et de la vitesse.

## Inventaire des preuves Base et Patch

| Source | Route du conducteur C5_R17 | Sortie |
| --- | --- | --- |
| Base | `C5_isu01` à 12, `C5_tank11` à 12, `C5_isu02` à 12 | conducteur puis signaux 31 aux sièges 1–3 |
| Patch 1.12 effectif | `C5_isu01` à 30 commenté, puis `C5_isu02` à 30 actif | conducteur sort, puis signaux 31 aux sièges 1–3 |

Autres preuves vérifiées :

- le registre lie `C5_R17` à `C5_R17.scr` ;
- `C5_isu01`, `C5_tank11`, `C5_isu02`, `C5_isu_tele`, `C5_kubel_tele` et
  `C5_kubel01` sont tous présents dans `Missions/CZECH6/check2.bin` ;
- `C5_objective.scr` et `C5_objective2.scr` envoient le signal 1 à C5_R17 et aux
  équipiers 18–20, puis réveillent `C5_player_teleporter` ;
- le téléporteur envoie ensuite le signal 2 à C5_R17 ;
- C5_R18 reçoit aussi le signal 2 du conducteur avant le délai de 3 secondes ;
- après le dernier `HUMAN_Drive`, C5_R17 sort du siège 0 et envoie 31 à C5_R18,
  C5_R19 et C5_R20, qui quittent respectivement les sièges 1, 2 et 3 ;
- C5_R18–20 et les deux contrôleurs ne sont pas remplacés par le Patch : leurs
  scripts Base restent effectifs autour du conducteur Patch.

## Niveaux de spéculation

- **Nul** : les deux routes livrées et leurs vitesses sont lisibles dans Base et
  Patch.
- **Faible** : les checkpoints anciens existent encore dans la mission finale.
- **Faible à moyenne** : la route Base reste franchissable avec la géométrie et
  les acteurs du Patch 1.12 ; l’existence des points ne garantit pas l’absence
  de collision.
- **Moyenne** : la route hybride `C5_isu01` → `C5_isu02` à 30. Elle combine deux
  faits livrés, mais n’est active dans aucune version.
- **Exclue** : remplacer définitivement la route 1.12 avant comparaison en jeu.

## Prototype additif

`PROTOTYPE_ROUTE_SELECTOR.scr.disabled` part de la copie Patch de C5_R17 :

- sans signal supplémentaire, le signal 2 conserve exactement la route directe
  vers `C5_isu02` à 30 ;
- un signal 3 envoyé à C5_R17 avant le signal 2 sélectionne la route Base exacte
  à 12, y compris `C5_tank11` ;
- un signal 4 sélectionne la route hybride à 30 via `C5_isu01`, sans
  `C5_tank11`.

Les recherches n’ont trouvé aucun signal 3 ou 4 adressé à C5_R17 dans les
scripts Base/Patch. Ils restent néanmoins réservés au laboratoire et doivent
être réaudités après toute fusion. L’ordre Patch de sortie du conducteur et des
trois équipiers est conservé dans toutes les branches.

## Activation et désactivation

1. Dupliquer Czech 6 et copier la version Patch effective de C5_R17.
2. Ajouter le sélecteur, sans modifier `C5_objective*`, le téléporteur ou
   C5_R18–20.
3. Pour la baseline directe, ne rien envoyer avant le signal 2.
4. Pour la Base, envoyer 3 à `C5_R17` après son signal 1 et avant le signal 2.
5. Pour l’hybride, envoyer 4 dans la même fenêtre.
6. Ne changer de mode qu’après rechargement de la mission : le choix est fait
   pour un seul trajet.
7. Désactivation : restaurer C5_R17 Patch et supprimer le sender de laboratoire.

## Risques

- collision de l’ISU sur le détour ancien, particulièrement à vitesse 30 ;
- point `C5_tank11` devenu incompatible avec la disposition 1.12 ;
- équipage 18–20 désynchronisé pendant un trajet plus long ;
- C5_R18 commençant son action trop tôt alors que le véhicule roule encore ;
- conducteur ou passagers ne quittant pas le véhicule après une collision ;
- signal 2 reçu avant le signal de sélection ;
- reprise de sauvegarde entre deux checkpoints avec un mode non sérialisé.

## Protocole de test en jeu

1. Baseline Patch : mesurer le temps signal 2 → arrivée `C5_isu02`, relever la
   trajectoire, les collisions, la position finale et l’ordre de sortie 0/1/2/3.
2. Route Base exacte : répéter à 12 via `C5_isu01`, `C5_tank11`, `C5_isu02`.
3. Route hybride : répéter à 30 via `C5_isu01`, puis `C5_isu02`.
4. Pour chaque mode, filmer les virages et tester véhicule intact, endommagé,
   obstacle mobile et joueur placé près de chaque checkpoint.
5. Vérifier que le signal 2 à C5_R18 reste envoyé une seule fois et que les
   signaux 31 partent seulement après le dernier déplacement.
6. Contrôler les quatre sorties, la possibilité de combattre ensuite et la
   progression du contrôleur d’objectifs.
7. Sauvegarder/reprendre avant le signal 1, entre 1 et 2, entre chaque checkpoint
   et juste avant la sortie.
8. Revenir à la copie Patch et confirmer la route directe inchangée.

Critères d’arrêt : collision reproductible, équipier coincé, sortie anticipée,
signal dupliqué, progression d’objectif différente ou route directe altérée.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_R17.scr` ;
- `.analysis/scripts/patch/SCRIPTS/CZECH6/C5_R17.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_objective.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_objective2.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_player_teleporter.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_R18.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_R19.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH6/C5_R20.scr` ;
- `Missions/CZECH6/check2.bin` et `Scripts.dta` de `missions.dta`.
