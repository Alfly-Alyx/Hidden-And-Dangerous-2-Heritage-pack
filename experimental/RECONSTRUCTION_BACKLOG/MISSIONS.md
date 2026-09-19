# Inventaire des missions et scripts

Les noms en capitales correspondent aux dossiers existants ou aux dossiers à
créer. Les chemins existants sont indiqués lorsqu'une étude est déjà disponible.

## Arctic 1 et 2 — études consolidées

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `ARCTIC1_GATE_CUTSCENE2_ADDITIVE` | Documenté | Variante K2 exclusive avec le mouvement commercial; conserver une seule réplique de sortie; aucun signal direct vers K2a; surveiller le `OnCutsceneDone(2)` imbriqué. |
| `ARCTIC1_FIRE_OBJECT155_LMP` | Bloqué preuve | L'objet 155 n'existe que comme bloc LMAP sans transformation autonome. La boucle historique est trop serrée et sans délai. Aucun propriétaire fiable ne doit être créé. |
| `ARCTIC1_KANISTERNIK_CARNAGE_SIT_SMOKE` | Prototype désactivé | La primitive `Sit` est attestée et des transitions Sit→Smoke existent. `%%kourimsed2` n'a aucun usage actif. Variante Carnage minimale seulement; ne pas modifier les cutscenes 4. |
| `ARCTIC1_MOLE_AND_WALKER_IDLE_VARIANTS` | Bloqué preuve | `SpotRight`, `SpotLeft` et `!strazny01..03` n'ont pas de précédent actif démontré. Aucun prototype actif. |
| `ARCTIC1_CISTERN_EFFECTS_LAB` | Validation jeu | Particule 53 et son 6,2 sont commentés sur six citernes Arctic1 et six Arctic3; les versions multijoueur les omettent. Procéder par sonde A/B sur une seule citerne. |
| `ARCTIC1_REBEL_TEST_LEGACY_BRANCH` | Faux positif | `Rebel_Test` n'a pas de propriétaire et la version commerciale choisit déjà deux branches complètes via `swampYesNo`; ne pas ajouter de second sélecteur. |
| `ARCTIC1_FALSE_POSITIVES` | Faux positif | Verrouille l'impression d'objectif, le test d'équipe de sauvegarde, `tree01`, les jumelles remplacées, le téléport souterrain remplacé et `CUDLIK` déjà stable. |
| `ARCTIC1_CAMPFIRE_LIGHTMAP` | Historique non promouvable | Le prototype ancien est conservé comme trace, mais le propriétaire et le contrôle LMAP autonome ne sont pas démontrés. |
| `ARCTIC2_RADIO1_SECOND_SOUND` | Bloqué preuve | `S_radio` utilise `l_ar2radio` à 0,273 m de `m_radiog_1`; le second poste `m_radiog_` est à 19,499 m. Aucun second émetteur sérialisé. Le précédent Arctic1/3 utilise `l_haydn_`/`_2` avec gains 1/0,2. |

Chemins : `experimental/ARCTIC1_*` et
`experimental/ARCTIC2_RADIO1_SECOND_SOUND/`.

## Arctic 4

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `ARCTIC4_RADIO_DESTRUCTION_FAILURE_ADDITIVE` | À documenter | `m_AF5_stul_4.Box17` pointe vers `R_Arc3_fail.scr`. L'ancien signal 4 et l'échec objectif 6 sont commentés car la radio n'est pas destructible. Trouver une vraie radio destructible ou un proxy, jamais la table. |
| `ARCTIC4_STATIC_GUARD3_ALARM_POST_ADDITIVE` | À documenter | Le mouvement vers `StaticGuard3_5` est commenté, mais le checkpoint existe. Étudier deux profils exclusifs : combat libre et poste fixe. |
| `ARCTIC4_KRA_NEARBY_REACTIONS` | Documenté, à enrichir | Réexaminer l'étude avec les binaires complets présents sous `.analysis/arctic4-full/`, puis extraire positions et distances si elles sont résolubles. |
| `ARCTIC4_STATIC_GUARD3_SIT_SMOKE` | À documenter | Deux frames existent; séquence historique TurnAt/délai/Sit/délai/Smoke/délai/`%%kourimsed2`. Fournir une transcription désactivée et une variante moderne sans animation nommée. Séparer du poste d'alarme. |
| Faux positifs | À fermer | Les Hunters reçoivent déjà le signal 13 par activateur; les jumelles de `sub_gunner` ont été remplacées par `Binoculars`. |

## Czech 2

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `CZECH2_LEGACY_PLAYER_STAGING_ADDITIVE` | À documenter | Scripts libres `player1assign..4` et `startscriptengl1..4`; checkpoints `en1..4` et `Ger1_1` présents. Les frames player ne sont pas initialisées. Garder `cut2` du joueur le plus proche par défaut et empêcher tout double téléport. |
| `CZECH2_GER12_DEATH_STAGING` | À documenter | `R_Cz2_Ger12` est lié. L'ancien `Lie` précédait `mrtvolak`; `dummy_ger12_sit` existe sans usage. Tester une posture minimale, puis un placement assis séparé uniquement si la géométrie le confirme. |
| `DOCUMENTS_LOST_MESSAGE_19993808` | Bloqué preuve | L'identifiant n'apparaît que dans quatre lignes commentées et aucun texte n'a été retrouvé dans 9 643 entrées. Le signal de perte reste actif. Une phrase moderne optionnelle doit être anti-répétition et ne jamais être présentée comme officielle. |

## Czech 3

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `CZECH3_END_CUTSCENE_PLAYER_VISIBILITY` | À documenter | Les doubles sont créés et les joueurs réels téléportés vers `Com1..4`. Masquer un joueur seulement si son double existe et garantir le rétablissement même en cas d'interruption. |
| `CZECH3_NOSIC2_SMOKE_IDLE_VARIANT` | À documenter | Ancienne pause/rotation vers `ja_patnik17` contre délai commercial de 5 s. Variante sélectionnable qui ne doit pas bloquer objectifs ou partie de cartes. |
| `CZECH3_FORMATION_CLEANUP_DUAL_PATH` | À documenter | `zlesa1` contenait nettoyage global et `Formation_Destroy`; `zlesa_zrusformaci` reste lié; `zlesa2` retire individuellement. Décider entre superviseur one-shot et faux positif. |
| `CZECH3_OBJ_RADIO` | Bloqué preuve | `czech3_obj` n'a que la liaison Box29. Le script libre vise `l_a1ra_`, absent; la scène contient `la_b1_radio_` et son enfant. Reconstituer hiérarchie, propriétaire et son avant toute substitution. |

## Czech 4 et 6

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `CZECH4_SKLEPERS_MISSING_RETREAT_POINTS` | À documenter | Trois scripts utilisent `Move("???")`; la note indique un ancien redesign de checkpoints. Rechercher trois destinations distinctes dans la géométrie, avec comportement immédiat comme profil par défaut. |
| `CZECH4_PLATOON04_SIGNAL5` | Documenté | `APumperz` envoie le signal 5 aux pelotons 01–06; le pianiste 04 n'a pas de récepteur. Le correctif doit arrêter piano/son/animation, activer le combat et conserver la proximité 40. |
| `CZECH4_COUNTER_PLATOON07_09` | Documenté, bloqué preuve | Le compteur libre vise 06–09 après trois signaux 10, mais seul 06 possède un acteur. Déterminer renommage, suppression ou abandon. |
| `CZECH4_DOG01_OWNERLESS` | Documenté, bloqué preuve | Script libre maître `Runner03`, sans chien ni liaison. Exiger modèle, placement et route avant activation. |
| `CZECH4_R_CZ4_HODINY` | Faux positif | Fichier vide résiduel; rien à restaurer. |
| `CZECH6_ISU152_DUAL_ROUTE` | Documenté | Profil historique C5_isu01→C5_tank11→C5_isu02 à 12, contre route directe à 30. Tous les checkpoints existent. Tester passagers R18–20 et collisions. |
| `CZECH6_RADIO_SABOTAGE_DUAL_PATH` | À documenter | La base conditionnait l'objectif 02 au signal d'alarme 1; le patch rend l'accès immédiat. Garder l'immédiat par défaut, sans créer de nouvel objectif. |
| `CZECH6_G40_ALERT_RECEIVERS` | À documenter | G40 envoie signal 1 à G11/G43 sans récepteur. Déduire seulement depuis `OnAlarm`; ne pas heurter le signal 2 de sabotage ni la proximité. |
| `CZECH6_G40_G41_DIALOGUE_SYNC` | À documenter | La conversation envoyait autrefois signal 1 aux deux acteurs. Tester si un arrêt de boucle gestuelle avant parole est nécessaire; sinon classer faux positif. |

## Normandy 1

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `NORMANDY1_INNER_GUARD_ALTERNATE_TRIGGERS` | À documenter | Détecteurs N24/N25 orphelins, portée 2–3 m; positions d'acteurs perdues. La version commerciale active N01 sur alarme. Recréer uniquement avec placement géométrique démontré et anti-double. |
| `NORMANDY1_N13_EXTRA_APPROACHES` | À documenter | A2/A3 envoyaient signal 1 à N13, mais leurs positions manquent. N12_A1..4 activent déjà N12/N13. Ne restaurer que si des emplacements distincts sont prouvés. |
| `NORMANDY1_N17_SIGNAL2_BRANCH` | Bloqué preuve | Ancien A2 envoyait signal 2 à N17, sans gestionnaire. L'acteur actuel A1 déclenche N17/18/19 par signal 1. Ne pas inventer de réaction. |
| `NORMANDY1_ACTIVATOR_VARIANTS` | Faible priorité | N14_A2 historique portée 3 contre A1 portée 2; N12_A5 est un duplicata sans acteur. |
| `X_N1_kamera-ya` | Faux positif | Reconnexion déjà stable. |

## Normandy 2 et 3

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `NORMANDY2_ESCORT_GUIDANCE_GRID` | Documenté, reconstruction lourde | Réseau Dummy_Go et 14 scripts orphelins; récepteurs alliés présents, mais aucune liaison ni signal 5 initial. Corriger aussi Go13 qui désactive Go11a deux fois. La variante statique commerciale reste le défaut. |
| `NORMANDY2_RETURN_DETECTORS` | Documenté | Detector9/10/11 existent et attendent signal 10 sans émetteur. Les trois devraient viser le récepteur 10, car les Blues n'activent que celui-ci. Garder expérimental. |
| `NORMANDY2_FAKE_DEFENCE_COORDINATOR` | À documenter | Script complet mais sans propriétaire : proximité, choix de cibles, signal 25 aléatoire. Ajouter anti-répétition et valider les cibles avant intégration. |
| `NORMANDY2_INCOMPLETE_WAVES` | À documenter | Wave1 a un déplacement de bâtiment incomplet; Wave2 contient des chemins vides; certains acteurs manquent. Créer des checkpoints modernes depuis la géométrie. |
| `NORMANDY2_ACTIVE_PLACEHOLDERS` | À documenter | Séparer : panique/mort Red31, regard du conducteur Tiger vers balcon, orientation `Ally_1` des Blues. |
| Correctifs déjà stables | Faux positif | Compteur allié, signal 7 Red26 et boucle Blue OnSignal5 A1→A5 pour 15 acteurs. Blue12/16 sont absents. |
| `NORMANDY3_MP_ZONE_TRUNCATED_CONTAINERS` | À documenter | Conteneurs Zone tronqués tandis que les fichiers MP complets existent. Étudier une fusion par préfixe; ne jamais versionner les binaires commerciaux. |

## Norway

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `NORWAY_MISSING_TIRPITZ_GUARDS_1_2_6_7_12_13_16` | Documenté, à corriger | Les checkpoints des gardes retirés existent. Acteurs/liaisons manquants : 1,2,6,7,10,12,13,16,17. `Dummy_see1/2` et les scripts survivent. Rechercher surtout identité, équipement et positions des gardes 10/17. |
| Émetteur commercial | Information stable | Les gardes 4,5,8,9,11,14,15,18 sont complets et ne doivent pas être dupliqués. |
| `NORWAY_TIRPITZ_GUARD3_AMBIENCE_HANDLERS` | À documenter | Acteur, liaison et checkpoints du garde 3 existent, mais ses gestionnaires 1..4 manquent alors que l'émetteur le vise. Comparer chapeau, bouteille, froid et regard des gardes voisins. |

## Sicily

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `SICILY1_IT40_DUAL_DOOR_BEHAVIOR` | À documenter | La version commerciale déverrouille deux portes; l'ouverture automatique est commentée. Offrir `unlock-only` par défaut et `unlock+open` historique. |
| `SICILY2_CHARGES_DUAL_STATE_WAVE` | À documenter | Six charges avaient une transition 0→3 commentée. L'activateur de vague met exactement trois charges à l'état 3; l'objectif exige les six à l'état 0. Compter les charges retirées/désamorcées sans casser l'objectif. |

## Burgundy et Co-Burgundy

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `BURGUNDY2_GUMAK_ESCAPE_ROUTE` | À documenter | Trajet `bmv1` commenté, `citron1` actif, `bmv4` absent; les véhicules sont retirés en coop. Exiger preuve géométrique et tester l'objectif d'évasion. |
| `BURGUNDY2_CAMERY_AND_PRUCHOD_STUBS` | À documenter | `camery` contient K1..K8 incomplets et seul K1 après 60 s; `ge_pruchod` est un no-op réutilisé. Classer chaque stub, sans activation en bloc. |
| `CO_BURGUNDY2_CLOSURE` | À fermer | Seuls les scripts libres de cheval/cochon subsistent, propriétaires absents; `ge_pruchod2` diffère des profils coop `nuda`; les sauts commentés n'ont pas de labels/valeurs. |
| `BURGUNDY3_INTERROGATION_GESTURES` | Documenté | Le contrôleur envoie 10..17 en alternance; les 19 répliques fonctionnent, mais les gestes manquent. N'utiliser que des animations commerciales prouvées et interrompables sur alarme. |
| `BURGUNDY3_JEEP_24_REPLACED_BRANCH` | Documenté, bloqué preuve | Branche véhicule commentée, `car05` absent; la version commerciale joue l'animation de bureau et la coop `nuda`. Reconstituer le chemin avant sélecteur. |
| `BURGUNDY3_EXPLOSION_SOUND_DUAL_TRIGGER` | Documenté | La branche directe envoie signal 10, le son réagit à cutscene4, et la cutscene émet déjà les deux. Toute variante doit être idempotente pour éviter le double son. |
| `BURGUNDY3_EN22_EN23_END_STATE` | À documenter | La branche directe tue sous distance <15; la cutscene applique de gros dégâts, avec anciens `Kill` commentés. Comparer dégâts seuls et mort explicite sous le même filtre. |
| `CO_BURGUNDY3_CLOSURE` | À fermer | Dix porteurs ambiants absents; Maquis signal1 sans émetteur mais déjà détruit sur alarme; frames manquantes = sous-nœuds, pas routes. |
| `CO_BURGUNDY1_CLOSURE` | À fermer | Douze contrôleurs oiseaux/portes sans `dummy_snd1..12`; JohnAshley et chien absents; explosion 05 déjà liée à objectif02; commentaires LookAround identiques solo/coop. |

## Libye et Co-Libye

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `CO_LIBYE1_OBJ2_AND_AF1_48_49` | Documenté, à compléter | Tester deux synchronisations exclusives : ajouter AF1_48 au coordinateur comme 08/12 et 33/34, ou démarrer le premier acteur depuis le coordinateur comme 23/24. Ne pas inventer les réactions signal2. |
| Objectif prisonnier historique | Information | L'ancien objectif 7 d'escorte est distinct de l'objectif 2 actuel sur l'officier; ne jamais les substituer. |
| Fermetures CoLibye1/2 | À fermer | CoLibye1 : 385 liaisons, 140 utilisées, aucun Move/Frame manquant. CoLibye2 : trois scripts jeep signal2 et deux OpelFlak vides, sans liaison; objectif survie 4 distinct. |
| `CO_LIBYE3_OPEL_OWNER` | Documenté | Variantes cargo/flak exclusives; fermeture générale : 296 liaisons, 148/149 utilisées. |
| `CO_LIBYE3_HALFTRACK_ROUTES` | À documenter | `Hammer1_SMG_3`/`LMG_1` manquent GO4_1/GO5_1, alors que le départ actif utilise `_2`. Recréer les points et conserver le départ direct en alternative. |
| `CO_LIBYE1_AF1_23_24_DIALOGUE` | À documenter | Douze lignes coop sont commentées. AF1_23 envoie une synchronisation, AF1_24 aucune; le coordinateur attend deux signaux et les fins signal2 existent. Exiger audio et lipsync. |
| `LIBYE2_DIALOGUE_24_25_CONDITIONAL_53990023` | À documenter | Réplique enregistrée/lipsync commentée sur le parc détruit. La déclencher seulement après destruction réelle des huit véhicules, avec gestion mort/alarme/rejeu. |
| `LIBYE3_GERMAN15_ALARM_DUAL_BEHAVIOR` | À documenter | Ancien `MoveToAlarm` avant posture basse/course/agressif. Définir un sélecteur; checkpoints présents. |
| `LIBYE3_PANZER_DRIVER_ALARM_GATE` | À documenter | Alarmes historiquement désactivées au départ puis réactivées après route. Comparer conducteurs et états du char avant option. |

## Africa 1 à 6

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `AFRICA1_AF1_26_INCOMPLETE_START_LOOP` | À documenter | Le script actif contient `START doplnit` en boucle et y revient après alarme. Corriger la boucle sans inventer de route. |
| `AFRICA1_OFFICER_21_CUTSCENE_MOVE` | À documenter | `Move AF1_21_01` est commenté avant cutscene10; checkpoint présent. Tester cadrage caméra et variante exclusive. |
| `AFRICA1_M_DVR_H01_LIGHTMAP_DOOR` | Bloqué preuve | Frame visuelle présente, script libre complet mais groupe lightmap absent. Retrouver un nom d'éditeur valide ou classer irréparable. |
| `AFRICA1_PLAYER_INTRO_AND_OFFICER_REACTION_COMPOSITE` | À documenter | Les anciens player01..04 réagissent à cutscene10; les scripts actuels affectent `CUTSAS` pour intro3 puis finissent. Composer sans double affectation et garder le gestionnaire vivant. |
| Africa1 déjà étudiés | Documenté | Ne pas dupliquer AF1_20, AF1_04, AF1_22 ni l'introduction Heritage. |
| `AFRICA2_AA_SPIT01_ADDITIVE_ATTACK` | À documenter | Frame présente, script orphelin presque complet qui masque puis attend signal1; aucun émetteur. Ajouter une activation cohérente sans remplacer l'aviation existante. |
| `AFRICA2_MES05_SECOND_ATTACKER` | Bloqué preuve | Script orphelin, frame `mes_05` et signal absents. Rechercher ressource officielle/copie expérimentale, préserver mes03/04. |
| `AFRICA2_CAMP_AMBIENT_VOICES` | À documenter | Sept scripts orphelins pilotent 17 frames sonores existantes. Concevoir des contrôleurs non concurrents et éviter le déclenchement simultané. |
| `AFRICA2_REINFORCEMENT_POST_ARRIVAL_ACTIVITY` | À documenter | Quatre scripts de renfort finissent sur `ACTIVITY doplnit`. Ajouter des activités seulement; ne pas rétablir le trajet de camion explicitement retiré. |
| `AFRICA3_OPEL_ENGINE_SMOKE_ADDITIVE` | Bloqué preuve | Script orphelin attend signal1 et crée Particle21; aucun émetteur et ancre apparente absente. Le contrôleur racine existant reste intact. |
| `AFRICA4_PASSENGER09_ORIENTATION` | À documenter | `TurnAt` commenté sans déclaration/target, contrairement aux passagers 06–10. N'utiliser qu'une cible attestée ou explicitement moderne. |
| `AFRICA4_LEADER11_CHANGEPOS` | À documenter | Sous-routine entièrement commentée et jamais appelée; comparer leaders 16–25/31–33 et les appels stables 27–30 avant de choisir un moment. |
| `AFRICA4_INVASION_TRANSITION_VARIANT` | À documenter | Ancien fondu radio et délai 20 s avant Opel. Variante de rythme compatible avec la conséquence radio stable, sans délai doublé. |
| Africa4 déjà étudiés | Documenté | Ne pas dupliquer les dossiers d'introduction, compteur, proximité et autres études existantes. |
| `AFRICA5_PALM14_AMBIENT_SOUND` | À documenter | Contrôleur présent mais non lié; source `S_vrzplm14` absente, chaînes 1..13/15 complètes. Déduire la source 14 depuis les voisines et la transformation du contrôleur. |
| `AFRICA5_ENDING_RADIO_LINES_58_60` | Bloqué ressource | IDs 09991958/60 commentés, tables de synchronisation présentes, WAV absents, 61 actif. Rechercher les langues officielles; sinon étiqueter toute voix/sous-titre comme moderne. |
| `AFRICA5_STORAGE_ALARM_FILTER_VARIANTS` | À documenter | Les filtres `SetAlarmType` commentés diffèrent; créer profils exclusifs et tests. |
| `AFRICA5_SNIPER31_RANGE_VARIANT` | À documenter | `Whenever npir` 14 m et bascules commentés; proposer uniquement un profil de portée. |
| `AFRICA5_RANDOM_FACE_SEED_VARIANT` | À documenter | Initialisations aléatoires commentées contre valeurs déterministes 10/3…; sélecteur exclusif. |
| Correctifs Africa5 stables | Information | `SetEvents(true)` AF4_43 et visage `e_f0w1` AF4_10 forment le socle; ne pas les dupliquer. |
| `AFRICA6_AIRANIM_OWNER_AND_SEQUENCE` | À documenter | Script libre saute à END avant six appels d'animation avion; aucun propriétaire/modèle. Étendre `AIRCRAFT_DECOR_LAB`, recherche historique puis laboratoire moderne seulement. |

## Burma et Tutorial

| Dossier | État | Informations disponibles et suite |
|---|---|---|
| `BU1-BRIDGE` | À documenter | Script libre : détecteur 7 m puis signal1 vers 32/33/34, sans gestionnaires; les acteurs se réveillent déjà à 60 m. Propriétaire, transformation et contrat manquent. |
| `TUTORIAL_EASTER_EGG_ACCESS_112` | Documenté | Chaîne de jeu complète; seul l'accès physique est cassé par la désactivation de l'escalade véhicule. Ajouter un appui/échelle existant, sans téléport ni rollback moteur. Bedford (-17.804197,-1.512808,80.766449), bouton modèle (-52.354725,1.906093,-2.890001), activateur (57.962864,1.353687,41.821579). |
| `TUTORIAL_SW2_THREE_ACTION_VARIANT` | À documenter | `dummy_SW2` libre envoie signal2; SW1/SW3 liés envoient 1/3; compteur ne traite que 1/3. Le chemin commercial 1+3 reste suffisant; la variante 1+2+3 ne doit jamais bloquer. |
