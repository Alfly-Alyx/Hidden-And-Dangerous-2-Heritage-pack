# Animations originales de pièces : FG42 et MG34

**MODERNE, 26 septembre 2026. Dix-huit séquences construites et désactivées ;
compatibilité moteur, mains et arme jouable non validées.**

Les recettes [FG42](../FG42/modern-animation-bank.json) et
[MG34](../MG34_PORTABLE/modern-animation-bank.json) décrivent des mouvements
originaux de l'arme seule. Elles ne lisent ni modèle, pose, clé, son ou
animation commerciale. Elles reprennent les géométries originales déjà
fabriquées, sans modifier leurs fichiers statiques.

## Réalisations et limites

- FG42 : deux pivots, chargeur latéral et pièces de culasse ; 33 nœuds.
- MG34 : trois pivots, tambour, poignée de culasse et couvercle ; 42 nœuds.
  Le repère d'alimentation reste fixé au corps, pas au tambour détaché.
- Les pivots sont insérés avant leurs enfants. Le décalage local opposé
  conserve la position de repos et tous les octets de géométrie des deux LOD.
  Aucun sommet commercial, squelette ou poids de peau n'est ajouté.
- Chaque séquence réinitialise tous les contrôles. Les boucles et raccords
  repos/visée/tir visé/retour/prise/retrait sont contrôlés hors moteur.
- Les trajectoires de chargeur, couvercle, recul et manipulation sont des
  choix visuels contemporains. Elles ne décrivent pas une opération historique
  certifiée. La pose de visée n'est pas calibrée à la caméra du jeu.
- Les bipieds restent fixes. Pas de mains, éjection, flash, son, note
  événementielle, projectile, recharge de munition ou consommation effective.

| Séquence | Frame terminale incluse | Alias final |
|---|---:|---|
| Idle1 | 60 | Idle |
| Aim | 12 | Aim |
| Daim | 12 | Daim |
| Arm | 20 | Arm |
| Disarm | 20 | Darm |
| Shot | 8 | Shot |
| AimShot | 8 | ASht |
| Rel | 80 | Rel |
| Jammed | 28 | Jam |

Les alias complets suivent `PROTOTYPE_FG42_…` ou
`PROTOTYPE_MG34_…` et restent sous la limite de 19 caractères, sans
troncature. Les noms de pistes désignent exactement des nœuds du modèle.

## Format et temps

Le nouvel encodeur original `tools/modern_animation.py` écrit le 5DS
v122 : positions, rotations XYZW et échelles, offsets et alignements bornés,
sans pistes d'événements. Les descriptions publiques
[5ds.bt](https://github.com/RoadTrain/mafia-formats/blob/master/5ds.bt) et
[4ds.bt](https://github.com/RoadTrain/mafia-formats/blob/master/4ds.bt) sont des
références de format, pas du code recopié.

Le banc choisit explicitement une interpolation linéaire des positions et une
interpolation quaternionique au plus court chemin, en transformations locales
absolues. **Ce choix n'est pas une preuve d'identité avec l'interpolation du
moteur.** Les 24 images/s sont uniquement un rythme de prévisualisation moderne :
le fichier natif ne démontre ni cette fréquence ni une durée de jeu équivalente.

Les 514 poses à frames entières des deux banques sont évaluées hors moteur.
Les deux planches de rechargement, six poses et trois angles chacune, ont été
inspectées. Le rendu de profondeur par pixel remplace l'ancien tri des
triangles, qui produisait des occultations erronées sur des pièces inclinées.
Il ne modifie pas les modèles ni leurs animations.

## Construction reproductible

```powershell
.\.venv\Scripts\python.exe tools/build_modern_animation_bank.py --case FG42 --output-name FG42Motion_nouveau
.\.venv\Scripts\python.exe tools/build_modern_animation_bank.py --case MG34 --output-name MG34Motion_nouveau
```

Omettre `--output-name` pour compiler et vérifier uniquement en mémoire.
Chaque dossier neuf sous `.analysis/modern-assets/` reçoit 27 fichiers :
un modèle de repos, neuf paires 4DS/5DS, six vues de poses, une planche et un
manifeste. Les ressources natives portent toutes `.disabled`.

Le modèle de repos garde le drapeau de chargement d'animation à zéro ; les
neuf modèles compagnons le portent à un, avec un 5DS du même nom présent.
C'est une préparation de format contrôlée, **pas une preuve que le chargement
automatique est validé en moteur**. Aucun déploiement ni Item n'est créé.

Empreintes des modèles articulés au repos, lots privés `FG42Motion_v2` et
`MG34Motion_v2` :

- FG42 : `531c5364f46776d53ff5e4ae4ba9033c3c736c0cfc02f8d74cb8914bb1412d18` ;
- MG34 : `e87a3403e887ddec2a792fde39eedc1968ab299e435e1490acdf32cb116c33ba`.

Chaque manifeste contient aussi les empreintes des recettes, des 18 fichiers
compagnons et des aperçus. Les lots v1 restent historiques : même géométrie
native, ancien rendu d'aperçu.

Vingt nouveaux tests : dix pour codec/pivots/interpolation, six pour banques,
raccords/export/refus, quatre pour profondeur, ordre des faces, coutures et
clipping. Les tests existants continuent à verrouiller les empreintes des
modèles statiques.

## Suites de réalisation, pas seulement de test

Créer/raccorder les mains et le squelette joueur/IA ; calibrer la vue FPV,
les prises et la tenue extérieure ; ajouter les événements et sons ; établir
les entrées additives et les comportements d'arme. Ensuite seulement qualifier
les chargements 4DS/5DS, les transitions natives, sauvegardes et hôte/client.
Les slots réutilisés par les casques restent intacts.

