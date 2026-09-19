# Menu de missions personnalisées — prototype retiré

## Résultat des essais

La première sonde est abandonnée : les groupes du menu se chevauchaient et le
bouton `bcampaign02` n'était pas pris en charge par le moteur.

Une seconde approche ajoutait le routage uniquement en mémoire. Elle est elle
aussi abandonnée : son utilisation de fonctions de modification de processus a
été détectée par l'antivirus. Le lanceur, son code source et ses outils de
construction ont été retirés. Il ne faut pas désactiver l'antivirus ni créer
d'exclusion.

## Décision de sécurité

Le prototype statique reconstruisait `HD2_SabreSquadron.exe`, ajoutait une
section exécutable `.patch` et détournait plusieurs branchements du moteur.
Cette structure a été détectée sous le nom `Drop.Win32.ScoreInject.131`.
Elle n'est plus produite, installée ni appelée par le gestionnaire pris en
charge. Il ne faut pas désactiver l'antivirus ni créer d'exclusion.

La copie de test doit employer l'exécutable commercial original, sans aucune
différence d'empreinte avec sa sauvegarde. Le mode pris en charge modifie
uniquement les fichiers de données et ajoute les missions au catalogue natif
`Gamedata01.gdt`, après les missions officielles.

## Ancien contenu de validation

Le catalogue de test expose d'abord trois rubriques : adaptations multijoueur,
missions utilisateur et exploration libre / tests d'armes. Chacune ouvre une
liste distincte qui contient provisoirement un essai basé sur `Brest`,
`Libye1` ou `Sicily1`. Ces dossiers servent uniquement d'emplacements
techniques pour vérifier la navigation.

Les vraies adaptations et créations seront ajoutées dans des dossiers séparés
après leur propre validation. Les deux catalogues commerciaux ne sont jamais
modifiés.

## Intégration destinée aux créateurs

Dans la version distribuée, `HD2-Custom-Mission-Manager.exe` est placé à la
racine du jeu. Il utilise automatiquement le dossier imposé `CustomMissions`
situé à côté de lui : aucun chemin du jeu ou de bibliothèque n'est demandé.
Chaque mission y possède son propre sous-dossier, un petit fichier
`mission.json` et un dossier `payload` qui reprend l'arborescence du jeu.

L'utilitaire détecte la langue configurée de H&D2 pour adapter son interface,
vérifie tous les paquets, conserve les missions officielles de `Gamedata01.gdt`,
ajoute les missions personnalisées avec un préfixe de catégorie traduit, ajoute
les titres et objectifs traduits, puis copie les ressources dans ce même jeu avec
sauvegarde. Il ne lance pas le jeu et n'utilise ni injection ni modification
d'un processus. Le guide complet se trouve dans `custom-missions/README.md`.
Une réintégration refuse d'écraser un fichier géré qui a ensuite été retouché.
Le retrait d'un paquet et la restauration appliquent la même protection, et
l'ensemble des écritures est annulé automatiquement si une étape échoue.

## Retour arrière

Le gestionnaire sauvegarde les fichiers de données qu'il remplace et peut les
restaurer sans lancer le jeu. L'exécutable commercial n'entre jamais dans la
transaction.

## Conclusion technique

Le chargeur sait construire des noms `Gamedata%02d.gdt`, mais l'écran Solo
n'enregistre explicitement que les contrôles officiels. Un troisième bouton ne
peut donc pas être ajouté par la seule modification de `singleplayer.4ds`.

Le projet privilégie désormais la compatibilité antivirus : exécutable intact,
catalogue natif unique et catégories visibles dans les titres localisés. Le
bouton autonome et les sous-menus internes restent abandonnés.
