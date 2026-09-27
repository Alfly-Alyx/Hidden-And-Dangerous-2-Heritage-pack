# Échec de réinstallation du setup 0.10.0 — 27 septembre 2026

## Symptôme observé

La première installation dans le jeu commercial s'est terminée et le contrôle en lecture seule indique : menu actif, 11 adaptations présentes, diagnostics actifs. Une seconde exécution du setup a échoué lors de l'activation du nouveau menu. Le journal système finit par « Installation du nouveau menu impossible. ».

## Cause vérifiée

La passe Exploration libre a modifié exactement 11 fichiers Missions/HP_Solo_*/tree.klz après leur intégration par le gestionnaire. Le gestionnaire conserve leurs empreintes originales et refuse, par sécurité, de les remplacer à la relance. Les 11 fichiers du jeu correspondent octet pour octet à la transformation TreeKlzPatcher.Patch appliquée aux 11 fichiers originaux de la bibliothèque. Aucun autre fichier de l'inventaire géré ne divergeait lors du contrôle.

## Correctif et vérifications avant publication

- L'inventaire des arbres gérés empêche la passe Exploration libre de modifier ces fichiers.
- Avant la réintégration, les onze arbres historiques sont remis sous gestion uniquement si leurs octets correspondent exactement à la transformation attendue. Toute autre modification reste intacte et sera signalée par le gestionnaire.
- Les onze messages d'export sont transmis à l'interface dès leur émission pour rendre la phase de création visible.
- Le jeu de test a été lancé avant la reconstruction du 27 septembre. Le setup EXE local a été reconstruit pour essai utilisateur ; son empreinte SHA-256 est `754CD883F807278F5D13B6D626D9C92E8C8CB77F38D0F52816B491B8692434DC`.
- La reconstruction a réussi les 31 tests du menu natif, les 2 tests des lignes de missions, les autotests du pack solo, du pont GameSpy et du moniteur de diagnostics. Le contrôle local en lecture seule sur la copie du jeu s'est terminé avec le code 0.
- La version 0.10.1 n'ajoute ensuite que son numéro de version et la documentation au candidat essayé. Son exécutable final porte SHA-256 `B8AE5C3154FB43F00341662E2664448CED960AE159CA3044CAF15B7EBE16C700` et son contrôle local en lecture seule s'est aussi terminé avec le code 0.

## Vérification sur une copie du jeu

La copie de test a été sauvegardée puis modifiée avec la même passe : le gestionnaire a reproduit l'erreur sur le premier arbre. Le correctif compilé a restauré les onze empreintes, puis le gestionnaire a réintégré les 11 missions et 1300 fichiers avec succès. Une fixture séparée contenant les onze arbres gérés confirme que la passe Exploration libre les laisse tous inchangés. Une autre fixture confirme qu'une modification différente, assimilable à une édition utilisateur, reste intacte.

Le jeu d'origine n'a pas été modifié par cette réparation de test. La release 0.10.0 actuelle porte toujours le défaut de réinstallation ; un avertissement a été ajouté à sa page. Le candidat local a ensuite été testé par l'utilisateur sur le jeu installé : réinstallation terminée, menu actif et 11 adaptations présentes. Le diagnostic indique 149/160 autres arbres libres : les 11 arbres des adaptations gérées ne sont volontairement pas modifiés par la passe Exploration libre.
