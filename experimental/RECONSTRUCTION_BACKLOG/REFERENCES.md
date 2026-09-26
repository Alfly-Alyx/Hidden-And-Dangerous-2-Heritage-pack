# Références, provenance et conservation des preuves

## Hiérarchie des preuves

Du plus fort au plus faible :

1. comportement observé et reproductible dans le jeu commercial 1.12;
2. acteur lié, script actif et ressource présente dans la même variante;
3. donnée commerciale sérialisée avec chemin, taille et empreinte;
4. équivalent actif dans une mission sœur ou une autre édition;
5. script libre, commentaire, nom de frame ou checkpoint isolé;
6. reconstruction moderne motivée par la géométrie et les contraintes du jeu.

Les niveaux 5 et 6 ne doivent jamais être présentés comme une intention
historique certaine.

## Installation commerciale de référence

Édition : GOG anglaise de *Hidden & Dangerous 2: Sabre Squadron 1.12*.

Chemin observé : `D:\Games\Hidden and Dangerous 2`.

Archives présentes et rôles principaux :

| Archive | Usage de preuve |
|---|---|
| `missions.dta` | scènes, acteurs, scripts et données de missions de base; |
| `SabreSquadron.dta` | variantes et missions de l'extension; |
| `Scripts.dta` | scripts génériques et fonctions partagées; |
| `Maps.dta`, `Maps_U.dta` | géométrie, cartes et données associées; |
| `models.dta` | modèles, nœuds et LOD; |
| `Sounds.dta` | ressources audio; |
| `LangEnglish.dta` | textes localisés anglais; |
| `Patch.dta`, `PatchX01.dta` | substitutions et suppressions de la version 1.12; |
| `others.DTA` | ressources diverses. |

Les archives sont des entrées de lecture. Aucun fichier extrait ni archive du jeu
ne doit être ajouté à Git.

## Références internes prioritaires

- `README_FR.md` et `README.md` : portée publique du Heritage Pack;
- `docs/AUDIT.md` et `docs/AUDIT_COMPLET_JEU.md` : état global et preuves;
- `docs/ETAT_DES_LIEUX_ET_ROADMAP.md` : ordre de travail et limites;
- `docs/CREATIONS_EXPERIMENTALES.md` : statut des créations;
- `docs/PROTOTYPES.md` : prototypes installés et limites de qualification;
- `docs/AUDIT_SIGNAUX.md` et `docs/OBJECTIFS_ET_CHEMINS.md` : graphes et
  progression;
- `docs/ARMES.md` et `docs/INVENTAIRE_ARMES_VEHICULES.md` : ressources et
  collisions d'objets;
- `docs/MULTIJOUEUR_VERS_SOLO.md` et `docs/INVENTAIRE_CARTES_MP.md` : conversion
  des cartes;
- `experimental/PRINCIPE_RECONSTRUCTION_ADDITIVE.md` : contrat de coexistence;
- `validation/runtime-validation.json` : 56 scénarios manuels encore en attente;
- `validation/reconstruction-runtime.json` : 27 profils expérimentaux, 165
  contrôles distincts encore en attente; protocole dans `validation/RECONSTRUCTION.md`;
- `validation/multiplayer-solo-runtime.json` : 21 candidates, aucune validée;
- `validation/stable-candidate-dispositions.json` : disposition des candidats
  structurels prioritaires.

Rapports JSON versionnés : `output/audit/full-game-audit.json`,
`script-bindings.json`, `signal-graph.json`, `asset-presence.json`,
`map-inventory.json`, `boundary-labels.json`, `stable-candidate-coverage.json` et
les autres rapports du même dossier.

## Espaces locaux non versionnés

- `.analysis/` : extractions temporaires et comparaisons binaires;
- `.research/` : notes et matériaux de recherche non distribuables;
- `.venv/` : dépendances Python locales;
- `build/` et `dist/` : artefacts reconstruits.

Une conclusion dépendant de ces espaces doit être résumée dans un fichier suivi
avec archive source, chemin interne, taille, empreinte et méthode de reproduction.
Le chemin local seul n'est pas une preuve portable.

## Sources externes déjà retenues par le projet

- jeu en ligne et serveurs communautaires : <https://www.rprclan.com/hd2/play-online>;
- création de serveur : <https://www.rprclan.com/hd2/create-server>;
- dépôt CMP : <https://github.com/ehylla93/had2-cmp>, version de référence
  `793d979748b27a9924fccc30fa0fba6edb7cd70f`;
- GameSpy2 : <https://int64.org/docs/gamestat-protocols/gamespy2.html>;
- méthode historique pour les objets `border` :
  <https://hidden-and-dangerous.net/board/viewtopic.php?t=2173>;
- correctif écran large : <https://github.com/ThirteenAG/WidescreenFixesPack>.

Toute vérification dépendant du réseau doit être datée. Une disponibilité passée
ne constitue pas une garantie actuelle.

## Fiche de preuve minimale

Pour chaque nouvelle découverte, enregistrer :

- identifiant du cas et variante de mission;
- édition/version du jeu;
- archive et chemin interne exacts;
- taille et SHA-256 si la donnée est binaire;
- extrait minimal ou observation reproductible;
- propriétaire, transformation, binding, signaux d'entrée/sortie;
- comparaison avec la branche commerciale;
- qualification `OFFICIEL`, `INFERENCE` ou `MODERNE`;
- test effectué, résultat, date et limites;
- méthode de désactivation et de retour à la baseline.

## Ce que la branche ne contient volontairement pas

- archives ou fichiers extraits du jeu;
- identifiants, positions ou dialogues inventés présentés comme officiels;
- prototypes actifs;
- modifications automatiques de l'installation commerciale;
- résultats d'exécution déclarés réussis sans preuve;
- les travaux locaux non liés qui étaient présents au moment de sa création.
