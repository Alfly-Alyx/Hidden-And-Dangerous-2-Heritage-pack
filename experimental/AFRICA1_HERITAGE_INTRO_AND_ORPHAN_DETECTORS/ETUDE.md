# Étude expérimentale — introduction héritage et détecteurs orphelins d'Africa 1

État : option exclusive et maquettes désactivées, 14 septembre 2026. Aucun
registre, script actif, installateur ou fichier du jeu n'est modifié. Cette
étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md)
sous forme de **choix exclusif** : les deux introductions restent disponibles,
mais une seule peut être liée et exécutée pour une partie donnée.

## Verdict

`AF1_cutscene.scr` conserve une introduction héritage presque complète, mais il
ne peut pas être simplement ajouté au registre : il lance immédiatement la
cinématique 1, tandis que `CUT_af1start.scr`, déjà lié, lance la cinématique 3
après 500 ms. Deux propriétaires de démarrage entreraient en course sur la
caméra, les sous-titres et l'état des acteurs.

Une option expérimentale est toutefois bornable : remplacer conditionnellement
le binding actuel `m_palma68 -> CUT_af1start.scr` par une copie **intro 1
seulement** du script héritage. Le porteur `m_palma68` existe et son emplacement
est déjà celui du contrôleur de démarrage release ; aucun nouvel acteur ou
position n'est inventé.

Les quatre anciens détecteurs sont d'une autre nature. Ils sont non reliés,
n'ont aucun acteur homonyme libre et leurs fonctions sont soit remplacées, soit
incompatibles avec la progression courante. Aucun prototype de détecteur n'est
proposé.

## Deux introductions, un seul binding

| Option | Binding de `m_palma68` | Cinématique lancée | Statut |
| --- | --- | ---: | --- |
| release | `CUT_af1start.scr` | 3 | comportement par défaut, inchangé |
| héritage | prototype intro 1 isolé | 1 | expérimental, exclusif |

Il ne faut jamais lier `AF1_cutscene.scr` sur une seconde frame en conservant
`CUT_af1start.scr`. Le choix doit être réalisé avant le chargement de la mission
et rester stable pendant toute sauvegarde. Désactiver l'option doit restituer
exactement le binding release.

### Pourquoi le fichier ancien ne doit pas être lié tel quel

Le fichier contient aussi `OnCutscene(10)` et `OnCutsceneDone(10)`. Ce bloc
référence `cam_ingame_01`, seule caméra recherchée qui n'existe plus. La
cinématique 10 actuelle possède déjà ses propriétaires actifs :

- `dummy_cut10_detect -> AF1_cut10_detector.scr` la déclenche ;
- AF1_21 gère caméra, conversation et progression ;
- `dummy_dabing_01 -> AF1_dabing_01.scr` gère les voix ;
- les scripts joueurs conservent leurs réactions visuelles.

Lier le fichier ancien complet ajouterait donc un gestionnaire concurrent et
une caméra non résolue à une cinématique 10 fonctionnelle. La maquette
[`PROTOTYPE_INTRO_HERITAGE_EXCLUSIVE.scr.disabled`](PROTOTYPE_INTRO_HERITAGE_EXCLUSIVE.scr.disabled)
ne conserve que la cinématique 1.

## Inventaire des actifs de la cinématique 1

L'inventaire direct de `scene2.bin`, `actors.bin` et `sounds.bin` confirme :

| Référence du script | Présence | Note |
| --- | --- | --- |
| `camera_cut01_01/02/03` | oui | trois plans sur les bâtiments |
| `camera_cut02_01/02` | oui | deux plans intermédiaires |
| `camera_cut03` | oui | la variable locale s'appelle `camera03`; la frame littérale `camera03` n'existe pas |
| `camera_let01` | oui | plan de l'avion |
| `la_macchi_cut` | oui | avion héritage |
| `la_macchi_cut.listy` | oui | hélice liée à `AF1_vrtule.scr` |
| `cam_ingame_01` | non | utilisée uniquement par l'ancien bloc de cinématique 10, exclu du prototype |
| `m_palma68` | oui | porteur actuel de `CUT_af1start.scr`, réutilisable par substitution |

La piste `pristani` passée à `FRM_WatchTrack` n'apparaît pas comme nom de frame
dans les trois fichiers de mission. Elle peut appartenir aux données internes
du modèle `la_macchi_cut`; son existence et son mouvement doivent être validés
en jeu et ne sont pas considérés comme prouvés par l'inventaire de frames.

## Réactions commerciales encore actives

La présence des handlers suivants renforce l'ancienneté de la cinématique 1 :

- `dummy_prelet_organizer -> AF1_prelet.scr` affiche les éléments de train de
  l'avion pendant la cinématique puis les masque ;
- AF1_12 range son arme, s'assoit, puis rejoint sa patrouille à la fin ;
- trois pales/flous utilisent `AF1_vrtule.scr`, qui accepte l'événement 1 et
  maintient leur rotation.

Un défaut latent doit être corrigé dans la copie de test : `AF1_prelet.scr`
déclare `tycr`, mais appelle `FRM_FindFrame(tycl,
"la_macchi_cut.rtycpodvozek")`. La référence droite écrase donc `tycl` et
laisse `tycr` non initialisée, alors que les deux variables sont utilisées dans
`OnCutscene(1)` et `OnCutsceneDone(1)`. La maquette
[`PROTOTYPE_PRELET_TYCR_FIX.scr.disabled`](PROTOTYPE_PRELET_TYCR_FIX.scr.disabled)
décrit uniquement cette correction protectrice.

L'introduction envoie aussi le signal 12 à AF1_11. Le script actuel d'AF1_11 ne
possède aucun handler 12. Ce signal reste un résidu sans effet ; aucun handler
n'est inventé dans ce lot.

## Voix et sous-titres

L'introduction héritage affiche trois identifiants, `05011001`, `05011002` et
`05011003`, avec `SUBTITLES_SetText`. Elle ne contient aucun
`FRM_MorphSpeech`, aucun `PlaySound` et aucune frame sonore.

L'inventaire de `LangEnglish.dta` ne contient ni WAV ni table de morphing dont
le nom porte ces trois identifiants. `05011003` est en outre réutilisé par
`AF1_dead_vehicles.scr` comme texte d'échec tardif. Il faut donc classer cette
introduction comme **séquence textuelle sans voix attestée**, pas comme dialogue
dont trois voix seraient simplement à reconnecter.

La cinématique 3 release est beaucoup plus riche : elle pilote huit frames
`S_cut1` à `S_cut8` et `CUT_af1dabing.scr` appelle dix-sept répliques
`05991054` à `05991068`, puis `05991074` et `05991075`. Les dix-sept tables de
morphing correspondantes sont présentes dans l'inventaire anglais. L'option
héritage remplace volontairement cette longue introduction ; elle ne doit pas
essayer de mélanger ses voix ou ses acteurs à la cinématique 1.

## Maquette exclusive

La maquette apporte trois différences explicites par rapport au fichier
commercial dormant :

1. un délai moderne de 500 ms, repris du démarrage release, laisse les autres
   scripts enregistrer leurs handlers `OnCutscene(1)` ;
2. seuls les blocs `OnCutscene(1)` et `OnCutsceneDone(1)` sont conservés ;
3. le bloc cinématique 10 et sa caméra absente sont supprimés.

Ce n'est donc pas une copie « officielle réactivée », mais une adaptation
**HÉRITAGE/MODERNE**. Son binding expérimental remplace celui de
`CUT_af1start.scr`; il ne s'y ajoute jamais.

## Protocole de test

1. Baseline release : tracer l'unique appel à `CSC_RunCutscene(3)`, la caméra,
   les dix-sept répliques, les huit sons et la restitution des acteurs.
2. Activer l'option héritage dans une copie de mission : vérifier un seul
   binding sur `m_palma68`, vers la maquette, et zéro exécution de cinématique 3.
3. Vérifier la résolution des sept caméras, de `la_macchi_cut` et de la piste
   `pristani` avant de juger la mise en scène.
4. Tracer AF1_12, `AF1_prelet` corrigé et les trois instances
   d'`AF1_vrtule.scr` pendant l'événement 1 et sa fin.
5. Confirmer trois sous-titres et aucune attente de voix. Aucun son ou morphing
   nouveau ne doit être inventé.
6. Après l'introduction, déclencher la cinématique 10 auprès d'AF1_21 : elle
   doit rester identique à la baseline et ne jamais rechercher
   `cam_ingame_01`.
7. Tester skip, mort/alarme précoce, sauvegarde juste après l'introduction et
   rechargement. L'option choisie ne doit ni relancer l'autre introduction ni
   laisser l'avion, ses roues, une caméra ou les sous-titres actifs.
8. Désactiver l'option et confirmer la restauration du binding
   `m_palma68 -> CUT_af1start.scr`.

Acceptation : une seule introduction démarre ; la cinématique 10 courante reste
intacte ; aucun accès à la caméra absente ; aucun acteur ou élément d'avion ne
reste dans l'état hérité après `OnCutsceneDone(1)`.

## Détecteurs orphelins

L'audit du registre classe les quatre fichiers comme non reliés et ne trouve
pour aucun d'eux un acteur homonyme présent, libre ou déjà occupé.

| Détecteur | Fonction conservée | Remplacement ou conflit actuel | Classement |
| --- | --- | --- | --- |
| `AF1_cut02_detector` | `OnUse` lance 10 ; après 16 signaux 10, réveille six renforts | cinématique 10 par `AF1_cut10_detector`; renforts par `AF1_posily_detector` | agrégat ancien remplacé |
| `AF1_dvereonuse_detector` | `OnUse` envoie 5 à AF1_20 ; même compteur de 16 morts | AF1_20 n'a plus de handler 5 ; compteur moderne de renforts actif | résidu doublement obsolète |
| `AF1_obj01_detector` | `OnUse` à 3 m lance 10 | déclencheur actif à 1 m, conditionné par AF1_21 vivant | ancien détecteur de porte remplacé |
| `AF1_obj03_detector` | tous les joueurs en zone après objectifs 1/2, puis valide 3 | l'objectif 3 actuel « éliminer tous les ennemis » est validé par `AF1_obj.scr` | ancienne progression incompatible |

`dummy_cut10_detect` et `dummy_posily_detector` sont déjà liés à leurs scripts
modernes. Ils ne sont pas des frames libres sur lesquelles empiler les anciens
détecteurs. Le premier protège la cinématique 10 par la présence d'AF1_21 ; le
second calcule un seuil depuis `_GetCountOfCarnageEnemies()`, réveille dix
renforts par vagues et active aussi le char. Restaurer le compteur fixe de 16
morts et six renforts créerait une seconde autorité concurrente.

Aucune position sûre n'est conservée pour les quatre détecteurs orphelins.
Verdict : documenter leurs protocoles, ne créer ni binding ni maquette.

## Sources internes

- registre effectif `missions/africa1/scripts.dta`
- `.analysis/binding-carnage-check.json`
- scripts Base/Patch `AF1_cutscene.scr`, `CUT_af1start.scr`, `AF1_prelet.scr`,
  `AF1_12.scr`, `AF1_vrtule.scr` et `AF1_11.scr`
- scripts Base/Patch des six détecteurs cités et `AF1_obj.scr`
- `scene2.bin`, `actors.bin`, `sounds.bin` d'Africa 1
- `.analysis/langenglish-list.json`
