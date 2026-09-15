# Étude expérimentale — ancienne introduction de l'oasis d'Africa 4

État : architecture sélectionnable, étude seule, 14 septembre 2026. Aucun
prototype de script n'est produit, car deux plans actifs n'ont plus de caméra
et plusieurs contrats d'acteurs ont été remplacés.

Cette étude applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
l'introduction Dakota/parachutiste reste la release. L'introduction oasis ne
peut exister que comme variante `LEGACY/MODERNE` séparément sélectionnable.

## Verdict

`AF3b_cutscene.scr` conserve le squelette d'une courte introduction autour de
l'oasis : sous-titre `08011601`, quatre caméras déclarées, deux points de
regard, un Opel et deux Tiger. Il lance toutefois immédiatement la cinématique
1, exactement l'identifiant déjà utilisé par l'introduction release complète.

Le binding `camera_cut01 -> CUTcamera_Af3b.scr` appartient à la release.
`script_mise_next.scr` prépare les joueurs, lance lui aussi la cinématique 1 et
orchestre la séquence Dakota/parachutiste. Ajouter le contrôleur ancien créerait
deux propriétaires du même événement et de la même caméra initiale.

La reconstruction sûre est une **seconde entrée de mission** — nom de travail
`Africa4 — Intro Oasis [Legacy]` — qui mène au même gameplay après une
introduction exclusive. Elle doit recevoir un identifiant de cinématique
réservé, des caméras recréées et un contrôleur propre. L'entrée `Africa4`
commerciale, son registre et sa cinématique 1 restent inchangés.

## Baseline release à préserver

La couche Patch fournit une séquence cohérente :

- `camera_cut01` pilote les animations `#CamA3b1`, `#CamA3b2`,
  `#CamA3b4` et `#CamA3b5` ;
- `camera_cut00` fournit le troisième plan `#CamA3b3` ;
- le Dakota, le parachute, la torche, les particules et deux sons sont activés
  puis nettoyés ;
- deux joueurs sont dupliqués pour la mise en scène ;
- les répliques `08991614` et `08991615` sont déclenchées ;
- `OnCutsceneDone(1)` restaure sons, acteurs et caméra.

Le déclenchement par `script_mise_next.scr` dépend de la composition des
joueurs entre deux missions. La variante legacy doit reproduire ou remplacer
explicitement cette condition dans sa propre entrée ; elle ne doit pas laisser
la release se lancer ensuite.

## Squelette legacy attesté

La portion active d'`AF3b_cutscene.scr` utilise :

1. `camera_cut01` pendant environ 2 s ;
2. `camera_cut02` pendant environ 2 s ;
3. `camera_cut03` pendant environ 2 s ;
4. le sous-titre `08011601` ;
5. une fin de cinématique et la désactivation des sous-titres.

`camera_cut04` n'est utilisée que par `OnCutscene(2)`, alors que l'appel à cette
seconde cinématique est commenté. `camera_rozhlizeni01` et les glissements vers
`dummy_rozhlizeni01`, `dummy_rozhlizeni02` et `Opel02` appartiennent eux aussi à
un bloc commenté. Ces éléments attestent une intention, pas une séquence active
complète.

| Référence legacy | État dans la scène finale | Statut de reconstruction |
| --- | --- | --- |
| `camera_cut01` | présente, mais occupée par la release | dupliquer sa transformation sous un nom legacy |
| `camera_cut02` | absente | caméra active à recréer |
| `camera_cut03` | absente | caméra active à recréer |
| `camera_cut04` | absente | optionnelle/spéculative, seulement pour la cinématique 2 abandonnée |
| `camera_rozhlizeni01` | absente | optionnelle/spéculative, bloc de regard commenté |
| `dummy_rozhlizeni01/02` | présents | points de regard, sans caméra |
| `Opel02` | présent | troisième point de regard potentiel |
| `tiger01/02` | présents | déclarés, mais leur masquage est commenté |
| `dummy_organizer` | présent et déjà lié | ne pas réaffecter |
| `minaret08` | présent | cible du geste de l'officier |
| `Spawnsingle01–04` | présents | porteurs potentiels dont les bindings ont disparu |

## Acteurs et spawns

Les quatre scripts `AF3b_player01–04.scr` ne font que régler une posture ou un
regard pendant la cinématique, puis revenir en garde. Les quatre scripts
`AF3b_spawn01–04.scr` tentent de leur assigner dynamiquement ces comportements
sur `OnUse`, mais les variables `player`/`player02` ne sont pas résolues dans
les fichiers conservés. Aucun de ces huit scripts n'est lié dans le registre.

La reconstruction doit donc définir un contrat moderne explicite : quel joueur
est associé à chaque `Spawnsingle`, quand l'assignation a lieu, et comment son
script précédent est restauré. Il ne suffit pas de réattacher les quatre
fichiers de spawn.

`AF3b_dustojnik01.scr` semble être une ancienne variante du soldat `AF3b_01` :
il réagit à la cinématique, pointe `minaret08` et signale
`dummy_organizer` à sa mort. Or `AF3b_01` existe et est déjà lié à
`AF3b_01.scr`, tandis que l'organisateur possède lui aussi son script actif.
La branche legacy devra **ajouter seulement la réaction de cinématique** au
comportement actuel, pas remplacer l'IA complète de l'officier.

## Contrat de sélection proposé

| Entrée | Introduction | Propriétaire | Statut |
| --- | --- | --- | --- |
| `Africa4` | Dakota/parachutiste, cutscene 1 | scripts Patch actuels | release inchangée |
| `Africa4 — Intro Oasis [Legacy]` | oasis reconstruite, identifiant réservé | nouveau contrôleur | variante séparée |

Dans l'entrée legacy, un arbitre préchargement désactive uniquement le lancement
release et démarre la nouvelle cinématique. Après la fin, les deux entrées
doivent converger vers le même état jouable : joueurs restaurés, sons de jeu
actifs, Tiger/Opel dans leur état de mission, caméra libérée et scripts IA
originaux conservés.

## Pourquoi aucun prototype n'est fourni

Les transformations et animations de `camera_cut02/03` ne sont pas présentes.
Inventer deux plans permettrait au script de s'exécuter, mais ne restaurerait
pas la mise en scène commerciale. De plus, le contrat d'assignation des quatre
joueurs et la fusion de l'officier restent à concevoir.

Un prototype ne devient recevable qu'après création assumée de ces éléments,
listés séparément dans
[`ELEMENTS_A_RECREER_OU_SPECULATIFS.md`](ELEMENTS_A_RECREER_OU_SPECULATIFS.md),
et choix d'un identifiant de cinématique sans propriétaire.

## Protocole futur

Tester la release seule, puis la variante seule. Pour chacune : un seul appel
de cinématique, un seul propriétaire de caméra, skip propre, aucun sous-titre
persistant et restauration des quatre joueurs. Tester ensuite mort/alarme de
`AF3b_01`, présence des deux Tiger, rejoindre/quitter pendant la cinématique et
rechargement juste avant/après le choix d'introduction.

## Sources internes

- registre effectif `missions/africa4/scripts.dta` ;
- scripts Base/Patch `AF3b_cutscene.scr`, `AF3b_dustojnik01.scr`,
  `AF3b_player01–04.scr` et `AF3b_spawn01–04.scr` ;
- scripts Patch `CUTcamera_Af3b.scr` et `script_mise_next.scr` ;
- `scene2.bin`, `actors.bin` et `sounds.bin` d'Africa 4.

## Sous-cas AFRICA4_CUTSCENE2

État : **reconstruction incomplète, caméra principale absente**.

AF3b_cutscene.scr conserve un OnCutscene(2) minimal qui ne fait qu’activer
camera_cut04. L’appel CSC_RunCutscene(2) depuis OnCutsceneDone(1) est commenté.
AF3b_player04.scr conserve, lui aussi entièrement commentés, le mouvement du
joueur vers AF3b_pl04_01, sa mise accroupie, l’arme au bras, la fin de scène,
puis un nettoyage/téléport dans OnCutsceneDone(2).

Le checkpoint AF3b_pl04_01 est attesté par l’inventaire de mission, mais le
cadre camera_cut04 est absent de scene2 et actors. Le contrôleur principal ne
fixe en outre ni durée, ni fade de sortie, ni piste de caméra pour la scène 2 :
il dépendait manifestement du handler joueur 04 pour appeler CSC_EndCutscene.

Cette scène ne peut donc pas être qualifiée de simple réactivation. Elle cumule
une caméra perdue, un porteur joueur aujourd’hui non lié, un appel désactivé et
deux EndScript dont le cycle entre les cinématiques 1 et 2 doit être prouvé.

### Maquette admissible

Une future maquette doit créer une caméra **distincte**, par exemple
camera_legacy_cut04_modern, avec transformation et champ de vision documentés
comme MODERNES. Elle ne remplace ni camera_cut01 ni la cinématique 1 release.
La scène 2 appartient uniquement à l’entrée « Intro Oasis [Legacy] » décrite
plus haut, après attribution d’un identifiant sans propriétaire.

Le porteur joueur 04 doit recevoir sa réaction par fusion contrôlée avec le
mapping legacy des joueurs ; réattacher AF3b_player04.scr tel quel ferait
EndScript dès OnCutsceneDone(1), avant la scène 2. Aucun prototype exécutable
n’est produit tant que ce cycle et la caméra ne sont pas définis.

### Validation spécifique

1. Confirmer qu’une seule introduction est choisie avant la mission.
2. Lancer la cinématique 1 legacy, puis la scène 2 une seule fois.
3. Vérifier le trajet vers AF3b_pl04_01, l’accroupissement et l’arme sans
   téléport visible.
4. Vérifier fade, durée bornée, CSC_EndCutscene unique, restitution caméra et
   reprise du contrôle joueur.
5. Tester skip, mort/absence du joueur 04, sauvegarde entre les deux scènes et
   retour arrière complet.
6. Rejouer la release : sa cinématique 1, camera_cut01 et la séquence Dakota ne
   doivent présenter aucune différence.

Le plan AFRICA4_CUTSCENE2.plan.disabled fixe ces préconditions sans créer la
caméra ni modifier un registre.
