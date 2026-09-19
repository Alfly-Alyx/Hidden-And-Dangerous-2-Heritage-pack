# Menu natif expérimental — non validé dans le jeu

Cette extension est une nouvelle piste, pas une livraison terminée. Aucun
lancement du jeu n'est effectué par sa construction ou ses tests hors ligne.
Le jeu de test ne doit pas être lancé tant que le contrôle de son interface
n'est pas fiable, conformément à la demande de l'utilisateur.

Le module est compilé normalement en DLL x86 `.asi`, destiné au chargeur
Ultimate ASI Loader déjà présent avec le correctif écran large. Il ne crée pas
de lanceur, ne reconstruit pas l'EXE commercial et n'ouvre pas d'autre processus.
Il adapte néanmoins le code du menu **dans le processus du jeu** ; cela ne
garantit pas l'acceptation par tous les antivirus. Aucune exclusion ni modification
de l'antivirus n'est autorisée.

Le module compare toutes les signatures attendues avant de poser ses points
d'entrée. Une version différente du client doit être refusée. Les routes sont
dans `Hooks.S` et la navigation est dans `CustomMenu.c`.

Correction par rapport à l'ancien essai : la construction des lignes et leur
affichage réutilisaient seulement la taille du catalogue 0 pour tous les
catalogues suivants. Les identifiants et les noms des lignes entraient donc
en conflit. La nouvelle route utilise la somme des tailles précédentes lors de
la création des libellés, de leur affichage **et** du traitement du clic.

Construction de développement : `python tools/build_native_custom_menu.py`.
TinyCC x86 0.9.27 doit être disponible dans `tmp/native-menu-toolchain/tcc`.
Ce programme lance le compilateur et les tests d'émulation, jamais le jeu.

À valider avant toute livraison : chargement ASI à la bonne étape du démarrage,
bouton localisé, trois catégories, titres/listes corrects, sélection/lancement
d'une vraie mission, retours, absence de régression des menus officiels,
absence de détection sur la configuration de test. Les vérifications hors ligne
ne remplacent aucun de ces contrôles.
