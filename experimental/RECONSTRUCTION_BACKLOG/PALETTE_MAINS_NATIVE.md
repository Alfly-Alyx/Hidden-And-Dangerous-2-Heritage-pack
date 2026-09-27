# Assemblage natif des matrices des mains

**27 septembre 2026.** Après le [calcul de déformation](DEFORMATION_MAINS_NATIVE.md),
le banc exécute maintenant la construction des matrices depuis des poses locales,
la remontée des parents et la composition avec les matrices inverses de repos.
Il utilise des objets synthétiques reproduisant le domaine examiné des mains ;
aucun modèle n'est chargé par le moteur et aucune partie n'est lancée.

## Contrat observé et exécuté

Dans la bibliothèque `LS3DF.dll` épinglée (même empreinte que les autres bancs),
le segment `0x1005307a…0x10053172` prépare la palette. Les branches de parent
`0x1005327f…0x10053311` restent accessibles, ainsi que trois calculs examinés :

- `0x1001b8f0` : construction de la base locale et application des échelles ;
- `0x1002d450` : base de rotation à partir du quaternion XYZW natif ;
- `0x1002d830` : multiplication de matrices affines avec stockage float32.

Les positions sont déjà présentes dans la matrice locale de l'objet synthétique.
Le constructeur de rotation n'efface pas cette translation. Les échelles portent
sur les trois lignes de la convention native à vecteurs-lignes. Le quaternion
n'est pas normalisé par ce constructeur, et son raccourci `abs(w) >= 1` subsiste.

Chaque os est traité dans l'ordre de son identifiant, pas dans l'ordre physique
des nœuds du fichier. Sa matrice locale est multipliée par ses ancêtres ; si la
matrice d'un parent est déjà calculée, ce cache est réutilisé. Le banc couvre
les parents avant **et après** leurs enfants. L'ordre des produits et des arrondis
est conservé dans la référence indépendante.

Dans le domaine des mains, un ancêtre de type visuel 1 termine cette remontée :
sa transformation n'est pas incluse dans la palette relative. Les tests n'étendent
pas cette conclusion à tous les types de cadres ou à tous les espaces du rendu.
Le produit final est `inverse_repos × matrice_joint` en convention native ;
la translation et la rotation ne sont pas commutatives.

## Confinement

Les entrées et les liaisons synthétiques sont contrôlées : 1 à 64 joints, aucune
boucle parentale, positions finies dans ±10, quaternions proches de l'unité,
échelles de 0,01 à 2. Les matrices composées sortant de ±10 sont refusées avant
l'exécution. Il s'agit de bornes de banc, pas des limites annoncées du moteur.

Les seules écritures permises sont la pile, les trois lignes de base locale,
les champs de cache explicitement suivis et les matrices de la palette native
temporaire `0x100bf3e0`. Les pages de données concernées sont non exécutables.
Positions, quaternions, échelles, parents et champs étrangers sont comparés
après calcul. Tout saut hors des segments revus est refusé, notamment l'accès
GPU, la récupération depuis une rotation matricielle et le traitement d'un os
manquant. Le banc s'arrête **avant** la manipulation des buffers de rendu.

Budget : `4 096 + 800 × joints²` instructions, cinq secondes par appel.
Contrôle x87 synthétique 0x027f ; tolérance numérique maximale de 5 × 10⁻⁵.
Aucun point d'entrée DLL, TLS, import Windows, chargeur ou pilote appelé.

## Résultats

`ls3d-native-palette-20260927.json` : **46 cas**, **748 joints**, **4 030 produits
matriciels** et **313 réutilisations d'ancêtres**. Chaînes, étoiles et forêts,
deux ordres d'identifiants, 64 joints, rotations et échelles non uniformes.
Le résidu maximal est de **3,807 × 10⁻⁸**.

`benelli-native-palette-20260927.json` raccorde ce calcul au noyau de peau :

| Main | Poses locales | Joints évalués | Sommets déformés |
|---|---:|---:|---:|
| fpv_hands | 37 | 1 332 | 36 667 |
| fpv_hands_r | 37 | 1 332 | 39 812 |

Soit **74 poses, 2 664 joints et 76 479 sommets**. Par main, une pose de repos
et 36 diagnostics remplaçant volontairement une rotation locale. Ces diagnostics
sont inventés, **pas des animations commerciales Benelli**. Les descendants
reçoivent cette transformation par la véritable remontée native de la hiérarchie.

Résidu maximal : **1,314 × 10⁻⁷** sur la palette, **nul** sur le noyau de peau
alimenté par cette palette. Le repos natif déplace les sommets d'au plus
**1,789 × 10⁻⁷** par rapport au fichier, sous la tolérance de 10⁻⁵.
Les rapports ne conservent que comptes, empreintes et résidus, aucune géométrie
ou matrice commerciale. Quatorze nouveaux tests synthétiques ne nécessitent
aucune ressource du jeu.

## Reproduction et limites restantes

```powershell
.\.venv\Scripts\python.exe tools/ls3d_palette_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/palette-native-nouveau.json'
.\.venv\Scripts\python.exe tools/benelli_palette_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/palette-mains-nouveau.json'
```

Rapports neufs obligatoires ; installation personnelle en lecture seule.
La chaîne joint→palette→peau est qualifiée **sur ces entrées et dans ce domaine**.
La sélection des poses par les animations Benelli, leur initialisation réelle,
les transitions, la caméra, les événements, les sons et le rendu du jeu demeurent
distincts. Aucun prototype n'est activé ou déclaré jouable.

Le [raccordement aux canaux Benelli](CHAINE_ANIMATION_MAINS.md) est maintenant
contrôlé séparément avec une pose initiale de diagnostic explicitement fournie,
sans revendiquer la politique d'initialisation ou les transitions du client.
