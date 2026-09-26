# Vérification du suivi des scripts — travail en cours

## 26 septembre 2026

- Travail isolé sur `codex/mission-diagnostics`, sans modification du jeu d'origine.
- Copie utilisée : `D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise`.
- Le premier lancement sans identifiant `process:` a ouvert le jeu d'origine.
  Son rapport d'installation indique zéro mission personnalisée. Ses trois
  catalogues personnalisés font 120 octets chacun et sont vides.
- La copie de test contient trois démonstrations, une dans chaque catégorie :
  `TestMultiBrest`, `TestUserLibye1`, `TestExploreSicily1`. La bibliothèque et ses
  39 fichiers de contenu passent la validation. Ce ne sont pas les nouvelles
  campagnes ni une preuve que toutes les adaptations ont été installées.
- Le lancement avec l'identifiant exact `process:` ouvre bien la copie de test,
  mais Windows rapporte son chemin en minuscules. Une comparaison sensible à
  la casse empêchait le démarrage du menu et du moniteur. Correction effectuée
  dans `MenuExecutableKind`, vérifiée par tests sur plusieurs casses et sur des
  exécutables étrangers qui doivent rester refusés.
- 29 tests du menu et 5 tests d'intégration du diagnostic réussis.
- Module corrigé installé dans la copie de test après fermeture par l'utilisateur.
  SHA-256 : `DB685910AF17CCF76CC2DFDB4B6A297E17B2423A5DCBA65A1708E24BC7D4E0E8`.
- Les journaux du nouveau lancement confirment le démarrage du menu et du
  moniteur. La trace native contient `script-engine-tracing-active`.
- Capture Windows impossible : `window capture timed out: timed out waiting on channel`,
  y compris après nouvelle sélection de la fenêtre et activation. Aucun clic
  ni résultat visuel n'est revendiqué. Une vérification utilisateur a été demandée.

### Listes vides : correction distincte après retour utilisateur

- Les trois captures utilisateur montrent que chaque catégorie reste vide : le
  correctif de casse ne résolvait donc pas ce deuxième défaut.
- Le journal du chargeur natif, dans le processus de test 9772, confirme six
  catalogues et respectivement **24, 9, 3, 1, 1, 1 missions**. Le même résultat
  est reproduit avec le vrai parseur GDT et les données locales dans un test
  hors jeu. Les missions ne sont pas absentes des catalogues.
- Le vrai constructeur de lignes génère les bons identifiants, y compris les
  trois lignes personnalisées. Le test plus complet du vrai gestionnaire de
  liste reproduit le défaut : groupe visible, ligne masquée après le sélecteur.
- Cause : le jeu ne rafraîchit pas les lignes ajoutées pendant que leur groupe
  est caché ; réafficher le groupe seul ne les réaffiche pas. Un rafraîchissement
  des lignes est désormais envoyé après la réapparition du groupe.
- Les identifiants des boutons de catégorie sont aussi copiés avant que le jeu
  ne libère leurs définitions temporaires, évitant une lecture après libération.
- Les 34 tests du menu et du chargement natif passent après correction, dont le test qui échouait
  avant correction. **Validation visuelle et lancement réel encore attendus**.
- Module destiné au prochain essai (pas encore installé) :
  `AC3EC00ECC6C48E79FF3267320AA4D36C997882CEBAE2A28011BCB4D6E455838`.
- La session précédente (19828) et son moniteur se sont tous deux arrêtés ; il
  reste à répéter la vérification après une vraie session en mission.

## Encore à vérifier avant livraison

- Affichage et lancement d'une mission depuis chaque catégorie personnalisée.
- Mission officielle, sauvegarde et rechargement, puis mission personnalisée.
- Sources réellement compilées, décisions, compteurs, signaux et objectifs dans
  une trace de mission réelle, sans perte d'événements ni régression de performance.
- Production automatique du rapport après erreur contrôlée dans la copie de test : validée dans la mise à jour ci-dessous.
- Arrêt du moniteur avec le jeu ; comparaison avec une session sans instrumentation.
- Application native du profil H&D2 de base (les tests des instructions passent).
- Règles attendues par mission pour diagnostiquer les blocages logiques silencieux.
  Enregistrer les instructions ne suffit pas à prouver qu'un objectif aurait dû
  se terminer : il ne faut pas présenter ce travail comme une détection universelle.

Au moment de ce premier relevé, aucun nouvel installateur de livraison n'avait été compilé.

## Mise à jour du 26 septembre 2026 — intégration sur master

- Branche de livraison : master, le dépôt ne possède pas de branche main. Le commit 014cec8 corrige le rafraîchissement des lignes après le choix d'une catégorie.
- Une copie isolée du jeu commercial a été lancée avant la compilation du nouvel installateur. Son rapport d'intégration confirme 11 adaptations solo et 1300 fichiers, toutes rangées dans le catalogue des conversions multijoueur vers solo.
- Le journal natif du jeu chargé contient catalogue-load count=6 puis onze entrées mission-context pour le catalogue 3, lignes 0 à 10. Cela atteste l'accès aux onze lignes par le menu ; la fin de chaque mission reste à vérifier en jouant.
- Le menu chargé en jeu et le module compilé ont la même empreinte SHA-256 : AC3EC00ECC6C48E79FF3267320AA4D36C997882CEBAE2A28011BCB4D6E455838.
- Une erreur de script factice, volontairement ajoutée au journal pendant la session de test, a déclenché automatiquement un rapport local dans %LOCALAPPDATA%\HD2 Heritage Pack\Reports avec report.txt, game-log.txt, custom-menu-log.txt et une archive ZIP. Cela vérifie le chemin de remontée d'erreur du journal, sans simuler un véritable crash.
- Après ces lancements, le gestionnaire et l'installateur ont été reconstruits. Leurs ressources embarquées ont été comparées par SHA-256 au menu corrigé et au moniteur de diagnostics ; les trois comparaisons concordent.
- Le gestionnaire recompilé a ensuite réintégré les onze missions dans la copie de test ; son rapport et le fichier ASI déployé donnent tous deux l'empreinte du menu corrigé.
- Suites ciblées réussies après compilation : 6 tests d'adaptation solo, 5 tests de diagnostic, 31 tests du menu natif et 2 tests des lignes masquées. Le test de chargement de catalogue qui dépend d'une autre installation locale a été ignoré ; les journaux de cette copie de test fournissent les comptages réels.
- La comparaison des fichiers avec les missions solo officielles est détaillée dans SOLO_ADAPTATIONS_COMPARAISON.md.
- La commande de validation locale de l'installateur compilé a réussi sur la copie du jeu de test.

Restent à valider en jeu : le démarrage, les objectifs, la sauvegarde et la fin des onze adaptations ; un crash réel et le rapport de blocage ; l'effet en performance pendant une mission complète. Les tests et le rapport contrôlé ne prouvent pas ces points.
