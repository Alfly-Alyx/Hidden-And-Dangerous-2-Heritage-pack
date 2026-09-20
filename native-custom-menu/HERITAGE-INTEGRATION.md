# Transmission au Heritage Pack — 20 septembre 2026

## Ensemble à distribuer

- `dist/HD2-Custom-Mission-Manager.exe`, installé à la racine du jeu.
- Le dossier `CustomMissions`, son aide et le modèle facultatif.
- Le chargeur ASI du correctif écran large, déjà fourni par le Heritage Pack.

`build.ps1` reconstruit le gestionnaire, embarque son EXE et son empreinte
dans `dist/H-D2-Heritage-Pack-Setup.exe`. Le raccordement est dans
`installer/CustomMissionManagerInstaller.cs` et `InstallerCore.cs`.
Préserver les missions et autres fichiers utilisateur non suivis lors des mises
à jour ; ne pas redistribuer les fichiers commerciaux utilisés pour les tests.

Le setup principal doit aussi exécuter l'intégration avec une bibliothèque vide
après l'installation du CMP et des autres surcharges. Cela déploie réellement
les scènes, catalogues, textes et le module ASI dans le jeu dès l'installation,
même si le joueur n'a encore ajouté aucune mission. Copier seulement le
gestionnaire ne constitue pas une intégration de la GUI.

## Parcours joueur

Le joueur dépose `CustomMissions/Nom de la mission/` avec `tree.klz` et les
fichiers nécessaires, ouvre le gestionnaire, puis clique sur **Scanner et
installer**. Aucun manifeste ni import manuel n'est requis. Le dossier source
reste intact. Les dispositions `Missions/<nom interne>/tree.klz` et
`payload/Missions/<nom interne>/tree.klz` sont aussi reconnues.

Le scan produit un descriptif en mémoire : titre = nom du dossier, catégorie
utilisateur, ID stable. Les ressources Maps/Models/Scripts/Sounds/Text/Tables
sont installées dans les racines correspondantes du jeu. Un `mission.json`
facultatif conserve les catégories, traductions et paramètres avancés des
paquets existants. Consulter `custom-missions/README.md`.

## GUI dans le jeu

Solo → Missions personnalisées → trois boutons → trois listes distinctes :
missions utilisateur, adaptations multijoueur, exploration libre.
Les libellés utilisent les tables de langue du jeu.

Le gestionnaire génère les catalogues personnalisés Gamedata02–05, les deux
scènes de menu, les textes et `Scripts/HD2.CustomMenu.asi`. Gamedata00/01
restent officiels. L'EXE commercial n'est pas modifié sur disque.
Le module vise le client Sabre Squadron 1.12 vérifié par signatures.
Son fonctionnement est documenté dans `ABI.md`.

Les corrections essentielles sont la création des contrôles au préchargement,
la distinction définitions/contrôles actifs, les messages natifs SHOW/HIDE,
les événements privés des trois boutons et l'interception globale de Retour
limitée au navigateur de missions. Ne pas réintroduire les anciens correctifs
de textes vides ou de second bouton Retour.

## Validation et limites

- L'utilisateur a confirmé le fonctionnement des menus dans la copie de test.
  Ce n'est pas une validation visuelle automatisée par l'agent.
- 28 tests natifs hors ligne passent, dont le cycle de préchargement et les
  véritables fonctions natives de visibilité exécutées en émulation.
- Les auto-tests du gestionnaire couvrent les trois structures brutes, les
  ressources, les espaces, les ID stables, les sources intactes, les collisions,
  les refus de contenu dangereux, les sauvegardes et le retour arrière.
- Le test réel de l'EXE livré dépose un dossier brut dans la copie de test,
  passe de 3 à 4 missions, vérifie les fichiers et Gamedata04, archive seulement
  la fixture puis rétablit les 3 missions et leurs fichiers inchangés.
  Script reproductible : `tools/test_custom_mission_manager.ps1`.
- Cette fixture est volontairement non jouable : ce test prouve l'installation,
  pas la jouabilité de n'importe quelle mission. Le logiciel ne crée pas de
  scripts et ne convertit pas automatiquement du multijoueur en solo.
- L'extension graphique des menus hors 4:3 reste un chantier séparé, non validé
  par cette livraison.

Avant distribution, lancer `tools/custom_mission_setup_audit.py` et
`tools/installer_wiring_audit.py`. Vérifier également les ressources réellement
embarquées avec `CustomMissionManagerInstaller.ValidateOnly()` dans le setup.

Pour toute question, contacter la tâche **Modifier la GUI du jeu**
(`01a0bb2f-44c0-7161-aaf6-4cbbddf99429`). Les deux tâches utilisent actuellement
le même dossier : éviter les changements de branche ou les reconstructions
concurrentes sans coordination.
