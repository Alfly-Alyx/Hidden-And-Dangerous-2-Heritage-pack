# Plan de reconstruction — compteur et Platoon 07–09

## Graphe proposé

`mort P01/P02/P03` → observateur monostable propre → `signal 10` → compteur
propre → troisième événement, latch → `signal 7` vers P06/P07/P08/P09.

## Classification

| Élément | Statut |
| --- | --- |
| noms P06–P09, signaux 10 et 7, seuil de trois | vestiges officiels |
| placement correct du seuil dans `OnSignal(10)` | correction mécanique |
| P01/P02/P03 comme sources | choix `MODERNE` |
| latch d'émission unique | garde `MODERNE` |
| réveil idempotent de P06 | composition de son signal 5 officiel |
| acteurs, équipements et routes P07–P09 | manquants ; à créer/valider |
| extension du scan `CZ4_OD` | adaptation obligatoire de la variante |

## Porte avant scripts

Aucun contrôleur `.scr.disabled` n'est fourni avant que P07–P09 aient : un
acteur, un transform sans collision, un équipement, une route valide, un
handler 7 et un handler de mort vers le **contrôleur de variante**. Le compteur
doit ensuite être testé avec des observateurs instrumentés avant toute liaison
aux trois soldats release.

## Sauvegarde

Le compteur, le masque des trois sources et le latch final doivent être
persistés ensemble dans des valeurs réservées à la variante. À la reprise, un
acteur déjà mort ne doit pas émettre une seconde fois et un compteur arrivé à
trois ne doit pas rediffuser le signal 7.

