# Correction de mains entièrement compilée sur objets fournis

Composant C original du 28 septembre 2026. Il réunit le calcul des cibles,
les deux résolutions de bras et l'application des six rotations dans un seul
appel `Hd2CorrectHandPose`. Il ne contient ni chargement Windows, API système,
allocation, données commerciales, installation, découverte de modèle ou hook.

## Contrat borné

L'appelant fournit une arène de nœuds, leurs offsets, 11 à 128 poses locales,
leurs parents, onze rôles, les paramètres de repos et les deux prises modernes.
Les rôles désignent la racine tenue, les deux contacts, les deux coudes puis
les six os des bras dans l'ordre gauche / droite, épaule / avant-bras / main.

Les offsets doivent être alignés, distincts, non chevauchants et contenus dans
l'arène. Les chaînes des bras et les rôles des coudes doivent correspondre.
Chaque position, rotation et échelle de l'instantané doit être identique aux
octets de son nœud courant, avant le calcul. Les bases de clavicule doivent
rester dans la tolérance du repos. La liaison au bon modèle et l'identité de
ses données de repos restent des préconditions, pas une découverte automatique.

Un espace temporaire de 7 536 octets est fourni par l'appelant, aligné sur huit
octets. Cela évite une grosse allocation sur la pile x86. Les buffers sont
distincts, valides et exclusivement possédés par l'appelant ; aucune sécurité
sur des pointeurs arbitraires ou des modifications concurrentes n'est promise.
Le composant est sans état global mutable ; deux appels ne doivent pas partager
une arène ou un espace temporaire en cours d'utilisation.

Le préparateur et les deux solveurs doivent tous réussir avant l'application.
Les rotations calculées sont converties en float32 et canonicalisées à W positif.
Le dernier composant contrôle les six nœuds avant sa première écriture. Un échec,
y compris sur le second bras ou le dernier nœud, conserve **toute l'arène**.
Seul l'espace temporaire peut changer en cas d'échec. Ce n'est pas une transaction
atomique entre threads.

## Construction et preuve indépendante

La construction compile les quatre sources C originales ensemble, sans modifier
les calculs internes des composants précédents. Les deux points d'entrée de
chargement isolés sont omis par une option de compilation ; le point d'entrée
unique refuse toujours un chargement Windows normal. Les deux constructions
isolées restent identiques octet pour octet à leurs images précédentes.

L'image `hand-pipeline-v1.dll.disabled` fait 17 408 octets et n'a aucun import.
SHA-256 : `62f1827ab5d173d9f683fc4b896a83862752219b392222ff60295f01787e2a65`.
La section de code fait 14 864 octets. Le contrôleur exige l'empreinte de l'image
complète et les quatre exports attendus avant toute instruction.

Le constructeur exécute 36 cas valides inventés : 11 ou 128 nœuds, deux positions
de parents, puis huit réapplications conservant les poses précédentes. Les
résultats sont comparés au calcul indépendant, et tous les octets étrangers aux
rotations / indicateurs autorisés sont conservés. Écart maximal de matrices de
rotation : `6,168954525e-8`.

Seize refus couvrent les tailles, offsets, rôles, chaînes, instantanés périmés,
clavicules déplacées, nombres invalides, portée impossible de chacun des bras,
type ou indicateurs du dernier nœud, callbacks interdits et quaternion nul.
Les échecs de portée confirment un ou deux appels au solveur selon le bras,
sans jamais appeler le composant d'application.

## Connexion au banc natif

Le banc `unified_hand_pose_audit.py --compiled-pipeline ...` utilise le même
processeur émulé et **les mêmes nœuds** pour les poses natives, le préparateur,
les deux solveurs, l'application compilée, le rafraîchissement et les palettes.
Le contrôleur ne recopie pas l'arène avant l'appel compilé : il vérifie qu'elle
n'a pas changé. Il ne réapplique pas les rotations par un second appel séparé.
Les références corrigées restent indépendantes, conservées d'un instant à l'autre.
Les anciens modes à processeurs séparés restent disponibles, mais ne peuvent pas
être combinés silencieusement avec ce mode.

Le corpus complet est conservé dans
`.analysis/unified-hand-pipeline-mg34-v1-20260928.json` : **80 séquences,
578 appels au composant unifié**, donc 578 préparations, 1 156 résolutions
de bras et 3 468 rotations appliquées. L'animation effectue 37 128 appels
de pose natifs ; les palettes reconstruisent 17 356 matrices locales.
Les 102 instants sans nouvel appel de pose natif conservent les corrections.
Les maximums correspondent à ceux du mode séparé : préparation `1,11e-16`,
rotations `1,56e-7`, matrices `2,38e-7`, poignets corrigés `1,51e-7`.
Les 70 dépassements avant correction de l'instant courant ne sont pas
comparables directement aux 72 dépassements du banc de clips bruts.

La construction reproductible privée `HandPipeline_Compiled_v2` conserve
l'image à l'identique et vérifie aussi l'absence d'appel à l'application
lorsque l'un des deux solveurs refuse sa cible.

La collecte des instantanés, le contrôle des modèles épinglés et l'appel après
le tick restent du code Python de diagnostic. Le point d'interception du client,
les liaisons et durées de vie des modèles réels, la réentrance du moteur, les
limites du visuel propriétaire et le budget par frame restent à construire ou
qualifier. Cette implémentation ne déclare aucune arme jouable.

## Reproduction

Construire avec `tools/build_native_hand_pipeline.py --output-name HandPipeline_Compiled_v2`
dans une destination neuve. Pour le banc unifié, remplacer `--compiled-solver`
et `--compiled-targets` par
`--compiled-pipeline .analysis/modern-assets/HandPipeline_Compiled_v2/hand-pipeline-v1.dll.disabled`.
Le composant de palettes et rafraîchissement reçoit encore `--compiled-commit`
pour son initialisation historique, mais son export isolé n'est pas appelé
en mode unifié ; l'application fait partie de la nouvelle image unique.
Les exécutables désactivés, données dérivées et rapports privés restent hors Git.
