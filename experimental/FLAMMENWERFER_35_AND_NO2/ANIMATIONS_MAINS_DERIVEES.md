# Clips natifs dérivés de mains et équipement

**27 septembre 2026. DÉRIVÉ MODERNE, privé, désactivé.**
Les [prises modernes](PRISES_MAINS_DERIVEES.md) sont encodées en banques 5DS :
deux équipements × deux variantes de mains × neuf séquences, soit **36 clips**.
Cette construction n'est toujours ni une arme jouable ni un chargement FPV qualifié.

## Construction et provenance

Chaque clip contient **49 pistes** : 37 cibles de mains, les onze pistes de
l'assemblage moderne et une translation constante de sa racine. Les six
rotations bras/avant-bras/poignets sont calculées à chaque frame entière ;
seuls les canaux réellement constants sont réduits à deux clés. Positions
et échelles locales des mains restent celles du squelette de repos, sans
allongement de membre.

Les 36 clips utilisent les squelettes commerciaux sous empreinte ; leurs
transformations de repos sont donc **privées et dérivées**, même lorsque le
mouvement est inventé. Aucun modèle de main, texture ou animation historique
n'est exporté. Le modèle d'équipement reste entièrement moderne et inchangé.
Son encodage d'origine et celui des clips dérivés ont des portes de provenance
distinctes ; les noms de joints avec espaces ne sont pas autorisés dans
l'ancien constructeur de ressources entièrement originales.

Les clés natives de la pièce tenue et du tuyau sont reprises **sans
renormalisation ni conjugaison supplémentaire**, avec comparaison exacte après
relecture. Les fichiers font 7 464 à 13 987 octets, sous les limites du banc
natif. Les deux variantes ont leur propre banque, jamais une animation
partagée supposant leurs squelettes identiques.

## Correction détectée par le contrôle natif

La première construction utilisait l'interpolation géométrique idéale des
aperçus. Le contrôle natif a refusé un écart de poignet de **2,29 × 10⁻⁵**
dès la première frame du repos allemand. Dans le moteur vérifié, un quaternion
dont la composante scalaire arrondie atteint 1 donne une matrice identité,
même lorsque ses autres composantes ne sont pas nulles.

La génération prend désormais ses cibles dans la référence numérique native
de pose et de matrice, y compris cette règle. La tolérance aux clés n'a pas
été élargie. Un test synthétique/moderne reproduit cette différence ; aucune
donnée commerciale n'est nécessaire pour ce test.

Un second contrôle a isolé le glissement entre clés pendant Arm/Disarm.
La rotation minimale de chaque os par rapport au repos faisait varier trop
rapidement sa torsion. La banque résout maintenant cette liberté par le plan
de flexion du bras. Sur les 36 clips, la référence numérique ramène l'écart
intermédiaire maximal de **8,04 × 10⁻⁴ à 1,57 × 10⁻⁴**, sans changer durée,
trajectoire de l'équipement, position locale ou longueur d'un os.
La méthode minimale du premier lot d'aperçus reste disponible et inchangée.

## Validation

Dix tests supplémentaires couvrent provenance, espaces de noms, conservation
des clés modernes, cuisson dense, réduction des constantes, refus d'étirement,
limites natives et petites rotations. La copie de publication passe **928 tests
sur 929**, avec un test optionnel ignoré ; ce lot passe 932 sur 933 dans
le dossier local qui contient aussi des travaux distincts.
Quatre nouvelles planches privées ont été inspectées à partir des clips
sérialisés, dont une pose Arm à la frame 13,5. Les doigts/pouces et la caméra
ne sont pas déclarés qualifiés par cette inspection géométrique.

Le banc fait avancer mains, tenue et tuyau dans **le même contrôleur et la même
mémoire de poses**, puis vérifie séparément palettes et skins. Il compare les
poignets aux repères effectivement calculés par le moteur, aux clés et entre
clés, ainsi que les raccords des deux LOD de tuyau. Le contrôle couvre les
**36 séquences, 2 316 mises à jour persistantes, 173 700 poses de nœuds,
2 393 586 sommets de mains et 2 001 024 sommets de tuyau**.

Écarts maximaux : lecture/pose **0**, palette **2,99 × 10⁻⁷**, skin **0**,
poignet aux clés **1,35 × 10⁻⁷**, poignet entre clés **1,57 × 10⁻⁴** ;
raccord de tuyau tenu **5,27 × 10⁻⁸**. Les 4 632 cibles de poignet passent
les limites distinctes de 5 × 10⁻⁶ aux clés et 2 × 10⁻⁴ entre clés.
Rapport privé : `.analysis/modern-hand-animation-native-20260927.json`.

Ce ne sont pas des appels au jeu, au chargeur de scène ou au rendu. Les
poses persistent à l'intérieur de chaque séquence, mais le changement
de clip pendant la lecture n'est pas encore exécuté dans ce banc.

## Reproduction privée

```powershell
.\.venv\Scripts\python.exe tools/build_equipment_hand_animation.py --case F35 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --previews --output-name F35_HandMotion_nouveau
.\.venv\Scripts\python.exe tools/build_equipment_hand_animation.py --case F2 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --previews --output-name F2_HandMotion_nouveau
.\.venv\Scripts\python.exe tools/hand_animation_native_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/modern-hand-animation-native_nouveau.json'
```

Les banques actuelles sont `F35_HandMotion_v4` et `F2_HandMotion_v4`, sous
`.analysis/modern-assets/`. Chacune contient dix-huit clips désactivés, un
modèle moderne désactivé, douze images, deux planches et un manifeste, soit
34 fichiers. Aucun compagnon de chargement automatique n'est créé.
Les versions v1/v2 antérieures aux corrections sont conservées comme essais
non qualifiés ; les v3 contiennent les mêmes clips que v4, sans aperçus.

## Travail restant

Raccorder effectivement le modèle au contrat FPV chargé, calibrer la caméra,
les proportions et la visibilité ; affiner pouces et contact des doigts.
Les transitions, événements, effets, sons, attache dorsale joueur/IA et
fonctionnement d'arme restent des travaux distincts. Les séquences Rel/Jammed
restent des gestes de présentation, pas une recharge ou un déblocage fonctionnel.
Les 304 contrôles moteur des missions ne couvrent pas ces nouveaux assets.
