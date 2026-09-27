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
aux clés de position `fpv_weapon` ; les autres canaux d'équipement sont
conservés. La révision v3 ajoute pour MG34 un décalage moderne de rangement
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

**Version candidate actuelle : v4.** Le coude ZK-383 ne change donc que dans
`Arm`/`Disarm`, avec une courbe réversible qui retrouve la prise normale à
l'arrivée au repos. Les dernières marges de doigts ont été ajustées sans
changer les modèles. Sur les **162 poses v4**, zéro triangle/cellule pénétrant
à la tolérance fixée, aucune pièce omise. Rapport privé :
`.analysis/rigid-hand-surfaces-v4-20260927.json`. Les vues rapprochées de sortie
MG34/ZK-383 de la variante R ont aussi été inspectées. Ce résultat n'établit
ni prise naturelle, ni absence d'auto-intersection, ni qualité de cadrage.
Le contrôle dense de toutes les clés/demi-clés est lancé séparément.

Le filtrage accéléré des triangles utilise leurs boîtes complètes, préparées
une seule fois par pose. Seuls les couples triangle/cellule disjoints sont
écartés ; les autres passent toujours par la troncature exacte. Un test
compare compte, aire et profondeur avec le parcours non filtré, y compris
pour des triangles traversants et des coutures de cellules.

La prise droite ZK-383 garde deux doigts insuffisamment proches. Un second
ajustement réduisait légèrement l'objectif global mais augmentait la
pénétration maximale sondée : **il n'est pas adopté**. Un objectif numérique
plus petit ne constitue pas automatiquement une meilleure prise.

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
natif complet v4 de cette politique est en cours ; les anciens rapports ne
sont pas réétiquetés comme preuve de cette nouvelle politique.

## Associations de ressources

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
raccordement du correcteur, chargement/copie FPV en scène, cadrage, associations
et descripteurs additifs complets, événements, sons, comportement, inventaire,
IA, sauvegarde et réseau. La Garota n'est pas couverte par ces banques.
