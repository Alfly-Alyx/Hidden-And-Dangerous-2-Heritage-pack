# Ajouter des missions personnalisées à H&D2

Le fonctionnement est volontairement fixe : placez
`HD2-Custom-Mission-Manager.exe` à la racine du jeu, à côté de
`HD2_SabreSquadron.exe`. L'utilitaire utilise uniquement le sous-dossier
`CustomMissions` situé au même endroit. Aucun emplacement n'est à choisir.

L'interface adopte automatiquement la langue détectée pour le jeu. Elle ne
lance jamais H&D2. Elle ne modifie jamais `HD2_SabreSquadron.exe` et refuse
l'installation si le client n'est pas la version 1.12 originale vérifiée.
Le chargeur ASI fourni par le correctif écran large du Heritage Pack doit être
présent (`d3d8.dll`).

L'utilitaire installe un bouton **Missions personnalisées** dans le menu Solo.
Ce bouton ouvre exactement trois choix, traduits dans la langue active du jeu :

- missions créées ou ajoutées par l'utilisateur ;
- missions multijoueur adaptées au jeu solo ;
- cartes d'exploration libre ou de test d'armes.

Chaque choix ouvre sa propre liste. Les catalogues officiels restent dans
`Gamedata00.gdt` et `Gamedata01.gdt` ; les listes personnalisées utilisent
`Gamedata02.gdt` à `Gamedata05.gdt`. Le module
`Scripts/HD2.CustomMenu.asi` raccorde ces écrans sans réécrire l'exécutable
commercial.

## Installation la plus simple

1. Fermer le jeu.
2. Déposer le dossier portant le nom de la mission dans `CustomMissions`.
3. Ouvrir `HD2-Custom-Mission-Manager.exe`, puis cliquer sur
   **Scanner et installer**.

Par exemple, sans aucun fichier `mission.json` à créer :

```text
Hidden and Dangerous 2/
  HD2-Custom-Mission-Manager.exe
  CustomMissions/
    Operation Lune/
      tree.klz
      ...autres fichiers de la mission...
      Maps/
        ...textures supplémentaires éventuelles...
      Models/
        ...modèles supplémentaires éventuels...
```

Le gestionnaire détecte automatiquement le dossier. Son nom devient le titre
affiché dans la liste **Missions utilisateur**. Les fichiers de mission sont
installés dans `Missions/Operation Lune`, et les ressources des sous-dossiers
`Maps`, `Models`, `Scripts`, `Sounds`, `Tables` et `Text` sont placées dans les
dossiers correspondants du jeu. Le dossier déposé reste intact.

Une arborescence complète `Operation Lune/Missions/<nom interne>/tree.klz`
(avec ses ressources à côté de `Missions`) est également reconnue, ainsi que
la même arborescence sous `payload`. Un dossier doit contenir une seule
mission identifiable ; les cas ambigus ou incomplets sont signalés.

La liste est scannée à l'ouverture. **Scanner** actualise l'aperçu ;
**Scanner et installer** effectue un nouveau scan puis l'installation.

Le bouton **Ouvrir le dossier** mène toujours au dossier imposé. Le bouton
**Nouvelle mission** peut créer automatiquement le squelette d'un nouveau
paquet au bon endroit.

Le bouton facultatif **Ajouter une mission** permet aussi de copier une mission
depuis un autre emplacement vers `CustomMissions` et de lui donner un titre.
Il n'est pas nécessaire pour les dossiers déposés directement.
Pour conserver la catégorie, les objectifs et les autres métadonnées d'un
paquet déjà préparé, copiez-le directement dans `CustomMissions` au lieu de
le réimporter : le bouton d'ajout crée une nouvelle fiche de mission utilisateur.

Le logiciel ajoute une mission existante ; il ne crée pas ses scripts et ne
convertit pas automatiquement une mission multijoueur en mission solo.
La validation des fichiers et de leur installation ne garantit pas la
jouabilité d'une mission fournie : son contenu doit déjà fonctionner avec H&D2.

## Paquet avancé avec manifeste facultatif

Un créateur peut toujours fournir `mission.json` pour personnaliser la
catégorie, les traductions, les objectifs et les autres paramètres. Les
paquets existants restent reconnus sans modification.

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

Ces catégories sont visibles dans le gestionnaire et déterminent la liste du
jeu dans laquelle la mission apparaît.

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
- `preserveTemplateObjectives` : avec la valeur `true` et un `templateMission`
  explicite, conserve exactement les objectifs du gabarit, leurs textes, leur
  ordre et leurs drapeaux. Le champ `objectives` doit alors être absent, même
  s'il aurait été vide. Cette option sert notamment aux copies de laboratoire
  d'une mission existante. Elle ne valide pas leurs scripts ni leur jouabilité.

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
`payload`, puis cliquez de nouveau sur **Scanner et installer**. Le catalogue,
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

La restauration couvre également les quatre catalogues personnalisés, les
deux scènes de menu, le module ASI et les traductions. Les fichiers officiels
modifiés après l'installation sont conservés et signalés au lieu d'être
écrasés.
