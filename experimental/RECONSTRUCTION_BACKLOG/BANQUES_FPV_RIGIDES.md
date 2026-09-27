# FG42, MG34 et ZK-383 : modèles FPV rigides et clips recalculés

**27 septembre 2026.** Trois banques modernes, sans mains ni arme fonctionnelle.
Cette étape adapte les hiérarchies et les repères des extérieurs originaux ;
elle ne remplace pas le raccordement au personnage et au moteur.

## Construction

`tools/build_rigid_weapon_fpv_bank.py` part des banques de pièces originales
FG42/MG34 et [ZK-383](../GAROTA_AND_ZK383/ANIMATIONS_ZK383_MODERNES.md). Le corps
rigide `MOD_receiver` devient le visuel racine `fpv_weapon`. Les autres nœuds
deviennent ses enfants directs, pour satisfaire le parcours d'enregistrement
FPV étudié dans le client. La racine décorative vide précédente est retirée.
Ce contrat structurel ne prouve pas l'exécution réelle du chargement ou de la copie.

Avant conversion d'axes, **tous les octets des géométries et deux LOD sont
conservés**. Les positions de repos sont recalculées lors du changement de
parenté. Ensuite, le repère +Y avant/+Z haut devient +Z avant/+Y haut :
positions, rotations, normales, faces et boîtes de repères sont converties.
Le double échange des axes restaure exactement les octets du modèle aplati.
Ces banques sont entièrement rigides : aucun faux skin commercial n'est créé.

Les animations précédentes ne sont **pas compatibles** avec la nouvelle
hiérarchie. Vingt-sept clips sont donc recalculés : racine copiée avec ses axes
convertis, rotations des pivots conservées et trajectoires locales de chaque
pièce recalculées aux frames entières. Les alias `PROTOTYPE_FG42V*`,
`PROTOTYPE_MG34V*` et `PROTOTYPE_ZK3V*` distinguent les nouvelles banques.

| Banque | Nœuds / pièces rigides | Échantillons clés et demi-clés | SHA-256 du modèle FPV |
| --- | --- | --- | --- |
| FG42 | 32 / 25 | 505 | `0ae8254f8ad43678ac7e02086ffc72eff7bb03ba9a1a996eb7e85f432f1062f6` |
| MG34 | 41 / 33 | 505 | `9cc238c77e9a1a38f844977f417e802118026258a27f40103af9d680b076e672` |
| ZK-383 | 40 / 33 | 537 | `554a5721a39fffc7d65ac94fb4762a7847f233eef4a214bb9376953c4256b6ef` |

## Comparaison avec les banques source

La référence numérique reproduit les conventions natives de pose et de
composition, dont les arrondis et les petites rotations. Les **1 547 instants**
comparés couvrent chaque clé et demi-clé des vingt-sept clips ; toutes les
matrices de nœuds sont comparées dans le repère converti.

| Banque | Écart matriciel maximal aux clés | Écart matriciel maximal entre les clés |
| --- | --- | --- |
| FG42 | `2,980232239e-8` | `2,942979336e-6` |
| MG34 | `2,235174180e-8` | `0,000186076854` |
| ZK-383 | `2,980232239e-8` | `5,140900612e-7` |

Le plus grand résidu est sur le couvercle MG34, `Rel`, temps natif de diagnostic
2260. Une trajectoire de point entraîné par rotation n'est pas exactement la
droite reliant deux positions recalculées. Ce résidu est conservé dans le
rapport, **pas assimilé à zéro**. Les maxima portent sur des composantes de
matrices, sans les présenter globalement comme des millimètres. L'équivalence
continue et les mélanges de pistes ne sont pas prouvés par ces échantillons.

## Sorties, aperçus et limites

Les dossiers privés `FG42_RigidFPV_v1`, `MG34_RigidFPV_v1` et `ZK383_RigidFPV_v1`,
sous `.analysis/modern-assets`, contiennent quatorze fichiers chacun : un modèle
désactivé, neuf clips désactivés, trois PNG diagnostiques et un manifeste.
Les vues FG42 repos, MG34 présentation de rechargement et ZK-383 visée ont été
inspectées. Le repère, les pièces mobiles et l'occlusion sont lisibles ; ce
n'est pas une approbation du cadrage final.

Les aperçus ajoutent `[0.07, -0.15, 0.25]` **uniquement pour l'image**, avec un
champ horizontal de 65°. Cette translation n'est pas incorporée aux modèles
ni aux animations. Elle sert à inspecter le repère +Z ; une implantation FPV
compatible avec les mains et la caméra reste à concevoir. Les bipieds restent
dans leur présentation actuelle, sans logique de déploiement.

Sept tests nouveaux vérifient les empreintes, noms courts, hiérarchie directe,
conservation complète des géométries, conversion réversible des deux LOD,
normales/UV/faces, recalcul des trajectoires, séparation du décalage d'aperçu,
refus d'entrées inconnues et sorties désactivées. Les huit tests antérieurs
de repères lance-flammes passent également après l'extension du lecteur rigide.

`rigid_weapon_fpv_native_audit.py` vérifie séparément le chargement des clips,
leurs poses et la composition des matrices. Pour cette dernière uniquement,
les nœuds rigides sont fournis comme **articulations diagnostiques** au noyau
de palette : aucun skin réel ni chargement de ces modèles en scène n'est
prétendu. Les sous-systèmes emploient des émulateurs isolés distincts.

Audit terminé dans `.analysis/rigid-weapon-fpv-native-20260927.json` :
**27 lectures natives, 27 séquences, 1 601 instants et 1 601 palettes
diagnostiques**. Écart des poses natives/référence : zéro ; écart maximal de
composition des matrices : `5,960464478e-8`. La comparaison aux hiérarchies
source donne au plus `5,960464478e-8` aux clés et `0,000186076854` entre elles.
Les seuils de ce banc restent `5e-6` / `0,0002` ; le résidu MG34 n'est pas
masqué par la réussite des contrôles. Ni scène ni modèle natif n'est chargé.

```powershell
.\.venv\Scripts\python.exe tools/build_rigid_weapon_fpv_bank.py --case FG42 --output-name FG42_RigidFPV_Nouveau
.\.venv\Scripts\python.exe tools/build_rigid_weapon_fpv_bank.py --case MG34 --output-name MG34_RigidFPV_Nouveau
.\.venv\Scripts\python.exe tools/build_rigid_weapon_fpv_bank.py --case ZK383 --output-name ZK383_RigidFPV_Nouveau
.\.venv\Scripts\python.exe tools/rigid_weapon_fpv_native_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output .analysis/rigides-fpv-natif-nouveau.json
```

Chaque nom de sortie doit être neuf. Le générateur n'a besoin d'aucune archive
commerciale ; seul l'audit natif lit la bibliothèque épinglée et exige les
dépendances privées d'émulation. Aucun lancement ou installation.

Mains, contacts, gestes coordonnés, cadrage, associations et descripteurs
additifs, événements, sons, comportement, sauvegarde et réseau restent des
réalisations nécessaires. Les anciens modèles/animations restent intacts.
