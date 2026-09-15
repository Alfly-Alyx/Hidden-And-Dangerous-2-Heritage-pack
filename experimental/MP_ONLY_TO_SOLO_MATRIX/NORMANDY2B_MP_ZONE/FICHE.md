# Prototype — reconstruction — Normandy2B

Statut : **BLOQUÉ, registre commercial vide**.

## Origine

- entrée Teamplay `FRONTLINE`, fichiers effectifs issus de `Patch.dta` ;
- douze fichiers complets, dont chemins, items, volumes et `scripts.dta` ;
- le registre contient zéro binding et aucun script local n'est disponible ;
- 21 acteurs structurants : `player_1`, zones 1 à 5, dix caisses de munitions,
  statue et trois échelles.

## Wrapper

- **ORIGINE** : carte, `player_1`, zones, items et chemins ;
- **DÉDUCTION** : employer `player_1` comme candidat de départ et ordonner les
  zones après relevé spatial ; réutiliser seulement les primitives génériques
  de Normandy2 ;
- **CRÉATION** : tous les PNJ, leurs bindings, l'objectif, la fin et les textes.

Le contrôleur Normandy2 dépend de centaines de frames propres et ne peut pas
être copié en bloc. La variante `NORMANDY2_REMOVED_DEFENDERS` n'est pas un
roster prêt pour Normandy2B.

Tester sol de `player_1`, parcours de chaque chemin, volumes, navigation des
véhicules éventuels, victoire/échec et sauvegarde. Spéculation : **3/3**.

