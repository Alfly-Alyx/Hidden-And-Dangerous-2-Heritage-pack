# Czech 3 — acteurs retirés de la villa

État : **branche additive définie, implantation bloquée**, 14 septembre 2026.
Aucun acteur, binding ou script commercial n'est modifié.

## Verdict

Quatre scripts complets ou substantiels survivent sans acteur :
`InViller_1`, `Plotman_01`, `Plotman_02` et `SAS_1`. Ils forment des fragments
compatibles avec un événement de villa, mais pas un événement commercial prêt
à réactiver. Les transformations initiales, le déclencheur de la scène SAS et
son raccord d'objectif ont disparu ; le signal final 6 n'est traité par aucun
contrôleur actuel.

La seule voie sûre est une entrée séparée, proposée sous le nom
`Czech 3 — Villa [Reconstruction]`, avec son contrôleur, son latch et son
compteur de morts. Le compteur release de `dummy_reinforcement` ne doit pas
recevoir directement les morts ajoutées.

## Preuves conservées

L'audit compte 70 liaisons et 84 scripts. Les quatre scripts étudiés sont
orphelins ; leurs acteurs ainsi que `Shocker_1` sont absents. En revanche :

- `dummy_sit_vila1`, `dummy_reinforcement` et `e_ktable3` existent ;
- `Dog_0101`, `HP1_2`, `Dog_0103`, `Dog_0106` et `BFD_1` survivent dans
  `check2.bin` ;
- `camera_show` ne survit pas.

### `InViller_1`

Le script assoit l'acteur sur `dummy_sit_vila1`, le fait se lever et devenir
agressif à l'alarme, puis envoie le signal 0 à `dummy_reinforcement` à sa mort.
Le dummy donne un ancrage de pose, pas une transformation initiale complète.

### `Plotman_01` et `Plotman_02`

Ils démarrent suspendus. Les signaux 1, 2 ou 3 sélectionnent des variantes de
trajets parmi les repères encore présents. Aucun émetteur survivant ne vise les
noms d'acteurs retirés. Les routes prouvent des déplacements possibles, mais
pas leurs positions de départ ni la condition de choix.

### `SAS_1` et `Shocker_1`

Le signal 2 réveille le SAS. Après une seconde, le script enflamme puis tue
`Shocker_1`, joue deux sons, suit `BFD_1`, affiche successivement les
sous-titres `20994008`, `20994009`, `20994007`, puis envoie le signal 6 à
`e_ktable3`.

`e_ktable3` est aujourd'hui lié à `setobjectives.scr`, qui assigne le
contrôleur d'objectifs selon le type de partie. `R_Cz3_objectives.scr` traite
les signaux 2, 3 et 5, jamais 6. Le raccord final est donc mort. La présence et
l'affichage des trois textes doivent encore être vérifiés en jeu ; leur absence
de l'inventaire de noms de fichiers de langue ne suffit pas à conclure.

## Séparation obligatoire de la progression

`R_Cz3_reinforcement.scr` compte les signaux 0 issus des cadavres et déclenche
sa suite au-delà de 18. Ajouter les morts anciennes à ce compteur peut avancer
prématurément l'objectif release. La variante doit donc posséder :

- un contrôleur `villa_reconstruction` indépendant ;
- un latch de déclenchement, réinitialisé uniquement au chargement de mission ;
- un compteur propre pour les quatre acteurs ajoutés ;
- aucun signal 6 envoyé à `e_ktable3` ;
- soit une fin narrative sans progression, soit un objectif bonus moderne au
  slot libre 4 après validation du catalogue.

L'objectif bonus est un choix de conception, pas une restauration. Sa réussite
ne doit jamais compter les morts release ni débloquer une étape commerciale.

## Déclencheur proposé, non attesté

Le déclencheur moderne le moins intrusif serait un volume propre à la variante
à l'entrée de la villa. Il active une fois les Plotman et le SAS, après avoir
vérifié que les quatre acteurs et `Shocker_1` existent. Une activation par
alarme globale serait plus fidèle au comportement d'`InViller_1`, mais trop
large tant que la scène d'origine n'est pas connue.

## Exclusions

- `help_track.scr` reste exclu : il exige `camera_show`, absent ; la caméra C1
  seule ne reconstitue pas la trajectoire.
- `barel_1`, `barel_2`, `barel_3` restent un ensemble optionnel séparé : leurs
  cibles `la_bar_1`, `la_bar_2`, `la_bar_3` et leurs placements sont absents.
- aucun équipement, uniforme ou modèle n'est déduit du nom des scripts.

Les lacunes détaillées figurent dans
`ELEMENTS_A_RECREER_OU_SPECULATIFS.md`.

## Tests avant toute activation

Tester séparément : entrée furtive, alarme avant volume, volume avant alarme,
mort anticipée de chaque acteur, mort de Shocker, séquence complète des trois
sous-titres, sauvegarde avant/pendant/après la scène et désactivation totale de
l'option. Le compteur release doit produire exactement la même trace dans la
baseline et dans la variante sans acteurs additionnels.

