# Matrice d'activation et de tests

| John | Chien | But principal | Critères |
| ---: | ---: | --- | --- |
| 0 | 0 | baseline coop | objectifs, IA, sauvegarde et réseau inchangés |
| 1 | 0 | parcours John | trois routes, suspension, recrutement à 2 m, aucune incidence dynamite |
| 0 | 1 | comportement chien | maître, alarme, attaque, mort du maître, absence de route invalide |
| 1 | 1 | coexistence | aucun conflit de frame, de navigation, d'objectif ou de sauvegarde |

Pour chaque ligne : solo hôte, hôte avec au moins un client, arrivée tardive,
mort/respawn près de l'acteur, sauvegarde avant et après activation, tir ami,
alarme globale et fin de mission. Rejouer ensuite avec les options désactivées
et comparer la trace à la baseline.

## Critères d'arrêt

- John valide, bloque ou change un objectif coop ;
- un client ne voit pas la même équipe ou le même état de suspension ;
- le chien cible un allié, perd son maître différemment selon l'autorité ou
  appelle une route absente ;
- une sauvegarde chargée avec une autre combinaison conserve un acteur fantôme.

