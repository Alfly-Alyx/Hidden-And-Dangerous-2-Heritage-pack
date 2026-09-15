# Contrat commun d'un wrapper solo

## Artefacts attendus avant lancement

- dossier de mission portant un nom différent de la source MP ;
- copie documentée des fichiers de carte nécessaires ;
- `scripts.dta` propre au wrapper et scripts `.scr.disabled` avant test ;
- un point de départ allié, sans réemployer silencieusement tous les spawns MP ;
- un contrôleur d'initialisation monostable ;
- objectifs et textes réservés au wrapper ;
- une réussite et au moins un échec ;
- une fin idempotente, sans vote, respawn, drapeau ou score MP ;
- signature de sauvegarde propre.

## Stratégie minimale de test

1. ouvrir la carte source dans son mode MP et enregistrer la baseline ;
2. lancer le wrapper avec zéro ennemi pour valider chargement/collision ;
3. ajouter un acteur, un objectif et une sortie instrumentés ;
4. tester victoire, échec, mort d'équipe, sauvegarde et reprise ;
5. augmenter les groupes un par un et tester navigation/équilibrage ;
6. relancer la carte MP et comparer catalogue, spawns, zones et scripts.

Les contrôleurs de mission apparentés ne sont réutilisables que fonction par
fonction. Copier tout un script géométrie-dépendant n'est pas une déduction.

