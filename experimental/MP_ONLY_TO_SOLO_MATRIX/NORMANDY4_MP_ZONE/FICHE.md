# Prototype — reconstruction — Normandy4 Frontline

Statut : **BLOQUÉ, contrôleur et sons de mission absents**.

## Origine

- entrée Teamplay `FRONTLINE` ;
- neuf fichiers : acteurs, véhicules, chemins, items, géométrie et collision ;
- pas de registre, scripts, sons, effets ni volumes propres ;
- 15 acteurs structurants : deux Kübelwagen, half-track, Krupp, Panther,
  Sherman, deux MG, `multispawn` et zones 1 à 5.

## Wrapper

- **ORIGINE** : carte, véhicules, armes, cinq zones ;
- **DÉDUCTION** : séquence zone1 → zone5 et camps d'après le Frontline ;
- **CRÉATION** : acteurs/équipages, logique véhicules, volumes nécessaires,
  ambiance, objectifs, textes, échec et fin.

Aucun parent solo Normandy4 n'existe. Ne pas emprunter silencieusement les
volumes ou sons d'une autre carte.

Tester collisions de tous les véhicules, navigation, secteurs MG, absence de
volumes, sauvegarde et chargement sans son manquant. Spéculation : **3/3**.

