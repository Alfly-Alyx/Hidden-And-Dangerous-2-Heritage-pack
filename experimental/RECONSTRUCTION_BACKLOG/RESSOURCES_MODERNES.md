# Ressources modernes : autorisation et séparation des provenances

Le 26 septembre 2026, l'utilisateur a explicitement autorisé : **« Créer aussi
des ressources modernes, clairement identifiées »**, notamment lorsque les
armes et appareils ne disposent pas de modèles ou d'animations complets.

Cette décision autorise la fabrication des ressources manquantes. Elle ne
transforme pas une création en contenu officiel retrouvé et ne dispense pas des
essais en moteur. Le jeu personnel, les identifiants occupés et les archives
commerciales restent intacts.

## Contrat de fabrication

- Chaque recette et chaque manifeste portent `MODERNE` et un identifiant propre.
- Géométrie, matériaux, pivots, animations et réglages nouvellement conçus sont
  explicitement séparés des références commerciales, même lorsqu'ils cherchent
  à s'en rapprocher visuellement.
- Les fichiers reproductibles créés ici ne doivent lire ni incorporer un
  maillage, une texture, une animation ou un son commercial pour fabriquer une
  ressource présentée comme originale.
- Les ressources originales ne sont ni écrasées ni renommées. Préfixe
  `PROTOTYPE_HERITAGE_` pour les modèles modernes et suffixe `.disabled` pour
  les fichiers natifs non validés.
- Les champs natifs limités à vingt octets emploient, lorsqu'il le faut, un alias
  court `PROTOTYPE_` explicite, sans troncature. Les [deux alias Benelli](../BENELLI_M4_ADDITIVE/TABLES_ADDITIVES.md)
  conservent leurs provenances et empreintes séparées.
- Une géométrie inspectable n'est pas une arme jouable, une animation compatible
  ni un avion pilotable. Chaque étape garde son propre statut de validation.
- Aucun numéro Item/Weapon n'est réservé par la création d'un modèle. Un rescan
  complet et une voie additive distincte restent nécessaires avant intégration.

## Première réalisation

Le [modèle extérieur Benelli](../BENELLI_M4_ADDITIVE/MODELE_MODERNE.md) est
défini par une recette de géométrie originale et un générateur indépendant des
archives du jeu. Il vise la représentation extérieure/posée, pas le remplacement
des neuf couples FPV officiels ni l'invention de leurs animations.

Le [modèle FPV statique](../BENELLI_M4_ADDITIVE/BANC_FPV.md), lui, est une
**ressource dérivée du jeu**. Son extraction et son recalage sont modernes, mais
sa géométrie ne l'est pas. Le générateur est versionné ; le résultat et
l'inspecteur contenant poses, clés, bitmaps et sons sont privés, ignorés par Git.

Les laboratoires de scripts et leurs 304 contrôles moteur restent distincts de
la validation de ces nouveaux assets. Les contrôles de format et aperçus hors
moteur ne sont jamais comptés comme essais réussis dans le jeu.
