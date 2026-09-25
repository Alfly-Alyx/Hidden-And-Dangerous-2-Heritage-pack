# Co-Burgundy3 — ambiance restaurée

État : **comparaison scène/registre construite et désactivée**, 25 septembre 2026.
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

### Construction reproductible hors moteur

[`build_burgundy_ambient_patch.py`](../../tools/build_burgundy_ambient_patch.py)
réalise maintenant l'import local, sans extraire une mission jouable. Il vérifie
huit fichiers de mission épinglés, l'empreinte de l'ensemble des **67 scripts coop**,
et l'identité des dix scripts avec leurs versions solo : **85 sources lues et
consignées**. Les noms des 24 sons et des trois portes sont contrôlés dans les
sources coop typées, y compris `scene.4ds` pour les portes. Aucun autre script
coop de cet ensemble ne référence littéralement l'un de ces 24 sons.

Les dix records ont chacun 168 octets : type dummy 6, nom, position, quaternion,
échelle, position monde, référence `Primary sector` et boîte de bornes. Ils sont
copiés en entier, dans l'ordre de la scène solo, sans arrondir les flottants.
Le groupe de frames passe de 2028 à 2038 records. La suppression des seuls ajouts
et le rétablissement des deux longueurs de conteneurs doivent restituer chaque
octet de la scène coop originale. Le secteur parent est une référence commerciale
conservée, pas un nouveau secteur dont la géométrie aurait été validée en moteur.

Le registre coop est **`mpscripts.dta`**, pas `scripts.dta`. Ses 57 paires existantes
restent identiques et dix paires solo brutes sont ajoutées : 67 liaisons. Un
propriétaire homonyme, un script déjà lié, un record ambigu ou une source différente
sont refusés. Les fichiers de sons, scripts, acteurs, routes et objectifs ne sont
pas réécrits.

| Sortie variante locale | Octets | SHA-256 |
|---|---:|---|
| `scene2.bin.disabled` | 5008020 | `55f99680a526252219be8806c0af8727b3a5bdc1d3d8a7ca95cae1906370000c` |
| `mpscripts.dta.disabled` | 2470 | `06ed5eede4d97546228b336fb20878cf9f9512c72ba316656276d3b22870a934` |

Le ZIP local `co-burgundy3-ambience.scene-patch.zip.disabled` contient les deux
fichiers témoins, les deux variantes et un rapport, tous suffixés `.disabled`.
Il reste dans `.analysis/scene-patches/`, ignoré par Git. Il n'a ni manifeste
activable ni entrée de menu. **Ce n'est pas un 21e laboratoire de mission ni une
conversion coop vers solo**; sa sélection, son espace de mission et ses sauvegardes
restent à préparer dans une copie de test explicitement isolée.

Quinze tests sur des données inventées couvrent copie exacte, collisions,
réapplication, structure, parent/transform, registre tronqué, paire manquante,
empreinte incorrecte, extension active, écriture dans le jeu et écrasement.
Quatre tests de recettes portent ensuite le total commun à 19 : l'ajout de
Burgundy 2 ne relâche ni l'identité des dix scripts ni celle du fichier sonore
de Burgundy 3. Les deux sorties binaires Burgundy 3 restent byte-identiques.
Les deux surcharges locales préexistantes `bur3_obj3.scr` et `bur3_objectives.scr`
sont refusées en mode strict; `--archives-only` les exclut et consigne leurs
empreintes, sans les modifier ni valider leur compatibilité.

```powershell
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --archives-only
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --archives-only --build
```

Le premier appel n'écrit aucun résultat. Le second exige une sortie locale
désactivée inexistante; un ZIP déjà présent est refusé, jamais remplacé.

### Essais en jeu encore obligatoires

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
