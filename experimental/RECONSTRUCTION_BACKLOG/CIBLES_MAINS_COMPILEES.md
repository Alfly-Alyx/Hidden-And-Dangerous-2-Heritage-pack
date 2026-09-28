# Préparation compilée des cibles de mains

Implémentation C originale du 28 septembre 2026, sans données commerciales,
import système, allocation, chargement Windows ou raccordement au client.
Elle complète le [solveur de bras](CORRECTEUR_BRAS_COMPILE.md) : les entrées
courantes du solveur ne sont plus nécessairement calculées par Python.

## Contrat et limites

`native/hand_targets.c` expose `Hd2PrepareArms`, en convention x86 cdecl.
L'appelant fournit des buffers distincts et valides :

- 5 à 128 poses locales float32, position / quaternion natif / échelle ;
- les parents, obligatoirement antérieurs à leurs enfants ;
- cinq rôles distincts : racine tenue, repères gauche/droit, avant-bras gauche/droit ;
- 90 doubles de repos et 30 doubles décrivant les deux prises modernes ;
- un espace temporaire de `12 * nombre_de_nœuds` flottants ;
- une sortie de 120 doubles, soit les deux entrées complètes du solveur.

Le composant compose les transformations courantes avec les arrondis float32
du contrat natif, y compris le raccourci d'identité pour `abs(W) >= 1`.
Il calcule les deux poignets, les orientations de mains et les coudes observés.
Les 45 paramètres de repos de chaque bras sont copiés sans altération.
Les nombres, échelles, quaternions, indices et coordonnées composées sont bornés.

Les erreurs ne modifient jamais la sortie. L'espace temporaire peut changer,
mais ses limites sont contrôlées. Le composant ne valide pas des adresses de jeu
arbitraires et ne découvre ni les modèles chargés ni leur durée de vie.
La validité et l'exclusivité des buffers restent un contrat de l'appelant.

## Construction et contrôles

`tools/build_native_hand_targets.py` utilise uniquement le compilateur local
épinglé et refuse une destination préexistante. L'image privée désactivée fait
6 144 octets, SHA-256
`21ff73f49a776611b353b72f643d25bfb09d22a06e9239c2050cc1969e71718f`.
Elle n'a aucun import ; son entrée de chargement Windows refuse le chargement.
`tools/native_hand_targets.py` exécute uniquement les instructions autorisées
dans un processeur x86 émulé, avec gardes mémoire et contrôle de la convention
d'appel. Aucune bibliothèque n'est chargée dans Windows.

Huit cas inventés couvrent 5, 9, 64 et 128 nœuds, avec rotations, parents
enchaînés, résidus d'échelle et quaternion d'identité natif. Treize refus
couvrent les nombres invalides, échelles, quaternions, hiérarchies, rôles,
capacités, espace temporaire trop court et débordements de coordonnées.
La reconstruction privée `HandTargets_Compiled_v2` conserve exactement la
même image C et compare une référence arrondie à l'ABI float32 ; écart maximal
`1,110223025e-16`. Le premier manifeste v1 est conservé, sans écrasement.
Les premières poses de repos des deux mains commerciales ont aussi été
comparées à la référence indépendante : écart nul sur les 120 paramètres.

Le banc unifié accepte `--compiled-targets` en plus des deux autres composants.
Il transmet réellement les 120 résultats C aux deux appels du solveur et les
compare au calcul indépendant ; une sortie partielle, non finie ou trop éloignée
est refusée. Chaque instant conserve son reçu et les totaux distinguent les
appels au préparateur des deux appels au solveur.

## Corpus animé complet

Rapport privé :
`.analysis/unified-hand-memory-mg34-compiled-targets-v1-20260928.json`.
Les 80 séquences H/R représentent 578 instants et autant d'appels au préparateur,
1 156 appels au solveur et 3 468 rotations appliquées. Les 102 instants sans
nouvel appel de pose natif conservent les corrections. Les 120 paramètres
préparés sont comparés à chaque instant : écart maximal `1,110223025e-16`.
Les autres maximums restent identiques au corpus précédent : poignets
`1,512834184e-7`, matrices `2,384185791e-7`, rotations `1,561167536e-7`.
Les comptages avant correction ne sont toujours pas ceux du banc de clips bruts.

Reproduction : construire avec
`tools/build_native_hand_targets.py --output-name HandTargets_Compiled_v2`
dans une destination neuve, puis reprendre la commande du banc unifié avec
`--compiled-targets .analysis/modern-assets/HandTargets_Compiled_v2/hand-targets-v1.dll.disabled`.
Les binaires et rapports privés restent exclus du dépôt.

La collecte des poses et l'orchestration demeurent du code de diagnostic Python.
La construction isolée présentée ici reste disponible ; les trois composants
sont maintenant aussi [assemblés dans une image unique](CORRECTION_MAINS_COMPILEE_UNIFIEE.md).
Ni hook, scène chargée, enveloppe du visuel, temps par frame, caméra ou
comportement jouable ne sont qualifiés par ce travail.
