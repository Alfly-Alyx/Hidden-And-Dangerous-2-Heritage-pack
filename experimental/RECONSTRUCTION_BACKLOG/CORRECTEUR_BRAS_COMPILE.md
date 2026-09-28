# Correcteur de bras compilé — laboratoire, pas raccordement moteur

**28 septembre 2026.** Le calcul de correction des six rotations de bras
dispose maintenant d'une implémentation C originale, sans API Windows,
allocation, import système ou donnée commerciale. Il est exécuté en x86
dans un émulateur borné. **Aucun hook, chargement dans le jeu, installation
ou lancement du jeu n'est réalisé par ce travail.**

## Contrat et sécurité

`native/hand_constraints.c` expose `Hd2SolveArm`, convention cdecl. Chaque
appel reçoit 60 doubles : trois couples matrice/position de repos monde,
matrice du parent clavicule, position cible du poignet, rotation active de
la main et repère de coude. Les matrices sont rangées par lignes. Le côté
vaut +1 à gauche et −1 à droite. La sortie comporte 12 doubles : rotations
locales natives XYZW conjuguées du bras, de l'avant-bras et de la main.
Les tampons appartiennent à l'appelant et sont séparés dans le laboratoire.

Les tailles, nombres finis, bornes, bases propres, longueurs et accessibilité
de la cible sont contrôlés. Les résidus d'échelle float32 des squelettes
ne sont pas effacés des sources ; les échelles de colonnes sont retirées
lors de la décomposition de sortie, comme dans la référence indépendante.
Les échecs ne modifient aucun octet de sortie. Les codes sont : 0 succès,
1 contrat/taille/côté, 2 nombres, 3 bases, 4 longueur/accessibilité,
5 configuration singulière ou décomposition impossible.

`tools/native_hand_constraints.py` vérifie l'image complète et ses trois
sections avant exécution. Les seules écritures autorisées sont la pile et
les 96 octets de résultat ; les entrées et gardes sont vérifiées intactes.
Les registres préservés par cdecl, la pile au retour et la borne d'exécution
sont contrôlés. Le point d'entrée Windows n'est jamais exécuté et refuse
par construction le chargement normal. La correction des deux bras est
préparée avant de remplacer ensemble les six rotations. Racine, clavicule,
doigts, pouces, positions, échelles et équipement restent inchangés.

## Construction reproductible et résultats

`tools/build_native_hand_constraints.py` utilise seulement le compilateur
TinyCC local déjà disponible et épinglé par SHA-256
`11b86934bb2833f57fa0453a605ca342aee9207e193faea9b973baa2b2b4c35b`.
Rien n'est téléchargé. La sortie doit être neuve et son nom de fichier reste
`hand-constraints-v1.dll.disabled` (ABI 1, pas promotion en version jouable).
L'image de 7 168 octets a pour SHA-256
`bd5d8672695b70d5cc3d0e10608316abbe75763543640d1390f97890f60a5cb7` ;
sa section de code de 5 592 octets :
`f2ff000d24ab84ded2a71c409bb61fac825c7b5ea4aac52e6990422dcedaabac`.

Douze cas inventés couvrent les deux côtés, trois cibles et des parents
orientés ou non. Ils concordent avec le calcul Python indépendant à
`8,881784197e-16` sur les matrices de rotation. Huit entrées invalides sont
refusées avec sorties intactes. Ces vingt exécutions C privées ne sont pas
confondues avec les tests unitaires synthétiques du dépôt.

Le banc de transitions MG34 v10 a ensuite exécuté **1 092 appels compilés
sur 546 poses, 78 séquences et les deux squelettes commerciaux**, lus sans
modification. Les six rotations de chaque pose sont comparées à la référence
Python : écart maximal de matrice `1,170712388e-7`, inférieur au seuil `2e-6`.
Les routines natives de palette ont été exécutées 1 092 fois avant/après.
L'écart maximal de poignet après correction vaut `1,639074114e-7`.
Les 72 dépassements bruts restent rapportés, maximum `0,009477966838`.

Rapports privés :
`.analysis/modern-assets/HandConstraints_Compiled_v1/MANIFEST.json` et
`.analysis/rigid-hand-transitions-mg34-v10-compiled-20260928.json`.
Ces poses mélangées sont diagnostiques : leur atteignabilité dans le client,
les surfaces, le skin, le rendu et le budget d'une frame ne sont pas qualifiés.

```powershell
.\.venv\Scripts\python.exe tools/build_native_hand_constraints.py --output-name HandConstraints_Neuf
.\.venv\Scripts\python.exe tools/rigid_hand_transition_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix HandFPV_v10 --profile experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips-mg34-linear.json --case MG34 --native --compiled-solver .analysis/modern-assets/HandConstraints_Neuf/hand-constraints-v1.dll.disabled --json-output .analysis/transitions-compilees-neuves.json
```

Les dépendances d'émulation doivent être disponibles pour ces commandes.
Les sources commerciales, leurs poses et les binaires privés ne sont pas
publiés. Les anciens essais privés ne sont pas remplacés.

## Réalisation suivante

Le raccordement nécessite encore un point après mélange et avant skin,
le contrat vérifié de lecture/écriture des poses et des indicateurs de mise
à jour, l'identité des six os, le filtrage des seuls équipements modernes,
la durée de vie des modèles, le comportement en cas d'échec et la réentrance.
Le succès de ce solveur autonome ne démontre aucun de ces raccordements.
