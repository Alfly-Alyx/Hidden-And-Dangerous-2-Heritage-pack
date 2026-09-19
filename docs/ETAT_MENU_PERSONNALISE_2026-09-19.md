# Point de reprise — menu personnalisé, 19 septembre 2026

## Consigne utilisateur prioritaire

Ne pas lancer le jeu de test si le contrôle de son interface n'est pas fiable.
Aucun lancement n'a été effectué pendant la préparation décrite ci-dessous.
Ne pas demander à l'utilisateur de refaire les mêmes captures à notre place.
Ne pas qualifier le travail de terminé sans vérifier le parcours réel.

## État exact

- Nouvelle piste : module natif ASI utilisant le chargeur déjà présent avec le
  correctif écran large. Sources dans `native-custom-menu/`. Aucun lanceur ni
  nouvel EXE commercial modifié. Le module adapte le menu en mémoire dans son
  propre processus ; il n'est pas exempt de risque de détection antivirus.
- Candidat courant : `output/native-menu-candidate-20260919-r2/`.
  **Préparé dans le projet seulement, non installé, non validé dans le jeu.**
  Le répertoire sans suffixe `-r2` est une préparation antérieure obsolète.
- 16 tests d'émulation du module compilé passent. Ils couvrent les offsets
  des libellés et de visibilité, les clics de catégories, les retours, le
  blocage du lancement d'une catégorie et plusieurs invariants des menus officiels.
  Ils utilisent de faux objets du moteur : ce n'est pas un test de la GUI.
- F-Secure a analysé le module final : 1 fichier analysé, 0 élément nuisible,
  le 19 septembre à 12:03 heure locale. Aucun réglage ou exclusion modifié.
  SHA256 : `59F21ED312DA5ECD548B9EBE0A3B19E1028DADC34431868062C169D182D6EC3F`.
  Cela ne garantit ni l'absence de blocage à l'exécution, ni l'acceptation par
  d'autres antivirus.
- Les EXE original et de test ont été vérifiés identiques à l'original :
  `1EEBDE4710F800F712A05B1ECEE2BA862C144F478DF89B58E54C912E857EE78C`.

## Défaut identifié hors ligne

Le client original suppose deux catalogues. À partir du troisième, l'ancien
essai réutilisait la taille du catalogue 0 pour construire les identifiants des
lignes et choisir les lignes visibles. Cela faisait réapparaître les noms
officiels et rendait ambiguë la destination d'un clic. Le nouveau module
calcule les sommes cumulées dans les trois chemins : création, affichage, clic.
Il réserve les groupes de campagne aux deux catalogues officiels.

## Blocage du contrôle de l'interface

L'initialisation de `computer-use` via `node_repl` a échoué deux fois avec :
`trusted Node process exited unexpectedly; kernel reset, rerun your request`.
La disponibilité du contrôle de la GUI n'est donc pas établie. Les anciens
essais avec le programme local de captures/clics n'ont pas démontré un contrôle
fiable du jeu. Ne pas reprendre les lancements à l'aveugle.

## Ce qui reste réellement à faire

1. Rétablir un contrôle fiable et observable de l'interface avant tout lancement.
2. Valider le moment de chargement du module ASI. Il refuse une signature non
   reconnue ; aucune installation différée asynchrone n'est tentée.
3. Ajouter une limite explicite du nombre total de lignes compatible avec les
   identifiants 8 bits du moteur avant une utilisation avec de grosses bibliothèques.
4. Vérifier en jeu le bouton localisé, les trois catégories, leurs listes,
   une véritable sélection/lancement de mission, les retours et les menus officiels.
5. Adapter ensuite le gestionnaire `.exe` à cette architecture. Le gestionnaire
   actuellement construit conserve l'ancienne approche ajoutant les missions au
   catalogue officiel : **il ne constitue pas la livraison demandée**.

La copie de test reste la base restaurée lors du diagnostic précédent. Ses
anciens fichiers expérimentaux sont conservés dans
`D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise\__gui-baseline-20260919`.
Ne pas présumer que `STATIC_MENU_BACKUP` contient une version originale de tous
les fichiers : certains modèles/catalogues y étaient déjà modifiés.
