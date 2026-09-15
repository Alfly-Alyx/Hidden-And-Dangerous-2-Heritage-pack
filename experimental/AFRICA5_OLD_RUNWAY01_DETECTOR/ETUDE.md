# Africa5 — ancien détecteur `runway01`

État : **binding fossile classé comme prédécesseur probable**, 14 septembre
2026. Aucun remplacement n'est créé.

## Verdict

`dummy_runway01 -> AF4_runway01_detector.scr` est le seul binding Africa5 dont
le fichier est absent. La release lie aussi
`dummy_runway -> AF4_runway_detector.scr`, dont le contrôleur couvre déjà les
trois points de piste et possède toute l'autorité sur l'objectif concerné.

Les frames `dummy_runway` et `dummy_runway01` ont exactement le même transform
commercial. Cette superposition, le nom plus général du contrôleur actif et sa
couverture explicite de 01/02/03 forment un faisceau fort en faveur d'un ancien
détecteur par point remplacé par un contrôleur central.

**Décision :** ne pas recréer le fichier absent et ne jamais ajouter un second
écrivain de l'objectif 4 ou de la valeur sauvegardée 40 sans retrouver son code
original et une action distincte.

## Preuves

L'audit effectif trouve 168 bindings, 178 scripts disponibles et un seul script
attaché manquant : `AF4_runway01_detector.scr`. Une recherche sur les 377
entrées Africa5 de `Scripts.dta`, `Patch.dta` et `SabreSquadron.dta` ne trouve
aucune copie de ce nom.

| Frame | Position commerciale `(x, y, z)` |
| --- | --- |
| `dummy_runway` | `(101.101448, -1.002588, 43.667885)` |
| `dummy_runway01` | `(101.101448, -1.002588, 43.667885)` |
| `dummy_runway02` | `(78.255165, -0.977530, 38.970543)` |
| `dummy_runway03` | `(47.061558, -1.002592, 39.562462)` |

Les quaternions de `dummy_runway` et `dummy_runway01` sont eux aussi identiques :
`(0.896662, 0, -0.442717, 0)`.

## Autorité release actuelle

`AF4_runway_detector.scr` :

1. recherche `dummy_runway01`, `02` et `03` ;
2. attend le signal 1 pour activer la surveillance ;
3. toutes les trois secondes, teste les ennemis dans un rayon de 30 autour des
   trois points ;
4. si les trois zones sont vides, réussit exactement l'objectif 4 et écrit
   `SaveGameValue(40, 1)` ;
5. si un ennemi revient, remet l'objectif 4 à l'état incomplet et la valeur 40
   à 0 ;
6. utilise `splneno` pour ne changer l'état qu'à une transition.

`AF4_23.scr`, après la conversation avec Hans Schumann, réussit l'objectif 1,
désactive l'objectif 5 et envoie le signal 1 à `dummy_runway`. La chaîne release
possède donc son déclencheur, ses trois zones, son état courant et sa valeur de
sauvegarde.

## Pourquoi le doublon serait dangereux

Un script recréé sur `dummy_runway01` partirait du même point que le contrôleur
central. S'il testait seulement la première zone, il pourrait réussir trop tôt
l'objectif 4. S'il testait les trois, il doublerait exactement les écritures et
pourrait diverger après réentrée d'un ennemi, sauvegarde ou reprise. Même un
second `splneno` serait indépendant et ne garantirait aucune idempotence entre
les deux propriétaires.

La seule variante expérimentale acceptable avant découverte du fichier est un
**moniteur passif** dans une copie de mission : il peut journaliser l'état de la
zone 01, mais ne doit envoyer aucun signal, modifier aucun objectif et écrire
aucune valeur. Un tel outil serait un diagnostic moderne, pas une
reconstruction.

## Protocole de confirmation

1. mesurer la baseline avant le dialogue de Schumann : aucune surveillance
   active de l'objectif 4 ;
2. terminer le dialogue et vérifier le premier contrôle dans la fenêtre de
   trois secondes ;
3. vider les zones dans tous les ordres : l'objectif 4 ne réussit que lorsque
   01, 02 et 03 sont vides ;
4. réintroduire un ennemi dans chaque zone séparément puis simultanément : la
   valeur 40 et l'objectif reviennent une seule fois à l'état incomplet ;
5. tuer Schumann avant et après son dialogue ; confirmer que seul son chemin
   release décide si le signal 1 part ;
6. sauvegarder/reprendre avant le signal, avec une zone occupée et après succès ;
7. activer éventuellement le moniteur passif et confirmer une trace de
   progression strictement identique ;
8. désactiver toute variante et comparer à la baseline.

Critères d'arrêt : seconde écriture de l'objectif 4, seconde écriture de la
valeur 40, succès avec une zone occupée, oscillation en double, réarmement après
chargement ou dépendance au nombre de clients.

## Sources internes

- `missions.dta : MISSIONS\AFRICA5\scripts.dta`, `scene2.bin`, `actors.bin` ;
- `Scripts.dta` et `Patch.dta : SCRIPTS\AFRICA5\AF4_runway_detector.scr`,
  `AF4_23.scr` ;
- `.analysis/script-bindings-refresh.json` ;
- audit effectif `tools/script_binding_audit.py --mission Africa5`.
