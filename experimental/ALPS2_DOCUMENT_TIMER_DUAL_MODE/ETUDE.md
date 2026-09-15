# Alps 2 — chronomètre documents en double mode

État : **mode historique/hardcore optionnel, désactivé**, 15 septembre 2026.
La liberté d'exploration actuelle reste la valeur par défaut.

## Vestige officiel

`AL2_alarm.scr` et `AL2_alarm_carn.scr` conservent exactement, au niveau
principal juste avant `Label end`, les deux lignes commentées :

```text
//Delay(90000);
//SendSignal(obj, 1);
```

`obj` résout `AL2_objective`. Le bloc représente l'ancien échec automatique
après 90 secondes. Il n'est pas rattaché au handler d'entrée dans l'archive :
le réactiver tel quel démarre le délai dans le flux principal du contrôleur.

La release actuelle commente le bloc dans les deux scripts. Cette décision est
conservée par le profil `EXPLORATION_FREE`, y compris en Carnage.

## Modes additifs

- `EXPLORATION_FREE` — défaut, aucun chronomètre ; fichiers inchangés ;
- `HISTORICAL_90S` — copie expérimentale du couple de lignes officiel ;
- `HARDCORE_90S` — même mécanique et même durée, étiquette de difficulté
  explicite ; jamais activé implicitement par Carnage.

Les deux derniers profils sont mutuellement exclusifs et mécaniquement
identiques. Ils existent comme choix utilisateur/test, pas comme modification
de la difficulté de base.

## Risques et tests

- vérifier le moment exact de départ au chargement initial et après reload ;
- vérifier que `SendSignal(obj,1)` ne part qu'une fois ;
- terminer les documents avant 90 s puis attendre au-delà ; aucun échec tardif
  ne doit contredire un objectif déjà fini ;
- tester mort/reload et chargement d'une sauvegarde à 89 s ;
- tester normale et Carnage séparément ;
- confirmer que le délai ne retarde pas l'enregistrement des `Whenever` ni la
  cascade d'alarme ;
- rendre le profil indisponible si le moteur ne permet pas d'annuler proprement
  le signal après réussite.

Le fragment brut est fourni pour une reproduction historique contrôlée. Une
version distribuable devrait placer le timer dans un contrôleur dédié et
annulable, mais ce contrôleur serait une création moderne et n'est pas inventé
dans ce lot.
