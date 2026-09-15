# Registre de faisabilité des créations expérimentales

État de l'étude : 14 septembre 2026. Ce document prépare des prototypes ; il ne
constitue ni une promesse d'intégration, ni une preuve que le contenu décrit a
existé sous une forme jouable.

## Périmètre et règle de preuve

Le registre ne couvre que les cas qui demanderaient de recréer ou de compléter
une carte, un modèle, des animations, une physique, un comportement, une chaîne
d'objectifs ou un script. Les simples réactivations de données commerciales
complètes restent hors de ce périmètre.

Chaque constat emploie l'une des étiquettes suivantes :

- **OFFICIEL** : élément observé dans les archives commerciales, les démos ou
  les fichiers de mission conservés ;
- **INFÉRENCE** : interprétation cohérente avec plusieurs éléments officiels,
  mais non démontrée par un fichier source complet ;
- **CRÉATION MODERNE** : contenu ou raccord qu'il faudrait concevoir aujourd'hui.

La faisabilité technique et la fidélité historique sont évaluées séparément :

| Niveau | Faisabilité technique | Fidélité historique atteignable |
| --- | --- | --- |
| 4 | correction chirurgicale, faible surface de changement | chaîne officielle presque complète |
| 3 | prototype borné, mécanismes connus | plusieurs preuves convergentes |
| 2 | chantier substantiel ou dépendant de l'éditeur | intention partielle seulement |
| 1 | R&D lourde, nombreux systèmes à créer | trace nominale ou visuelle isolée |
| 0 | comportement impossible à déduire actuellement | aucune base probante exploitable |

Les verdicts ci-dessous proviennent d'un audit statique des couches commerciales
de base, Patch et Sabre, complété par les démos extraites. Aucun test dans
l'installation du jeu n'a été effectué par cette tâche.

## Synthèse de décision

| ID | Cas | Faisabilité | Fidélité | Décision actuelle |
| --- | --- | ---: | ---: | --- |
| WPN-FLAM-GB | Flamethrower Portable No. 2 | 1 | 1 | concept moderne seulement ; reporter |
| WPN-FLAM-DE | Flammenwerfer 35 | 1 | 1 | concept moderne seulement ; reporter |
| WPN-GAROTA | Garota | 1 | 0 | ne pas produire sans nouvelle source |
| WPN-ZK383 | ZK-383 | 2 | 1 | étude visuelle préalable, pas d'intégration par défaut |
| MAP-ENGLAND | ENGLAND | 2 | 1 | démonstrateur de logique, jamais présenté comme carte restaurée |
| MAP-CASTLE1 | CASTLE1 | 1 | 1 | conservation et analyse seulement |
| MAP-CASTLE2 | CASTLE2 | 2 | 2 | meilleur candidat à une tranche verticale de carte |
| AIR-SET | Aéronefs conservés | 3 à 4 en décor ; 1 à 2 pilotables | 1 à 3 | animer d'abord ; isoler ensuite un prototype pilotable |
| N2-RETURN | Normandy 2, retour par détecteurs 9–11 | 3 | 2 | prototyper après traçage de l'événement d'activation |
| BU1-BRIDGE | Burma 1, renforts 32–34 | 2 | 1 | vérifier d'abord si le script est obsolète |
| CZ4-PLATOON | Czech 4, groupe 06–09 | 1 | 0 | création moderne trop large ; reporter |
| AF3-SYNC-1415 | Africa 3, synchroniseur 14/15 | 3 | 2 | ne rien ajouter si la conversation actuelle fonctionne |
| AF3-SYNC-2223 | Africa 3, synchroniseur 22/23 | 0 | 0 | aucune reconstruction sans invariant observable |
| CZ3-CARNAGE-OBJ4 | Czech3, doublon Carnage au slot 4 | 3 | 2 | substitution 1→4 seulement dans une copie 3/7 ; jamais deux objectifs visibles |
| BU2-CUTSOUND | Burma 2, `CUTSOUNDSHLIDKA.scr` | 3 | 2 | inventaire sonore terminé ; reconstruction bloquée sans ordre ni timecodes |
| TUT-ACCESS | Tutorial, accès au lingot | 4 | 2 | adaptation physique minimale si l'accès original échoue |
| AL1-WIND | ALPS1_MP_ZONE, rafale manquante | 4 | 2 | petite adaptation locale après test du chargement |
| AL1-FORGE24-1011 | Alps 1, `ge_10/ge_11` depuis forge24 | 3 | 3 | déclarations reconstruites ; ajout en fin de projet après test d'idempotence |
| AL1-GE24-SNIPER | Alps 1, poste de réaction ge24 | 2 | 2 | `ge16_sniper` réservé à ge16 ; branche ge24 bloquée sans point distinct attesté |
| AL1-HAKL2 | Alps 1, second half-track `hakl_na` | 3 | 2 | tester atomiquement signal 11 et correction du point `H2` |
| AL1-FORGE40-DEATH | Alps 1, compteur de morts vers forge40 | 3 | 2 | hypothèse 2-sur-3 ; ge02/ge03 reconstructifs et signal 2 à prouver en jeu |
| CO-BURG-DOORS | Co_Burgundy1/3, portes sonores | 4 | 3 | recréer dix porteurs inertes attestés |
| CO-BURG1-SURVIVAL | Co_Burgundy1, objectif 7 de survie | 2 | 3 | bloquer le prototype jusqu'à preuve d'une mort joueur fiable en coop |
| CO-LIB1-LEGACY | Co_Libye1, ancien objectif 2 et dialogue 48/49 | 2 | 3 | objectif remplacé ; variante additive seulement, dialogue bloqué |
| CO-BURG2-LEGACY | Co_Burgundy2, évasion et survie | 2 | 2 | scénario remplacé ; ne pas raccorder les seuls signaux 3/4 |
| BURG2-POLISH | Burgundy2 solo, reprise du polissage | 4 | 4 | **MIGRÉ VERS STABLE** — signal 3 et animation exacte intégrés |
| CZ6-G11-G43 | Czech6, réveil de G11/G43 | 3 | 2 | baseline hors rayon avant tout handler de réveil |
| BREST-Z2-WAKE | Brest, réveil de `z2_agresor1` | 3 | 2 | prototype réveil seul ; conserver la garde de valeur 6 |
| AF5-HANDLERS | Africa5, récepteurs 43 et sklad04 | 3 | 2 | essais gradués vers `ACTIVATE`, jamais alarme inventée |
| COOP-OBJ-OMISSIONS | Brest/Sicily, objectifs solo omis | 2 | 3 | Carnage, étapes solo et conflits : aucune copie directe |
| AF5-RUNWAY01 | Africa 5, détecteur de piste 01 | 4 | 3 | probablement obsolète ; ne pas recréer par défaut |
| AF5-ACTIVATORS | Africa 5, activateurs 14/20/22 | 2 | 2 | supports spatiaux à recréer ; priorité au groupe 14 |
| AF5-READ19 | Africa 5, lecture d'archives par AF4_19 | 2 | 3 | API `Read` sans précédent actif ; laboratoire avec cleanup seulement |
| AF5-FAN-PHYS | Africa 5, ventilateur physique | 3 | 2 | interaction monostable moderne ; proximité seulement en comparaison |
| AF4-PROX-ASSAULT | Africa 4, assaut simultané à 60 m | 3 | 3 | profil exclusif avec organisateur filtré ; jamais deux propriétaires |
| AF4-ALT-INTRO | Africa 4, intro panoramique et scène 2 | 2 | 2 | caméras à recréer ; sortie centralisée avant tout essai |
| NOR-TIRPITZ-7 | Norway, gardes Tirpitz 1/2/6/7/12/13/16 | 2 | 2 | scripts retrouvés ; acteurs et routes sans placement historique |
| AF1-04-G067 | Africa 1, prolongement de ronde AF1_04 | 2 | 2 | g06/g07 à placer et relier ; branche longue exclusive |
| AF1-20-PATROL | Africa 1, patrouille post-alarme AF1_20 | 2 | 2 | point 01 et `LOOKAROUND` manquent ; garder la rotation release |
| AF3-SLEEP-2426 | Africa 3, sommeil des gardes 24/26 | 2 | 2 | préserver l'assise stable ; tester Sleep séparément |
| AF3-G13-SIT | Africa 3, siège aléatoire du garde 13 | 3 | 2 | placement moderne guidé par 14/15, sans copier leurs transforms |
| AF1-G12-VOICE | Africa 1, voix du garde de toit 12 | 3 | 2 | banques 9/50 et 9/53 à identifier et auditionner d'abord |
| AF2-JUNKERS-FX | Africa 2, particule du Junkers | 4 | 3 | probablement obsolète ; effet déjà créé par le script actif |
| AF1-OBJ-PLANE02 | AFRICA1_OBJ, second avion | 2 | 2 | implantation réelle à créer ; pas une simple liaison |
| LI3-OBJ4-SURVIVAL | Libye3, survie de l'unité | 4 | 3 | fragment de sortie désactivé, calqué sur Libye1/2 |
| LI3-OBJ6-DUP | Libye3, second texte Carnage 15533 | 0 | 4 | résidu exact du n°5 actif ; ne rien reconstruire |
| NOR-GARY | Norway, personnage Gary | 1 | 1 | personnage, position et rôle à reconstruire ; suspendre |

## Armes à recréer

### WPN-FLAM-GB et WPN-FLAM-DE — les deux lance-flammes

**OFFICIEL.** Les appellations *Flamethrower Portable No. 2* et
*Flammenwerfer 35*, leurs munitions et leurs identifiants subsistent dans les
listes historiques. Des définitions génériques d'effets et de sons subsistent
également. En revanche, aucun ensemble local complet ne fournit le modèle tenu,
le modèle au sol, les animations, la réserve, le jet, les dégâts et le
comportement IA. `MODELS\flame1.4ds` ne pèse que 471 octets et ne contient que
le nœud `fire01` : c'est une amorce d'effet, pas la preuve d'une arme finie.

**INFÉRENCE.** Les deux armes pourraient partager un socle technique, mais ni
leur cadence, ni leur portée, ni leur consommation, ni leur présentation
exactes ne sont récupérables à partir des seules traces restantes.

**CRÉATION MODERNE minimale.** Il faudrait au moins deux modèles d'arme avec
variantes tenue/sol, les animations première et troisième personne, un réservoir
et sa jauge, un jet continu, une collision ou un balayage de dégâts, l'allumage
des cibles, les réactions IA, les sons, l'équilibrage et les règles réseau. Un
prototype acceptable doit rester dans une mission laboratoire et porter une
mention explicite « interprétation moderne ».

**Porte de décision.** Ne commencer qu'après validation d'une méthode stable
pour : (1) un tir continu, (2) une consommation continue, (3) un volume de
dégâts sans traversée abusive des murs et (4) la réplication multijoueur. Sans
ces quatre preuves, produire les modèles ne ferait que déplacer le risque.

### WPN-GAROTA — Garota

**OFFICIEL.** Une mention attribuée à la conception subsiste dans la
documentation d'audit, mais aucune chaîne locale complète — modèle, inventaire,
animation ou script — n'a été retrouvée.

**INFÉRENCE.** Une arme silencieuse à courte portée est plausible, mais sa
forme, sa cible, son animation et ses conditions d'emploi ne sont pas
reconstructibles de manière historique.

**CRÉATION MODERNE.** Une implémentation exigerait une paire d'animations
attaquant/victime, l'alignement et le verrouillage des deux personnages, des
interruptions sûres, la réaction des témoins, la létalité et les cas réseau.

**Verdict.** Aucun prototype tant qu'une source nouvelle n'apporte pas au moins
un visuel ou une description mécanique. Une attaque générique étranglée serait
une fonctionnalité neuve, pas une restauration.

### WPN-ZK383 — ZK-383

**OFFICIEL.** L'arme apparaît dans l'iconographie alpha/bêta, mais aucun modèle
et aucune définition jouable complète ne subsistent localement.

**INFÉRENCE.** La famille des pistolets-mitrailleurs existants fournirait une
base de comportement technique. Elle ne prouve ni les proportions exactes du
modèle d'origine, ni ses animations, ni son équilibrage prévu.

**CRÉATION MODERNE minimale.** Modèles tenu/sol, texture, icône, point de prise,
chargeur, rechargement, sons et réglages de tir. C'est plus faisable qu'un
lance-flammes parce que le système balistique existe déjà, mais l'authenticité
visuelle doit d'abord être documentée par des références externes attribuables.

## Cartes sans géométrie commerciale complète

### MAP-ENGLAND

**OFFICIEL.** Quatorze scripts, environ 382 lignes, 14 références de frames et
sept chemins subsistent. `EN_obj.scr` décrit une progression textuelle : tuer
les ennemis, trouver l'otage, réussir. Aucun appel conservé ne change cependant
un état d'objectif. Aucun dossier de carte autonome `MISSIONS\ENGLAND` n'a été
retrouvé.

**INFÉRENCE.** Ce lot ressemble à une démonstration de logique ou à un fragment
de mission, pas à une carte commerciale prête à réactiver.

**CRÉATION MODERNE.** Une petite scène d'exposition pourrait matérialiser les
frames, les chemins et la succession suggérée par les scripts. Elle doit être
nommée « démonstrateur ENGLAND fondé sur des scripts conservés », jamais
« mission restaurée ».

**Condition d'arrêt.** Ne pas étendre le démonstrateur en campagne sans
géométrie, acteurs, briefing ou objectifs officiels supplémentaires.

### MAP-CASTLE1

**OFFICIEL.** Soixante scripts, environ 4 118 lignes, 41 références de frames,
203 noms de chemins et les objectifs 1 à 3 subsistent. `objectyves.scr` gère les
signaux 20 à 23. Aucun dossier de carte autonome ni animation de mission
associée n'a été retrouvé.

**INFÉRENCE.** Le volume des patrouilles démontre une architecture de mission,
mais ne permet pas de retrouver le château, les positions ni la topologie. Il
peut aussi s'agir d'une branche plus ancienne que CASTLE2.

**Verdict.** Conserver la chaîne comme matériau d'étude. Toute carte jouable
serait majoritairement inventée ; priorité inférieure à CASTLE2.

### MAP-CASTLE2

**OFFICIEL.** Cinquante-cinq scripts, environ 4 522 lignes, 72 références de
frames, 63 chemins et quatre objectifs principaux subsistent : rester discret,
contacter l'agent Aika/Salter, récupérer les documents et rejoindre la sortie.
Un cinquième objectif secondaire, « récupérer les armes saisies », est commenté
à l'initialisation mais conserve son activation et son achèvement. Deux
apparitions aléatoires, quatre caméras et les auxiliaires du cinquième objectif
sont encore décrits par les scripts. La géométrie, les acteurs, les checkpoints,
le briefing et les sons de la carte autonome ne subsistent pas comme paquet
complet.

**INFÉRENCE.** C'est la chaîne de mission la plus structurée des trois lots et
le meilleur candidat à une tranche verticale. Les scripts ne déterminent pas à
eux seuls l'architecture du château.

**CRÉATION MODERNE minimale.** Construire une seule aile de test comprenant le
contact, les documents, le dépôt d'armes et la sortie ; matérialiser uniquement
les checkpoints nécessaires ; utiliser des éléments commerciaux apparentés
sans prétendre qu'ils étaient ceux de CASTLE2.

**Critères du prototype.** Les objectifs 1 à 5 doivent avoir un état initial,
une activation et une résolution cohérents ; les deux apparitions doivent être
rejouables ; l'alerte, la mort de l'agent, la récupération anticipée des armes
et la sauvegarde/reprise ne doivent pas bloquer la sortie.

## Aéronefs : animation puis pilotage

**OFFICIEL.** Les modèles conservés contiennent des hiérarchies utiles : moteurs,
hélices ou rotors, gouvernes, roues, sièges et parfois caméras. Ces noms de
nœuds prouvent un modèle articulé ; ils ne prouvent pas l'existence d'une
physique de vol, d'entrées joueur ou d'un véhicule opérationnel.

Trois paliers doivent rester séparés :

1. **Décor animé** : hélices, gouvernes et trajectoire scénarisée.
2. **Véhicule scénarisé** : montée à bord éventuelle, piste imposée, états de
   dommage et sortie contrôlée.
3. **Pilotage libre** : commandes, enveloppe de vol, collisions, dommages,
   caméra, HUD, sièges, armes éventuelles, IA et réseau.

| Aéronef | Preuve officielle utile | Décor animé | Véhicule scénarisé | Pilotage libre | Première décision |
| --- | --- | ---: | ---: | ---: | --- |
| Ju 52 | modèle, sous-modèles, portes/train/ailes et scripts de scène Africa 1 | 4 | 3 | 1 | premier décor animé |
| La-5 | moteur, hélice, gouvernes, roues, `SEAT00`, `cameraFPV` | 3 | 2 | 2 | meilleur candidat avec l'Aichi au banc monoplace |
| Aichi | moteur, hélice, gouvernes, roues, deux sièges et caméras FPV | 3 | 2 | 2 | comparer au La-5 avant choix |
| M323 | six moteurs, gouvernes, plusieurs sièges et caméras | 3 | 2 | 1 | trop complexe pour le premier pilotable |
| Li-2 | deux moteurs, gouvernes, cinq sièges et caméra FPV | 3 | 2 | 1 | phase ultérieure multisiège |
| Fa 223 | deux rotors, gouvernes, quatre sièges et caméras | 3 | 2 | 1 | reporter : physique rotor spécifique |
| Fw 200 | quatre moteurs et hélices, gouvernes, seulement `cameraD` | 3 | 1 | 1 | décor seulement au départ |
| DFS 230 | planeur, gouvernes, roues, quatre sièges et caméra | 3 | 1 | 1 | reporter : remorquage/largage et vol plané à créer |

**Ordre expérimental.** Commencer par le Ju 52 en décor, puis comparer La-5 et
Aichi dans une mission laboratoire. Le premier prototype pilotable doit valider
le roulage, le décollage, le décrochage, l'atterrissage, les collisions, la
sauvegarde et le retour au personnage avant toute généralisation. Aucun appareil
ne doit être annoncé « restauré pilotable » sur la seule base de ses nœuds 4DS.

## Chaînes de scripts et comportements incomplets

### N2-RETURN — Normandy 2, détecteurs de retour 9 à 11

**OFFICIEL.** Les scripts `R_N2_Detector_9.scr`, `10.scr` et `11.scr` existent
dans la base et les démos. `scene2.bin` contient les frames `detector_9`,
`detector_10` et `detector_11`, mais le registre commercial effectif ne les lie
pas. Les trois scripts désactivent d'abord leur détection, puis attendent le
signal 10, commenté comme la route de retour depuis l'objectif. Le détecteur 9
signale Blue_1 à Blue_6 ; le 10 signale Blue_7 à Blue_11 et Blue_13 ; le 11
signale Blue_14, Blue_15 et Blue_17. Blue_12 et Blue_16 sont commentés.

**INFÉRENCE.** Les trois scripts et leurs frames décrivent une embuscade ou une
réactivation étagée sur le trajet retour. Aucun émetteur officiel démontré ne
leur envoie le signal 10 ; les autres usages de ce numéro ont des contextes
différents.

**CRÉATION MODERNE minimale.** Trois liaisons de registre et un seul raccord
d'activation depuis la transition d'objectif correcte. Il ne faut pas utiliser
un signal 10 choisi au hasard ni réactiver Blue_12/16.

**Porte de décision.** Tracer en jeu la transition d'objectif, l'ordre spatial
des trois volumes et l'état des groupes Blue. Tester route normale et détours,
alarme, difficulté, mort préalable des acteurs et sauvegarde/reprise. Classer le
résultat « reconstruction expérimentale », car l'amorce officielle est
incomplète.

### BU1-BRIDGE — Burma 1, renforts 32 à 34

**OFFICIEL.** `BU1_bridge.scr` existe mais n'est pas lié dans le registre
effectif. Il détecte le joueur à sept unités et envoie le signal 1 à `BU1_32`,
`33` et `34`. Ces trois acteurs et leurs scripts existent. Les acteurs 33 et 34
ont les chemins `BU1_33_01` et `BU1_34_01` ; le 32 embarque dans `Type97_18`.
Cependant, aucun de leurs scripts ne traite le signal 1 : ils disposent déjà
d'une activation indépendante à 60 unités. Le patch corrige aussi le traitement
du véhicule par l'acteur 32.

**INFÉRENCE.** `BU1_bridge.scr` est probablement un vestige d'une architecture
d'activation remplacée. Le placer aujourd'hui enverrait des signaux ignorés.

**Décision.** Vérifier d'abord si les acteurs 32–34 se réveillent déjà près du
pont. Si oui, archiver le cas sans correction. S'ils restent inertes, toute
solution demandera à la fois une position de volume et un contrat de réception
nouveaux : déclencheur près du détecteur de pont existant, gestion explicite du
signal 1 et comportement distinct pour le char et les deux fantassins. Ce serait
une création moderne, à tester avec et sans alarme, mort anticipée, siège du
char et sauvegarde/reprise.

### CZ4-PLATOON — Czech 4, groupe 06 à 09

**OFFICIEL.** `CZ4_Counter_01.scr` vise `CZ4_Platoon_06` à `09`, incrémente un
compteur au signal 10 puis leur envoie le signal 7 après trois occurrences. Seul
`CZ4_Platoon_06` possède un acteur, un item, un script et deux chemins `p6_1` et
`p6_2`. Les acteurs, scripts et chemins 07–09 sont absents. Le script 06 ne
traite que le signal 5, pas le signal 7. Le compteur n'est pas lié et aucun
émetteur de ses trois signaux 10 n'est démontré.

**CRÉATION MODERNE minimale.** Trois acteurs, trois scripts, au moins six
checkpoints, une liaison du compteur, quatre récepteurs du signal 7 et trois
liaisons émettrices du signal 10 : environ vingt éléments créés ou modifiés,
sans compter l'équilibrage et les tests.

**Verdict.** Très faible fidélité et surface trop large pour le paquet par
défaut. Ne prototyper qu'après une preuve que ce groupe était du contenu coupé,
et non un échafaudage abandonné.

### AF3-SYNC-1415 — Africa 3, synchroniseur 14/15

**OFFICIEL.** Le registre lie `AF3a_1415synchronizer.scr`, fichier absent, à
`AF3a_14_lookAF15`. Une autre chaîne conservée est déjà complète :
`AF3a_rozhovor_02_activator.scr` vérifie la proximité du joueur et de l'acteur
14, puis déclenche `AF3a_rozhovor_02.scr`. Les acteurs 14 et 15 conservent leurs
états et les annulations liées à l'alarme ou à la mort.

**INFÉRENCE.** Le synchroniseur manquant peut être une ancienne version du
déclenchement actuel. Le cloner depuis le synchroniseur 05/06 risquerait de
lancer deux fois la conversation.

**Décision.** Tracer la conversation, les signaux 9 à 12 et les valeurs de jeu.
Si la scène fonctionne une fois et se termine proprement, ne rien recréer. Un
shim vide n'est justifié que si l'absence du fichier produit une erreur de
chargement réellement nuisible.

### AF3-SYNC-2223 — Africa 3, synchroniseur 22/23

**OFFICIEL.** Le registre lie `AF3a_2223synchronizer.scr`, absent, à
`AF3a_22_look1_01`. Les acteurs 22 et 23 subsistent, mais aucun récepteur de
signaux 1/2 ni aucune conversation aval comparable n'a été identifié.

**Verdict.** Le nom ne suffit pas à déduire une fonction. Ne pas copier le
synchroniseur 05/06. Une reconstruction ne devient recevable qu'après découverte
d'un invariant observable — blocage, séquence muette ou signal sans destinataire
— ou d'une nouvelle source officielle.

### BU2-CUTSOUND — Burma 2, son de patrouille

**OFFICIEL.** Le registre lie le fichier absent `CUTSOUNDSHLIDKA.scr` au frame
`l_b2str_4`, dans le groupe de la cinématique comprenant `CUTSCENE.scr`,
`CUTHLIDKA1/2/3.scr` et `CUTDABING.scr`. Les soldats de patrouille et les voix
de la séquence subsistent. Le porteur est uniquement sonore : `sounds.bin` le
place à 1,44 m du chef de patrouille et l'associe à `l_b2str1.wav` (2,955 s),
pas à `l_b2str4.wav`.

**INFÉRENCE BORNÉE.** Deux porteurs sont proches des positions initiales des
gardes et deux autres de leurs positions après le téléport à 37 s. Le nom
pluriel du script suggère donc un séquenceur de cues de patrouille, pas une
logique d'objectif ni un simple lecteur mono-son.

**BLOQUÉ.** Les positions, mappings WAV, durées, deux phases de mouvement et la
fin `OnCutsceneDone(1)` sont établis. La liste des porteurs pilotés, l'ordre, les
délais, les boucles et le comportement au skip restent inconnus. Aucun
prototype n'est produit avant une source originale ou une capture audio isolée
prouvant la séquence. Étude :
[`BURMA2_CUTSOUNDSHLIDKA_MISSING`](../experimental/BURMA2_CUTSOUNDSHLIDKA_MISSING/ETUDE.md).

### TUT-ACCESS — Tutorial, accès au lingot

**OFFICIEL.** Le lingot, l'interrupteur, les cibles et le déclencheur du secret
subsistent. `T_EE_Button.scr` utilise le Bedford et rend l'objet disponible ;
`T_EE_Activator1.scr` vérifie l'objet d'inventaire 245. La route historique
passait par le capot ou le toit du Bedford, tandis que la version 1.12 empêche
l'escalade des véhicules.

**CRÉATION MODERNE minimale.** Si une restauration locale de la mécanique
d'accès est impossible, ajouter une seule marche ou courte échelle physique,
réversible, construite avec un modèle commercial existant et placée près du
véhicule. Ne déplacer ni le Bedford, ni le lingot, ni l'interrupteur, ni les
déclencheurs. Un téléporteur invisible est à éviter ; déplacer le lingot est le
dernier recours.

**Critères.** Le secret doit être accessible sans exploit, sans sortir de la
zone ni sauter une étape du tutoriel. Vérifier collisions, caméra, IA,
sauvegarde/reprise et retour exact à l'état commercial après retrait du module.
Le module devra être nommé « adaptation d'accès Tutorial ».

### AL1-WIND — ALPS1_MP_ZONE, septième émetteur de vent

**OFFICIEL.** Le script solo `V_a1_vitr_stromy.scr` recherche `S_poryv` puis
`S_stromy1` à `6`. Toutes les 25 à 43 secondes, il active la rafale, attend trois
secondes, puis active les six sons d'arbres. La zone multijoueur lie ce nom de
script à `zvuk1`, possède `S_stromy1` à `6`, mais pas `S_poryv`. Le fichier audio
`a_a1wind.wav` existe globalement ; seule sa définition d'émetteur manque dans
la zone.

**INFÉRENCE.** Copier le script solo tel quel pourrait appeler `FRM_SetOn` sur
un frame nul. La position originale du septième émetteur n'est pas démontrée.

**Deux prototypes bornés.** Option fidèle : créer un `S_poryv` avec les
paramètres sonores du solo, placé délibérément près de `zvuk1`, puis fournir une
copie locale du script. Option minimale : adapter localement le script pour ne
piloter que les six émetteurs existants, au prix de la rafale d'introduction.
Dans les deux cas, le placement ou la suppression de la rafale est une création
moderne.

**Porte de décision.** Vérifier d'abord la résolution inter-dossiers du script,
les journaux de frame absent et la tolérance aux frames nuls. Comparer ensuite
volume, spatialisation et cadence en partie multijoueur.

### AL1-FORGE24-1011 — gardes 10 et 11 depuis forge24

**OFFICIEL.** `detector_forge24.scr` conserve deux envois commentés du signal 1
vers `ge10` et `ge11`, mais ne déclare aucun de ces handles. Les déclarations
exactes existent dans `detector_forge20.scr`. Les acteurs, leurs bindings, leurs
gestionnaires du signal 1 et les checkpoints `ge10_01..08` / `ge11_01..04`
sont complets. `detector_forge07.scr` est en outre un émetteur commercial actif
vers les deux gardes.

**RECONSTRUCTION.** Insérer dans forge24 les deux déclarations copiées depuis
forge20 est reconstructif : la validité des destinataires ne prouve pas que ce
raccord ait jamais été livré sous une forme exécutable. Le verrou local qui
limite les deux nouveaux envois à une fois par chargement est également une
création moderne de sûreté.

**Variante additive de fin de projet.** Tester une copie de forge24 seulement ;
ne supprimer, remplacer ou modifier aucune activation fidèle conservée dans
forge16/forge20, ni les scripts des deux gardes. Tracer aussi forge07. Promouvoir
uniquement si les signaux tardifs sont sans effet observable, quelle que soit
la source ou l'ordre, y compris après sauvegarde/reprise. Sinon, rejeter
forge24 plutôt que filtrer les activateurs existants ou rendre les récepteurs
artificiellement idempotents. Étude :
`experimental/ALPS1_FORGE24_GUARDS_10_11/ETUDE.md`.

### AL1-GE24-SNIPER — poste de réaction partagé

**OFFICIEL.** Ge16 conserve vers `ge16_sniper` la paire commentée complète
`HUMAN_Move` + `HUMAN_SetSniper`; ge24 ne conserve que le mouvement commenté.
Le point est à environ 1,24 unité de ge16 mais 77 unités de ge24. Aucun point de
déplacement ge24 distinct n'est présent dans la table commerciale.

**Contrat.** La restauration fidèle du paquet principal réserve
`ge16_sniper` à ge16. Ge24 reste release. Une branche additionnelle ge24 n'est
autorisée qu'après découverte d'un autre checkpoint commercial avec nom,
transform et navigation attestés ; elle ne reçoit pas de mode sniper sans
vestige correspondant. Étude :
`experimental/ALPS1_GE24_SHARED_SNIPER_POST/ETUDE.md`.

### AL1-HAKL2 — second half-track `hakl_na`

**OFFICIEL.** La fin de route de ge12 conserve un signal 1 commenté vers
`hakl_na`, mais son script ne traite que le signal 11. Ce handler révèle le
véhicule puis le téléporte entre `h1` et `" h2"`; la table contient exactement
`h1` et `H2`, sans espace initial.

**Reconstruction couplée.** Le seul essai cohérent remplace le vestige par un
signal 11 et corrige simultanément la borne en `H2`. Ces deux changements sont
indissociables et restent inférés : ils ne prouvent ni le rôle du second
véhicule, ni l'ordre historique de substitution. Aucun alias du signal 1 ne
doit être ajouté. Étude :
`experimental/ALPS1_SECOND_HALFTRACK_HAKL2/ETUDE.md`.

### AL1-FORGE40-DEATH — compteur de morts ge01–ge03

**OFFICIEL.** Ge01, ge02 et ge03 déclarent tous `starterforge40` et maintiennent
le triplet de valeurs 21/22/23. Seul ge01 conserve un envoi commenté dans
`OnDeath()`. Le contrôleur compte des signaux 1 anonymes, ouvre après `a>1` une
fenêtre de dix secondes pour le signal 2 de ge40, puis réveille ge41 et assigne
`ge_40akce` à ge40.

**Variante 2-sur-3.** Réactiver l'envoi ge01 et reconstruire le même envoi dans
ge02/ge03, sans déplacer leurs sauvegardes ni sorties et sans modifier le
contrôleur. Cette lecture “deux premiers morts quelconques” est plus cohérente
que le choix arbitraire d'un couple fixe, mais reste à prouver sur les six
ordres et sur l'alarme de ge40. La troisième mort peut rouvrir la fenêtre
commerciale et doit être tracée. Étude :
`experimental/ALPS1_STARTERFORGE40_DEATH_CHAIN/ETUDE.md`.

### CO-BURG-DOORS — portes sonores coop Burgundy

**OFFICIEL.** `Co_Burgundy1` conserve sept scripts
`bur1_SND_door1.scr` à `bur1_SND_door7.scr`. Leurs empreintes sont identiques,
fichier par fichier, aux sept versions solo. Les portes et émetteurs qu'ils
nomment existent dans la carte coop :

| Script | Porte | Émetteur sonore | Porteur solo absent en coop |
| --- | --- | --- | --- |
| `bur1_SND_door1.scr` | `F_dr_door26` | `S_dorcon1` | `dummy_snd6` |
| `bur1_SND_door2.scr` | `F_dr_door00` | `S_dorcon5` | `dummy_snd7` |
| `bur1_SND_door3.scr` | `F_dr_door20` | `S_dorcon2` | `dummy_snd8` |
| `bur1_SND_door4.scr` | `F_dr_door19` | `S_dorcon3` | `dummy_snd9` |
| `bur1_SND_door5.scr` | `F_dr_door18` | `S_dorcon4` | `dummy_snd10` |
| `bur1_SND_door6.scr` | `F_bunk_door_34` | `S_dorcon10` | `dummy_snd11` |
| `bur1_SND_door7.scr` | `F_dr_door17` | `S_dorcon11` | `dummy_snd12` |

`Co_Burgundy3` conserve de la même manière trois copies strictement identiques
aux scripts solo :

| Script | Porte | Émetteur sonore | Porteur solo absent en coop |
| --- | --- | --- | --- |
| `bur3_snd_door1.scr` | `F_door_wood01` | `S_door02` | `snd_vrabec07` |
| `bur3_snd_door2.scr` | `F_door_wood00` | `S_door03` | `snd_vrabec08` |
| `bur3_snd_door3.scr` | `F_door_wood02` | `S_door04` | `snd_vrabec09` |

Chaque script surveille l'état de sa porte : états 1, 2 ou 3, son activé ; état
0, son coupé. Aucun ne lit son propre frame. Les dix scripts sont non liés dans
les registres coop parce que leurs porteurs solo ne sont pas présents.

**INFÉRENCE.** Les porteurs sont des hôtes de script inertes, et non les sources
du son. Leur transform n'influence probablement pas le calcul porte/son, mais
leur parent et leur durée de vie peuvent déterminer quand le script existe. Les
attacher directement à une porte ou à un émetteur déjà utilisé risquerait une
collision de liaison et ne reproduirait pas l'architecture officielle.

**CRÉATION MODERNE minimale.** Recréer dix frames inertes, un par script, avec
les noms solo. Pour chaque porteur, reprendre d'abord le parent et le transform
relatif solo si ce parent existe aussi dans la scène coop. À défaut, n'utiliser
que le parent commun ou la position de la paire porte/son effectivement
correspondante, en consignant ce placement comme adaptation moderne. Ne modifier
ni les scripts, ni les dix portes, ni les dix émetteurs.

**Critères.** Ouvrir, fermer et rouvrir chaque porte plusieurs fois ; couvrir
les états intermédiaires 1/2/3, deux portes simultanées, sauvegarde/reprise et
hôte/client. Couper volontairement un émetteur pendant que la porte est ouverte,
puis fermer et rouvrir la porte : le script doit rester vivant et le son doit
reprendre au cycle suivant. Le retrait des dix porteurs doit rétablir exactement
la carte coop commerciale.

### CO-BURG1-SURVIVAL — objectif 7 « tous doivent survivre »

**OFFICIEL.** Le catalogue solo Burgundy1 déclare huit objectifs : après les
quatre objectifs repris en coop viennent `15566`, `15567`, `15565` et `15564`.
Le slot 7 `15565` correspond à la survie de toute l'unité. Le script solo
`bur1_maquisend.scr` teste `_IsTeamMemberDead()` au contact final, affiche
`57999804`, puis valide l'objectif 7. `Co_Burgundy1/bur1_maquis01.scr` conserve
ce bloc au même endroit, mais entièrement commenté ; sa carte ne déclare que les
quatre premiers objectifs. La coop active aussi une zone de respawn par
`bu1_spawn3.scr`.

**INFÉRENCE.** La règle la plus fidèle rend toute mort d'un membre actif de
l'équipe définitivement disqualifiante pour la tentative ; un respawn ou une
reconnexion ne doit pas effacer cette perte. Une déconnexion vivante ne devrait
pas être assimilée à une mort, et un spectateur ne devrait pas entrer dans la
cohorte. Cette politique est cohérente, mais aucun événement coop officiel de
mort, respawn, connexion ou déconnexion n'est conservé. L'unique occurrence
coop de `_IsTeamMemberDead()` est précisément ce bloc commenté.

**Cas distinct, sans création.** Les objectifs de discrétion 5 et 6 reposent
sur la valeur d'alarme 70, un volume et trois explosifs fixes. Leur contrôleur
coop est identique au solo sauf une ligne : la branche `obj6done` vise 5 au lieu
de 6. Les textes `15566`/`15567` et la correction `SetObjectiveStatus(6, 1)`
sont donc déterministes. Leur restauration ne doit pas attendre l'objectif 7 ni
être présentée comme une nouvelle sémantique réseau.

**Alerte distincte sur l'objectif 8 Carnage.** La source principale recopiait
`bur1_obj_carnage.scr` vers la liaison coop manquante avant le reclassement
`F_sloup03`. Le fichier est officiel, mais il ne s'active que pour les types
3/7 et écrit dans le slot 8. Le bloc `Co_Burgundy1` appartient au style
`cooperative` et ne déclare que quatre objectifs, ou six après ajout déterministe
de `15566`/`15567`. Ni l'activation 3/7 en coop, ni l'usage d'un slot 8 hors
catalogue ne sont prouvés. Cette copie a donc été retirée du lot stable. Elle reste classée comme vestige
officiel incomplet, pas comme « objectif Carnage restauré ». Une éventuelle
reconstruction devra définir un type de partie coopératif et une numérotation
compatibles, ce qui dépasse une simple réactivation.

**Décision.** Ne pas décommenter la survie et ne pas produire de prototype tant
qu'un test hôte/client n'a pas prouvé une détection autoritaire, persistante et
non ambiguë des morts à travers respawn et déconnexion. Étude complète :
`experimental/CO_BURGUNDY1_OBJECTIVE7_SURVIVAL/ETUDE.md` ; comparaison :
`experimental/CO_LIBYE2_OBJECTIVE4_SURVIVAL/ETUDE.md`.

### CO-LIB1-LEGACY — ancien objectif et dialogue AF1_48/49

**OFFICIEL.** `AF1_obj2_succ_sender.scr` conserve la remise des deux prisonniers
et le signal 3 vers l'ancien objectif 2, mais se désactive explicitement. Le
contrôleur coop explique que cet objectif a été annulé et remplacé par
l'élimination de trois officiers. Réactiver le sender sur le slot 2 créerait donc
deux conditions de réussite incompatibles. Une variante additive pourrait
réutiliser `15511` au nouveau slot 7, mais son armement et son échec seraient des
raccords modernes.

Les douze voix du dialogue AF1_48/49 existent et les appels solo sont conservés.
La synchronisation ne l'est pas : seul 49 envoie le premier signal attendu deux
fois, et les signaux finaux 2 ne possèdent aucun récepteur dans le solo comme
dans la coop. Seule la paire voisine 33/34 démontre le protocole complet ; 23/24
est elle-même incomplète. Aucun prototype de dialogue n'est recommandé.

Étude : `experimental/CO_LIBYE1_OBJ2_AND_AF1_48_49/ETUDE.md`.

### CO-BURG2-LEGACY — évasion et survie

**OFFICIEL.** Le détecteur coop `detect_motopryc.scr` envoie toujours 3/4 quand
`ge_dilna` ou `gumak` atteint la sortie, mais les deux acteurs coop ne rejoignent
plus leurs séquences de véhicules. Les chemins `gumak1`, `gumak2`, `citron1`,
`bmv2` et les véhicules `bmw`/`la_citroen` existent encore dans les actifs de
mission ; leur logique d'embarquement et de conduite a été retirée.

**SCÉNARIO REMPLACÉ.** `15573` n'est pas fusionné littéralement dans `15572`,
mais « sécuriser la zone » le rend fonctionnellement caduc. Faire fuir `gumak`
empêcherait l'objectif coop 1, qui attend sa mort via la valeur 16, et pourrait
bloquer le compteur de sécurisation 14. Une variante demanderait de redessiner
ces contrats, l'autorité véhicule et les sièges joueurs : création moderne, pas
deux handlers restaurés. `15577` reste bloqué par la même absence d'historique
de mort que les autres objectifs de survie coop.

Étude : `experimental/CO_BURGUNDY2_ESCAPE_OBJECTIVE/PROPOSITION.md`.

### BURG2-POLISH — reprise de `ge_dilna`, migrée vers stable

**OFFICIEL PAR CONTRAT.** En solo, `ge_motorka` envoie 2 avant la conversation
(`nelesti`) puis 3 après (`lesti`). `ge_dilna` possède deux handlers 2 : le
premier efface l'animation, le second est commenté « animation de polissage »
mais vide. L'animation exacte `%%lestisamopal`, paramètres 500/500/1, est utilisée
dans l'activation du même acteur et n'apparaît nulle part ailleurs.

Le lot stable change le second récepteur 2 en 3 et reprend exactement cette
ligne, sans rejouer l'activité assise. La coop retire les deux signaux et emploie
`%%nudazed1` : c'est une mise en scène distincte, pas un analogue. Ce cas n'est
plus un travail expérimental restant ; sa fiche est conservée pour traçabilité :
`experimental/BURGUNDY2_DILNA_POLISHING/PROPOSITION.md`.

### CZ6-G11-G43 — deux réveils probables de Czech6

G40 envoie officiellement le signal 1 à G11 et G43 lors de son alarme. Les deux
acteurs sont suspendus, possèdent déjà leur comportement de proximité et
d'alarme, mais aucun handler 1. Plusieurs gardes voisins démontrent le patron
`HUMAN_Suspend(false); GoTo end;` ; aucun analogue ne prouve une route ou une
alarme forcée pour ces deux acteurs.

Tester d'abord l'alarme de G40 hors de leur rayon de 50 unités. Si le moteur les
réveille déjà, les signaux sont redondants. Sinon, prototyper uniquement le
réveil du ou des acteurs restés inertes. Étude :
`experimental/CZECH6_G11_G43_SIGNALS/PROPOSITION.md`.

### BREST-Z2-WAKE — destinataire exceptionnel de `Mesh24`

L'ouverture de `Mesh24` envoie 1 à dix défenseurs ; neuf handlers les activent.
`z2_agresor1` est le seul récepteur absent, bien que son label `vybeh` ouvre les
portes, réveille `z2_agresor2` et lance la route. Aucun analogue exact ne prouve
que l'ouverture devait lancer immédiatement cette attaque.

Le prototype désactivé réveille seulement l'acteur et conserve son drapeau local
`suspend=1`, afin que l'alarme officielle continue d'attendre la fin de la valeur
6 avant de rejoindre `vybeh`. Étude et prototype :
`experimental/BREST_Z2_AGRESOR1_SIGNAL1/`.

### AF5-HANDLERS — alertes manquantes d'Africa5

Base et Patch conservent deux émissions sans récepteur. `AF4_44` et `AF4_49`
envoient 5 à `AF4_43` en alarme ; le premier essai acceptable est seulement
`goto ACTIVATE`, puisque le type d'alarme n'est pas porté par le signal. Six
autres acteurs ont un handler 5, mais leurs routes appartiennent à deux groupes
d'alerte et `AF4_43` n'a ni `ALARMDONE` ni destination équivalente à copier.
`AF4_sklad_activator` envoie 1 aux sept acteurs du magasin ; seul le mécanicien
04 ne le traite pas. Six voisins rejoignent `ACTIVATE`, cinq activant aussi le
type d'alarme 2. Essayer d'abord le label seul, puis le type 2 uniquement si le
test démontre qu'il reste sourd hors de son rayon de 20 unités. Les comparaisons
Base/Patch sont faites après normalisation des fins de ligne ; la seule variation
voisine, un bloc sonore retiré de `AF4_sklad01`, n'affecte pas ces handlers.

Étude : `experimental/AFRICA5_MISSING_ACTIVATION_HANDLERS/PROPOSITION.md`.

### COOP-OBJ-OMISSIONS — Brest et Sicily

La comparaison systématique exclut toute copie numérique directe. Brest 15502,
Sicily1 15544 et Sicily2 15552 appartiennent au mode Carnage. Sicily1 15543
est un sas de sortie solo sans contrat réseau ; Sicily2 15558 est une étape de
briefing volontairement raccourcie en coop. Brest 15505 et Sicily2 15555 sont
des objectifs de survie bloqués par les respawns. Enfin, Sicily2 15551 est un
slot solo d'échec critique du pont, déjà absorbé en coop par l'échec des cinq
objectifs et par le positif 15557 « pont intact » ; l'ajouter serait contradictoire.

Étude : `experimental/COOP_OBJECTIVE_OMISSIONS_BREST_SICILY/ETUDE.md`.

### AF5-RUNWAY01 — Africa 5, détecteur de piste 01

**OFFICIEL.** `dummy_runway01` est lié au fichier absent
`AF4_runway01_detector.scr`. En parallèle, `dummy_runway` est lié au script
présent `AF4_runway_detector.scr`, qui surveille déjà `dummy_runway01`, `02` et
`03`, puis met à jour l'objectif 4 et la valeur de jeu 40. Il est activé par
`AF4_23.scr` lorsque Hans coopère.

**INFÉRENCE.** La liaison manquante est très probablement un vestige d'une
ancienne architecture à un script par point, remplacée par le détecteur maître.

**Décision.** Tester séparément un ennemi dans chacun des trois volumes, son
entrée et sa sortie, la sauvegarde/reprise et les ennemis scriptés. Si le point
01 est bien pris en compte, ne pas recréer le fichier. Si lui seul échoue,
corriger le détecteur maître existant est plus fidèle que d'inventer un
comportement distinct. Un shim vide n'est recevable qu'en cas d'erreur de
chargement nuisible.

### AF5-ACTIVATORS — Africa 5, activateurs 14, 20 et 22

**OFFICIEL.** `AF4_14_activator.scr`, `AF4_20_activator.scr` et
`AF4_22_activator.scr` existent dans les couches base et patch, mais les acteurs
ou volumes propriétaires auxquels les lier sont absents des scènes et des
registres. Le premier était placé, d'après son commentaire, à l'unique entrée de
la pièce du commandant. À une unité du joueur, il réveille successivement les
acteurs 14, 15, 19, 16, 17 et 18, avec des délais d'une seconde. Le second était
« sur la porte » et réveille l'acteur 20 à l'utilisation. Le troisième réveille
l'acteur 22 à deux unités.

**OFFICIEL, récepteurs.** Les scripts 14, 16, 17, 18 et 19 acceptent bien le
signal 1 ; le 15 l'accepte également et possède un réveil autonome à 100 unités.
Les acteurs 20 et 22 possèdent chacun un réveil autonome de proximité,
respectivement à 15 et 20 unités, en plus du signal 1. Les scripts survivants
prouvent donc les comportements, mais pas les transforms des trois supports.

**INFÉRENCE.** L'activateur 14 porte une orchestration de groupe qui n'est pas
remplacée de façon évidente. Les activateurs 20 et 22 peuvent en revanche être
des déclencheurs fins abandonnés au profit des rayons autonomes ; leur recréation
aveugle risquerait seulement d'avancer ou de doubler l'activation.

**CRÉATION MODERNE minimale.** Pour le 14, créer un volume invisible dédié à
l'entrée réellement unique de la pièce, lui attribuer le script officiel et ne
changer ni l'ordre ni les délais. Pour le 20, identifier la porte exacte avant
de créer un objet utilisable. Pour le 22, placer un petit volume uniquement si
un défaut de réveil est observable. Chaque transform de frame demeure une
création moderne tant qu'aucune coordonnée officielle n'est retrouvée.

**Porte de décision.** Cartographier les positions des acteurs 14–22, les accès
et les portes ; tracer leur état suspendu, le signal 1 et l'alarme. Tester entrée
discrète et bruyante, porte ouverte/fermée ou détruite, approche par un autre
accès, mort anticipée, repli et sauvegarde/reprise. Prototyper le 14 séparément ;
ne conserver les 20/22 que si le test démontre une différence fonctionnelle
utile par rapport à leurs rayons autonomes.

### AF5-READ19 — lecture interrompable d'AF4_19

**OFFICIEL.** `AF4_19` est lié, le livre `m_AF5_slozky01a7` et l'archive
`m_AF5_slozky01b14` existent. La boucle active inspecte l'archive et change de
posture ; prise, démarrage/arrêt de `HUMAN_ACTIVITY_Read` et dépôt sont
commentés avec la note d'attendre que `Read` fonctionne. Aucun appel actif de
cette API n'existe dans Base/Patch.

**Décision.** Garder la release comme repli. L'essai complet ajoute arrêt de
lecture et dépôt à la fin normale, à `OnAlarm()` et à `OnDeath()`. Une lecture
non interruptible, un livre attaché ou une duplication invalide immédiatement
la variante. Étude : `experimental/AFRICA5_READING_GUARD_19/ETUDE.md`.

### AF5-FAN-PHYS — ventilateur physique monostable

**OFFICIEL.** Les deux ventilateurs sont liés à leurs scripts de rotation. Le
premier conserve un `Whenever _PlayerInRange(3)` commenté qui appelle
`FRM_CreatePhysicalObject(this, 5)` ; le second n'a aucun équivalent.

**Décision.** Ne pas réactiver la chute automatique dans le lot stable. Tester
d'abord hiérarchie, pivot et collision ; préférer une interaction moderne avec
verrou posé avant la conversion. Le jumeau reste strictement release. Étude :
`experimental/AFRICA5_PHYSICAL_FAN/ETUDE.md`.

### AF4-PROX-ASSAULT — alternative aux vagues d'Africa 4

**OFFICIEL.** `dummy_inrange` porte le script dont le rayon de 60 m et les dix
signaux vers `AF3b_16..25` sont commentés. `dummy_organizer` active déjà ces
acteurs dans trois vagues avec le reste de l'assaut. Le script charge la valeur
radio 20 mais la copie conservée force ensuite sa branche vraie.

**Décision.** Deux profils préchargement seulement. La release garde
l'organisateur complet. Le profil proximité attribue les dix soldats au rayon
monostable et filtre uniquement leurs émissions dans une copie de
l'organisateur, qui conserve véhicules, autres soldats et délais. Aucun double
signal ni bascule à chaud. Étude :
`experimental/AFRICA4_PROXIMITY_ASSAULT_VARIANT/ETUDE.md`.

### AF4-ALT-INTRO — panoramique et scène joueur 04

**OFFICIEL.** L'ancien contrôleur conserve le panoramique commenté vers deux
dummies et `Opel02`, puis une scène 2 commentée avec `camera_cut04`. Les deux
dummies et l'Opel existent, mais les caméras 02/03/04 et panoramique manquent.
La release possède déjà son propriétaire de cinématique 1 et sa séquence
Dakota. La réaction scène 2 du joueur 04 est elle aussi commentée.

**CRÉATION MODERNE.** Une entrée exclusive doit créer quatre caméras sous noms
nouveaux, réserver deux identifiants libres et faire du contrôleur central
l'unique propriétaire de la fin. Le timeout ne dépend pas de la présence du
joueur 04 ; chaque sortie neutralise caméra, sous-titres et fade. Étude :
`experimental/AFRICA4_ALT_INTRO_CUTSCENE/ETUDE.md`.

### NOR-TIRPITZ-7 — sept gardes et routes absents

**OFFICIEL, corrigé.** Les acteurs, bindings et chemins de 1, 2, 6, 7, 12, 13
et 16 sont absents de Base/Patch. Leurs sept scripts commerciaux existent
cependant dans la couche Base et sont non liés ; ils ne doivent pas être
réinventés à partir des gardes voisins. `dummy_see1` manque aussi.

**Décision.** Aucun placement sans source attribuée ou choix moderne explicite.
Le sender éventuel reste unique et conserve son tirage 1–18 : réactiver les sept
issues ne change ainsi pas la probabilité 1/18 de chacun des neuf gardes
existants. Étude :
`experimental/NORWAY_MISSING_TIRPITZ_GUARDS_1_2_6_7_12_13_16/ETUDE.md`.

### AF1-04-G067 — prolongement de ronde

**OFFICIEL.** AF1_04 et sa ronde g01–g05 sont complets. Les mouvements g06/g07
sont commentés et les deux checkpoints sont absents de Base/Patch.

**Décision.** Conserver un profil g01–g05 et un profil long exclusifs. Le profil
long exige deux transforms attribués, des liens g05→g06→g07→g01 validés et ne
change aucun handler d'alarme, signal ou mort. Étude :
`experimental/AF1_04_ROUTE_G06_G07/ETUDE.md`.

### AF1-20-PATROL — patrouille après alarme

**OFFICIEL.** La sortie d'alarme joue aujourd'hui deux rotations. La longue
boucle commentée vise `_01..08` ; `_02..08` existent, `_01` manque et la
sous-routine `LOOKAROUND` appelée quatre fois n'existe pas dans le script.

**Décision.** Garder la rotation release. Un profil long doit fournir séparément
un point 01 sourcé/moderne et une pause moderne annoncée, sans toucher à la
conversation initiale ni aux alarmes. Étude :
`experimental/AF1_20_LONG_POST_ALARM_PATROL/ETUDE.md`.

### AF3-SLEEP-2426 — sommeil séparé de l'assise stable

**OFFICIEL, corrigé.** `some_bed` d'AF3a_24 est absent, mais
`m_postel_a7` d'AF3a_26 est bien présent dans `scene2.bin`. Aucun appel actif de
`HUMAN_ACTIVITY_Sleep` n'est attesté. AF3a_24 possède désormais une assise
stable complète qui reste la baseline.

**Décision.** Le sommeil d'AF3a_24 exige un lit et un placement modernes dans
un profil exclusif ; celui d'AF3a_26 teste d'abord le lit commercial. Les
activations ajoutent un réveil minimal, tandis que les alarmes commerciales
restent autoritaires. Étude :
`experimental/AFRICA3_SLEEPING_GUARDS_24_26/ETUDE.md`.

### AF3-G13-SIT — siège aléatoire du garde 13

**OFFICIEL.** La branche `rnd == 1` conserve mouvement, résolution du siège et
`HUMAN_ACTIVITY_Sit` commentés, puis l'animation assise/chaleur active.
Checkpoint et dummy 13 sont absents. Les gardes 14/15 démontrent le patron
Move→Sit→activité→reprise, mais pas le transform de 13.

**Décision.** Créer checkpoint et siège sous noms modernes, sans changer la
ronde ni le tirage. Les transforms 14/15 sont des références d'alignement, pas
des positions à copier. Étude :
`experimental/AFRICA3_GUARD13_SIT_BRANCH/ETUDE.md`.

### AF1-G12-VOICE — voix du garde de toit

**OFFICIEL.** `PlaySound(9,53)` reste commenté au signal 20 et
`PlaySound(9,50)` après l'embarquement MG42 en alarme. Aucun autre appel exact
n'est actif. L'inventaire audio ne fournit pas de correspondance directe entre
ces couples et une ressource nommée.

**Décision.** Auditionner 53 et 50 séparément, vérifier langue, locuteur,
spatialisation, durée et absence de régression des deux chemins. Laisser les
lignes commentées sans identification positive. Étude :
`experimental/AFRICA1_ROOF_GUARD12_VOICE/ETUDE.md`.

### AF2-JUNKERS-FX — Africa 2, moteur du Junkers en feu

**OFFICIEL.** Le registre lie le fichier absent `AF2_particle_junkers.scr` à
`HoriciJunkers.engine_l00`. Or `AF2_actprelet.scr`, présent en base et dans le
patch, cible exactement ce même frame, crée `FRM_CreateIndexedParticle(16, ...)`
au début de la séquence aérienne et termine l'effet après environ 19 secondes.
`AF2_hidejunkers.scr` cible aussi le Junkers et tente de terminer une particule
quand l'appareil est masqué.

**INFÉRENCE.** Le fichier manquant est vraisemblablement un ancien producteur
de fumée devenu redondant lorsque la gestion de la particule 16 a été intégrée à
`AF2_actprelet.scr`. Le recréer pourrait doubler l'effet et laisser un index
orphelin.

**Décision.** Ne rien créer par défaut. Tracer une exécution de la séquence : une
seule particule doit apparaître sur le moteur et disparaître avec l'avion. Si ce
comportement est correct, classer la liaison comme obsolète. En cas d'échec,
réparer la durée de vie dans le script actif plutôt que cloner un fichier dont
le contenu est inconnu.

### AF1-OBJ-PLANE02 — AFRICA1_OBJ, second avion

**OFFICIEL.** `AF1_mp_letadlo02.scr` et l'ancien compteur portant sur six avions
subsistent. La carte objectif ne contient toutefois ni l'acteur `la_macchi02`,
ni la charge `w_explosive14`, ni le frame `dummy_let02`. La version active
emploie uniquement `la_macchi01` et valide directement l'objectif 2.

**INFÉRENCE.** Le deuxième avion appartenait probablement à une variante
antérieure de l'objectif, mais les fichiers conservés n'en donnent ni la
position, ni l'inventaire exact, ni la condition d'achèvement complète.

**CRÉATION MODERNE minimale.** Implanter l'acteur, sa charge et un emplacement
de détection ; raccorder le script survivant au compteur seulement si le passage
de un à plusieurs avions est cohérent avec l'objectif affiché. Le nombre final
d'avions ne doit pas être déduit automatiquement du seul ancien seuil de six.

**Critères.** Tester pose et retrait de charge, destruction anticipée, ordre des
avions, objectif 2, sauvegarde/reprise et multijoueur. Présenter le résultat
comme variante expérimentale de l'objectif, jamais comme liaison restaurée.

### CZ3-CARNAGE-OBJ4 — slot Carnage 4 de Czech3

**OFFICIEL.** Les catalogues Base, Patch et Sabre déclarent tous le n°4 avec le
texte 6063 « Kill the enemy », sémantiquement identique au n°1 texte 6201. En
types 3/7, `setobjectives.scr` remplace déjà le compteur par
`Mrtvoler_carn.scr` ; arrivé à zéro, celui-ci envoie le signal 2 au contrôleur
Carnage, qui réussit explicitement l'objectif 1. Aucun script Czech3 n'écrit le
statut 4 et les variantes CMP ne restituent pas ce corps.

**Décision.** Le n°4 est un slot résiduel probable, pas une seconde victoire à
ajouter. Seule une copie laboratoire peut tester la substitution exclusive du
n°1 par le n°4, sous garde 3/7 et avec le compteur commercial inchangé. Si les
deux textes restent visibles, la variante est refusée. Étude :
`experimental/CZECH3_CARNAGE_OBJECTIVE4/ETUDE.md`.

### LI3-OBJ4-SURVIVAL et LI3-OBJ6-DUP — Libye3

**OFFICIEL.** Le n°4, texte 15534, signifie « All members of the unit must
survive ». Le contrôleur Libye3 ne l'écrit pas, mais son signal 3 correspond
exactement au rassemblement final avec véhicule. Libye1 et Libye2 réussissent
leur objectif homologue à ce moment, après `_IsTeamMemberDead()` et hors type
2. Un fragment désactivé reprend uniquement ce contrat avant la réussite du
n°3 ; il n'invente ni échec, ni texte, ni compteur.

**RÉSIDU.** Les n°5 et 6 emploient tous deux 15533 « Eliminate all enemies ».
Le n°5 est déjà activé en 3/7 et validé par le compteur Carnage ; le n°6 n'a
aucune condition distincte. La coop commerciale et les variantes CMP réservent
leurs slots 4/6 à d'autres objectifs multijoueur et ne sont pas des sources du
solo. Aucun prototype du n°6 n'est justifiable. Étude :
`experimental/LIBYE3_OBJECTIVES4_6/ETUDE.md`.

### NOR-GARY — Norway, personnage Gary

**OFFICIEL.** `Scripts/Norway/R_nor_Gary.scr` subsiste, mais son contenu se
limite à `HUMAN_SETMODE_Crouch()` et `HUMAN_SETAIMODE_Zombie()`. Aucun acteur ni
frame nommé Gary n'a été retrouvé dans `Missions/Norway/scene2.bin`,
`actors.bin` ou le registre commercial effectif. Le script est non lié.

**INFÉRENCE.** Les deux appels indiquent tout au plus un humain accroupi soumis
au mode IA « Zombie ». Ils ne démontrent ni son camp, ni son apparence, ni son
emplacement, ni son objectif, ni ses interactions, ni même que Gary devait
rester dans la version publiée.

**CRÉATION MODERNE minimale.** Il faudrait créer ou choisir un personnage,
déterminer sa position, son équipement, son état initial, son rôle narratif ou
tactique et ses conditions de retrait. Attacher le script à un acteur existant
au seul motif qu'il est accroupi serait arbitraire et pourrait altérer son IA.

**Verdict.** Suspendre toute implantation jusqu'à découverte d'au moins une
source officielle sur la position ou la fonction de Gary. Un éventuel prototype
devrait être présenté comme interprétation moderne isolée, jamais comme acteur
restauré.

**Faux positifs Norway exclus.** `R_Nor_OBJ_1.scr` est l'ancienne variante qui
ne surveille que `d_magmineicon_2`. La variante active
`R_Nor_OBJ_1_a.scr` surveille les deux mines et valide l'objectif après les deux
poses : l'ancien script ne doit pas être lié en parallèle. De même,
`S_open_door.scr` reproduit le moniteur de la porte `m_dvo02` et du son
`S_door1` déjà assuré par le script actif `m_dvo02_s.scr`. Ces deux fichiers
restent des variantes obsolètes, pas des créations à entreprendre.

## Ordre de travail recommandé

1. **Éliminer les faux positifs** : LI3-OBJ6-DUP, AF5-RUNWAY01,
   AF2-JUNKERS-FX, AF3-SYNC-1415 et BU1-BRIDGE par traçage en jeu.
2. **Prototypes chirurgicaux** : LI3-OBJ4-SURVIVAL, CO-BURG-DOORS, AL1-WIND,
   puis TUT-ACCESS ; CZ3-CARNAGE-OBJ4 reste un test de substitution exclusif et
   BU2-CUTSOUND a son inventaire audio mais attend encore l'ordre et les
   timecodes de la séquence.
3. **Implantations bornées** : AF5-ACTIVATORS (14 d'abord), puis N2-RETURN et
   AF1-OBJ-PLANE02 après identification de leurs événements et emplacements.
4. **Carte verticale** : MAP-CASTLE2, limitée à un enchaînement complet des
   objectifs conservés.
5. **Animation d'aéronef** : Ju 52 décoratif, puis banc comparatif La-5/Aichi.
6. **R&D longue** : ZK-383, lance-flammes, autres aéronefs pilotables. Garota,
   CASTLE1, CZ4-PLATOON, AF3-SYNC-2223 et NOR-GARY restent suspendus sans
   nouvelle preuve.
7. **Tout à la fin** : AL1-FORGE24-1011, seulement après stabilisation des
   activations forge16/forge20 et traçage de l'idempotence avec forge07.

## Convention pour les futurs prototypes

Toute création issue de ce registre devra rester sous
`experimental/<ID>/` et inclure une note locale indiquant :

- les fichiers officiels réutilisés, avec archive et chemin ;
- chaque hypothèse et la preuve qui la motive ;
- chaque création moderne (modèle, position, nombre, timing, valeur ou script) ;
- le scénario de test, le résultat et les limites connues ;
- la procédure de retrait garantissant le retour aux données commerciales.

Une proposition ne devient intégrable qu'après validation séparée. Aucun
prototype de ce registre ne doit écrire directement dans l'installation du jeu
ni être incorporé implicitement à l'installateur principal.

## Sources internes principales

- `output/audit/full-game-audit.json`
- `output/audit/script-bindings.json`
- `output/audit/asset-presence.json`
- `output/audit/map-inventory.json`
- `docs/ARMES.md`
- `docs/PROTOTYPES.md`
- `docs/EASTER_EGGS_AUDIT.md`
- `docs/ETAT_DES_LIEUX_ET_ROADMAP.md`
- scripts et fichiers de mission extraits sous `.analysis/`
