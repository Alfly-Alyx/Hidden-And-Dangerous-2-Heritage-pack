# Registre maître des reconstructions expérimentales

Inventaire initial : **2026-09-19**. Dernière mise à jour : **2026-09-26**.

Branche de travail actuelle : `codex/reconstruction-phase-1`.
La préparation de `codex/experimental-reconstruction-inventory` a été intégrée
à `master` avant la création de cette branche; sa photo historique est conservée.

Ce dossier réunit l'état des connaissances disponible pour la restauration et la
reconstruction additive de contenu de *Hidden & Dangerous 2*. La branche part de
`master` et contient donc tous les fichiers déjà versionnés du projet. Le présent
registre complète ces fichiers sans activer de script expérimental dans
l'installation personnelle. Les déploiements privés de test sont isolés et journalisés.

## Principes

- La version commerciale reste le comportement par défaut.
- Une ligne commentée, un script libre ou un nom de checkpoint est une preuve de
  vestige, pas une preuve suffisante du comportement final.
- Les éléments officiels, les inférences et les créations modernes sont toujours
  distingués.
- Aucun binaire commercial extrait n'est ajouté au dépôt.
- Les prototypes restent en `.disabled` tant que leurs propriétaires, liaisons,
  positions et conditions de fin ne sont pas démontrés puis testés en jeu.
  Seuls les essais explicitement préparés dans une copie isolée peuvent utiliser
  des fichiers actifs, avec empreintes et restauration; aucune promotion n'en découle.
- Une reconstruction ne doit jamais doubler un signal, un objectif, une voix, un
  effet ou un acteur déjà pris en charge par la version commerciale.

## Légende d'état

### Avancement vérifié le 26 septembre 2026

- **47 profils / 55 scripts dérivés** reconstruits depuis les archives, avec
  157 sources de mission, trois preuves de campagne Africa 3, deux ressources de dialogue et trois modèles
  d'accessoires supplémentaires;
  les archives de prototypes restent désactivées et aucune
  variante n'est validée en jeu.
- **20 laboratoires A/B / 40 entrées** contrôlés hors moteur, objectifs
  commerciaux conservés. Sept profils Africa 5 restent sans laboratoire renommé :
  leur détecteur de piste commercial absent empêche la copie complète.
- **429 tests Python réussis sur 430 dans la copie de publication**; un test de lien symbolique non exécuté
  faute de privilège Windows. Compilation console et auto-tests de sécurité C#
  précédemment réussis, sans nouvelle modification C# dans ce lot.
- Lecteur audio DPCM complété : vingt WAV de missions décodés et mesurés en mémoire,
  sans export ; deux sons Benelli supplémentaires sont mesurés et incorporés
  uniquement au banc privé, sans modification du jeu. [Méthode](AUDIO_RESSOURCES.md).
- [Banc Benelli FPV](../BENELLI_M4_ADDITIVE/BANC_FPV.md) : 28 sources verrouillées,
  neuf animations décodées, modèle FPV statique dérivé, inspecteur de poses/clés/sons.
  Trois tests JavaScript synthétiques réussis ; affichage navigateur et moteur
  non validés. Le modèle extérieur moderne demeure distinct.
- [Tables Benelli](../BENELLI_M4_ADDITIVE/TABLES_ADDITIVES.md) : lecteurs centraux
  et associations FPV structurées réalisés, 359 vide dans Sabre/PatchX01 mais
  hors capacité Base/Patch. Les modèles ont maintenant des alias courts natifs.
  Ni sauvegarde ni liaison d'arme qualifiée : aucune entrée n'est allouée.
- Trois comparaisons binaires Co_Burgundy1/2/3 supplémentaires reconstruisent
  respectivement douze/deux/dix porteurs et leurs liaisons sans modifier les scripts
  ou sons. Elles restent inertes, hors compte des laboratoires de mission.
- **180 dossiers** recensés. Les études continuent : certains vestiges exigent
  encore une cible, un propriétaire, une ressource ou une observation préalable.
- L'installation actuelle n'est pas modifiée. Cinq profils refusent ses
  surcharges pertinentes en mode strict; les exclusions et empreintes sont
  consignées pour Africa 1, Normandy 1 et Africa 5.
- **Trois copies indépendantes** pour hôte/deux clients : 24 385 fichiers et
  6 508 813 370 octets chacune, même manifeste initial, aucun lien partagé.
  La [voie d'essai native](../../validation/ESSAIS_NATIFS.md) prépare les
  **49 configurations** dans chacune, sans nouveau menu ni lancement du jeu.
  Le client ouvert par un autre usage a été fermé indépendamment : les huit
  derniers profils ont pu être ajoutés, sans fermer de processus ni contourner
  la protection des copies.
  La cinquantième paire, transition Africa 4 sur témoin radio Heritage, est
  construite et contrôlée en mémoire; son ajout attend la fermeture du client
  externe qui a été rouvert entre-temps.
- **90 cycles réels de fichiers**, en trois rapports conservés : 49 pour la
  première série, 28 pour les quatorze ajouts, 13 pour les huit derniers profils.
  La comparaison globale finale
  retrouve tous les fichiers initiaux. Ces cycles ne sont pas des essais en jeu.

Ces nombres ne signifient pas que la reconstruction globale est terminée :
le registre du paquet stable reste à **56 cas pending**, et les 21 candidates
multijoueur vers solo n'ont toujours aucune validation de jeu. Le nouveau
[registre expérimental](../../validation/RECONSTRUCTION.md) suit séparément
**50 profils et 304 contrôles pending**, sans inventer de résultats moteur.
Un [préparateur de fiches](../../validation/RECONSTRUCTION.md#préparer-les-fiches-sans-rien-lancer)
réunit désormais les protocoles, manifestes exacts, incompatibilités et consignes
de retour arrière. Les nouveaux outils d'essais natifs prennent maintenant en
charge la copie indépendante et le déploiement réversible. Les sept variantes
Africa 5 et l'ambiance Co-Burgundy 1 exigent d'abord une preuve réelle du témoin
natif : leurs références commerciales absentes sont préservées, pas remplacées
par des scripts inventés. Aucun jeu ni installateur n'a été lancé par ces outils.

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
- [Variantes reproductibles](VARIANTES_REPRODUCTIBLES.md) : quarante-sept profils et cinquante-cinq scripts
  expérimentaux générés localement, contrôles automatisés, provenance,
  conflit de surcharge Africa 1 et validations en moteur encore en attente.
- [Laboratoires désactivés](LABORATOIRES_DESACTIVES.md) : copies A/B complètes,
  fermeture des scripts et préservation des objectifs Base/Sabre, sans installation.
- [Ressources modernes](RESSOURCES_MODERNES.md) : autorisation utilisateur,
  provenance séparée et premier modèle extérieur original Benelli. Un modèle
  statique ne constitue ni une arme jouable ni une animation FPV compatible.

## Travaux immédiatement recommandés

1. Poursuivre les contrats encore incomplets : synchronisations coop, positions
   réellement absentes et autorité des événements réseau. Les lignes de missions
   auparavant « À documenter » ont désormais une étude ou un renvoi précis.
2. Conserver fermés les faux positifs prouvés; ne pas recréer les six barils du
   dépôt Co_Burgundy3 ni réactiver le signal maquis remplacé par l'alarme.
3. Utiliser les trois copies de test isolées déjà préparées et observer les signaux
   ambigus avant de proposer une réaction inventée; aucun résultat moteur n'est
   encore acquis.
4. Tester les variantes en solo, Carnage et coopération quand la mission existe
   dans plusieurs modes.
5. Ne promouvoir un prototype qu'après réussite des contrôles décrits dans
   [VALIDATION.md](VALIDATION.md).

## Limites de cet inventaire

Ce registre décrit les preuves actuellement accessibles dans le dépôt et dans les
archives commerciales examinées. Il ne prétend pas que chaque intention originale
est récupérable. Les points explicitement marqués « moderne » sont des créations
compatibles avec les vestiges, pas des contenus historiques authentifiés.
