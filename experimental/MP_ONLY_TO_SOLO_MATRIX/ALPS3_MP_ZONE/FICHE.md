# Prototype — reconstruction — Alps3 Frontline

Statut : **BLOQUÉ, contrôleur solo à créer**.

## Origine

- entrée `Alps3`, Teamplay `FRONTLINE` ;
- dix fichiers : acteurs, chemins, effets, items, loader, map, scene, scene2,
  sons et collision ;
- aucun registre ni script ;
- sept acteurs structurants : `multispawn`, `zone1..5`, secteur primaire ;
- chaque zone possède un repère `zoneNspawn` et trois jeux de drapeaux dans la
  scène.

## Wrapper

- **ORIGINE** : carte et cinq zones ;
- **DÉDUCTION** : progression linéaire zone1 → zone5, car elle reprend l'ordre
  spatial Frontline ;
- **CRÉATION** : spawn solo dans zone1, groupes ennemis, validation séquentielle,
  texte et extraction en zone5.

Les scripts d'Alps1/Alps2 peuvent fournir des patrons d'IA, jamais des noms de
frames ou objectifs transplantés en bloc.

## Tests

Tracer l'ordre réel des zones, refuser toute zone inaccessible, tester retour
arrière, capture anticipée, mort du dernier ennemi, équipe incomplète et
sauvegarde entre chaque étape. Niveau de création : **3/3 pour la mission,
0/3 pour la carte**.

