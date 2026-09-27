# Calcul natif des rotations et des canaux d'animation

**27 septembre 2026.** Les calculs ci-dessous sont exécutés dans une émulation
x86 bornée, pas par chargement d'une DLL Windows. Ils complètent les
[preuves de convention 4DS/5DS](ROTATIONS_NATIVES.md). Ils ne constituent ni
une lecture complète de scène, ni une arme jouable ou une validation en jeu.

## Source et périmètre de sécurité

La bibliothèque personnelle `LS3DF.dll` examinée comporte **864 256 octets**,
SHA-256 `12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee`.
Toute autre version est refusée avant import des dépendances d'émulation.
L'image PE32, sa base `0x10000000`, trois exports et les constantes numériques
sont vérifiés. `LS3DRF.dll` n'est pas assimilée à cette version.

- Aucun point d'entrée, TLS, import Windows, chargeur, pilote ou jeu exécuté.
- Instructions limitées à chaque calcul et à ses auxiliaires mathématiques
  examinés ; aucun gestionnaire d'exception externe admis.
- Bibliothèque en lecture/exécution, entrées en lecture seule ; écritures
  limitées à la pile synthétique et à la sortie exacte de la phase.
- Budget de 2 048 instructions et une seconde par appel, conventions d'appel
  et préservation intégrale des entrées contrôlées.
- Le contrôle x87 **0x027f est imposé au banc** : il ne prouve pas l'état de
  tous les threads du jeu. Les références Python ne sont pas un émulateur x87
  universel ; leurs résidus sont mesurés sur les corpus décrits ci-dessous.

## Matrice et interpolation de quaternion

`SetRot` (`0x1002d260`, auxiliaire `0x1002d450`) et l'opérateur de vecteur
(`0x1002ea40`) confirment le sens de rotation déjà établi par les matrices de
repos. Le quaternion est XYZW natif, sans normalisation implicite. Si
`abs(w) >= 1`, le constructeur retourne l'identité, même si de petites
composantes XYZ subsistent après arrondi float32.

`S_quat::Slerp` (`0x100302e0`) choisit l'antipode droit si le produit scalaire
est négatif. Le branchement sphérique s'applique lorsque
`1 - abs(dot) > 0.0001` ; sinon les poids sont linéaires. Le résultat **n'est
pas renormalisé**. Le booléen historique n'est pas lu dans la routine revue ;
ses deux valeurs concordent sur les 180 contrôles. Aucun sens supplémentaire
n'est attribué à ce paramètre.

Les aperçus modernes conservent leur interpolation normalisée, explicitement
distincte : ils ne sont pas présentés comme une reproduction numérique exacte
du lecteur natif entre les clés.

## Un canal, avant tout mélange de pistes

| Canal | Début examiné | Arrêt avant mélange | Sortie |
|---|---|---|---|
| Rotation | `0x1001f0fa` | `0x1001f1cf` | quaternion XYZW |
| Position | `0x1001ef37` | `0x1001f015` | trois composantes |
| Échelle | `0x1001f2c7` | `0x1001f3a5` | trois composantes |

Le temps fourni au calcul est un entier non négatif. La sélection des clés
utilise `temps / 40`, tronqué, puis un indice sur 16 bits. Le banc refuse
les valeurs supérieures à **2 621 439**, avant rebouclage de cet indice.
Une clé unique est conservée ; avant la première ou après la dernière,
l'extrémité correspondante est maintenue. Les intervalles irréguliers sont
traités avec leurs véritables repères, sans densification préalable.

Le facteur est le float32 **0.02500000037252903**, pas une division exacte
par 40. La fraction de rotation est stockée en float32 avant Slerp. Pour
position/échelle, elle reste dans la pile de calcul jusqu'au stockage des
trois composantes interpolées. Les vecteurs ne sont pas normalisés.

**40 unités par repère ne prouvent pas 40 millisecondes ni 25 images/seconde.**
Le producteur du temps, ses conversions et la vitesse de lecture ne sont pas
qualifiés. Les 24 images/seconde de nos aperçus modernes restent un choix
de présentation, sans valeur de preuve sur le jeu.
Le [contrôleur temporel isolé](TEMPS_ANIMATION_NATIF.md) établit séparément
le calcul de durée et les limites/boucles, toujours sans qualifier l'horloge.

Le domaine borné accepte 1 à 180 clés ordonnées, repères 0 à 65 535, vecteurs
de composantes dans [-10, 10], quaternions natifs presque unitaires. L'écart
admis sur leur norme au carré est 2 × 10⁻⁵ : les clés commerciales atteignent
1,005 × 10⁻⁵. Elles ne sont jamais corrigées ou normalisées silencieusement.
Ces bornes de sécurité ne sont pas annoncées comme les limites du format.

## Résultats reproductibles

Le rapport privé `ls3d-math-native-v3-20260927.json` conserve :

- 32 rotations et 128 transformations de points ; résidus maximaux
  **5,161 × 10⁻⁸** et **1,181 × 10⁻⁷** ; huit raccourcis identité.
- 180 interpolations : 120 sphériques et 60 linéaires ; résidu nul sur ce
  corpus, écart maximal à la norme au carré **4,900 × 10⁻⁵**.
- 49 échantillons de canaux de rotation, et 98 de position/échelle ; résidu
  nul. Clés uniques, paires, intervalles irréguliers, 180 clés et limite
  16 bits inclus ; arrêts avant mélange vérifiés.

Sur les neuf animations Benelli épinglées, le rapport privé
`benelli-native-rotation-samples-20260927.json` vérifie **224 canaux,
5 167 clés et 20 220 échantillons**, aux clés, de part et d'autre et au milieu
des intervalles. Résidu nul sur ce corpus. L'écart maximal à la norme au carré
du résultat atteint **4,929 × 10⁻⁵**, conservé tel quel.

Le rapport `benelli-native-vector-samples-20260927.json` contrôle séparément
**190 canaux de position / 1 376 clés / 5 124 échantillons**, et **11 canaux
d'échelle / 22 clés / 66 échantillons**. Résidu nul dans les deux cas ; aucun
canal absent n'est créé pour gonfler ces comptes.

Les rapports exportent comptes, empreintes et résidus, **pas les valeurs des
clés commerciales**. Les tests du dépôt utilisent uniquement des données
inventées ; leurs doubles de référence ne constituent pas une preuve native.
Vingt-neuf tests nouveaux couvrent références numériques, domaines bornés,
arrêts avant mélange et refus des reçus incomplets ou non finis.

## Outils et suites nécessaires

```powershell
.\.venv\Scripts\python.exe tools/ls3d_math_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/calcul-natif-nouveau.json'
.\.venv\Scripts\python.exe tools/benelli_rotation_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/rotations-benelli-nouveau.json'
.\.venv\Scripts\python.exe tools/benelli_vector_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/vecteurs-benelli-nouveau.json'
```

Chaque nom de rapport doit être neuf : aucun résultat antérieur n'est écrasé.
Ces outils lisent l'installation personnelle, sans l'écrire.

L'[assemblage des poses partielles](POSES_PARTIELLES_NATIVES.md) est maintenant
recoupé sur un objet synthétique et un domaine restreint. Il confirme notamment
la normalisation lors de l'application, après l'interpolation non normalisée.
Restent distincts : initialisation et pilotage réels de ces canaux,
héritage des poses Benelli en situation réelle, application au modèle chargé, déformation des mains,
liaison caméra, événements, sons et comportement de l'arme. Aucun prototype
n'est activé ou promu sur la seule base de ces calculs.
