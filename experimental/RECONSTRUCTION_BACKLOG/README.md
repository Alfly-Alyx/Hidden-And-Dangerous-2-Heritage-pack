# Registre maître des reconstructions expérimentales

Inventaire initial : **2026-09-19**. Dernière mise à jour : **2026-09-25**.

Branche de travail actuelle : `codex/reconstruction-phase-1`.
La préparation de `codex/experimental-reconstruction-inventory` a été intégrée
à `master` avant la création de cette branche; sa photo historique est conservée.

Ce dossier réunit l'état des connaissances disponible pour la restauration et la
reconstruction additive de contenu de *Hidden & Dangerous 2*. La branche part de
`master` et contient donc tous les fichiers déjà versionnés du projet. Le présent
registre complète ces fichiers sans activer de script expérimental dans le jeu.

## Principes

- La version commerciale reste le comportement par défaut.
- Une ligne commentée, un script libre ou un nom de checkpoint est une preuve de
  vestige, pas une preuve suffisante du comportement final.
- Les éléments officiels, les inférences et les créations modernes sont toujours
  distingués.
- Aucun binaire commercial extrait n'est ajouté au dépôt.
- Les prototypes restent en `.disabled` tant que leurs propriétaires, liaisons,
  positions et conditions de fin ne sont pas démontrés puis testés en jeu.
- Une reconstruction ne doit jamais doubler un signal, un objectif, une voix, un
  effet ou un acteur déjà pris en charge par la version commerciale.

## Légende d'état

| État | Sens |
|---|---|
| Documenté | Une étude existe déjà dans `experimental/`. |
| À documenter | Les faits sont inventoriés ici, mais aucun dossier dédié n'existe encore. |
| Bloqué preuve | Un propriétaire, une position, une ressource ou un contrat manque. |
| Prototype désactivé | Une proposition existe mais ne peut pas être distribuée active. |
| Faux positif | La fonctionnalité est déjà remplacée ou la restauration serait trompeuse. |
| Validation jeu | La preuve statique existe, mais les essais en moteur restent obligatoires. |

## Carte du registre

- [Missions et scripts](MISSIONS.md) : toutes les missions et chaînes de signaux
  connues, y compris les éléments encore sans dossier dédié.
- [Armes, véhicules, avions et conversion solo](SYSTEMES_ET_ASSETS.md) : ressources
  transversales, collisions d'identifiants et limites techniques.
- [Validation et critères de promotion](VALIDATION.md) : contrôles à appliquer
  avant toute activation ou intégration dans les outils publics.
- [Catalogue physique](CATALOGUE_DOSSIERS.md) : liste exhaustive des dossiers
  expérimentaux présents sur cette branche et de leurs fichiers directs.
- [Outils et démarrage](OUTILS_ET_DEMARRAGE.md) : installation isolée,
  commandes d'audit, construction et checklist avant la première modification.
- [Références et provenance](REFERENCES.md) : hiérarchie des preuves, archives,
  rapports internes, sources externes et règles de conservation.
- [État de préparation](ETAT_PREPARATION.md) : photo vérifiée de la branche et
  de l'environnement juste avant le début des travaux.
- [Variantes reproductibles](VARIANTES_REPRODUCTIBLES.md) : vingt-deux profils et vingt-cinq scripts
  expérimentaux générés localement, contrôles automatisés, provenance,
  conflit de surcharge Africa 1 et validations en moteur encore en attente.
- [Laboratoires désactivés](LABORATOIRES_DESACTIVES.md) : copies A/B complètes,
  fermeture des scripts et préservation des objectifs Base/Sabre, sans installation.

## Travaux immédiatement recommandés

1. Créer les dossiers dédiés marqués **À documenter**, en commençant par les cas
   qui disposent d'un propriétaire et de checkpoints existants.
2. Fermer les faux positifs pour éviter de les réexaminer et de réintroduire des
   régressions.
3. Instrumenter les signaux ambigus avant de proposer une réaction inventée.
4. Tester les variantes en solo, Carnage et coopération quand la mission existe
   dans plusieurs modes.
5. Ne promouvoir un prototype qu'après réussite des contrôles décrits dans
   [VALIDATION.md](VALIDATION.md).

## Limites de cet inventaire

Ce registre décrit les preuves actuellement accessibles dans le dépôt et dans les
archives commerciales examinées. Il ne prétend pas que chaque intention originale
est récupérable. Les points explicitement marqués « moderne » sont des créations
compatibles avec les vestiges, pas des contenus historiques authentifiés.
