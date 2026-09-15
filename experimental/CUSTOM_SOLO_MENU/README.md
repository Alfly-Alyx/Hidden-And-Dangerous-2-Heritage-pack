# Menu de missions personnalisées — prototype statique

## Résultat des essais

La première sonde est abandonnée : les groupes du menu se chevauchaient et le
bouton `bcampaign02` n'était pas pris en charge par le moteur.

Une seconde approche ajoutait le routage uniquement en mémoire. Elle est elle
aussi abandonnée : son utilisation de fonctions de modification de processus a
été détectée par l'antivirus. Le lanceur, son code source et ses outils de
construction ont été retirés. Il ne faut pas désactiver l'antivirus ni créer
d'exclusion.

## Prototype préparé

- L'installation d'origine reste intacte.
- La copie séparée `Hidden and Dangerous 2 - Test Menu Personnalise` contient
  maintenant un exécutable reconstruit statiquement : aucun lanceur, aucune
  injection dans un processus et aucune exclusion antivirus.
- `singleplayer.4ds` contient un troisième contrôle `bcampaign02`, placé seul
  au milieu de l'espace d'origine entre `SINGLE MISSION - CARNAGE` et `BACK`.
- Les 42 éléments officiels gardent exactement leurs coordonnées d'origine.
- Le texte du bouton emploie l'identifiant localisé 20402 : il suit la langue
  active dans les huit langues installées au lieu d'être gravé dans une image.
- Le bouton ouvre le navigateur de missions solo avec le catalogue 2 actif ;
  il ne suit plus la commande Campagne qui lançait directement une mission.
- Un essai suivant a montré que le navigateur parcourait encore les catalogues
  officiels : son itération et sa sélection sont désormais limitées à
  `Gamedata02.gdt` après le bouton personnalisé. Les entrées personnalisées
  sont visibles sans écriture dans la progression du profil.
- Les deux boutons `SINGLE MISSION` officiels réinitialisent ce filtre et
  conservent leur catalogue d'origine.
- `Gamedata02.gdt` est indépendant de `Gamedata00.gdt` et `Gamedata01.gdt`.
- Les libellés sont ajoutés dans les huit tables de langue installées.
- Le jeu n'a pas été lancé après la préparation.

## Contenu de validation

Le catalogue de test expose trois rubriques : adaptations multijoueur,
créations originales et exploration libre. Elles emploient provisoirement
trois missions commerciales existantes (`Brest`, `Libye1`, `Sicily1`) comme
emplacements techniques. Cela permet de vérifier la navigation et le routage
du troisième catalogue sans présenter ces missions comme des conversions.

Les vraies adaptations et créations seront ajoutées dans des dossiers séparés
après leur propre validation. Les deux catalogues commerciaux ne sont jamais
modifiés.

## Intégration destinée aux créateurs

Le dossier `custom-missions` à la racine du projet contient désormais un
gabarit de paquet et une bibliothèque. Chaque mission est décrite par un petit
fichier `mission.json`; ses ressources gardent simplement la même arborescence
que dans le jeu sous un dossier `payload`.

`PreparerMissionsPersonnalisees.ps1` vérifie tous les paquets, régénère le seul
catalogue `Gamedata02.gdt`, ajoute les titres et objectifs traduits, puis copie
les ressources dans la copie de test avec sauvegarde. Il ne lance pas le jeu et
ne fabrique aucun exécutable auxiliaire. Le guide complet se trouve dans
`custom-missions/README.md`.

## Retour arrière

La copie originale de l'exécutable est conservée sous
`HD2_SabreSquadron.original.exe`. `RestaurerMenuTest.ps1`, placé à la racine de
la copie de test, restaure l'exécutable, les textes et l'ancien menu sans lancer
le jeu.

## Conclusion technique

Le chargeur sait construire des noms `Gamedata%02d.gdt`, mais l'écran Solo
n'enregistre explicitement que les contrôles officiels. Un troisième bouton ne
peut donc pas être ajouté par la seule modification de `singleplayer.4ds`.

La prise en charge du troisième suffixe est ajoutée directement dans la copie
de l'exécutable, après décompactage et reconstruction hors ligne. La structure
PE obtenue, ses 287 importations, ses quatre sections, son point d'entrée et les
signatures des deux branchements ont été vérifiés statiquement. La validation
en jeu reste à effectuer par l'utilisateur.
