# ZK-383 : banque originale de mouvements des pièces

**27 septembre 2026.** Neuf animations visuelles réalisées sur le
[modèle extérieur moderne](MODELES_MODERNES.md). Ni animation de mains,
interaction Garota, logique d'arme ou installation n'est introduite.

## Réalisation

`modern-zk383-animation.json` définit les mouvements de la racine, d'un pivot
de chargeur et d'un pivot de pièces mobiles. `tools/build_zk383_animation_bank.py`
utilise le compilateur partagé en verrouillant le modèle original et le nom
court `ZK3`. Celui-ci est un alias technique moderne du ZK-383, pas une ressource
historique retrouvée. Les neuf noms `PROTOTYPE_ZK3_*` respectent la limite de
dix-neuf caractères des noms courts natifs.

| Séquence | Dernière frame d'auteur | Rôle visuel |
| --- | ---: | --- |
| Idle1 | 60 | Présentation au repos, boucle fermée |
| Aim / Daim | 12 / 12 | Aller/retour vers une pose de présentation, pas une caméra calibrée |
| Arm / Disarm | 24 / 24 | Apparition et retrait |
| Shot / AimShot | 10 / 10 | Impulsion visuelle, aucun tir émis |
| Rel | 80 | Déplacement décoratif du chargeur et des pièces mobiles |
| Jammed | 32 | Geste illustratif, aucun état d'enrayage implémenté |

Ces gestes ne constituent ni une simulation mécanique ni une procédure réelle
d'utilisation. Le taux de 24 images/s n'est utilisé que pour l'aperçu d'auteur ;
aucune équivalence avec les secondes du moteur n'est affirmée.

La nouvelle hiérarchie contient 41 nœuds, dont deux pivots ajoutés, et trois
pistes par clip. Les matériaux, sommets, faces et deux LOD restent identiques.
Seuls parentés et décalages locaux nécessaires aux pivots changent ; un test
compare **tous les autres octets** de chaque nœud aux données modernes source.
Le repère de chargeur suit sa pièce, mais logement, bipied et repère d'appui
restent attachés au corps. Le bipied n'est pas animé dans cette banque.

Empreinte du rig :
`435af83a166304d70565cb6fe3b354547ae3dc1e82c499291a074e18cbd12af8`.
Les sorties privées `.analysis/modern-assets/ZK383Animations_v1` comprennent
27 fichiers : un rig désactivé, neuf paires 4DS/5DS désactivées, six aperçus,
une planche et un manifeste. La planche de six poses `Rel` a été inspectée.
Le drapeau de compagnon automatique des neuf modèles n'est pas une preuve
que le chargeur de modèle en jeu l'exécute correctement.

## Contrôles réalisés

Huit tests nouveaux, sans installation commerciale : alias, pistes, empreinte,
géométrie de repos, parentés des pièces, raccords entre clips, boucle,
**537 poses entières et demi-entières**, refus d'une autre géométrie ou de
champs fonctionnels, sorties désactivées et refus d'écrasement. Il existe
273 poses entières dans les neuf séquences, bornes incluses.

Le rapport privé `.analysis/zk383-animations-native-20260927.json` exécute
les routines épinglées de `LS3DF.dll` dans des mémoires isolées et bornées :

- neuf lectures natives de 5DS avec résolution des noms et relocalisation ;
- 146 séquences d'attachement, 466 opérations, 438 allocations et 438 libérations ;
- vingt séquences de mise à jour, 180 instants, 426 appels de pose et 798 canaux écrits ;
- écart maximal des poses natives par rapport à la référence : **zéro**.

Les poses initiales sont des graines explicites de diagnostic. Les routines
de lecture, d'attachement et de temps utilisent des émulateurs séparés ; ni
bibliothèque chargée par le système, ni scène, rendu, skin de personnage,
événement ou callback ne sont exécutés. Aucune clé ou géométrie commerciale
n'est utilisée dans cette banque, même si le code natif commercial épinglé est
lu pour l'audit. Le jeu personnel reste intact et fermé.

```powershell
.\.venv\Scripts\python.exe tools/build_zk383_animation_bank.py --output-name ZK383Animations_Nouveau
.\.venv\Scripts\python.exe tools/build_zk383_animation_bank.py --native-library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --native-report .analysis/zk383-natif-nouveau.json
```

La seconde commande exige les dépendances privées d'émulation et un chemin
de rapport neuf. Elle ne lance pas le jeu et n'écrit pas dans son installation.

## Reste à implémenter

Mains et repère FPV, cadrage, gestes coordonnés de rechargement, événements,
sons, descripteurs additifs, comportement d'arme, sauvegarde et réseau.
Les états de cette banque sont des choix d'auteur : ils ne réservent aucun
Item/Weapon, groupe d'animation ou emplacement de munition dans le jeu.
La Garota conserve pour le moment son seul extérieur statique distinct.
