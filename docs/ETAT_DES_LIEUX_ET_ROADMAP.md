# État des lieux et feuille de route

Date : 15 septembre 2026.

## Ce que nous nous sommes fixé

Le projet doit produire un ensemble installable pour Hidden & Dangerous 2: Sabre Squadron 1.12 qui :

- restaure la visibilité des serveurs Internet ;
- intègre des campagnes, cartes et missions communautaires sélectionnées ;
- ouvre l'exploration sans avertissement ni échec de sortie de zone ;
- recherche et réactive missions, cartes, objectifs, actions et routes officielles désactivées ;
- active les vestiges expérimentaux quand les données sont suffisamment complètes ;
- étudie la finition des prototypes incomplets au lieu de les écarter ;
- recherche l'histoire de Londres, Gary Bristol, Dunkerque, Allemagne, pont/train, entrepôt et environnements urbains ;
- classe correctement les armes et véhicules retirés, présents mais non jouables, ou seulement hypothétiques ;
- fournit un guide PDF joueur des easter eggs et coins secrets ;
- fournit un second PDF expliquant les découvertes ;
- installe le tout par un exécutable réversible.

## Acquis au jalon 0.7.5

### Réseau et communauté

- serveur maître communautaire RpR identifié et joignable ;
- redirection des trois noms GameSpy automatisée ;
- DirectPlay contrôlé ;
- CMP 2.6.5 figée par commit, taille et SHA-256 ;
- 156 entrées de cartes et missions communautaires intégrables.

### Exploration

- 82 arbres officiels audités ;
- avertissement 0x40 et échec 0x20 neutralisés sans toucher aux collisions physiques ;
- 104 405 surfaces officielles prises en charge dans 70 arbres ;
- 561 objets physiques dont le nom contient `border` neutralisés dans 44 arbres ; 75 cartes contiennent au moins une des deux familles de limites ;
- les 207 objets nommés `wall`, les 1 128 clôtures `zabr*` ou `barier*` et les zones sans `border` restent inchangés ;
- même traitement appliqué aux cartes CMP ;
- dans Arctic 1, les deux retours d'Albert ne réactivent plus le détecteur qui affichait trois reproches avant de faire échouer la mission ; le choix marais/route et les cinématiques restaurées restent inchangés.

### Affichage et performances

- la résolution appliquée est toujours la résolution physique active de l'écran principal ; elle n'est plus abaissée à 1080p ou 1440p selon le profil matériel et n'est plus plafonnée artificiellement à 4K ;
- le profil de qualité reste indépendant et additionne des indices CPU, mémoire vive, mémoire vidéo et famille de GPU ;
- le contrôle de câblage refuse désormais une régression qui réintroduirait un plafond 4K, oublierait une des trois familles de performances ou appliquerait la résolution avant le correctif écran large.

### Objectifs et chemins

- Arctic 3 corrigé avec la nuance qu'une route peut parfois contourner l'anomalie ;
- Arctic 2 écrit de nouveau le succès des cinq charges dans l'état 6 de l'objectif optionnel, au lieu d'écraser l'état 5 de l'alarme et de la discrétion ;
- Africa 2 relié au bon signal de destruction du char ;
- Normandy 2 recompte correctement les cinq survivants à la validation finale ;
- Africa 1 réactive l'objectif 8 « Tuez l'ennemi » uniquement dans les types Carnage 3 et 7, à partir du contrôleur officiel entièrement commenté ;
- Libye 3 valide enfin l'objectif officiel où toute l'unité doit survivre ;
- Africa 6 rétablit le bloc officiel de validation de la survie de l'équipe, présent mais commenté ;
- Africa 5 exige de nouveau la destruction des cinq avions de l'objectif 8 : la seconde initialisation du quatrième état est corrigée vers le cinquième, déjà utilisé par le dernier avion ;
- Burgundy 1 solo révèle de nouveau le second sabotage, le dépôt de carburant, à partir du bloc officiel commenté et de son script complet ;
- Libye 2 coopératif retrouve dans sa liste multijoueur l'objectif optionnel 15523 de destruction des huit véhicules ennemis, dont le détecteur et la validation étaient restés entièrement actifs ;
- Brest coopératif retrouve l'objectif 15504 des deux générateurs, son acteur libre étant relié à son script identique au solo dans les deux registres ;
- Burgundy 1 coopératif retrouve les objectifs 15566 et 15567 de discrétion ; la branche des trois explosifs valide de nouveau le numéro 6 comme dans le script solo ;
- Burgundy 3 coopératif réactive l'objectif principal des prisonniers après ses trois sous-objectifs, corrige le cas bloqué des survivants répartis entre deux paires et empêche l'objectif optionnel « tous sauvés » après une perte ;
- Czech 2 affiche désormais l'objectif officiel « Quittez la zone » après la capture de Freiberg et le valide lorsque tous les joueurs et le prisonnier atteignent le déclencheur endgame déjà présent ;
- Africa 5 objectif 2 est identifié comme reconstruction minimale : activation conservée mais validation absente ;
- deux guidages Arctic 1 restaurés ;
- le bouton utilisable de la radio Arctic 1 retrouve son état visible au départ et son masquage à la destruction, conformément à la radio commerciale sœur d'Arctic 3 ;
- les autres vestiges d'Arctic 1 sans propriétaire, remplacés ou dépendants d'animations non validées sont confiés à la reconstruction expérimentale.
- choix visuel des deux accès souterrains de Lighthouse en France restauré ;
- seconde route de Brest restaurée en solo et en coopération en reliant son second détecteur à son script original complet ;
- conseil contextuel 15600 de Brest coopératif reconnecté à son acteur, à la même position que sa version solo active ;
- second poste radio destructible d'Arctic 2 reconnecté à son script et à son modèle complets ;
- première radio d'Arctic 2 classée séparément : son second émetteur est explicitement noté à compléter et reste à reconstruire après identification d'un cadre sonore fiable ;
- l'interrupteur d'Arctic 2 pilote de nouveau la lumière dynamique `1sut-vratnice`, toujours présente dans la scène corrigée, en parallèle des deux modèles d'ampoule et de la lightmap déjà actifs ;
- les six alarmes de Sicily 1 retrouvent l'enfoncement visuel de leur bouton en solo et en coopération ; les douze scripts, leurs acteurs, leurs liaisons et le nœud `Cylinder01` du modèle officiel sont tous présents ;
- journal officiel de Burgundy 1 coopératif restauré depuis sa copie commerciale présente dans le dossier solo ; le contrôleur Carnage orphelin est désormais classé vestige incomplet et n'est pas installé ;
- barrière de Burgundy 1 refermée après les vingt secondes prévues, en remplaçant le signal inexistant 0 par sa commande officielle 2 dans les variantes solo et coopérative ; son garde reprend aussi le trajet `04_01` conservé vers la conversation qui libère le camion ;
- cinématique finale de Burgundy 1 complétée par la réplique enregistrée 57990065, dont la commande, la voix et la synchronisation labiale subsistent dans les archives commerciales ;
- porte 35 de Czech 4 Zone reconnectée à son script officiel complet, identique aux huit portes déjà actives et toujours présente dans la géométrie ;
- seconde zone d'approche du civil 03 d'Alps 1 reconnectée à son script et au signal 8 déjà géré par le civil ;
- dans Alps 1, les détecteurs de forge 16, 20 et 30 réactivent de nouveau les gardes `ge_10`, `ge_11` et `ge_43` par leurs quatre envois officiels commentés ; leurs signaux, acteurs, liaisons et quinze points sont complets ; le détecteur 24 dépourvu de déclarations reste confié à la reconstruction ; la variante Carnage du maître-chien reprend aussi le trajet distinct `ge08_02` et arrête le chien par son signal 2, tandis que le mode normal garde `ge08_01` ; les gardes 16, 17 et 23 rejoignent en plus leur poste de précision ou leur MG42 grâce à leurs instructions officielles commentées et à leurs points toujours présents, tandis que la patrouille 18 retrouve son terminus `ge18_01` et sa boucle symétrique complète ; le garde 34 exécute de nouveau son tir scénarisé de cinq secondes sur l'acteur `ge34attack` encore présent ; l'informateur 35 quitte à nouveau sa suspension au même signal que les sept autres soldats de la forge, ce qui rend son écoute des tirs et explosions effective ; après deux événements d'alerte, les renforts 38/39 arrivent selon les délais existants et le signal 18 rejoint de nouveau sa conséquence officielle sur l'objectif des documents ;
- détecteur d’alarme de proximité d’Alps 2 reconnecté à la chaîne officielle `shotalarm` ;
- alerte vocale `PlaySound(9,49)` du garde `AL2_36` d'Alps 2 réactivée exactement à l'endroit où la version commerciale la jouait avant que la 1.12 ne la commente ; le même appel reste actif dans Alps 1 ;
- dans Africa 1, le mécanicien `AF1_16` rejoint et regarde de nouveau son avion avant ses animations de réparation, tandis que `AF1_19` reprend après une fausse alerte sa ronde complète sur quatre checkpoints encore présents ;
- zone de découverte du véhicule d'Africa 3 reconnectée à `AF3a_obj2.scr`, sans altérer le compteur central géré par le mécanicien ;
- le mécanicien `AF4_sklad04` d'Africa 5 reçoit désormais le même signal d'ouverture que les six autres hommes du magasin et rejoint son label `ACTIVATE` déjà complet ;
- le garde `AF4_sklad06` retrouve sa branche complète pour l’alarme extérieure 256 : comme quatre voisins du même magasin, il arrête son activité, passe en course et rejoint la source avec `HUMAN_MoveToAlarm()` ; sa réaction intérieure au signal 2 reste prioritaire et inchangée ;
- le garde d’entrée `AF4_03` d’Africa 5 reprend la cigarette officielle après son geste autorisant le passage ; son arrêt à l’alarme, son trajet et les quatre checkpoints restent inchangés ;
- dans Africa 5, Schumann arrête son activité, rejoint `AF4_blesz_end` et s’accroupit pendant la cinématique 20 de l’embuscade ; le détecteur, le tireur, la liaison de Schumann et le point de mise en scène sont tous actifs, et son script se termine après la séquence comme prévu ;
- le garde caché `AF4_43` d'Africa 5 reçoit de nouveau les événements d'alarme pendant sa suspension, `AF4_10` retrouve sa texture féminine `e_f0w1` toujours présente, et `AF4_sklad01` récupère le bloc vocal joué une fois que le patch 1.12 avait supprimé ;
- dans Burgundy 2, le polisseur `ge_dilna` arrête toujours son animation au signal 2 avant le dialogue, puis reçoit désormais le signal 3 officiel de reprise et relance exactement `%%lestisamopal` sans modifier sa pose ni ses réactions de combat ;
- dans Burgundy 2 solo et coopératif, `ge_cesticka` reprend désormais son cinquième segment après une interruption, et la boucle de marmonnement de `gumak` rejoue sa parole temporisée officielle au lieu de tourner à vide ;
- dans Burgundy 3 solo, le garde `BUR03_32` reprend sa ronde entre `32_01` et `32_02` ; les deux points sont présents dans la carte et la version coopérative du même script conserve ces déplacements actifs, tandis que sa réaction de combat reste inchangée ;
- dans Burgundy 3 solo, le premier prisonnier SAS retrouve sa phrase d'ouverture 59990052 ; la version coopérative conserve déjà la séquence complète, et la voix ainsi que le lipsync sont présents ;
- dans Africa 1, les soldats `AF1_24` et `AF1_25` sortent de nouveau leurs cartes puis jouent en boucle dans le hangar ; leurs acteurs et liaisons existent, et la même activité 1/2 est utilisée activement dans Czech 3 et Castle 2 ; les gestionnaires d’alarme arrêtent déjà leur animation ;
- dans Africa 3, la ronde `AF3a_08` exécute de nouveau les deux inspections d'arme encore placées dans sa branche `PATH_CWEAPON` ; la commande est attestée active dans Africa 2 et Arctic 1, et les temps d'attente ainsi que la sortie de la pose assise sont conservés ;
- dans Africa 3, le mécanicien `AF3a_21` réutilise sa branche complète de blessure : il interrompt sa réparation, court à son point de repli, se couche sous l’Opel puis ressort par le trajet déjà actif lorsque le joueur vient lui parler ;
- dans Africa 3, le garde `AF3a_24` retrouve l’activité assise sur `dummy_24_sit` au démarrage et après une alarme, avec retour par `AF3a_24_sit` ; le lit et l’activité de sommeil absents ne sont pas inventés ;
- dans Africa 3, le garde `AF3a_03` exécute de nouveau `HUMAN_ACTIVITY_Hot()` pendant sa pause assise et fumante ; la combinaison est déjà active pour le garde 16 de la même mission et aucune route ni durée n’est modifiée ;
- dans Africa 3, le distributeur d'alarme global avertit de nouveau `AF3a_22` et `AF3a_23` par le signal 20 ; les deux acteurs, leurs liaisons et leurs gestionnaires complets sont présents, et aucun autre émetteur ne leur envoie déjà ce signal ;
- dans la cinématique d’arrivée en Jeep d’Africa 3, les deux fumées sont déjà créées et détruites ; le paquet réactive le son `cut_para` aux mêmes instants, comme le fait la variante Opel, après vérification de son ancre sonore et des quatre cadres de particules ;
- dans Libye 1 coopératif, `AF1_33`, `AF1_50`, `AF1_52` et `AF1_53` relancent leur animation de cigarette dans les branches déjà prévues et l'arrêtent à l'alarme ; les mêmes appels sont actifs dans la version solo et dans Libye 3 ;
- dans Libye 1 coopératif, les conversations 08–12 et 33–34 retrouvent leurs vingt répliques officielles, avec leurs synchronisations, acteurs, sons, animations labiales et retours complets ;
- dans Libye 3 coopératif, la capture du poste échange de nouveau les drapeaux allemand et britannique et le garde de toit 7 reprend sa MG `Kulas2`, comme le garde parallèle sur `Kulas3` ;
- dans Libye 2, la conversation des soldats 16–17 retrouve ses deux réponses finales enregistrées 53990012 et 53990013 en solo et en coopération ; les acteurs atteignent déjà le lieu du combat, et les sons ainsi que les animations labiales sont présents ;
- dans Libye 3, le soldat `Li3_German_3` emprunte de nouveau les cinq points G3_02 à G3_06 de sa route détaillée avant de remplacer le servant de la mitrailleuse ; tous les checkpoints, le signal de relève et la MG sont présents ;
- dans Brest, 33 scripts reliés retrouvent 49 animations d'observation de sentinelles et 10 réactions à la découverte d'un cadavre en solo et en coopération ; les cibles, activités et déclencheurs commerciaux sont tous présents ;
- dans Arctic 4, `Walking_Guard_3` retrouve l'ordre `HUMAN_SETMODE_Walk()` explicitement retiré pour un test avec son chien ; le propriétaire, le signal de mort et les deux liaisons du registre sont conservés ;
- dans Arctic 4, le repère `k_vykricnik_` des documents redevient visible lorsque le joueur entre dans son rayon de 10 mètres et se masque après la collecte ; sa liaison, son cadre de scène, le signal 24 et le contrôleur d’objectif sont conservés ; le marqueur distinct de l’officier reste désactivé conformément à la note explicite des développeurs ;
- dans Arctic 4, le danger de chute de glace `dummy_bouchni` retrouve son explosion exacte avant l'activation du fragment `ulomek_4` ; son déclencheur à douze mètres et toutes ses valeurs commerciales sont conservés ;
- dans Czech 5, les acteurs `3crib144` et `light_lightnings` retrouvent les deux scripts officiels de météo et d'éclairs dont le corps complet avait été commenté ; l'unique gabarit invalide reste désactivé ;
- dans Norway, les trois éléments visuels de l'Enigma changent désormais ensemble de lightmap : `Mesh46`, déclaré et présent dans les deux scènes officielles, retrouve son unique appel commenté ;
- deux identifiants de voix de la conversation 05 d'Africa 3 corrigés d'après les commentaires officiels (`07991601` et `07991604`) ; les conversations 03/04/05 restent expérimentales faute de déclencheur démontré ;
- Red 26 de Normandy 2 reçoit de nouveau le signal 7 envoyé à l'ensemble de sa vague, au lieu d'attendre le signal 6 d'un autre groupe ;
- les quinze soldats Blue présents de Normandy 2 restent désormais dans leur boucle de riposte contre Ally 5, au lieu de revenir par erreur vers celle d'Ally 1 ;
- la première zone d'approche Norway cible de nouveau `detect_player2`, ce qui rétablit l'exclusion mutuelle exacte conservée dans les deux scripts ;
- le contrôleur commercial du Tirpitz, débranché par le Patch 1.12, retrouve sa liaison au cadre `m_tirpitz low.t_kotva41` et rend les quatre animations aléatoires à huit gardes dont les récepteurs sont complets ; le garde 3 et les neuf soldats supprimés restent au laboratoire ;
- le garde 3 du chalutier adresse de nouveau le signal 3 à `small3_timer` lorsqu'il est blessé, ce qui interrompt l'attente de fausse alerte au lieu de le rappeler ensuite à sa ronde ;
- le détecteur 4 de Czech 4 conserve le comportement distinct de `Plazzars_01`, mais emploie désormais le signal 3 déjà géré par `Plazzars_02` et `03`, ce qui réveille les trois soldats sur cette seconde approche ;
- dans Czech 4, le second combattant `CZ4_Chatter_02` est désormais recherché sous son propre nom par le contrôleur : il rejoint ainsi le compteur de l'objectif principal qui pointait auparavant deux fois sur `CZ4_Chatter_01` ;
- la commande de la porte `dobytcak146` de Czech 2 avertit désormais une fois chacun les soldats 24 et 25 ; le script déclarait les deux acteurs mais envoyait deux fois le signal 3 au premier ;
- à la mort du chef du groupe `Wood_1` dans Arctic 3, les deux membres `Wood_2` et `Wood_3` reçoivent désormais chacun leur signal 5 et rejoignent leur position défensive ;
- lorsque le camion `Opel_01` d'Arctic 3 est touché, son script officiel envoie de nouveau le signal 4 aux six occupants, qui possèdent chacun leur réaction complète de débarquement et de combat ;
- dans Czech 5, l’Opel `La_OpelE_1` de la cinématique retrouve son petit effet officiel de destruction : le véhicule et le script `Opel_1_OnDeath.scr` subsistent, et la cinématique remet explicitement ce camion en jeu après son passage ;
- l'audit complet de Czech 5 confirme aussi ses 66 liaisons, ses trois objectifs et ses 125 checkpoints actifs : aucune autre action stable n'y manque ; le gabarit zombie sans acteur et quatre postures redondantes ne sont pas réactivés ;
- l'audit complet de Czech 6 confirme ses 94 liaisons, ses six objectifs et ses 135 checkpoints actifs ; la route Base de l'ISU-152, le verrou historique du sabotage radio et deux réactions d'alerte sans récepteur sont réservés à des variantes additives qui conservent les comportements du Patch ;
- l'audit complet de Normandy 1 confirme ses 241 liaisons, ses huit objectifs, ses 144 checkpoints actifs et ses 204 cibles principales de scène ; la cinématique commerciale des deux accès souterrains est reconnectée, tandis que les anciens détecteurs sans position sont réservés à la reconstruction additive ;
- dans Czech 3, le contrôleur des deux zones `detector_blockerz` et `detector_blockerz1` active désormais chaque détecteur une fois, au lieu d’activer deux fois le premier ; le camion normal retrouve les quatre points de sa manœuvre complète déjà active en Carnage, la mort du mécanicien coupe de nouveau son dialogue de proximité et le radio-opérateur reprend son poste de précision attesté par `co_czech3` ;
- Africa 4 respecte de nouveau le résultat sauvegardé de l'opérateur radio d'Africa 3 : les conducteurs, fantassins, chars, réserves, délais et textes de journal possèdent encore leurs variantes avertie et non avertie, mais une affectation de test forçait toujours la première ;
- les dix alertes croisées des gardes 07, 08, 09, 10 et 12 d'Africa 1 emploient de nouveau le signal 20 déjà géré par leurs quatre destinataires, au lieu du signal 10 ignoré ;
- dans Africa 1, la porte `HL_dvh_x01` retrouve son contrôleur commercial de lightmap au clic, et le garde 06 monte de nouveau sur la MG42 après avoir rejoint son point `AF1_06_kulomet` ;
- trois gardes d'Africa 2 rejoignent de nouveau la réaction coordonnée de leur groupe : `AF2_02` reçoit son signal d'alerte 20, `AF2_05` son signal d'alerte 5 et `AF2_03` retrouve sa liaison de registre ainsi que ses quatre envois officiels — activation lointaine, détection rapprochée, alerte directe et alarme générale — et les trois déclarations correspondantes ; ses signaux 1, 5 et 20, sa ronde et ses points sont déjà complets ; le détecteur rapproché coupé des gardes 14–15 est également rétabli avec son arrêt en cas d'alarme, le signal 10 d'`AF2_14` et les trois déplacements d'`AF2_15` ; le garde 14 récupère son filtre 512 cohérent avec tout le groupe et le premier renfort sa mise à couvert symétrique aux trois autres ;
- CASTLE2 objectif 5 identifié comme action complète commentée.

### Cartes et prototypes

- Normandy3 Zone activable ;
- Africa5 Prototype complété à partir de ressources officielles identiques ;
- ENGLAND, CASTLE1 et CASTLE2 classés comme branches internes, pas faussement annoncés comme cartes complètes ;
- ALPS3_OBJ : version Sabre complète déjà active, plus un prototype Base distinct à trois véhicules qui exige une reconstruction additive ; ARDENS1_OBJ conserve une composition Base inachevée avec un Sherman et un Tiger supplémentaires, à préserver seulement sous forme d'une variante additive distincte de la version Sabre complète.

### Easter eggs et secrets

- six easter eggs publics vérifiés ;
- septième easter egg Africa 4 confirmé dans les fichiers ;
- neutralisations explicites d'Africa 1 et Africa 4 par le patch 1.12 inversées ;
- positions des trois clés Africa 4 relevées ;
- positions exactes des trois crânes Burma 1 décodées dans la scène Patch 1.12 et protégées par un audit de leurs quatre liaisons et de leur compteur ;
- 36 ancres spatiales de six autres secrets décodées en coordonnées mondiales, avec distinction des transformations locales et mondiales ;
- double liaison officielle du déclencheur Africa 4 identifiée sur la MG42 couchée et sur le volume `dummy_ee_activator` ; les deux zones doivent être départagées en jeu avant de figer le guide ;
- carte schématique originale préparée pour le guide joueur ;
- route Tutorial identifiée, mais l'escalade du camion reste bloquée en 1.12.

### Contenu coupé

- campagne Angleterre/Londres distinguée de l'arène London_mp/Poland ;
- intrigue Gary Bristol / Scarred Man, Dunkerque et M. Murrau recoupée avec la presse d'époque ;
- modèles M323, Aichi, La-5, Fa 223, Fw 200, Li-2, DFS 230 et Ju 52 retrouvés ;
- Ju 52 confirmé dans une scène d'Africa 1 ;
- deux lance-flammes diagnostiqués : noms et munitions présents, modèle d'arme et comportement absents ;
- flame1.4ds identifié comme un simple effet fire01 de 471 octets.

## Démarrage de l'audit exhaustif

Le premier inventaire automatisé couvre désormais les trois couches commerciales : jeu de base, Patch et Sabre Squadron.

- 68 missions ou variantes analysées dans 79 registres solo et multijoueurs ;
- 71 dossiers de scripts recensés ;
- 5 347 scripts effectifs comparés ;
- 54 entrées de catalogue retrouvées : 33 solo et 21 coopératives ;
- 619 scripts remplacés entre les trois couches ;
- inventaire séparé des dossiers de cartes non déclarés dans le multijoueur ;
- comparaison des catalogues de neuf couples solo/coopératif présentant 28 omissions, 9 ajouts ou plusieurs renumérotations, avec trois chaînes déjà restaurées de façon stable ;
- inventaire des modèles, scripts et tables liés aux armes et véhicules retirés.
- audit manuel complet du Tutoriel, d'Arctic 1 à Arctic 4, de Czech 1 à Czech 6, de Normandy 1 à Normandy 2, de Norway, Sicily 1–2, Burgundy 1–3, Burma 1–2, Libye 1–3 et Africa 1–6 : les restaurations démontrables sont intégrées aux sources, tandis que les branches incomplètes, remplacées ou réellement manquantes restent isolées ;
- audit de fermeture des 25 variantes multijoueurs officielles possédant un registre : 203 liaisons, 172 scripts utilisés, 183 scripts disponibles, 12 scripts libres classés et une seule liaison manquante ; cette dernière restaure le placement aléatoire officiel de la radio de Burma 2 Objectif ;
- couverture multijoueur fermée : les 47 dossiers commerciaux et les deux prototypes sont tous déclarés après installation, sans troisième carte cachée complète ;
- contrôle statique permanent du câblage de l'installateur : chaque restauration détectée est reliée à son autocontrôle et à son étape d'installation, et le compteur détaillé vérifie lui-même son total.

L'ordre de traitement est désormais : restaurer tout ce qui possède encore ses données suffisantes, y compris les véhicules utilisables comme décors ou objets scriptés ; tester ; puis réserver pour la fin les créations qui exigent géométrie, modèles, animations, physique ou scripts nouveaux.

## Roadmap

### Phase 1 - Validation du jalon 0.7.5

Objectif : prouver dans le jeu ce qui est déjà automatisé.

- installer le paquet sur une copie de test ;
- afficher la liste Internet et rejoindre un serveur ;
- déclencher les easter eggs Africa 1 et Africa 4, essayer séparément les deux propriétaires du déclencheur des trois clés, puis valider l'objectif 8 d'Africa 1 en mode Carnage ;
- valider Arctic 3 par les deux routes connues ;
- valider Africa 2, la sortie de Czech 2 avec Freiberg, son comportement hostile en Carnage et la fin de la fumée de sa cinématique, Normandy 2, sa vague Red 26 et les quinze ripostes Blue vers Ally 5, la paire de zones Norway, le changement d'éclairage des trois éléments de l'Enigma, les animations aléatoires des huit gardes du Tirpitz et l'arrêt du minuteur de `Small3`, la mise en place du mécanicien 16 et la ronde après alerte du garde 19 d'Africa 1, la partie de cartes des soldats 24 et 25, Libye 3, la survie d'Africa 6, les cinq charges et l'interrupteur lumineux d'Arctic 2, le repos assis du garde 24 d'Africa 3 et le geste de chaleur du garde 03, la réaction des gardes 22 et 23 à l'alarme globale, les réactions défensives des gardes 06 et 16, les événements des gardes 25, 28, 29, 31 et 32 et les embuscades 33 à 37 d'Africa 3, le sifflement de vapeur de l'arrivée en Jeep, les cinq passagers d'Opel et les postures des réservistes 27 à 30 d'Africa 4, la mise en place de Schumann pendant l'embuscade, les événements d'AF4_43, le visage d'AF4_10, l'alerte vocale d'AF4_sklad01 et les cinq avions d'Africa 5, le marqueur de proximité des documents et l'impact de la chute de glace d'Arctic 4, les deux sabotages, la fermeture de la barrière, le retour du garde et la réplique 57990065 de Burgundy 1, l'objectif des huit véhicules de Libye 2 coopératif, les deux générateurs de Brest coopératif, les deux objectifs sans alarme de Burgundy 1 coopératif, puis les trois ordres possibles de sauvetage et les pertes partielles de Burgundy 3 coopératif dans plusieurs difficultés ;
- charger Normandy3 Zone et Africa5 Prototype ;
- tester les six boutons d'alarme de Sicily 1 en solo et en coopération, puis sauvegarde, chargement et restauration complète.
- tester en solo et en coopération la reprise de `ge_cesticka` après une alarme et la boucle de marmonnement de `gumak` dans Burgundy 2.
- tester dans Burgundy 3 la ronde du garde 32, la séquence complète 59990052–59990056 du premier SAS, puis une sauvegarde et un chargement avant et après sa libération.
- tester dans Libye 1 coopératif les dialogues 08–12 et 33–34 avec fin normale, alarme et mort d'un participant ; tester dans Libye 3 coopératif l'échange des drapeaux et les deux mitrailleurs de toit.
- tester dans Arctic 1 Objectif l'extinction conjointe des deux halos du transformateur, dans Burma 2 Objectif les deux emplacements aléatoires de la radio, et dans Normandy MP les deux états successifs du phare (rotation et trois lumières).

Sortie attendue : tableau de tests signé avec captures et anomalies.

Le registre exécutable de cette phase est conservé dans
`validation/runtime-validation.json`. Il impose pour tout résultat réussi
l'identité du testeur, la date, le hash exact de la construction et au moins
une capture ou un journal. `tools/runtime_validation_audit.py` contrôle aussi
que les deux déclencheurs possibles de l'easter egg d'Africa 4, les deux
prototypes multijoueurs, le réseau, l'exploration, la résolution, la
restauration et la barrière multijoueur-vers-solo ne puissent pas être oubliés.

### Phase 2 - Tutorial et guide des secrets

Objectif : rendre le septième ensemble de secrets réellement accessible en 1.12.

- essayer de restaurer l'escalade uniquement dans Tutorial ;
- si impossible, créer un nouvel accès physique vers le toit en conservant le lingot à sa cache d'origine ;
- n'utiliser le déplacement du lingot qu'en dernier recours et l'indiquer comme adaptation ;
- transformer les positions exactes déjà décodées des trois crânes Burma 1 en repères visuels validés par captures, puis relever les autres caches difficiles ;
- enrichir le guide joueur après vérification visuelle.

Sortie attendue : sept procédures toutes réalisables sous 1.12.

### Phase 3 - Objectifs multiples et chemins désactivés

Objectif : trouver les actions encore présentes mais non reliées.

- maintenir le graphe déjà construit de tous les objectifs, signaux et compteurs, puis fermer les candidats un par un ;
- vérifier les chaînes multi-actions déjà cartographiées dans Norway, Normandy 2, Sicily 1 et 2, Africa 3, Burgundy 1 et 2, Burma 1 et 2, Brest coopératif, Libye 1 à 3 coopératifs et Burgundy 1 à 3 coopératifs ;
- tester en jeu les deux libérations, la remise conjointe à la LRDG et la destruction des deux véhicules de ravitaillement de Libye 1 ; comparer séparément les deux variantes expérimentales de synchronisation du dialogue 48–49 ;
- rechercher les objectifs à deux ou trois actions réduits à une ;
- éprouver dans le module expérimental la reconstruction minimale de l'objectif de coopération d'Africa 5 ;
- reconstruire additivement dans Sicily 2 le déclenchement de la deuxième vague après trois charges retirées, sans rétablir la transition 0→3 qui bloquerait la validation des six charges désamorcées ;
- étudier une définition et un suivi fiables de « toute l'unité doit survivre » dans Libye 2 coopératif, où la validation solo n'a pas d'équivalent conservé ;
- tester une réactivation d’Africa 3 objectif 6 strictement limitée aux modes Carnage 3 et 7, car la garde d’origine n’est plus conservée ;
- tester en jeu les deux approches de Brest et confirmer les comportements distincts du soldat `z3_ven4` ;
- comparer scripts de base, Patch et Sabre ;
- tester les bords rendus accessibles par le mode exploration ;
- recenser portes, tunnels, secteurs et routes avec géométrie et collision ;
- documenter chaque chemin comme actif, cassé, décoratif ou absent.

Sortie attendue : registre mission par mission et deuxième lot de correctifs.

### Phase 4 - CASTLE2, ENGLAND et autres variantes

Objectif : étudier la finition des créations incomplètes.

- relier CASTLE2 à ses cartes et acteurs apparentés ;
- restaurer son objectif 5 dans une démonstration isolée ;
- évaluer CASTLE1 comme branche précédente ;
- placer les scripts ENGLAND sur une carte d'essai sans prétendre retrouver la mission originale ;
- rechercher d'autres archives, démos, patches et builds légitimes.

Sortie attendue : prototypes séparant clairement données officielles et création moderne.

### Phase 5 - Armes incomplètes

Objectif : produire un lance-flammes expérimental crédible.

- inventorier animations compatibles, sons, effets et paramètres de dégâts ;
- créer les modèles britannique et allemand ;
- intégrer tenue, visée, réservoir et rechargement ;
- tester IA, incendie, performance et multijoueur ;
- étudier ensuite Garota et ZK-383.

Sortie attendue : module optionnel, jamais présenté comme simple réactivation.

### Phase 6 - Aéronefs et véhicules

Objectif : mesurer ce qui manque à un appareil pilotable.

- choisir un seul banc d'essai, probablement Ju 52 ou La-5 ;
- inventorier sièges, caméras, surfaces mobiles et points moteur ;
- créer commandes, physique, dégâts et mission d'essai ;
- comparer ensuite M323, Aichi et Fa 223 ;
- décider pour chaque appareil entre décor animé, véhicule scripté ou pilotage complet.

Sortie attendue : prototype de véhicule et matrice de faisabilité.

### Phase 7 - Campagnes historiques et nouvelles créations

Objectif : exploiter les découvertes sans fabriquer de faux contenu officiel.

- poursuivre la recherche Londres, Angleterre, Allemagne et Dunkerque ;
- isoler les éléments réellement liés à Gary Bristol, Scarred Man et M. Murrau ;
- écrire une bible distinguant faits, inférences et inventions ;
- créer éventuellement une campagne communautaire inspirée de ces concepts ;
- créditer les auteurs, conserver les licences et isoler les dépendances.

Sortie attendue : campagne expérimentale clairement étiquetée.

### Phase 8 - Publication

Objectif : livrer un paquet robuste.

- options séparées par stabilité et niveau de spéculation ;
- sauvegardes et restauration testées ;
- contrôle de taille et d'empreinte pour chaque dépendance ;
- guide joueur et rapport des découvertes intégrés ;
- journal des versions et crédits communautaires ;
- tests sur une installation propre 1.12.

## Critère de décision

Une restauration entre dans l'installation standard si son intention et ses données sont démontrées. Une reconstruction entre dans un module expérimental si elle demande des raccords modernes. Une création entièrement nouvelle reste séparée et explicitement nommée.
