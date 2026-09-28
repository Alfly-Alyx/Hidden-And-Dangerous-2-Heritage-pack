# Animation et correction : mêmes objets en mémoire privée

**28 septembre 2026 — réalisation hors jeu, pas hook client.**
La [première application compilée](CORRECTEUR_BRAS_COMPILE.md) conservait les
mêmes objets pendant application, rafraîchissement et palette, mais recevait
ses poses d'un autre émulateur. `unified_hand_pose_oracle.py` ferme cette coupure :
les attaches de clips, changements de poids, calculs natifs de pose, écritures
compilées des six rotations, rafraîchissement récursif et palettes opèrent
maintenant sur **les mêmes enregistrements pendant toute une séquence**.

## Ce qui est réalisé

Les noms et transformations initiales sont fournis une fois, avant toute
attache. Le laboratoire réserve des enregistrements joints assez grands,
sans recouvrir les descripteurs des animations. La table de recherche native
pointe sur ces enregistrements dès la première attache réelle. Il n'y a pas
de migration d'os déjà animés, ni de copie des poses vers une seconde arène
entre deux mises à jour.

Chaque opération d'animation est comparée au calcul indépendant, y compris
les références de clips, canaux, compteurs de temps et indicateurs. Le
correcteur C est comparé à un correcteur Python qui conserve **ses propres
poses corrigées** pour la référence de l'instant suivant. Les quaternions
sont convertis en float32 et représentés avec une composante W positive ;
ce choix de signe ne change pas l'orientation et n'étire aucun os.

Les écritures du composant C restent limitées aux six rotations et à leurs
indicateurs. Le rafraîchissement natif et la palette conservent ensuite les
états des caches, du visuel propriétaire et des descendants. Le contrôleur
suivant retrouve exactement ces objets, notamment quand il ne rééchantillonne
aucun canal. Les entrées, autres canaux et objets non concernés sont vérifiés.

Le solveur numérique des bras utilise encore son propre processeur émulé,
avec des tampons bornés. C'est **la mémoire des objets animés** qui est réunie.
La commande entre les étapes est du code diagnostique Python, pas un callback
de jeu. La racine de mains est représentée comme un joint de diagnostic ;
le visuel propriétaire est un enregistrement fourni, pas une scène chargée.

## Contrôles

`unified_hand_pose_audit.py` reprend les 13 couples, trois phases et cinq poids
du banc précédent. Il ajoute un contrôle de conservation : huit pas nuls,
passage à poids nul, réactivation, détachement complet et quatre nouveaux pas
nuls. Les comptes distinguent les appels de pose d'origine, les appels au
solveur, les six rotations écrites et les matrices effectivement reconstruites.
Une frame sans appel de pose peut encore recevoir une correction ; aucune
mesure de budget temps réel n'est déduite de cette exécution en émulation.

Le premier passage historique avec le solveur v1, Arm → Idle/H, a vérifié vingt opérations et sept instants,
dont un dernier pas sans appel de pose natif. Écart de pose maximal
`5,960464478e-8`, matrices `1,788139343e-7`, rotations du solveur/référence
`3,841497200e-7`, poignets après correction `1,214810960e-7`.
Il s'agit d'un premier témoin, pas du résultat de l'ensemble du corpus.

```powershell
.\.venv\Scripts\python.exe tools/unified_hand_pose_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --bank-root .analysis/modern-assets --bank-suffix HandFPV_v10 --profile experimental/RECONSTRUCTION_BACKLOG/modern-rigid-hand-grips-mg34-linear.json --case MG34 --compiled-solver .analysis/modern-assets/HandConstraints_Compiled_v2/hand-constraints-v1.dll.disabled --compiled-commit .analysis/modern-assets/ArmPoseCommit_Compiled_v1/arm-pose-commit-v1.dll.disabled --json-output .analysis/memoire-unifiee-neuve.json
```

Dépendances privées d'émulation nécessaires ; rapport neuf obligatoire.
Aucune pose ou géométrie commerciale n'est exportée, ni jeu lancé ou modifié.

## Correction de la dérive à pas nul

Le premier corpus v1 a passé les 39 transitions H mais **échoué sur les pauses
répétées** : les poses corrigées compilées s'écartaient progressivement de la
référence indépendante. Le rapport complet en échec n'a pas été publié comme
une réussite. Le seuil `2e-6` n'a pas été relevé.

La source C utilisait la transposée des bases presque orthonormales comme
inverse. Les petits résidus d'échelle des repos commerciaux rendaient cette
approximation biaisée ; le coude corrigé observé au passage suivant réinjectait
ce biais. La v2 calcule l'inverse 3×3 exact, en conservant toutes les sources.
La construction ajoute douze cas inventés avec résidus d'échelle et exige une
comparaison à `5e-12` dans ces calculs doubles indépendants. **24 cas valides
et huit refus passent**, maximum `1,110223025e-15`. Le seuil de comparaison
des poses natives reste inchangé.

Image v2 de 8 192 octets, SHA-256
`d3ff9aa8bf18b947ad369e8ccc79809c773da9f9b8c102ae17b7ed1527e934bf` ;
section de code de 6 240 octets,
`be596ddb17eb8d1fdc15253f18c826713e0b80ae90a0fcac1d1b42a063b84f62`.
Le nom de fichier conserve `v1` pour l'ABI ; la nouvelle sortie privée est
`HandConstraints_Compiled_v2`. Les images antérieures ne sont ni écrasées ni
acceptées par le contrôleur courant. Le composant d'application des rotations,
lui, ne change pas.

La reprise ciblée des pauses sur H puis R passe : **16 instants par variante,
dont douze sans appel de pose natif**, 78 allocations puis 78 libérations de
descripteurs, 96 rotations appliquées et 189 reconstructions locales.
Écart natif/référence `2,980232239e-8`, rotations corrigées `5,222264022e-8`,
matrices `1,788139343e-7`, poignets après correction `1,214810960e-7`.
Le contrôle complet v2 est maintenant terminé et conservé dans
`.analysis/unified-hand-memory-mg34-v10-20260928.json` : **80 séquences H/R,
578 instants, 37 128 appels de pose natifs, 1 156 appels au solveur C,
3 468 rotations appliquées et 17 356 reconstructions locales**.
102 instants ne comportent aucun appel de pose natif, sans perte des corrections.
Maximum de pose/référence `5,960464478e-8`, rotations du solveur `1,561167536e-7`,
matrices `2,384185791e-7`, poignets après correction `1,512834184e-7`.

Les mesures avant la correction de l'instant courant dépassent le seuil sur
70 instants de transition. Ce compteur ne remplace **pas** les 72 dépassements
du banc sans mémoire corrigée persistante : les poses de départ peuvent ici
conserver la correction du passage précédent. La correction de v2 n'est donc
pas présentée comme une modification ou une qualification des clips bruts.

## Raccordements encore à réaliser

Le point après mélange repéré dans le relais de modèle n'est toujours pas
intercepté. Restent l'identification des modèles réellement chargés, leur
durée de vie, le filtrage strict des équipements modernes, la collecte des
poses vivantes, la réentrance, les limites du visuel propriétaire, le
budget par frame et les comportements du client. Surfaces, skin, caméra,
sons et jouabilité ne sont pas qualifiés par ce contrôle de mémoire.

Le [calcul des cibles sur buffers bornés](CIBLES_MAINS_COMPILEES.md) dispose
désormais d'une implémentation C indépendante ; sa collecte d'entrées et son
appel restent orchestrés par le banc Python, pas par un hook dans le jeu.

Le [mode à correction entièrement compilée](CORRECTION_MAINS_COMPILEE_UNIFIEE.md)
réunit désormais les trois composants dans une image et un processeur partagés
avec les nœuds animés. Le mode historique à solveur séparé décrit dans les
premiers résultats est conservé comme référence ; aucune preuve de hook ou
de modèle chargé n'est ajoutée par cet assemblage.
