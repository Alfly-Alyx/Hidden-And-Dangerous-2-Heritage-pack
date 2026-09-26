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
- Production automatique du rapport après erreur contrôlée dans la copie de test.
- Arrêt du moniteur avec le jeu ; comparaison avec une session sans instrumentation.
- Application native du profil H&D2 de base (les tests des instructions passent).
- Règles attendues par mission pour diagnostiquer les blocages logiques silencieux.
  Enregistrer les instructions ne suffit pas à prouver qu'un objectif aurait dû
  se terminer : il ne faut pas présenter ce travail comme une détection universelle.

Aucun nouvel installateur de livraison n'a été compilé pour ce lot.
