# Ajouter une mission personnalisée

Ce dossier sert de bibliothèque de travail pour le troisième catalogue du menu
Solo. La copie originale du jeu n'est jamais modifiée et le jeu n'est jamais
lancé par les outils de préparation.

## Méthode la plus simple

1. Dupliquer le dossier `_modele` dans `library`.
2. Renommer cette copie avec un nom propre à la mission.
3. Modifier `mission.json` avec un éditeur de texte.
4. Placer tous les fichiers de la mission dans `payload`, en gardant leur
   arborescence par rapport à la racine du jeu.
5. Exécuter `PreparerMissionsPersonnalisees.ps1`, situé à la racine du projet.

Par exemple, le fichier principal d'une mission appelée `MaMission` doit être
placé ici :

```text
custom-missions/library/mon-paquet/
  mission.json
  payload/
    Missions/
      MaMission/
        tree.klz
        ...autres fichiers de la mission...
    Maps/
      ...ressources éventuelles...
    Models/
    Scripts/
    Sounds/
    Tables/
    Text/
```

Le préparateur vérifie le paquet avant toute copie. Il refuse les chemins qui
sortent du jeu, les doublons entre paquets, les identifiants dupliqués et une
mission sans `tree.klz`. Un fichier déjà présent dans la copie de test est
sauvegardé avant remplacement.

## Les champs de mission.json

- `id` : identifiant stable et unique de l'auteur, par exemple
  `alfly.operation-lune`. Il ne doit plus changer après diffusion du paquet.
- `category` : `multiplayer-adaptation`, `original-creation` ou
  `free-exploration`.
- `missionDirectory` : nom exact du dossier placé sous `payload/Missions`.
- `title` : titre affiché dans le catalogue. `default` sert de repli lorsque
  la traduction de la langue active est absente.
- `loadingScreen` : nom facultatif de l'image de chargement.
- `objectives` : liste facultative des textes d'objectifs, traduisibles de la
  même manière que le titre.
- `templateMission` : mission officielle facultative dont les paramètres
  internes servent de gabarit. Sans ce champ, le gabarit associé à la catégorie
  est utilisé.

Les langues reconnues sont `czech`, `english`, `englishUS`, `french`, `german`,
`italian`, `japan` et `spanish`. Il n'est pas nécessaire de fournir les huit :
la valeur `default` est alors employée.

Les identifiants numériques des textes ne sont jamais choisis par l'auteur.
Ils sont calculés automatiquement à partir de `id` et restent stables lorsque
d'autres missions sont ajoutées.

## Vérifier sans installer

Depuis PowerShell à la racine du projet :

```powershell
.\PreparerMissionsPersonnalisees.ps1 -VerifierSeulement
```

Cette commande ne touche à aucun fichier du jeu.

## Mettre à jour une mission

Modifier son `mission.json` ou les fichiers de `payload`, puis relancer le même
script. Le catalogue `Gamedata02.gdt`, les traductions et les fichiers de la
mission sont régénérés ensemble. Les deux catalogues officiels restent séparés.

Pour revenir à l'état antérieur, utiliser `RestaurerMenuTest.ps1` dans la copie
de test. Les fichiers créés par les paquets sont supprimés seulement s'ils n'ont
pas été modifiés depuis leur installation ; sinon ils sont conservés avec un
avertissement.
