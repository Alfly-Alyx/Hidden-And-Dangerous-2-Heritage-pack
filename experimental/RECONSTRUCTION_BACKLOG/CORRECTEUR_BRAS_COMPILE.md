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
La première image historique (v1), de 7 168 octets, a pour SHA-256
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

## Application compilée et caches persistants — 28 septembre 2026

`native/arm_pose_commit.c` fournit un second composant original, distinct du
solveur. Il reçoit une arène privée bornée, six emplacements et leurs poses/
indicateurs attendus. Il vérifie tous les enregistrements avant toute écriture :
absence de recouvrement, alignement, taille, type joint 10, forme quaternion,
absence des callbacks non étudiés, poses et indicateurs inchangés. Une erreur
sur le **sixième** os laisse les cinq précédents intacts. Le résultat modifie
seulement les 24 composantes de rotation et les six indicateurs correspondants.
Ce protocole n'assure pas l'atomicité entre threads : l'arène est exclusivement
possédée par l'appelant. Il ne découvre ni ne valide des pointeurs du jeu vivant.

Le masque d'indicateurs reprend le chemin natif de pose :
`(flags & 0xfffffecb) | 0x40000008`, rotation à `+0xc0`, indicateurs à `+0xe0`.
Les autres canaux et octets restent conservés. L'image désactivée de 3 584
octets a pour empreinte
`cadf4a0bab1f3ac6c9e078f9e32e2dccaa048bf4f68183511bfdb81ce859e7e1`.
Elle ne comporte aucun import système, et son entrée Windows refuse le chargement.

`native_arm_pose_commit.py` exécute dans **la même mémoire** : palette initiale
mettant les matrices en cache → application compilée → rafraîchissement natif
récursif → nouvelle palette. Aucun os ni cache n'est réinitialisé entre ces
quatre étapes. Les objets, leurs liens et leur visuel propriétaire sont fournis
par le laboratoire ; ils ne proviennent pas d'un chargement de scène.

Les trois arbres inventés (chaîne, racines distinctes, deux branches) donnent
chacun six rotations appliquées, six matrices locales reconstruites et six
signaux de changement au visuel propriétaire. Écart maximal de matrice :
`5,960464478e-8`. Huit cas négatifs couvrent pose/indicateurs/type modifiés au
dernier os, quaternion invalide, doublon, débordement, défaut d'alignement et
callback non étudié. Toutes les arènes refusées restent entièrement intactes.
Rapport privé : `.analysis/modern-assets/ArmPoseCommit_Compiled_v1/MANIFEST.json`.

Le rafraîchissement natif `0x1001e610` et sa récursion `0x1001e550` propagent les
invalidations aux descendants. La méthode joint `0x10020ad0`, issue de la table
`0x1009b9d8`, retire les bits de cache `0x18` à `+0x164`, et signale les changements
locaux au visuel propriétaire `+0x168` (compteur `+0x218`, indicateurs `+0x1d0`).
Le parcours d'ancêtres de `0x1001e790` est exécuté. La file différée globale doit
rester vide ; ses traitements supplémentaires sont interdits dans ce banc.
Le visuel propriétaire est un enregistrement diagnostique séparé : **ses limites,
son skin et son rendu ne sont pas calculés par ce contrôle**.

Le relais de modèle `0x10034ba0` appelle le contrôleur à `0x10034bbe`, puis le
rafraîchissement du modèle à `0x10034bc6`. Cet intervalle est un **point candidat
d'insertion observé statiquement**, pas un hook installé. Le client appelle
ce relais par la méthode `+0x20` depuis `0x491fba` ; cette décision du client
n'est pas exécutée par le laboratoire de correction.

```powershell
.\.venv\Scripts\python.exe tools/build_native_arm_pose_commit.py --game 'D:\Games\Hidden and Dangerous 2' --output-name ArmPoseCommit_Neuf
```

L'option `--compiled-commit` du banc de transitions exige `--native` et
`--compiled-solver`. Elle passe les six rotations calculées au nouveau
composant, puis contrôle les matrices natives persistantes. La mémoire de
l'animation et celle de l'application/rafraîchissement restent distinctes ;
seules ces trois dernières étapes partagent les mêmes objets dans ce premier
banc. La [chaîne unifiée suivante](CHAINE_CORRECTION_UNIFIEE.md) inclut ensuite
l'animation native dans cette mémoire, sans prétendre charger une scène.

Le passage complet sur MG34 v10 est terminé : **546 poses H/R, 3 276 rotations
appliquées, 3 276 reconstructions locales et 3 276 signaux au propriétaire**.
Les nouvelles matrices natives après rafraîchissement concordent avec le
calcul indépendant à `2,384185791e-7`. Les deux variantes passent les 13 couples
de transitions et leurs trois phases. Rapport privé :
`.analysis/rigid-hand-transitions-mg34-v10-persistent-20260928.json`.
Les 72 écarts bruts d'animation restent présents avant correction ; aucun
résultat de ce banc n'est transformé en validation de scène ou de jouabilité.

## Réalisation suivante

La [chaîne unifiée](CHAINE_CORRECTION_UNIFIEE.md#correction-de-la-dérive-à-pas-nul)
a ensuite révélé un biais de cette première image lors de corrections répétées.
La source et le contrôleur courants exigent désormais l'inversion exacte v2 ;
les anciens résultats ponctuels et fichiers v1 sont conservés comme historiques,
pas réutilisés comme preuve de conservation des poses entre appels.

Le raccordement nécessite encore un point après mélange et avant skin,
le raccordement du contrat de poses/indicateurs aux objets réellement chargés,
l'identité des six os, le filtrage des seuls équipements modernes,
la durée de vie des modèles, le comportement en cas d'échec et la réentrance.
Le succès de ce solveur autonome ne démontre aucun de ces raccordements.
