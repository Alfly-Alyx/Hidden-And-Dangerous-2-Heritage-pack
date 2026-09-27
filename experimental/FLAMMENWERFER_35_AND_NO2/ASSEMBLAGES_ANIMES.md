# Assemblages modernes à animation unique

**MODERNE, 27 septembre 2026. Deux modèles complets de présentation, désactivés.**
La pièce tenue, le sac fixe et le [tuyau déformable](TUYAUX_ANIMES_MODERNES.md)
sont réunis dans un même 4DS. Chacune des neuf séquences utilise désormais un
seul 5DS : pièce tenue et tuyau partagent le même temps et le même emplacement
d'animation. Il ne faut plus synchroniser deux lectures indépendantes.

Ce sont des assemblages visuels complets, **pas des armes jouables, des FPV
calibrés ou des équipements rattachés à un personnage**. Le sac reste fixe
dans les coordonnées de présentation.

## Conservation et hiérarchie

| Modèle | Nœuds | Pistes par clip | Séquences |
|---|---:|---:|---:|
| Flammenwerfer 35 | 39 | 11 | 9 |
| Portable No. 2 | 37 | 11 | 9 |

Une nouvelle racine moderne contient trois sous-ensembles. Le sac et la pièce
tenue retrouvent leurs origines de présentation ; le skin du tuyau garde une
racine locale d'identité. Les indices de parent sont remappés, mais les indices
d'os internes restent inchangés.

Tous les blocs de composants sont comparés octet par octet, en neutralisant
uniquement leurs indices de parent et leurs positions de racine explicites.
Géométrie, matériaux, deux LOD, poids, inverse-binds et propriétés restent
identiques. Les tables de matériaux doivent être identiques et tous les noms
uniques ; aucune fusion ambiguë n'est acceptée.

Les clés des deux banques sont repaquetées **sans renormalisation ni nouvelle
conjugaison des rotations natives**. Seules les positions constantes de la
racine tenue sont recalées. Aucun événement, son ou effet n'est inventé.
Les banques sources restent inchangées et reproductibles séparément.

## Contrôles réalisés

Treize tests nouveaux couvrent l'assemblage, les bits des rotations, les refus
et l'observation des poses. Les 1 122 poses à demi-trame retrouvent les
transformations des composants indépendants. Les douze aperçus individuels
sont identiques par empreinte aux aperçus précédents ; les deux planches
d'assemblage ont été inspectées.

L'audit natif utilise d'abord 40 séquences de limites et de recouvrement :
360 mises à jour, 3 124 appels de pose, 5 852 canaux écrits, résidu nul.
Puis il attache les dix-huit clips un par un et avance en demi-trames :

- **1 158 mises à jour persistantes**, 44 004 poses de nœud observées ;
- 2 316 calculs de LOD, **1 000 512 sommets** déformés ;
- 500 256 sommets de raccord comparés aux composants ;
- résidus nuls pour temps/poses, skin et raccord fixe ; palette au plus
  5,97 × 10⁻⁸, raccord tenu au plus **2,58 × 10⁻⁸**.

Pièce tenue et tuyau sont réellement calculés dans la même mémoire du
contrôleur natif isolé. Les poses observées sont ensuite transmises aux
émulateurs séparés de palette et de skin. Le contrôle du repère tenu utilise
une hiérarchie diagnostique de deux joints, pas une scène rendue. Le sac et
tous les nœuds non animés conservent leur état initial.

L'observateur Python reçoit une copie détachée des valeurs validées ; il ne
s'agit pas d'un callback du jeu. La pose initiale reste explicitement fournie,
l'allocateur borné et la bibliothèque épinglée. Chargeur 4DS, callbacks,
événements, rendu et changements de clip pendant une même séquence ne sont
pas exécutés. Aucun de ces chiffres n'est une validation moteur.

Rapport privé : `.analysis/modern-equipment-assembly-native-20260927.json`.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/build_modern_equipment_assembly.py --case F35 --output-name F35_Assembly_nouveau
.\.venv\Scripts\python.exe tools/build_modern_equipment_assembly.py --case F2 --output-name F2_Assembly_nouveau
.\.venv\Scripts\python.exe tools/equipment_assembly_native_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/modern-equipment-assembly-native_nouveau.json'
```

Les lots privés `F35_Assembly_v1` et `F2_Assembly_v1` contiennent chacun un rig,
neuf couples de compagnons natifs, six aperçus, une planche et un manifeste.
Le suffixe `.disabled` reste obligatoire. Le drapeau de compagnon est écrit,
mais le chargement automatique réel n'est pas qualifié. Sans nom de sortie,
le constructeur ne fait que compiler en mémoire.

Empreintes :

- F35 : `ed213eee76c286aa9858f7d0f6e6210950fa0f0cd6566e253058d6dc40c73751` ;
- F2 : `c64d8b70809d7a760603c84cdffd6487199b27d5beb3f140d08e9a6226612055`.

## Travail restant

Les [poses de prise sur mains commerciales](PRISES_MAINS_DERIVEES.md) sont
maintenant calculées et inspectées séparément ; leur encodage natif et leur
raccordement FPV restent à réaliser. Gestes joueur/IA, attaches dorsales et
transformations de caméra restent à construire. Le tuyau ne résout ni collisions, longueur fixe ou positions
arbitraires. Événements, cycle fonctionnel, sons, effets, tables additives et
sauvegardes restent distincts. Les modèles ne remplacent ni Flak TMP ni une
arme installée ; aucune partie n'est lancée. **Il ne reste pas seulement des tests.**
