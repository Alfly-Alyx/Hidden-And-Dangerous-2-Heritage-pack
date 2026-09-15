# Co-Burgundy3 — ambiance restaurée

État : **import fidèle spécifié, aucun registre actif**, 14 septembre 2026.
La mission coop commerciale reste intacte.

## Verdict

La reconstruction peut être strictement additive et presque entièrement
officielle : les dix scripts coop orphelins sont octet pour octet identiques à
leurs versions solo, `sounds.bin` est lui-même byte-identique entre Burgundy3
et Co_Burgundy3, et chacune des 24 frames sonores visées survit en coop.

La seule pièce retirée est la rangée de dix propriétaires
`snd_vrabec01..10` et ses bindings. La variante
`Co-Burgundy3 — ambiance restaurée` doit copier exactement ces dix records de
scène depuis le solo et appliquer la matrice commerciale, sans attacher deux
scripts à un acteur existant et sans recopier les scripts ou les sons.

## Preuves binaires

- Burgundy3 : 87 bindings ; Co_Burgundy3 : 57 ;
- les dix scripts sont les dix orphelins coop concernés ;
- leurs tailles et condensats correspondent individuellement au solo ;
- les deux `sounds.bin` font 14 614 octets et ont le même SHA-256
  `d7991998f0e4e2988ce28d7b902cb19bb8e76cd5e6d481fd6cc234291a406e15` ;
- aucune autre source coop ne vise l'une des 24 frames sonores ;
- les portes `F_door_wood00`, `01`, `02` survivent aussi dans la scène et les
  chemins coop.

## Import exact

Pour chaque propriétaire : copier le record de scène solo, conserver son nom et
son transform, puis créer **un seul** binding suivant `MATRICE_OWNER_SCRIPT.md`.
Ne pas copier `sounds.bin`, ne pas dupliquer le script et ne pas modifier une
porte ou une frame sonore.

Les transforms des contrôleurs sont groupés autour de
`(-70..-73, -1.3, -137..-143)`. Ils servent à porter les scripts ; la
spatialisation est assurée par les frames `S_*` explicitement recherchées dans
les scripts. Les déplacer vers les sons n'est donc ni nécessaire ni fidèle.

## Comportements restaurés

- trois contrôleurs oiseaux choisissent chacun une des trois frames avec des
  pauses de 7,5–32,5 s ou 8–33 s ;
- le bunker choisit parmi trois sons toutes les 9–33 s ;
- pommes de pin, arbres et grincements utilisent respectivement 15–50 s,
  18–48 s et 15–35 s ;
- trois moniteurs suivent l'état ouvert/fermé de leur porte et activent ou
  coupent `S_door02..04`.

Les boucles et timings sont officiels. Toute garde supplémentaire serait une
modification moderne et ne sera ajoutée qu'après mesure d'un défaut réel.

## Tests

1. baseline coop de dix minutes : confirmer l'absence des sons pilotés ;
2. activer un propriétaire à la fois et vérifier qu'une seule famille apparaît ;
3. activer les dix et journaliser cent déclenchements aléatoires ;
4. ouvrir/fermer chaque porte lentement, rapidement et simultanément ;
5. sauvegarder/reprendre pendant une pause, un son et une porte ouverte ;
6. tester hôte, deux clients proches et un client hors portée ;
7. mesurer fréquence, chevauchements, nombre de scripts actifs et coût CPU ;
8. désactiver la variante et retrouver la baseline byte pour byte côté données.

Critères d'arrêt : doublon d'un son, boucle non interrompue, cadence multipliée
par le nombre de clients, porte contrôlée par le mauvais propriétaire ou pic de
coût durable. L'autorité réseau doit être comprise avant publication.

