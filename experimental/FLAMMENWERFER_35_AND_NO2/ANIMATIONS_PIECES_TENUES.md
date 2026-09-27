# Mouvements modernes des pièces tenues

**MODERNE, 27 septembre 2026. Dix-huit séquences natives désactivées.**
Les pièces tenues des [six composants séparés](COMPOSANTS_MODERNES.md) ont
chacune neuf mouvements originaux. Ni géométrie ni clé d'animation commerciale
n'est incorporée. Les sources statiques, sacs et tuyaux restent inchangés.

Les recettes [Flammenwerfer 35](modern-flmwr35-held-animation.json) et
[Portable No. 2](modern-flmthr2-held-animation.json) contrôlent un unique pivot
moderne, centré sur la prise droite. Tous les maillages et quatre repères de
la pièce tenue suivent ce pivot ; la racine conserve sa pose d'identité.
Ce repère n'est pas un os de personnage ni une calibration de caméra.

| Étiquette native | Fin, en indice de trame | Contenu moderne |
|---|---:|---|
| Idle1 | 60 | Tenue légèrement mobile, boucle |
| Aim / Daim | 12 / 12 | Levée et retour de présentation |
| Arm / Disarm | 24 / 24 | Entrée et sortie de présentation |
| Shot / AimShot | 24 / 24 | Tenue légèrement mobile, boucles sans tir |
| Rel | 64 | Abaissement et retour, **pas un rechargement fonctionnel** |
| Jammed | 32 | Inspection visuelle, **pas une mécanique d'enrayage** |

Les étiquettes reprennent les emplacements de la banque, pas des fonctionnalités
réalisées. Aucun recul balistique, débit, flamme, son, dégât ou événement n'est
créé. Les trames ne sont pas présentées comme une durée en secondes du jeu.
Les raccords repos/levée/retour et débuts/fins de boucle sont contrôlés.

## Construction et contrôles

Le générateur partage l'encodeur des [banques FG42/MG34](../RECONSTRUCTION_BACKLOG/ANIMATIONS_MODERNES.md).
Il exige l'empreinte du composant tenu, le groupe exact et la provenance moderne.
Les positions de recentrage sont déjà dans les nœuds natifs : les sommets
locaux originaux sont employés, sans appliquer cette translation une deuxième fois.
Les premières et dernières vues retrouvent les images des composants statiques.

Dix tests nouveaux vérifient les dix-huit clips, leurs deux pistes, les 570 poses
entières, les quinze/seize nœuds, les raccords, les refus, la conservation des
sources et les sorties sans écrasement. Les deux planches de six poses ont été
inspectées ; elles ne montrent ni mains ni tenue dans une caméra du jeu.

L'audit natif séparé réemploie l'[attachement](../RECONSTRUCTION_BACKLOG/ATTACHEMENT_ANIMATION_NATIF.md)
et le [contrôleur unifié](../RECONSTRUCTION_BACKLOG/CONTROLEUR_POSES_UNIFIE.md) :

- 292 séquences, 932 opérations et 584 allocations/libérations d'attachement ;
- 40 séquences de temps, 360 mises à jour, 568 appels de pose et 1 064 canaux écrits ;
- résidu maximal nul sur les poses comparées.

Le code commercial épinglé est exécuté en émulation bornée, jamais chargé par
Windows. L'allocateur est un double contrôlé et la pose initiale une condition
explicite. Chargeur natif, événements, skin, caméra, rendu et scène sont exclus.
Ce résultat ne démontre pas le chargement ou la jouabilité dans le moteur.
Rapport privé : `.analysis/modern-equipment-native-animation-20260927.json`.

## Reproduction

```powershell
.\.venv\Scripts\python.exe tools/build_modern_equipment_animation.py --case F35 --output-name F35_HeldMotion_nouveau
.\.venv\Scripts\python.exe tools/build_modern_equipment_animation.py --case F2 --output-name F2_HeldMotion_nouveau
.\.venv\Scripts\python.exe tools/equipment_animation_native_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/modern-equipment-native-animation_nouveau.json'
```

Omettre le nom de sortie pour compiler uniquement en mémoire. Les lots privés
`F35_HeldMotion_v1` et `F2_HeldMotion_v1`, sous `.analysis/modern-assets/`, contiennent
chacun 27 fichiers : un rig, neuf modèles compagnons, neuf clips, six aperçus,
une planche et un manifeste. Tous les fichiers natifs portent `.disabled`.

Empreintes des rigs :

- F35 : `ff9a8f3e649f91ef5556fb5dd148c53862985ad6c993d1aa862505e599b9e299` ;
- F2 : `d7fff8ff80378350be9487e5720041c6613156bd34c3c85410495bcb54921bab`.

## Réalisations encore nécessaires

Les [tuyaux déformables synchronisés](TUYAUX_ANIMES_MODERNES.md) sont maintenant
créés pour ces séquences, avec sac fixe, sans solveur physique ou liaison joueur.
Mains et gestes de personnage, attaches dorsales/joueur/IA,
transformations FPV, cycle fonctionnel et sonore, effets, entrée additive et
sauvegarde restent distincts. **Il ne reste pas seulement des tests pour ces armes.**
L'installation personnelle, les tables, Flak TMP et les munitions 207/208 ne
sont pas modifiés ; aucune arme ni partie n'est lancée.
