# Faisabilité — Alps 2, Tutorial et Co_Brest

Étude statique du 13 septembre 2026. Cette fiche reste expérimentale : elle ne
crée aucun acteur de mission, n'ajoute aucune liaison et ne modifie pas le jeu.

## Règle de preuve

- **OFFICIEL** : donnée trouvée dans une archive ou une mission commerciale.
- **INFÉRENCE** : interprétation soutenue par les données, mais non prouvée.
- **CRÉATION MODERNE** : acteur, position, comportement ou raccord à concevoir.

## Synthèse

| ID | Élément conservé | Donnée manquante | Faisabilité | Fidélité | Décision |
| --- | --- | --- | ---: | ---: | --- |
| AL2-GUARDS-13-14 | activateur `AL2_13_A1` et son transform | deux soldats et leurs comportements | 1 | 1 | ne pas activer seul ; rechercher une source des acteurs |
| TUT-TALKER-02 | dialogue, porteur de dialogue et script du personnage | acteur, apparence complète et placement | 2 | 2 | copie laboratoire possible avec placement explicitement moderne |
| COB-EXPLGEN | `OBJ_gener` et `obj_gener.scr` copiés du solo | `explgen` et `explgen2` | 3 | 3 | reporter les deux objets solo avant de lier l'objectif |

La variante additive détaillée des gardes 13/14 est maintenant isolée dans
[`ALPS2_AL2_13_14_REMOVED_BEHAVIOURS`](../ALPS2_AL2_13_14_REMOVED_BEHAVIOURS/ETUDE.md).
Elle conserve le verdict d'absence des deux acteurs et propose deux analogues
locaux sans route avant toute liaison du détecteur.

## AL2-GUARDS-13-14 — soldats Alps 2 absents

### Données conservées

**OFFICIEL.** L'acteur libre `AL2_13_A1` et son script complet existent. Sa
position enregistrée est `(1.55, 0.01, -0.68)` ; cette valeur doit être conservée
avec son repère et son parent, et ne doit pas être interprétée seule comme une
coordonnée monde. Lorsque le joueur est à deux unités du porteur, le script
envoie le signal 1 à `AL2_13` et `AL2_14`.

**OFFICIEL.** Aucun frame exact, acteur, script ou binding `AL2_13` ou `AL2_14`
n'a été retrouvé. Les contrôleurs d'alarme survivants contiennent même les
commentaires `al2_13 neni` et `al2_14 neni` (« n'existe pas »), au lieu de leur
envoyer un signal. Cela indique une suppression connue dans la branche finale,
pas une simple liaison oubliée.

### Limites des analogues

**OFFICIEL.** Les soldats voisins `AL2_15` et `AL2_16` acceptent le signal 1,
mais leurs scripts utilisent des chemins, points de regard, animations,
interactions de garde et réactions d'alarme qui leur sont propres. L'activateur
`AL2_15_A1` réveille 15, 16 et 17 après un signal d'alarme, tandis que
`AL2_13_A1` est immédiatement sensible à la proximité du joueur.

**INFÉRENCE.** Les cibles 13 et 14 étaient probablement deux gardes locaux
réveillés ensemble. Rien ne prouve leurs positions, uniformes, armes, modes IA,
trajets ni comportement après le signal 1. Dupliquer 15/16 inventerait ces
éléments et référencerait des checkpoints incompatibles.

### Surface de reconstruction

**CRÉATION MODERNE minimale.** Un prototype demanderait au moins :

1. deux acteurs humains `AL2_13` et `AL2_14` avec modèles, inventaires et camps ;
2. deux transforms, parents et orientations ;
3. deux scripts recevant le signal 1 ;
4. un état initial suspendu ou inactif cohérent avec l'activateur ;
5. une réaction après activation et une réaction d'alarme ;
6. les éventuels checkpoints et points de regard nécessaires ;
7. la liaison de l'activateur seulement après existence des deux récepteurs.

Le comportement moderne le plus petit serait un réveil sans trajet inventé,
suivi d'un mode défensif local. Même cette solution reste une interprétation et
ne doit vivre que dans une mission laboratoire tant qu'aucune source officielle
ne décrit les soldats.

**Interdiction.** Ne jamais lier `AL2_13_A1.scr` seul : il ne ferait qu'envoyer
deux signaux vers des frames inexistants et pourrait masquer l'ampleur réelle du
contenu absent.

### Tests et arrêt

- vérifier le repère/parent exact du transform de `AL2_13_A1` ;
- contrôler l'approche à deux unités, les approches répétées et plusieurs
  joueurs ;
- tester activation avant/après alarme, mort anticipée d'une cible et
  sauvegarde/reprise ;
- vérifier que les nouveaux acteurs n'empruntent aucun checkpoint de 15/16 ;
- arrêter le prototype si aucune position ou fonction des soldats ne peut être
  attribuée à une source officielle.

## TUT-TALKER-02 — second interlocuteur du Tutorial

L'étude dédiée, les transforms attestés et le placement candidat sont dans
[`TUTORIAL_T_DUMMY_SPEECH_RECONSTRUCTION`](../TUTORIAL_T_DUMMY_SPEECH_RECONSTRUCTION/ETUDE.md).
La recherche locale n'a pas retrouvé le transform original de Talker_02 ; le
candidat documenté ne change donc pas le niveau de fidélité de cette fiche.

### Chaîne officielle restante

**OFFICIEL.** Le porteur libre `T_dummy_speech` et son script complet existent,
ainsi que l'acteur `TUT_Talker_01`. À sept unités du porteur, la conversation
fait parler l'officier 01 puis `TUT_Talker_02`. Elle s'interrompt lorsque le
joueur s'éloigne à plus de dix unités.

**OFFICIEL.** `TUT_Talker_02.scr` subsiste mais son acteur est absent de
`scene2.bin`, `actors.bin` et `sounds.bin`. Son script applique la texture de
visage `e_f073`, signale la mort au contrôleur `dummy_objectives` par le signal
16, peut se tourner vers l'interlocuteur 01 ou vers le joueur et jouer
`%%rozhovor`. Le script du dialogue adresse directement ses répliques au frame
`TUT_Talker_02`.

**OFFICIEL, branche dormante.** `T_dummy_speech.scr` initialise `goodone` à 1.
La branche positive est donc celle qui est effectivement atteignable dans le
script conservé. Les répliques négatives présentes dans le fichier ne prouvent
pas qu'un calcul de performance ait été livré ; aucune logique ne change ici
`goodone`.

### Reconstruction proposée

**INFÉRENCE.** Le personnage 02 était placé assez près de l'officier pour une
conversation audible et visible. Sa texture de visage et ses commandes de
rotation prouvent un humain interlocuteur, mais pas son corps, uniforme,
équipement, position ou orientation initiaux.

**CRÉATION MODERNE minimale.** Rechercher d'abord le personnage dans une scène
de démo, une version antérieure ou une ressource de Tutorial. Si aucun transform
n'est retrouvé :

1. créer un seul acteur humain `TUT_Talker_02` utilisant la texture officielle
   `e_f073` et sans équipement inventé non nécessaire ;
2. le placer près de `TUT_Talker_01`, avec ligne de vue réciproque et hors du
   passage du joueur ;
3. lier `TUT_Talker_02.scr` au nouvel acteur ;
4. lier `T_dummy_speech.scr` uniquement à son porteur libre existant ;
5. conserver `goodone = 1` et ne pas inventer de calcul pour la branche négative.

La position, le corps et l'orientation choisis doivent être étiquetés comme
adaptation moderne. La présence du dialogue ne transforme pas ces choix en
données officielles.

### Tests

- une seule conversation lors de l'entrée à sept unités ;
- arrêt propre au-delà de dix unités et absence de voix résiduelle ;
- synchronisation des deux interlocuteurs, sous-titres et morphing facial ;
- comportement si l'un des deux personnages meurt avant ou pendant la scène ;
- signal 16 vers `dummy_objectives` sans double échec ;
- sauvegarde/reprise avant, pendant et après le dialogue ;
- absence de blocage du chemin et de conflit avec les autres séquences Tutorial.

## COB-EXPLGEN — objectif des générateurs de Co_Brest

### Données conservées

**OFFICIEL.** `OBJ_gener` et `obj_gener.scr` sont copiés du solo vers Co_Brest,
à la même position. Les versions solo et coop du script ont le même contenu. Le
script attend deux frames, `explgen` et `explgen2`, absents de `scene2.bin`,
`actors.bin` et `items.dat` coop.

**OFFICIEL.** Lorsque les deux objets atteignent l'état acteur 1, le script met
la valeur de jeu 12 à 1 et fait passer l'objectif 5 par actif puis réussi. Si
l'un des deux repasse à l'état 0, la valeur revient à 0 et l'objectif 5 devient
inactif. Un texte 51999802 n'est affiché qu'une fois lors de la première pose
complète.

**INFÉRENCE.** Les deux cibles sont des supports de minage des générateurs. Le
script prouve qu'il en faut exactement deux et qu'il surveille leur état ; il ne
prouve pas, à lui seul, leur modèle, leur volume de pose, leur parent ou leur
transform coop.

### Reconstruction proposée

**Priorité aux données solo.** Extraire pour `explgen` et `explgen2` les records
d'acteurs et d'items, modèles, transforms, parents et propriétés de minage du
solo. Les reporter sans changement lorsque les mêmes parents et la même
géométrie existent en coop. Toute adaptation de transform ou de parent doit être
documentée séparément.

**CRÉATION MODERNE minimale.** Deux objets de minage portant exactement les
noms attendus, avec les mécanismes nécessaires pour faire évoluer leur état de
0 à 1 et inversement. Lier `obj_gener.scr` à `OBJ_gener` seulement après avoir
vérifié les deux frames. Ne pas créer des dummies dont l'état serait forcé : cela
validerait l'objectif sans reproduire l'action de minage.

### Tests

- poser les charges dans les deux ordres et par deux joueurs différents ;
- poser une seule charge : objectif 5 non réussi ;
- retirer ou perdre une charge : retour cohérent à l'état incomplet ;
- vérifier le texte unique, la valeur de jeu 12 et tous les statuts de
  l'objectif 5 ;
- sauvegarder/reprendre avec zéro, une et deux charges ;
- vérifier la réplication hôte/client et l'absence de validation en double ;
- confirmer que l'explosion ou la destruction ultérieure des générateurs n'est
  pas supposée être gérée par ce seul script de minage.

## Exclusions confirmées

### Czech 2 — `bigboskecac.scr`

**OFFICIEL.** Ce fichier ne joue que les deux premières répliques 19993810 et
19993811 après le signal 1. `cut2.scr` contient ces répliques, poursuit la
conversation avec trois lignes supplémentaires, gère caméras, joueur dupliqué,
animations, musique et fin de cinématique. Dans `doors2.scr`, l'envoi du signal
à `bigboskecac` est commenté alors que l'autre action de porte reste active.

**Décision.** Ancienne conversation courte remplacée par la cinématique 2. Ne
pas recréer son propriétaire et ne pas rétablir le signal commenté.

### Norway — `tirpicmined.scr`

**OFFICIEL.** Ce fichier se contente de compter deux signaux puis d'envoyer le
signal 5 au contrôleur d'objectifs. `R_Nor_OBJ_1_a.scr` surveille directement
les deux objets de mine, gère pose et retrait, puis envoie le signal 5 et la
musique lorsque les deux mines sont posées.

**Décision.** Ancien compteur remplacé. Ne pas le lier en parallèle à la
variante active.

## Sources internes

- `output/audit/full-game-audit.json`
- `output/audit/script-bindings.json`
- `output/audit/candidate-owner-audit.json`
- `.analysis/scripts/base/SCRIPTS/ALPS2/`
- `.analysis/scripts/base/SCRIPTS/TUTORIAL/`
- `.analysis/scripts/sabre/Scripts/brest/`
- `.analysis/scripts/sabre/Scripts/Co_brest/`
- `.analysis/scripts/base/SCRIPTS/CZECH2/`
- `.analysis/scripts/base/SCRIPTS/NORWAY/`
