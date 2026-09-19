# Banc local de contrôle GUI H&D2

Outil interne de validation, non distribué avec le gestionnaire de missions.

- cible uniquement le PID qu'il a lancé et revérifie le chemin de l'exécutable avant chaque action ;
- utilise les entrées Windows ordinaires (`SendInput`) ;
- ne lit ni n'écrit la mémoire du jeu ;
- n'injecte aucun code et ne modifie aucun exécutable ;
- ne touche à aucun réglage de sécurité ou d'antivirus ;
- enregistre des captures PNG après chaque étape de test.

Il est destiné à contrôler visuellement la copie de test du jeu quand l'interface native de contrôle Windows de Codex n'est pas disponible.
