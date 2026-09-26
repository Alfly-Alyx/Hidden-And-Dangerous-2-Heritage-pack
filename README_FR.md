# Hidden & Dangerous 2 Heritage Pack

[**Français**](README_FR.md) · [English](README.md)

Un pack de restauration et d’extension pour **Hidden & Dangerous 2: Sabre Squadron 1.12**.

Heritage Pack remet en service le jeu en ligne, corrige des objectifs et des séquences oubliées, libère l’exploration des cartes, ajoute la grande collection communautaire CMP et rend accessibles plusieurs vestiges officiels clairement signalés comme expérimentaux.

> Le jeu original est nécessaire et n’est pas inclus.

[**Télécharger la dernière version**](https://github.com/Alfly-Alyx/Hidden-And-Dangerous-2-Heritage-pack/releases)

## Ce que le pack apporte

| Fonction | Résultat dans le jeu |
|---|---|
| Jeu en ligne | Réunit le service maître H&D2 déjà utilisé et OpenSpy dans une seule liste en jeu, retire les doublons et active DirectPlay si nécessaire. |
| Missions débloquées | Une option permet d’ouvrir immédiatement les 24 missions de H&D2 et les 9 missions de Sabre Squadron pour le profil actif. |
| Exploration libre | Supprime les avertissements, les échecs et les murs invisibles liés aux limites de zone, sans retirer les collisions normales du décor. |
| Contenu du jeu restauré | Remet en fonctionnement des parties du jeu original que la version finale n’utilisait plus : morceaux de missions, objectifs optionnels, dialogues, animations de personnages et passages alternatifs. |
| Easter eggs | Réactive les séquences d’Africa 1 et d’Africa 4 neutralisées par la mise à jour 1.12. |
| Contenu communautaire | Consulte le dépôt CMP officiel et installe ou met à jour sa dernière révision disponible (actuellement 2.6.5 avec 156 cartes et missions coopératives). |
| Missions personnalisées | Ajoute `Solo → Missions personnalisées`, avec des listes séparées pour les missions utilisateur, les adaptations multijoueur et l’exploration libre. Le gestionnaire fourni analyse le dossier `CustomMissions` sans remplacer les créations existantes. |
| Adaptations solo | Une option construit 11 missions solo à partir de missions coopératives et de variantes d’objectifs officielles déjà présentes dans le jeu installé. Elles sont clairement signalées et rangées dans `Adaptations multijoueur`. |
| Vestiges officiels | Ajoute Africa5 Prototype et Normandy3 Zone au menu multijoueur avec un nom qui indique clairement leur état expérimental. |
| Affichage | Détecte l’écran et le PC, applique la résolution maximale utilisable et adapte les graphismes aux performances de la machine. |
| Rapports d’erreur | Lance un moniteur uniquement avec le jeu, crée un rapport local et une archive ZIP en cas de plantage, blocage ou erreur signalée par le moteur, puis s’arrête avec le jeu. Aucun rapport n’est envoyé automatiquement. |
| Guides PDF | Peut télécharger sur le Bureau le guide joueur et le rapport des découvertes, en français sur un Windows français et en anglais dans les autres langues. |
| Restauration | Sauvegarde les fichiers remplacés et permet de revenir à l’état précédent. |

L’installateur reconnaît ce qui est déjà actif. Après une installation ou une vérification, les options déjà appliquées sont automatiquement décochées.

Heritage Pack remet en service du contenu conçu pour H&D2 mais supprimé, désactivé ou mal relié dans la version finale. Ce ne sont pas de nouvelles missions inventées pour le pack : ces éléments étaient déjà présents dans les fichiers originaux du jeu.

## Installation

1. Installez **Hidden & Dangerous 2: Sabre Squadron** et la mise à jour **1.12**.
2. Fermez le jeu.
3. Téléchargez `H-D2-Heritage-Pack-Setup.exe` depuis la page des Releases.
4. Lancez-le en tant qu’administrateur.
5. Vérifiez le dossier du jeu, choisissez vos options, puis cliquez sur **Installer**.
6. Relancez l’outil et cliquez sur **Vérifier l’état** si vous souhaitez contrôler l’installation.

La CMP 2.6.5 représente environ **1,08 Go à télécharger** et **3,12 Go installés**. L’installateur consulte le dépôt officiel, identifie sa version et son commit, puis télécharge uniquement la révision officielle sélectionnée.

## Où trouver les contenus

- Les campagnes et missions officielles restent dans les menus solo habituels.
- Les missions CMP se trouvent dans `Multijoueur → Créer → LAN → Coopération`.
- Ouvrez `Solo → Missions personnalisées` pour accéder aux trois listes séparées.
- La liste `Adaptations multijoueur` contient les versions solo d’Alps 3 Objectif, Ardennes 1 Objectif, Brest Coop, Bourgogne 1–3 Coop, Libye 1–3 Coop et Sicile 1–2 Coop lorsque l’option correspondante de l’installateur est sélectionnée.
- Pour ajouter une mission, placez son dossier contenant `tree.klz` et ses fichiers nécessaires dans `CustomMissions`, puis lancez `HD2-Custom-Mission-Manager.exe` depuis la racine du jeu et choisissez **Scanner et installer**. Les paquets avancés existants avec `mission.json` restent compatibles.
- `PROTOTYPE - Africa5` se trouve en Deathmatch.
- `PROTOTYPE - Normandy3 Zone` se trouve en Occupation.

Les deux prototypes servent à explorer des vestiges jouables. Ils ne sont pas présentés comme des missions solo terminées.

## Guides PDF

Ces PDF restent proposés séparément sur la page de la release GitHub. Une option de l’installateur peut aussi télécharger automatiquement les deux documents de la langue de Windows et les placer sur le Bureau. Ils ne sont jamais ajoutés au dossier du jeu.

### Pour les joueurs

- [Guide des secrets et easter eggs — français](output/pdf/HD2-Guide-Joueur-Secrets-et-Easter-Eggs.pdf)
- [Secrets and easter eggs player guide — English](output/pdf/HD2-Player-Guide-Secrets-and-Easter-Eggs-EN.pdf)

Ce guide explique comment déclencher les easter eggs et atteindre les lieux cachés, sans transformer la lecture en documentation technique.

### Pour découvrir l’enquête

- [Rapport des découvertes — français](output/pdf/HD2-Rapport-des-Decouvertes.pdf)
- [Discovery report — English](output/pdf/HD2-Discovery-Report-EN.pdf)

Le rapport raconte les découvertes : contenu coupé, variantes de missions, Londres, objectifs oubliés, prototypes, armes et véhicules retrouvés dans les archives.

## État actuel

La version **0.10.0** consolide notamment :

- la détection exacte des options déjà installées ;
- une seule liste H&D2 réunissant le service communautaire déjà utilisé et OpenSpy ;
- le menu natif des missions personnalisées, ses trois catégories séparées et l’analyse automatique des dossiers de mission sans manifeste obligatoire ;
- le déploiement automatique de ce menu dans le jeu par l’installateur principal, même avant l’ajout d’une mission personnalisée ;
- la création et l’installation facultatives de 11 adaptations solo depuis les archives H&D2 du joueur, sans remplacer les missions coopératives d’origine ;
- la remise en service de contenu original qui ne fonctionnait plus dans la version finale ;
- l’exploration libre appliquée aussi aux deux prototypes ;
- l’installation réversible et la protection des sauvegardes du joueur ;
- les rapports automatiques locaux, démarrés et arrêtés avec chaque session du jeu ;
- le téléchargement facultatif des deux guides PDF français ou anglais sur le Bureau.

## Ce qui n’est pas encore jouable

Les archives du jeu conservent des morceaux de contenus supprimés, mais pas toujours assez pour les réactiver tels quels. Cela concerne :

- le secret du Tutorial, toujours neutralisé par la version 1.12 ;
- les fragments de missions `ENGLAND`, `CASTLE1` et `CASTLE2`, dont l’objectif 5 de CASTLE ;
- l’ancienne intrigue autour de Gary Bristol et les missions ou campagnes annoncées à Londres/Angleterre, en Allemagne et à Dunkerque ;
- les armes incomplètes : les deux lance-flammes, la garrote et le ZK-383 ;
- les avions et le Fa 223 retrouvés comme modèles ou décors, mais sans système complet permettant de les piloter.

Il faudra recréer les éléments manquants — portions de carte, objectifs, réactions de mission, animations ou comportement des armes et véhicules — puis les tester avant de présenter ces contenus comme jouables.

## Revenir en arrière

Relancez l’installateur et choisissez **Restaurer**. Heritage Pack remet les fichiers sauvegardés et retire les ajouts qu’il gère, sans écraser une progression rejouée depuis l’installation.

## Signaler un problème

Le moniteur de diagnostic ne fonctionne que pendant le jeu. Il produit automatiquement un dossier et un ZIP lors d’un plantage, d’un blocage durable ou d’une erreur reconnue dans le journal du moteur. Pour un défaut visible qui ne fait pas planter le jeu, appuyez sur **Ctrl+Maj+F12** pendant la mission.

Utilisez **Ouvrir les rapports** dans l’installateur, puis joignez le ZIP le plus récent à une [issue GitHub](https://github.com/Alfly-Alyx/Hidden-And-Dangerous-2-Heritage-pack/issues) en indiquant ce qui se passe à l’écran. Les rapports restent sur le PC et ne sont jamais envoyés automatiquement.

## Licence actuelle

Le code de H&D2 Heritage Pack est actuellement publié sous [GPL-3.0-or-later](LICENSE). Il peut être utilisé, modifié et partagé, y compris commercialement. Une version modifiée qui est distribuée doit rester sous GPL et conserver son code source accessible.

Cette licence couvre le code du Heritage Pack, pas le jeu original ni les créations communautaires. Le correctif écran large conserve sa licence MIT, et les cartes du CMP restent attribuées à leurs créateurs. Les détails figurent dans [THIRD_PARTY.md](THIRD_PARTY.md) et dans la [notice sur le contenu communautaire](docs/CONTENU_COMMUNAUTAIRE.md).

Passer l’ensemble du projet sous MIT demanderait d’abord de remplacer les lecteurs d’archives liés au projet GPL **HD2unpacker**.

## Éléments extérieurs et leurs auteurs

Le Heritage Pack réunit les créations et services extérieurs suivants :

- **Hidden & Dangerous 2 et Sabre Squadron** — créés par **Illusion Softworks**. Le jeu commercial est nécessaire et n’est jamais inclus dans le pack.
- **Service de liste maître H&D2 déjà utilisé** — la solution est créditée à **JarnoKai (Mökki Medium)** et **Ondra** ; elle est hébergée et maintenue par le **clan =RpR=**. **DnA (Hawk)** a créé l’ancien outil de mise à jour du fichier hosts présenté par RpR.
- **Service réseau OpenSpy** — développé et maintenu par les **contributeurs du projet OpenSpy**. Le Heritage Pack interroge directement ce service ; la DLL séparée `openspy-client`, maintenue par **anzz1**, n’est pas embarquée puisque le pont local n’en a pas besoin.
- **Protocole GameSpy EnctypeX** — le pont local qui réunit les deux services adapte le décodeur/encodeur GPL-2.0-or-later publié par **Luigi Auriemma**.
- **Community Map Package 2.6.5** — compilé et conservé par le **clan =RpR=** ; son dépôt public `had2-cmp` est publié par **ehylla93**. Il est téléchargé depuis ce dépôt lorsque l’utilisateur le choisit et n’est pas stocké dans l’installateur.
- **Missions et cartes du CMP** — **BetterYouThanMe, Black Akres, culticaxe, Dr_NO, GS Hawk, GUB, HippoBlindEye, Joe66, Joel, Lars, Matro, miamidos, Polanski, ProSabre, Rs_sabre, Sasha, Sqdn. Ldr. Ted Striker, Stern** et **Zdenda** sont les auteurs ou convertisseurs nommés dans les crédits installés avec le CMP.
- **HiddenandDangerous2.WidescreenFix** — créé par **ThirteenAG** et inclus sous licence MIT.
- **Recherche sur le format de HD2unpacker** — les lecteurs DTA suivent la documentation publique et l’implémentation GPL-3.0 de **M3tox**.
- **DirectPlay** — ancien composant Windows fourni par **Microsoft**. L’installateur peut activer celui qui appartient déjà à Windows ; il ne le redistribue pas.

Le **H&D2 Heritage Pack** lui-même a été initié par **Alfly-Alyx**. Son installateur, son système de restauration, son pont local de fusion des listes, son gestionnaire de missions personnalisées, ses scripts restaurés, ses tests et ses guides sont publiés dans ce dépôt.

Le détail carte par carte est conservé dans `cmp_info/README.md`, installé avec le CMP. Certaines entrées y sont indiquées sans auteur ou avec un auteur inconnu ; Heritage Pack conserve honnêtement cette mention au lieu d’inventer une attribution.

Sources : [jouer en ligne avec RpR](https://www.rprclan.com/hd2/play-online), [OpenSpy](https://github.com/openspy), [dépôt du CMP](https://github.com/ehylla93/had2-cmp), [Widescreen Fixes Pack](https://github.com/ThirteenAG/WidescreenFixesPack) et [HD2unpacker](https://github.com/M3tox/HD2unpacker).

Heritage Pack est un projet communautaire indépendant, conçu pour préserver et redécouvrir le jeu.
