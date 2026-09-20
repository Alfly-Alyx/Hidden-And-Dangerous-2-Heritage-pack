# Module natif du menu de missions personnalisées

`HD2.CustomMenu.asi` est un module x86 chargé par l'Ultimate ASI Loader déjà
fourni avec le correctif écran large. Il ne lance aucun processus et ne modifie
pas `HD2_SabreSquadron.exe` sur disque.

Le module ajoute la route vers le menu personnalisé, relie les trois boutons
de catégories aux catalogues `Gamedata03` à `Gamedata05`, corrige les offsets
cumulés du navigateur natif et renvoie les listes détaillées vers le sélecteur
de catégories.

Avant toute modification en mémoire, les 18 signatures du client H&D2 1.12
sont vérifiées. Une signature inattendue annule toute installation des points
d'entrée. La somme des lignes des six catalogues est limitée à 255 par le
gestionnaire.

Construction de développement :

```text
python tools/build_native_custom_menu.py
```

TinyCC x86 0.9.27 doit être présent dans
`tmp/native-menu-toolchain/tcc`. La construction lance automatiquement les
tests d'émulation hors ligne. `build-custom-mission-manager.ps1` embarque
ensuite le module compilé dans `HD2-Custom-Mission-Manager.exe`.

Les tests hors ligne ne remplacent pas la validation visuelle : bouton
principal, trois catégories, listes, sélection d'une mission, retours et menus
officiels doivent encore être contrôlés dans le jeu pour chaque version
distribuée.

## Validation de la correction du 20 septembre 2026

- 28 tests d'émulation passent, notamment le préchargement des contrôles,
  les trois listes, les retours et les commandes natives de visibilité.
- Le gestionnaire reconstruit a intégré la correction et les trois missions
  de démonstration dans `D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise`.
- Après lancement de cette copie, l'utilisateur a confirmé : « ça fonctionne ».
  Le journal contient les transitions vers chacune des trois listes et leurs
  retours au sélecteur, puis au menu officiel.
- Cette confirmation utilisateur n'est pas une validation visuelle automatisée :
  aucune capture du jeu n'a été obtenue par l'agent pendant cette vérification.

Les détails du cycle de vie et des messages natifs sont documentés dans
[ABI.md](ABI.md).
