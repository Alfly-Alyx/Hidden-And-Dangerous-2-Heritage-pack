# État du menu personnalisé — 19 septembre 2026

## Résultat courant

La GUI et le gestionnaire forment maintenant un même ensemble sur la branche
`codex/experimental-gui`.

`HD2-Custom-Mission-Manager.exe` génère et installe :

- le bouton **Missions personnalisées** du menu Solo ;
- le sélecteur à trois catégories ;
- une liste native distincte par catégorie ;
- les traductions des huit langues du jeu ;
- le module `Scripts/HD2.CustomMenu.asi` ;
- les fichiers de mission placés dans `CustomMissions`.

L'exécutable commercial reste inchangé. Le client pris en charge est
`HD2_SabreSquadron.exe` 1.12 avec l'empreinte SHA-256
`1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C`.

## Correspondance des catalogues

- `Gamedata00` et `Gamedata01` : contenus officiels, non modifiés ;
- `Gamedata02` : trois catégories ;
- `Gamedata03` : adaptations multijoueur ;
- `Gamedata04` : missions utilisateur ;
- `Gamedata05` : exploration libre.

Le module natif utilise une somme cumulative pour les libellés, la visibilité,
la sélection et le décodage des lignes. Le gestionnaire refuse une bibliothèque
qui ferait dépasser la limite de 255 lignes du moteur.

## Validation effectuée

- construction du gestionnaire avec le module ASI embarqué ;
- égalité bit pour bit entre les sept fichiers GUI générés en C# et le candidat
  de référence généré en Python ;
- 31 tests d'émulation x86 du menu ;
- validation des trois catégories de la bibliothèque d'essai ;
- 4 groupes d'auto-tests de sécurité : conflit, restauration, retrait et
  annulation transactionnelle ;
- installation transactionnelle réussie dans la copie de test avec trois
  missions et 39 fichiers de mission.

## Validation visuelle restant à refaire

Le lancement du jeu a réussi, mais la capture Windows de la fenêtre a échoué
deux fois avec `SetIsBorderRequired` / `0x80004002`. Aucun clic n'a été envoyé
à l'aveugle. Il reste donc à refaire, dès que le contrôle de fenêtre répond :

1. le bouton du menu Solo ;
2. les trois catégories et leurs listes ;
3. tous les retours ;
4. la sélection et le lancement d'une mission d'essai ;
5. l'absence de régression des menus officiels.

La tâche **Heritage Pack** ne dispose actuellement d'aucune conversion solo
validée. Africa5 Prototype peut seulement servir d'entrée d'affichage dans la
catégorie exploration : il ne faut pas le présenter comme mission jouable ni
redistribuer ses fichiers commerciaux. Les fichiers doivent être extraits des
archives du jeu à l'installation.
