# Ajouter des missions personnalisées à H&D2

Le fonctionnement est volontairement fixe : placez
`HD2-Custom-Mission-Manager.exe` à la racine du jeu, à côté de
`HD2_SabreSquadron.exe`. L'utilitaire utilise uniquement le sous-dossier
`CustomMissions` situé au même endroit. Aucun emplacement n'est à choisir.

L'interface adopte automatiquement la langue détectée pour le jeu. Elle ne
lance jamais H&D2. Elle ne modifie jamais `HD2_SabreSquadron.exe` et refuse
l'installation si elle reconnaît l'ancien prototype exécutable portant une
section `.patch`.

Les missions sont ajoutées au catalogue natif **Single Mission** après les
missions officielles. Leur titre commence par une catégorie traduite, par
exemple `[Missions utilisateur]`, afin que les deux ensembles restent
immédiatement reconnaissables. Le jeu ne fournit pas de troisième route de
catalogue : un bouton et des sous-menus entièrement séparés exigeraient de
modifier son exécutable, solution retirée à cause des détections antivirus.

## Installation la plus simple

1. Placer un ou plusieurs paquets directement dans `CustomMissions`.
2. Ouvrir `HD2-Custom-Mission-Manager.exe`.
3. Cliquer sur **Vérifier**, puis sur **Installer les missions**.

Le bouton **Ouvrir le dossier** mène toujours au dossier imposé. Le bouton
**Nouvelle mission** peut créer automatiquement le squelette d'un nouveau
paquet au bon endroit.

## Structure d'un paquet

Chaque mission possède son propre sous-dossier. Par exemple :

```text
Hidden and Dangerous 2/
  HD2-Custom-Mission-Manager.exe
  HD2_SabreSquadron.exe
  CustomMissions/
    mission.schema.json
    mon-paquet/
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

L'arborescence placée dans `payload` reproduit celle de la racine du jeu. Le
fichier principal `tree.klz` doit donc se trouver dans
`payload/Missions/<nom exact de la mission>/tree.klz`.

Le dossier `_modele` fourni peut être copié et renommé. Son nom commence par
un tiret bas : l'utilitaire l'ignore tant qu'il sert de modèle.

## Catégories des missions personnalisées

- `multiplayer-adaptation` : adaptation d'une mission multijoueur ;
- `user-mission` : mission créée par un utilisateur ;
- `free-exploration` : exploration libre ou test d'armes.

Ces catégories sont visibles dans le gestionnaire et dans le préfixe localisé
du titre affiché par le jeu. Elles ne créent pas de sous-menus supplémentaires.

Les anciennes valeurs `original-creation` et `weapon-test` restent acceptées
et sont rangées automatiquement dans les catégories correspondantes.

## Champs de mission.json

- `id` : identifiant stable et unique, par exemple
  `alfly.operation-lune`. Il ne doit plus changer après diffusion du paquet.
- `category` : une des trois catégories décrites ci-dessus.
- `missionDirectory` : nom exact du dossier placé sous `payload/Missions`.
- `title` : titre affiché dans le catalogue. `default` sert de repli si la
  traduction de la langue active manque.
- `loadingScreen` : nom facultatif de l'image de chargement.
- `objectives` : liste facultative de textes d'objectifs traduisibles.
- `templateMission` : mission officielle facultative dont les paramètres
  internes servent de gabarit. Sans ce champ, le gabarit de la catégorie est
  utilisé.

Les langues reconnues sont `czech`, `english`, `EnglishUS`, `french`, `german`,
`italian`, `japan` et `spanish`. Il n'est pas nécessaire de fournir les huit :
la valeur `default` est alors utilisée.

Les identifiants numériques des textes sont attribués automatiquement dans
`CustomMissions/.catalogue-ids.json`. Ce fichier garantit leur stabilité et ne
doit pas être modifié à la main.

## Sécurité et mise à jour

Avant l'installation, l'utilitaire vérifie les paquets, refuse les chemins qui
sortent du jeu, les doublons et les missions sans `tree.klz`. Les fichiers déjà
présents sont sauvegardés avant remplacement.

Pour mettre une mission à jour, remplacez son `mission.json` ou son contenu
`payload`, puis cliquez de nouveau sur **Installer les missions**. Le catalogue,
les traductions et les fichiers sont régénérés ensemble.

Si un fichier déjà installé a été retouché directement dans le jeu depuis la
dernière intégration, l'utilitaire refuse de l'écraser. Retirez ou restaurez
explicitement cette modification avant de recommencer. Lorsqu'un paquet est
retiré de `CustomMissions`, ses fichiers intacts sont supprimés ou remis à leur
version sauvegardée ; ses fichiers retouchés sont conservés.

L'installation est transactionnelle : registre des identifiants, catalogues,
traductions, ressources, journal de suivi et rapport sont tous préparés avant
écriture. Si une seule écriture échoue, les écritures déjà effectuées sont
annulées automatiquement.

Le bouton **Restaurer** remet le catalogue et les fichiers sauvegardés. Un
fichier, créé ou remplacé par un paquet, n'est supprimé ou restauré que s'il
n'a pas été modifié depuis son installation.
