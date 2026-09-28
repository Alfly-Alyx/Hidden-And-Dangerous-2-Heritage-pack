# FG42, MG34 et ZK-383 : mains privées, prises modernes et associations

**27 septembre 2026 — réalisation en cours, aucune arme jouable annoncée.**
Les [modèles FPV rigides](BANQUES_FPV_RIGIDES.md) disposent maintenant de banques
de mains dérivées. Leurs ressources restent désactivées et privées. Les prises,
trajectoires et gestes doivent encore être distingués d'une intégration moteur.

## Construction et provenance

`tools/build_rigid_weapon_hand_bank.py` lit uniquement les squelettes de repos
et géométries de mains commerciales épinglées, jamais leurs animations. Le
profil `modern-rigid-hand-grips.json` contient des choix **MODERNES** : décalages,
orientations, courbures de doigts/pouces, directions de coudes et placement.
Sa base F35 moderne est verrouillée par une empreinte JSON canonique. Aucune
coordonnée de géométrie commerciale ni pose d'os commerciale n'est dans le profil.

Pour chaque arme et chaque variante H/R, neuf clips sont calculés sur toutes
les frames entières : **54 clips, 1 574 poses d'auteur** au total. Le solveur
refuse d'étirer les bras. Racine des mains, positions locales, échelles,
géométrie et liaisons de repos demeurent inchangées. Les pouces disposent de
leurs réglages propres. Les alias `PROTOTYPE_FG4PH*`, `FG4PR*`, `MG3PH*`,
`MG3PR*`, `ZK3PH*`, `ZK3PR*` restent dans la limite native de 19 caractères.

Les trois modèles modernes restent **identiques octet par octet** aux modèles
rigides précédents. Le décalage `[0.07, -0.13, 0.16]` est incorporé uniquement
aux clés de position `fpv_weapon`. Jusqu'à v6, les autres canaux d'équipement
sont conservés. La révision v3 ajoute pour MG34 un décalage moderne de rangement
`[0, 0.04, 0.04]`, décroissant linéairement sur `Arm`, croissant sur `Disarm`,
nul dans les autres clips. Ce changement est explicite et contrôlé ; il ne
modifie ni les mouvements relatifs des pièces ni les modèles source.

Chaque dossier privé `FG42_HandFPV_vN`, `MG34_HandFPV_vN` ou `ZK383_HandFPV_vN`
contient 36 fichiers avec les aperçus : un modèle moderne désactivé, dix-huit
clips dérivés désactivés, seize PNG privés et un manifeste. **Aucun modèle
commercial de mains n'est exporté.** Les versions précédentes sont conservées.

## Ajustement des prises et contrôle des surfaces

Les premiers essais v1 réutilisaient nos réglages F35. Les vues rapprochées
ont montré des mains gauches trop éloignées et une prise droite ZK-383
inadaptée. `fit_rigid_weapon_grips.py` explore des choix modernes bornés sur
la pose `Idle1` de la variante H. Il pénalise les pénétrations de sommets,
centres/arêtes de triangles et témoins de surfaces ; sa mesure de proximité
utilise les **triangles finis**, pas leurs plans infinis. Ce calcul ne suffit
pas à qualifier une prise naturelle, les autres poses ou l'autre variante.

`modern_contact_cells.py` décompose les pièces annulaires non convexes en
cellules convexes à partir de leurs **sommets sérialisés et transformés**.
Il ne remplace pas ces coordonnées par celles d'une recette idéale. Les
cavités restent vides. Les faces internes de découpe sont tronquées à
profondeur nulle, et non traitées comme des surfaces matérielles : une
collision sur une couture numérique ne disparaît donc pas artificiellement.

Le contrôle couvre les 25 / 33 / 33 pièces FG42 / MG34 / ZK-383, soit
86 / 125 / 119 cellules dans la pose de repos vérifiée. Les triangles des
mains sont tronqués par les volumes, y compris lorsque tous leurs sommets
sont extérieurs. Tolérance `1e-5`, seuil d'aire `1e-14`, résolution de recherche
de profondeur `1e-7`. Pour une pièce décomposée, un triangle peut être compté
dans plusieurs cellules ; la profondeur est relative aux plans matériels
de la cellule, **pas une distance globale au bord du solide non convexe**.

Diagnostic v2 terminé : **162 poses**, trois instants de chacun des 54 clips,
sans pièce laissée hors contrôle. Zéro triangle pénétrant sur les 54 poses
FG42. Il reste 329 occurrences triangle/cellule MG34 et 474 ZK-383, notamment
sur les avant-bras pendant `Arm`, `Disarm` et `Rel`. Ces résultats sont ceux
de v2, pas une qualification de la révision suivante.

Les corrections v3 comprennent des marges locales de doigts, les coudes
gauches MG34/ZK-383 et la trajectoire de rangement MG34. Une exploration de
125 directions de coude droit seule ne supprimait pas cette dernière
collision. Une proposition de translation avant de 0,12 a été refusée pour
cible inaccessible ; aucun étirement n'a été ajouté pour l'accepter.
Le contrôle v3 a confirmé la suppression des collisions d'avant-bras MG34
sur les échantillons mais a trouvé de nouvelles collisions ZK-383 au repos
et en visée : le coude corrigé pour le rangement ne convenait pas partout.

**Révision v4, non qualifiée.** Le coude ZK-383 ne change donc que dans
`Arm`/`Disarm`, avec une courbe réversible qui retrouve la prise normale à
l'arrivée au repos. Les dernières marges de doigts ont été ajustées sans
changer les modèles. Sur les **162 poses v4**, zéro triangle/cellule pénétrant
à la tolérance fixée, aucune pièce omise. Rapport privé :
`.analysis/rigid-hand-surfaces-v4-20260927.json`. Les vues rapprochées de sortie
MG34/ZK-383 de la variante R ont aussi été inspectées. Ce résultat n'établit
ni prise naturelle, ni absence d'auto-intersection, ni qualité de cadrage.
Le contrôle dense v4 est maintenant terminé : **3 094 poses, 94 022 comparaisons
pose/pièce, aucune pièce omise**. Il révèle des traversées absentes des trois
instants initiaux : FG42 H/R 852/820 occurrences triangle/cellule, MG34 79/79,
ZK-383 354/368. FG42 et ZK-383 traversent notamment leurs chargeurs latéraux
durant les portions intermédiaires de `Arm`/`Disarm`. MG34 conserve de petits
empiètements aux demi-clés sur la poignée et le manchon. **La v4 n'est donc pas
qualifiée**, malgré ses 162 premiers échantillons sans traversée. Rapport :
`.analysis/rigid-hand-surfaces-v4-dense-20260927.json`.

Les propositions suivantes sont conservées comme essais, pas promues comme
prises correctes :

- **v5 : 100 occurrences** sur 3 094 poses. Les directions de coude à plusieurs
  repères annulent les collisions aux clés d'auteur, mais leurs transitions
  créent encore des traversées importantes entre clés. Le raffinement des
  arêtes sérialisées a épuisé sa borne d'exploration ; il n'a pas été présenté
  comme une réussite.
- **v6 : 81 occurrences FG42/R**, zéro pour les cinq autres couples arme/mains
  sur 3 094 poses, aucune pièce omise. Le coude constant choisi pour FG42 et
  ZK-383 fait remonter l'avant-bras dans la vue de repos : **variante écartée
  visuellement**, même là où le compte de collisions est nul. Les petites
  marges MG34 sont conservées séparément.

**Candidate v7 : mouvement d'arme revu, coudes ordinaires FG42/ZK-383.** Le
champ moderne `stow_motion` remplace explicitement les seules positions et
rotations de la racine pendant `Arm`/`Disarm` : mouvement linéaire réversible,
orientation de la pose prête, décalages FG42 `[0, -0.08, -0.1]` et ZK-383
`[0, -0.04, -0.15]`. Une extrémité source différente de la pose prête attendue,
un décalage hors bornes ou une combinaison avec l'ancien décalage additif
font refuser la construction. Toutes les pistes des pièces, les échelles et
les autres clips sont conservés ; **les rotations de racine de rangement
ne sont plus celles des banques modernes précédentes**. Ce changement est
annoncé dans le manifeste, reproduit par le lecteur indépendant et testé.
Les premiers aperçus ne montrent plus l'avant-bras élevé. Ils montrent encore
une partie de l'arme au départ : sortie complète du champ et cadrage moteur
ne sont pas qualifiés. Le contrôle dense v7 est terminé : **3 094 poses,
94 022 comparaisons pose/pièce, zéro occurrence triangle/cellule pénétrante,
aucune pièce omise**. Rapport `.analysis/rigid-hand-surfaces-v7-dense-20260927.json`,
profil canonique SHA-256
`58742eb4478344766073ab4e75b8b72c9ead28992726c238b404446090f50634`.
Cette mesure porte sur les clés et demi-clés des clips bruts, pas sur tous
les instants continus, les auto-intersections ou les gestes naturels.

`fit_rigid_elbow_path.py` reste un outil de proposition borné : il compare
les clés puis, sur demande, les quarts/demis/trois-quarts des transitions
arrondies en float32. Ses contrôles portent sur les faces des bras désignés,
pas sur toutes les mains ; il ne modifie jamais le profil automatiquement.

Le filtrage accéléré des triangles utilise leurs boîtes complètes, préparées
une seule fois par pose. Seuls les couples triangle/cellule disjoints sont
écartés ; les autres passent toujours par la troncature exacte. Un test
compare compte, aire et profondeur avec le parcours non filtré, y compris
pour des triangles traversants et des coutures de cellules.

La prise droite ZK-383 garde deux doigts insuffisamment proches. Un second
ajustement réduisait légèrement l'objectif global mais augmentait la
pénétration maximale sondée : **il n'est pas adopté**. Un objectif numérique
plus petit ne constitue pas automatiquement une meilleure prise.

Le solveur autorise maintenant des courbures **modernes indépendantes** pour
les doigts 1 à 4, sans changer les os des bras, le pouce, les positions ni les
échelles. Les choix absents conservent exactement l'ancien réglage commun.
Les tests utilisent un squelette inventé et vérifient qu'un doigt modifié
ne change que ses trois rotations locales. Le pouce garde son contrat séparé.
`fit_rigid_finger_curls.py` compare les deux variantes H/R, toutes leurs faces
et toutes les cellules des pièces ; il ne peut échanger une collision
supplémentaire contre une meilleure proximité. Sur le seul repos v7, il
rapproche l'auriculaire du bois d'environ 15,7 mm à 0,154 mm, mais laisse
l'index à environ 81 mm de la détente. **Cette proposition n'est pas adoptée.**
Elle révèle que le rapprochement de tous les doigts vers le bois, utilisé
par le premier ajusteur, ne qualifie pas la position de l'index. Une option
explicite `--index-to-trigger`, limitée à ZK-383/R, distingue désormais ces
cibles dans l'ajusteur global ; la prise entière reste à corriger et vérifier.

L'ouverture latérale de chaque articulation de base peut ensuite être choisie
indépendamment, bornée à ±30 degrés ; zéro laisse les anciennes poses identiques.
L'exploration optionnelle de l'index compare 81 départs bornés plus la graine
si elle est distincte. Les seules courbures locales ne permettaient pas de
sortir du minimum précédent. Une contrainte artistique optionnelle de hauteur
de poignet est aussi disponible, sans prétention anatomique ou historique ;
son essai a gardé des traversées et n'est pas retenu comme solution.

Une **candidate ZK-383 distincte**, reproduisible avec
`modern-rigid-hand-grips-zk383-trigger.json`, ajoute la prise réorientée,
les réglages propres de l'index/annulaire et une marge de 0,2 mm. Son profil
canonique porte SHA-256
`c5cfc4d7b161f5da6a94eefb7c30acfc17aa9d004ed9fc9ed08f9c9b109076b4`.
Les dix-huit clips privés `ZK383_HandFPV_v9` donnent **1 074 poses de surface
sans traversée, aucune pièce omise**. Les aperçus montrent une main droite
réorientée avec le poignet plus haut ; naturel de cette posture, ouverture
de l'index et auto-intersections restent à examiner. **Ce profil ne remplace
pas le profil par défaut v7 et n'est pas une prise visuellement qualifiée.**
Rapport `.analysis/rigid-hand-surfaces-zk383-v9-dense-20260927.json`.

## Routines natives et correction de poignets

`rigid_weapon_hand_audit.py --native` utilise des émulateurs isolés distincts
pour le chargement des clips, la progression des poses et les palettes de
mains. La racine identité des mains sert d'articulation diagnostique ; les
matrices d'équipement utilisent la référence numérique. Aucun chargement de
modèle, copie de scène, skin natif ou rendu n'est prétendu.

Le premier contrôle v2 a refusé `FG42/H/Arm`, temps 20 : le poignet droit
s'écartait de `0,000408953366`, au-delà du seuil entre clés `0,0002`. Le seuil
n'est pas relevé. L'audit conserve désormais toutes ces occurrences dans le
rapport, séparément des clés entières, qui gardent leur seuil `5e-6`.

Le correcteur `fpv_contact_constraints.py` accepte maintenant explicitement
la racine `fpv_weapon`, en plus de son ancienne racine lance-flammes. Il
recalcule seulement six rotations de bras après les poses observées et
préserve doigts, pouces, positions, échelles et équipement. Un second passage
de palette native contrôle le résultat. **Ce correcteur Python est hors jeu ;
il n'est ni un raccordement au client ni une modification des clips stockés.**
L'audit dense v2 avec ce correcteur est terminé : **54 lectures, 54 séquences,
3 202 instants, 6 404 palettes natives et 12 808 observations de poignets**
avant/après. Écart de poses natives/référence nul ; écart maximal de palette
`2,384185792e-7`. Aux clés, les poignets s'écartent au plus de `1,470161932e-7`.
Entre clés, le maximum brut est `0,001915595006` et **104 instants dépassent
le seuil**. Après correction hors jeu : maximum `1,534671294e-7`.
Le contrôle brut entre clés est donc explicitement en échec, même si la
correction réussit. Rapport : `.analysis/rigid-hands-native-corrected-v2-20260927.json`.

Les dix-huit clips FG42 v3 sont identiques aux clips v2 contrôlés. L'audit
natif des trente-six clips MG34/ZK-383 v3 a vérifié 2 156 instants et 4 312
palettes, 56 dépassements bruts ; maximum après correction `1,535909002e-7`.
Ces mesures ne sont pas attribuées aux nouveaux clips modifiés v4.

Pour v4, le correcteur préserve en plus le **plan de coude réellement observé**
dans les poses, au lieu de réimposer un seul repère statique. Cela évite
d'annuler le coude adapté au mouvement ZK-383. Ses cibles de poignets restent
inchangées et seules les six rotations de bras peuvent changer. L'audit
natif complet v4 de cette politique est terminé : **54 lectures, 54 séquences,
3 202 instants, 6 404 palettes et 12 808 observations de poignets**. Écart de
pose nul ; maximum palette `2,980232239e-7`. Maximum aux clés `1,546438142e-7`,
entre clés `0,001539700379`, **96 instants hors seuil brut** ; après correction
`1,526020142e-7`. Rapport `.analysis/rigid-hands-native-corrected-v4-20260927.json`.
Cela prouve uniquement la correction hors jeu des poignets, ni ses contacts
de surface corrigés ni son intégration au moteur. Les anciens rapports ne
sont pas réétiquetés comme preuve de cette nouvelle politique.

Le contrôle natif **v7** vérifie à nouveau les 54 clips, 3 202 instants,
6 404 palettes et 12 808 observations. Écart de pose nul, maximum palette
`2,980232239e-7`, poignets aux clés `1,603257649e-7`. Le maximum entre clés
descend à `0,000451782386`, avec **36 instants hors seuil brut**, contre 96
en v4. Après correction hors jeu : `1,645983209e-7`. Le seuil `0,0002`
reste donc en échec pour les clips bruts, sans relèvement ni masquage.
Rapport `.analysis/rigid-hands-native-corrected-v7-20260927.json`.

Le mode distinct `--dense --post-blend-surfaces` vérifie désormais les
surfaces après la correction hors jeu, et non seulement les clips bruts.
Sur v7 : **3 094 poses corrigées, zéro traversée et aucune pièce omise**,
maximum de poignet `1,613405173e-7`. Les poses d'entrée sont celles de la
référence numérique sérialisée ; ce n'est pas un nouveau passage du skin
natif ou du rendu. Rapport `.analysis/rigid-hand-surfaces-v7-postblend-20260927.json`.
La racine, les doigts, les pouces, les échelles et l'équipement sont préservés.

La candidate ZK-383 v9 a aussi ses preuves natives propres : **18 lectures,
18 séquences, 1 110 instants, 2 220 palettes, 4 440 observations**. Écart de
pose nul ; palette `2,384185791e-7`, poignets aux clés `1,164748190e-7`, entre
clés `0,0000806768383`, **zéro dépassement du seuil brut**. Après correction
hors jeu : `1,228679178e-7`. Rapport `.analysis/rigid-hands-native-zk383-v9-20260927.json`.
Ces chiffres concernent ZK-383 seulement et ne qualifient pas sa posture.

## Associations de ressources

### MG34 v10 : sortie/rangement linéaires — 28 septembre 2026

Le profil séparé `modern-rigid-hand-grips-mg34-linear.json` remplace seulement
le mouvement de racine MG34 dans Arm/Disarm par une translation moderne
`[0,-0.04,-0.12]`, orientation de prise conservée. Les prises, doigts, coudes,
modèles, autres clips et profils FG42/ZK-383 ne changent pas. Empreinte JSON
canonique : `87d9f527feec4f2e7dcfdfad9e761782fbe4c8f83afdc08bd92a08609b2c9c91`.
Le profil général v7 demeure disponible ; les anciens rapports restent historiques.

La banque privée `MG34_HandFPV_v10` comporte 18 clips et 16 aperçus. Les vues
Arm/Idle et les détails Arm ont été examinés ; le cadrage reste diagnostique
et la posture n'est pas déclarée naturelle ou qualifiée en jeu.

- Surfaces brutes : **1 010 poses, 33 330 contrôles pose/pièce, zéro traversée,
  aucune des 33 pièces omise**. Rapport `.analysis/rigid-hand-surfaces-mg34-v10-dense-20260928.json`.
- Natif isolé : **18 lectures, 18 séquences, 1 046 instants, 2 092 palettes,
  4 184 observations**. Écart pose nul ; palette `2,980232239e-7`, poignets aux
  clés `1,603257649e-7`, entre clés `0,0000622360041` : **zéro dépassement**
  du seuil inchangé `0,0002`, contre 36 pour MG34 v7. Après correction hors
  jeu, `1,645983209e-7`. Rapport `.analysis/rigid-hands-native-mg34-v10-20260928.json`.

Cette amélioration n'établit pas la continuité pendant le mélange de clips.
`rigid_hand_transition_audit.py` contrôle séparément 13 couples d'animations,
trois phases d'interruption (début, milieu, fin), cinq poids et le détachement
de la source. Ces horaires sont des **entrées diagnostiques**, pas des
transitions toutes démontrées atteignables dans le client.

Sur MG34 v10, les deux variantes totalisent **78 séquences, 546 instants,
1 092 palettes, 2 184 observations**. **72 instants dépassent le seuil brut**,
maximum `0,009477966838` lors d'une interruption Arm → Idle. Le correcteur
hors jeu ramène le maximum à `1,527600945e-7` ; poses natives/référence identiques,
palette `2,384185791e-7`. Rapport `.analysis/rigid-hand-transitions-mg34-v10-native-20260928.json`.
Les surfaces mélangées ne sont pas contrôlées par ce banc. Le correcteur n'est
pas installé, les poses corrigées ne sont pas réécrites dans la banque.

```powershell
.\.venv\Scripts\python.exe tools/rigid_hand_transition_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix HandFPV_v10 --profile experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips-mg34-linear.json --case MG34 --native --json-output .analysis/mg34-transitions-neuves.json
```

### Groupes isolés antérieurs

`build_rigid_weapon_resource_lab.py` prépare six groupes isolés, une variante
de mains à la fois. Treize états sélectionnent les neuf clips ; les états
inutilisés ont des canaux vides, sans faux événements de tir ou de recharge.
Les emplacements **de laboratoire seulement** 362 / 363 / 364 et groupes
462 / 463 / 464 sont libres dans les tables d'archives épinglées contrôlées.
Cela ne réserve aucun identifiant à l'échelle du jeu installé ou d'autres mods.

Les six laboratoires v2, puis les six laboratoires v4 reconstruits, ont chacun
exécuté **234 demandes natives et 54 chargements d'animations**. Douze fichiers privés chacun, aucun modèle commercial de
mains, aucune table centrale ni descripteur Item/Weapon. Les groupes H/R
sont mutuellement exclusifs et doivent correspondre aux mains réellement
chargées. Les anciennes ressources et emplacements commerciaux sont intacts.

## Reproduction et suites

```powershell
.\.venv\Scripts\python.exe tools/build_rigid_weapon_hand_bank.py --case MG34 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name MG34_HandFPV_v99 --previews
.\.venv\Scripts\python.exe tools/rigid_weapon_hand_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix HandFPV_v99 --case MG34 --json-output .analysis/mg34-surfaces-neuf.json
.\.venv\Scripts\python.exe tools/build_rigid_weapon_resource_lab.py --case MG34 --hand H --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank .analysis/modern-assets/MG34_HandFPV_v99 --output-name MG34H_RessourcesNeuves
```

Ajouter `--dense` pour toutes les clés et demi-clés des surfaces, ou `--native`
pour les routines natives d'animation/palettes, qui nécessitent les dépendances
privées d'émulation. Chaque sortie doit être neuve. Le jeu personnel est lu
uniquement ; aucun lancement ou installation n'est effectué.

Restent des réalisations : prise droite ZK-383, contacts fins et
auto-intersections, gestes distincts de recharge/enrayage, transitions,
raccordement du correcteur, chargement/copie FPV en scène, cadrage, événements,
lecture des sons, comportement, inventaire,
IA, sauvegarde et réseau. La Garota n'est pas couverte par ces banques.
Les descripteurs et associations sont désormais réunis dans une
[préparation commune désactivée](ASSEMBLAGE_ARMES_COMMUN.md) ; cela ne réalise
pas leurs raccordements de jeu.
