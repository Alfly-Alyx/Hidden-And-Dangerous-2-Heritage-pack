# Faisabilité — déclencheurs Africa 1 et validation Opel Alps 1

Étude statique du 13 septembre 2026. Cette fiche est expérimentale et destinée
à une intégration contrôlée ultérieure. Elle n'ajoute aucun binding et ne
modifie aucune mission.

## Règle de preuve

- **OFFICIEL** : contenu présent dans les archives commerciales auditées.
- **INFÉRENCE** : fonction probable, mais non démontrée intégralement.
- **CRÉATION MODERNE** : position, acteur ou raccord qu'il faudrait concevoir.

Une faisabilité élevée ne prouve pas qu'une branche soit souhaitable : un petit
déclencheur peut modifier profondément l'ordre des objectifs ou lancer deux fois
une séquence déjà gérée par la version release.

## Synthèse

| ID | Script survivant | Support manquant | Faisabilité | Fidélité | Verdict |
| --- | --- | --- | ---: | ---: | --- |
| AF1-OLD-CUT02 | `AF1_cut02_detector.scr` | porte ou point d'utilisation | 2 | 1 | probablement remplacé ; comparer avant tout prototype |
| AF1-OLD-DOORUSE | `AF1_dvereonuse_detector.scr` | porte ou point d'utilisation | 1 | 1 | branche incomplète, signal principal sans récepteur |
| AF1-OLD-OBJ01 | `AF1_obj01_detector.scr` | point d'utilisation proche de la scène 10 | 2 | 1 | doublon probable du détecteur release |
| AF1-OLD-OBJ03 | `AF1_obj03_detector.scr` | volume de regroupement final | 2 | 1 | ancienne sémantique d'objectif ; position déterminante |
| AL1-OLD-OPEL | `obj_opel.scr` | objet utilisable et émetteur du signal 1 | 1 | 1 | ancienne validation en deux étapes ; ne pas lier au véhicule |

## Africa 1 — constat commun

**OFFICIEL.** Les quatre scripts sont présents mais non liés. Leurs frames
cibles internes existent. En revanche, aucun propriétaire nommé
`AF1_cut02_detector`, `AF1_dvereonuse_detector`, `AF1_obj01_detector` ou
`AF1_obj03_detector`, ni variante dummy évidente, n'apparaît dans `scene2.bin`,
`actors.bin` ou le registre effectif.

**INFÉRENCE.** Les noms et commentaires montrent des portes, points
d'utilisation ou volumes de proximité d'une branche antérieure. Ils ne donnent
ni transform, ni parent, ni dimensions, ni propriété « utilisable ».

**CRÉATION MODERNE commune.** Une reconstruction demanderait, selon le cas, un
acteur interactif ou un volume invisible, son transform, son parent, ses
dimensions et sa liaison. Pour un `OnUse`, un dummy purement inerte ne suffit pas
nécessairement : il faut prouver le type d'objet qui recevait l'action du joueur.
Pour une détection de distance, la position fait partie du comportement et ne
peut pas être choisie pour simplement « faire marcher » le script.

### AF1-OLD-CUT02 — `AF1_cut02_detector.scr`

**OFFICIEL.** À l'utilisation, le script lance la cinématique 10 et se termine.
Indépendamment, il compte les signaux 10 ; au seizième, il réveille
`AF1_posila_01` à `06` simultanément.

**Recouvrement release officiel.** `AF1_cut10_detector.scr` lance déjà la
cinématique 10, avec proximité stricte et vérification de l'état de `AF1_21`.
`AF1_posily_detector.scr` active déjà les renforts à partir d'un seuil dynamique
du nombre d'ennemis : il couvre `AF1_posila_01` à `10` et le char, avec une
séquence temporisée. La branche release est donc plus complète que le compteur
fixe de seize morts.

**Verdict.** Ne pas recréer par défaut. Il faudrait démontrer en jeu un défaut
distinct à la fois dans le lancement de la scène 10 et dans les renforts. Lier
l'ancien script en parallèle risquerait une double cinématique, des signaux
répétés et une vague déclenchée selon deux seuils incompatibles.

### AF1-OLD-DOORUSE — `AF1_dvereonuse_detector.scr`

**OFFICIEL.** Sa moitié renforts reproduit le compteur fixe de seize morts du
cas précédent. Son `OnUse`, limité à une exécution, envoie le signal 5 à
`AF1_20`.

**OFFICIEL, incohérence.** Le script survivant de `AF1_20` ne contient aucun
traitement du signal 5. Il accepte les signaux 20 et 21 et possède déjà des
réveils de proximité à 150 et 50 unités. L'effet principal de l'ancien `OnUse`
est donc sans récepteur dans la chaîne commerciale conservée.

**Verdict.** Branche ancienne ou incomplète. Ne pas créer une porte arbitraire
et ne pas ajouter un nouveau gestionnaire de signal à `AF1_20` sans source : ce
seraient deux inventions. Le cas reste suspendu même si une position plausible
est trouvée, tant que le contrat du signal 5 n'est pas prouvé.

### AF1-OLD-OBJ01 — `AF1_obj01_detector.scr`

**OFFICIEL.** À l'utilisation et à moins de trois unités, il lance une seule
fois la cinématique 10, puis se termine quand cette scène est achevée.

**Recouvrement release officiel.** `AF1_cut10_detector.scr` déclenche déjà la
même scène selon la proximité et l'état de l'officier `AF1_21`. Le script ancien
n'ajoute ni objectif, ni signal, ni conséquence aval différente.

**Verdict.** Doublon probable. Un prototype n'est recevable que si un scénario
reproductible montre que le détecteur release ne couvre pas un point
d'interaction officiel encore visible. Dans ce cas seulement, rechercher le
propriétaire dans une autre version de la scène avant toute création.

### AF1-OLD-OBJ03 — `AF1_obj03_detector.scr`

**OFFICIEL.** Le script surveille un rayon de dix unités. Lorsque tous les
joueurs y sont et que les objectifs 1 et 2 sont réussis, il marque directement
l'objectif 3 comme réussi.

**Recouvrement release officiel.** `AF1_obj.scr` définit l'objectif 3 comme
l'élimination de tous les ennemis et le résout à partir du compteur de carnage,
en coordination avec l'objectif des documents. La logique release possède aussi
ses propres transitions finales et de véhicules.

**INFÉRENCE.** Le script non lié pourrait représenter une ancienne zone de
sortie ou de regroupement. Sans position, l'ajouter changerait potentiellement
l'objectif « éliminer les ennemis » en simple présence dans un volume.

**Verdict.** Ne pas reconstruire sans retrouver le transform original et une
preuve que cette sémantique devait coexister avec la logique release. Même une
position historiquement plausible ne suffit pas si elle permet de valider
l'objectif avant l'élimination attendue.

## Alps 1 — AL1-OLD-OPEL

### Chaîne survivante

**OFFICIEL.** `obj_opel.scr` est présent mais non lié. Il commence désarmé. Un
signal 1 place sa variable interne à 1 ; une utilisation ultérieure envoie alors
le signal 15 au contrôleur `objectyves`. Aucun acteur propriétaire identifiable
et aucun émetteur démontré de ce signal 1 n'ont été retrouvés.

**OFFICIEL, logique release.** `opel_detector.scr` et `opel_detector2.scr`
envoient déjà le signal 15 lorsque `La_OpelE_` quitte sa position, selon l'état
du conducteur. `opel_ujel.scr` et `opel_znic.scr` gèrent d'autres résultats de
la même séquence, dont les signaux 4 et 20.

**INFÉRENCE.** `obj_opel.scr` correspond vraisemblablement à une ancienne
validation manuelle en deux étapes : un événement lié au conducteur armait un
point utilisable, puis le joueur confirmait l'action. Les scripts release ont
remplacé cette validation par le déplacement et l'état du véhicule.

### Reconstruction conditionnelle

**CRÉATION MODERNE minimale.** Il faudrait retrouver ou créer :

1. le propriétaire utilisable, distinct du véhicule ;
2. son transform et son parent ;
3. l'émetteur exact du signal 1 et sa condition ;
4. la liaison au script officiel, sans retirer la logique release pendant la
   phase comparative.

Il est interdit de lier directement `obj_opel.scr` à `La_OpelE_` : le véhicule
possède déjà sa chaîne et l'action d'utilisation peut servir à l'embarquement ou
à une autre interaction. Un proxy choisi près de l'Opel sans preuve de position
resterait également arbitraire.

**Condition d'arrêt.** Sans propriétaire ou transform officiel et sans émetteur
du signal 1, aucun prototype fonctionnel ne doit être produit. Si la chaîne
release envoie correctement les signaux 15, 4 et 20 dans tous les scénarios,
classer `obj_opel.scr` comme branche obsolète.

## Protocole comparatif avant création

Pour chaque candidat, établir d'abord une trace release sans aucune liaison
nouvelle :

- déclenchement unique de la cinématique 10 et état de `AF1_21` ;
- seuil, ordre et nombre des renforts Africa 1 ;
- progression des objectifs 1, 2 et 3, y compris en coopération ;
- état et réveil de `AF1_20` ;
- Alps 1 : conducteur vivant/mort, Opel immobile/parti/détruit, signaux 15/4/20 ;
- sauvegarde et reprise avant et après chaque transition.

Une différence observable doit être formulée avant de créer un support. Les
essais ultérieurs devront rester sous ce dossier, ne jamais écrire dans
l'installation du jeu et ne pas être incorporés à l'installateur principal.

## Sources internes

- `output/audit/script-bindings.json`
- `output/audit/full-game-audit.json`
- `.analysis/scripts/base/SCRIPTS/AFRICA1/`
- `.analysis/scripts/base/SCRIPTS/ALPS1/`
