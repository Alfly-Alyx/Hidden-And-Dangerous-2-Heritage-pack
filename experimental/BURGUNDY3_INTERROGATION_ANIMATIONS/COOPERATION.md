# Interrogatoire Co-Burgundy 3 : réalisation moderne distincte

26 septembre 2026 — **MODERNE**, non validé en jeu ni en réseau.

Le profil `co-burgundy3-interrogation-visual-phases` conserve la mission
coopérative d'origine. Il prend ses liaisons dans `mpscripts.dta`, jamais dans
une union de registres ni dans un wrapper solo. Les trois fichiers sont générés
et déployés comme un seul ensemble.

| Fichier Sabre, sous `scripts/co_burgundy3/` | Source → variante, octets | SHA-256 source |
|---|---:|---|
| `bur3_20.scr` | 1691 → 3280 | `3459502e41e62c3b4b4609e5caf92e5af4910240a85203517bb42416e35b6725` |
| `bur3_sas02.scr` | 1670 → 3064 | `ab91c1ca62bcd66196e80e03977aabdeffb04201743799eb85176e204e3d9c7e` |
| `bur3_rozhovor.scr` | 3543 → 3684 | `d16c3cb370569b99074f15b8be3301ca3d35a4de72ef63c9e9dc7233a04f8476` |

Huit sources sont épinglées. Les acteurs `BUR03_20` et `BUR03_SAS02` sont dans
`actors.bin`; le contrôleur lié est **`dummy_rozhovor_sas`** dans `scene2.bin`,
différent du `dummy_rozhovor01` solo. Les scripts coop `bur3_22` et `bur3_23`
attestent les trois animations génériques. Le coop `bur3_06` ne les atteste pas
et n'est pas employé comme preuve gestuelle.

## Protocole ajouté

- Quatre phases locales ordonnées par acteur : les doublons et signaux hors
  ordre ne font pas avancer l'état; les deux acteurs doivent être vivants.
- Garde : signaux 11/13/15/17, gestes `rozhovor2/3/4`, puis effacement.
- SAS : 10/12/14/16, seule l'assise commerciale `kucasedi.i3d` est réaffirmée.
- Arrêt moderne 99 après la dernière voix et avant les arrêts de voix des
  branches mort et interruption 1. Il désactive les seuls récepteurs visuels
  nouvellement introduits chez les deux acteurs.
- L'alarme/mort du garde, la mort du SAS et son dialogue de libération bloquent
  d'abord ces signaux afin qu'ils ne détournent pas les séquences de mission.

Les 19 voix et leurs portées 8/20, les huit signaux historiques, l'interruption
commerciale 1, les rayons 115/7/4, la valeur 17 et les signaux d'objectifs/textes
3/4/12 restent inchangés. Aucun handler nouveau ne saute vers `ACTIVITY` : sa
boucle coopérative existante n'est pas réutilisée comme point de reprise.

Ce profil ne corrige ni une répétition de conversation commerciale ni le
comportement coop général. Le retrait remet les trois sources commerciales;
aucune adaptation solo, aucun nouveau propriétaire ou objectif n'est créé.

## Essais encore nécessaires

Hôte et deux clients indépendants, même paire témoin/variante : chargement,
déclenchement par chaque joueur, entrées simultanées, chacune des quatre phases,
alarme/interruption/mort, libération, objectifs, reconnexion et retrait. Observer
les délais réseau et les signaux arrivés après fermeture. La reprise doit être
testée dans les fonctions effectivement offertes par le mode, sans prétendre
qu'il possède les mêmes sauvegardes que la campagne.

Le registre exige sept scénarios, dont `network`; une preuve solo ne peut pas
valider ce profil. Aucun jeu n'est lancé par le générateur. Le contrôle des
scripts et des fichiers ne démontre pas la priorité réelle des événements.

Référence de comparaison : [étude des deux variantes](PROPOSITION.md).
