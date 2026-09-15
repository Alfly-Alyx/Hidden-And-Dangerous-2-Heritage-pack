# Principe expérimental — conserver la release et la branche reconstruite

État : règle générale pour les études présentes et futures, 14 septembre 2026.
Elle ne rend aucun prototype actif et n'autorise aucune modification silencieuse
de la version release.

## Principe

Le fait qu'un ancien comportement ait été remplacé n'est plus, à lui seul, un
motif d'abandon. L'étude doit d'abord chercher une reconstruction **additive** :

- la branche release reste intacte et demeure le choix par défaut ;
- la branche ancienne ou reconstruite reçoit une condition de sélection claire ;
- les identifiants d'objectifs, signaux et états sauvegardés sont séparés ;
- les deux branches peuvent être testées seules puis ensemble ;
- tout raccord non commercial porte l'étiquette `MODERNE`, `CMP/MODERNE` ou
  `EXPERIMENTAL` appropriée.

Si cette coexistence n'est pas démontrable sans collision de progression,
d'objectif, de signal ou de sauvegarde, l'étude conserve la proposition mais
n'en produit pas d'intégration activable.

## Contrat minimal à deux branches

| Élément | Branche release | Branche additive |
| --- | --- | --- |
| activation | inchangée, toujours disponible | option ou condition propre, désactivée par défaut |
| objectif | numéro et validation existants | nouveau numéro ; jamais de seconde validation du numéro release |
| signal | protocole existant inchangé | canal distinct ou arbitre monostable documenté |
| sauvegarde | valeurs existantes préservées | état nouveau, versionné et sans réemploi ambigu |
| fin/progression | autorité actuelle | ne peut ni court-circuiter ni valider deux fois la release |
| repli | comportement commercial | désactivation complète sans modifier la baseline |

Une proposition doit nommer précisément la condition de choix : option de
mission, nouvel objectif, déclencheur exclusif, état sauvegardé ou autre arbitre
observable. « Les deux scripts sont présents » n'est pas une condition de choix.

## Risques à documenter systématiquement

- double succès, double échec ou deux textes incompatibles pour un objectif ;
- deux signaux distincts aboutissant au même effet non idempotent ;
- reprise de sauvegarde dans une branche différente de celle enregistrée ;
- deux dialogues ou sons utilisant simultanément une ressource globale ;
- route additive qui bloque ou anticipe la route release ;
- respawn, déconnexion ou changement d'hôte réarmant un événement monostable.

## Cartes multijoueur sans variante solo

L'absence de données suffisantes pour une mission solo ne clôt pas l'étude.
Toute carte uniquement multijoueur reçoit aussi une proposition de variante
solo distincte, marquée `PROTOTYPE` ou `RECONSTRUCTION` :

- la carte et le mode multijoueur officiels restent intacts ;
- la variante solo possède son propre identifiant, son répertoire et sa fin de
  mission ;
- le dossier sépare actifs officiels réutilisés, logique solo créée, choix
  spéculatifs, blocages et protocole de test ;
- une conception documentée peut être livrée sans script jouable lorsque les
  placements, textes ou règles de progression manquent encore ;
- aucun comportement solo inventé n'est présenté comme contenu commercial.

## Protocole commun

1. Mesurer séparément la baseline release et tous ses points de sortie.
2. Tester la branche additive seule, toujours sous un artefact désactivé.
3. Tester les deux ordres : release puis additive, additive puis release.
4. Tester simultanéité, répétition, mort, respawn, déconnexion et
   sauvegarde/reprise aux frontières de choix.
5. Vérifier qu'un événement n'est compté, joué ou validé qu'une fois.
6. Désactiver l'option additive et confirmer une trace fonctionnelle identique à
   la baseline release pour les fichiers réellement modifiés.

## Application aux études actuelles

- Co_Libye1 : conserver l'objectif 2 « officiers » et porter l'ancienne escorte
  sur un objectif 7 distinct.
- Africa3 : conserver les activités et synchroniseurs courants ; toute
  conversation dormante exige un déclencheur exclusif et un mutex audio.
- Burgundy 3 : conserver le son de `OnCutscene(4)` ; une restitution hors
  cinématique doit utiliser un canal réservé à la seule branche directe.
- Africa 1 : les introductions 1 et 3 restent deux choix exclusifs sur le même
  binding de démarrage ; elles ne doivent jamais être lancées ensemble.
- Africa1_Obj : conserver la mission multijoueur release à un avion ; les
  variantes multi-avions et solo sont des entrées modernes distinctes avec
  leurs propres actifs, progression et fin.
- Africa 2 : conserver `AF2_actprelet.scr` comme propriétaire de la particule
  du Junkers ; le binding orphelin ne justifie pas un second émetteur.
- Burma 2 : ne pas rétablir un son de cinématique tant qu'un horaire complet ne
  prouve pas qu'il ne masque ni ne double les dialogues actifs.
- Alps3_Obj : conserver l'entrée multijoueur Sabre ; les variantes legacy à
  trois véhicules, multijoueur et solo, sont des missions distinctes.
- Normandy 1 : conserver les signaux de N01 ; l'option de proximité solo ne
  peut qu'activer le détecteur 30 m déjà contenu dans N24/N25.
- Africa 4 : conserver l'introduction Dakota ; l'oasis legacy utilise une
  entrée sélectionnable et un identifiant de cinématique distincts.
- Arctic 1 : conserver `Object155` sans binding ; l'animation de lightmap
  reçoit un contrôleur séparé, temporisé et désactivé par défaut.
- Ardens1_Obj : conserver la carte multijoueur Sabre ; les rosters Base
  multijoueur et solo sont des entrées prototype distinctes.
- Arctic 2 : conserver les portes de bunker jointes de la release ; un mode à
  portes indépendantes exige d'abord des portails et propriétaires séparés, pas
  la simple réactivation des anciens émetteurs.
- Czech 3 : conserver la villa release ; les quatre acteurs retirés ne peuvent
  revenir que dans une branche avec placements, déclencheur et comptage propres.
- Czech 4 : conserver Czech4 et Czech4 Zone ; la mission « Prototype —
  vestiges » possède ses propres acteurs, compteur et raccords explicitement
  modernes.
- Co_Burgundy1 : conserver la coop release ; John Ashley et le chien solo sont
  deux options indépendantes d'une variante Reconstruction distincte.
- Burgundy 2 : la garde importée de la coop et l'ambiance animale importée du
  solo sont deux variantes additives distinctes ; ni `ge_pruchod2` ni la
  cinématique K1–K8 de la release ne sont remplacés.
- Normandy 2 : les quinze défenseurs retirés appartiennent à une copie
  « défense élargie » avec activation, comptage et nettoyage de fin propres ;
  le réseau `R_N2_Go_*` reste une branche séparée.
- Cartes MP-only : chaque conversion vit dans `MP_ONLY_TO_SOLO_MATRIX`, sous un
  nom « Prototype/Test — reconstruction », et ne devient une mission solo
  qu'après lancement, objectif et fin observés ; l'entrée MP reste intacte.
- Co_Libye3 : `Opel.scr` ne reçoit aucun propriétaire dans la release ; les
  hypothèses cargo et FlaK restent deux copies de test séparées tant qu'un
  binding historique ou une observation discriminante ne tranche pas.
- Co_Burgundy3 : l'ambiance solo revient seulement par copie exacte des dix
  propriétaires `snd_vrabec01..10` et de leurs bindings, sans dupliquer les
  scripts ou `sounds.bin` déjà identiques en coop.
- Alps 2 : l'activateur 13 ne peut être lié qu'après création des deux acteurs,
  de leurs items et de deux comportements locaux ; les routes de 15/16 ne sont
  jamais réutilisées sous de nouveaux noms.
- Czech 2 : les voix 19993810/11 ont un propriétaire audio unique ; une branche
  alternative arbitre porte et cinématique, tandis que la release conserve
  intégralement `cut2.scr`.
- Tutorial : la conversation `T_dummy_speech` revient seulement dans une copie
  laboratoire avec un unique Talker_02 ; son placement, son corps et son item
  restent modernes tant qu'aucun transform commercial n'est retrouvé.
- Africa 3 : le synchroniseur 14/15 n'est pas recréé à côté de la conversation
  active ; une coordination 22/23 ne peut être qu'une variante moderne sans
  voix, contrôleur, signaux et sauvegarde séparés.
- Africa 5 : `AF4_runway_detector.scr` reste l'unique autorité de l'objectif 4
  et de la valeur 40 ; le binding `runway01` manquant ne reçoit aucun substitut
  qui écrirait la progression une seconde fois.
- Burgundy 2 : la garde importée de la coop et l'ambiance animale importée du
  solo sont deux variantes additives distinctes ; ni `ge_pruchod2` ni la
  cinématique K1–K8 de la release ne sont remplacés.
- Normandy 2 : les quinze défenseurs retirés appartiennent à une copie
  « défense élargie » avec activation, comptage et nettoyage de fin propres ;
  le réseau `R_N2_Go_*` reste une branche séparée.

Cette règle ouvre une piste d'étude ; elle ne transforme jamais une hypothèse
en contenu officiel ni une maquette `.disabled` en fonctionnalité release.

Dans une étude existante, la conclusion « ne pas restaurer parce que remplacé »
doit désormais se lire comme « ne pas écraser la branche release ». Le blocage
du prototype reste valable tant qu'aucun canal, objectif, binding ou arbitre
distinct ne rend la coexistence sûre ; il doit être réévalué si cette séparation
devient démontrable.
