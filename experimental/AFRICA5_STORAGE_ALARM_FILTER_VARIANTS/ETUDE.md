# Africa 5 — variantes historiques des filtres d'alarme du magasin

État du 25 septembre 2026 : **trois scripts complets désactivés construits;
laboratoires bloqués par une dépendance commerciale absente**. Aucun registre,
installateur ou fichier de jeu modifié. Le comportement commercial reste le
profil par défaut; chaque garde est étudié dans une variante indépendante.

## Changement et différences entre voisins

Chaque profil retire exactement les deux caractères de commentaire d'une seule
ligne d'initialisation. Aucun autre `SetAlarmType` commenté n'est réactivé.

| Profil | Ligne historique | Effet initial proposé | Après le signal 2 commercial |
|---|---|---|---|
| `africa5-storage01-alarm-filter` | `SetAlarmType(4, false)` | ne réagit plus aux pas | pas de réactivation du bit 4 dans ce handler |
| `africa5-storage02-alarm-filter` | `SetAlarmType(516, false)` | ignore pas (4) et vue de cadavre (512) | `SetAlarmType(6, true)` réactive les pas, pas le bit 512 |
| `africa5-storage03-alarm-filter` | `SetAlarmType(516, false)` | mêmes deux exclusions | `SetAlarmType(1023, true)` réactive toutes les catégories |

La signification des bits vient des tables de catégories présentes dans le
corpus commercial. Les tirs, dégâts et autres catégories ne sont pas désactivés
par ces deux masques. Les gardes 05/06/07 utilisent déjà 516 false dans leur
initialisation; ce précédent ne prouve pas que 01/02/03 doivent être identiques.
Les différences de détection sont précisément l'objet des essais A/B futurs.

Les acteurs et leurs trois liaisons sont présents et uniques. Chaque profil
épingle son script Patch, le registre Base, les acteurs Base et le script 05
Patch de comparaison. Les routes, dialogues, signaux, la valeur 32, les modes
de combat et le réveil restent intégralement commerciaux. Les correctifs
Heritage existants du mécanicien 04, du garde 43 ou des visages ne sont pas
réappliqués ni réputés compatibles par ce travail.

## Résultats locaux

| Garde | Octets | SHA-256 de la sortie `.scr.disabled` |
|---|---:|---|
| 01 | 1733 | `702a6dcbea0f0d823cc5fc1fdb4ba694fbea4627609bd0a33b200aa070586e6a` |
| 02 | 2536 | `7cdfd0cba404299588deaaf2414a7fb06c4c724556bba0a321331d7b648b2ec9` |
| 03 | 2682 | `68051d380d7512b700aa08e30fb0b39a5b490f7270664042e17d45de597ef5b2` |

Ces scripts sont construits par le
[générateur reproductible](../../tools/build_reconstruction_variant.py) dans
`.analysis/generated/`. Trois tests contrôlent les deltas et les masques
binaires; ce n'est pas une validation du moteur.

Le garde 01 possède aussi un script libre déjà modifié dans l'installation :
1806 octets, SHA-256
`3c4c4295c2f627490ebb63bdb2e3a9e77d2cf6d5dfab51107b416231a25cb138`.
Le contrôle strict le refuse; la sortie ci-dessus vient exclusivement du Patch
commercial de 1735 octets. Cette surcharge est laissée intacte et enregistrée
comme exclue. Ce conflit est distinct du détecteur de piste absent.

## Pourquoi aucune mission complète n'est fabriquée

La tentative de laboratoire échoue pour chacun des trois profils avec
`Missing script dependencies: af4_runway01_detector.scr`. Le registre
commercial contient ce binding, mais le fichier est absent des archives
effectives inspectées. Les 194 fichiers disponibles de la mission ne forment
donc pas une fermeture complète au sens du générateur.

L'[étude du détecteur de piste](../AFRICA5_OLD_RUNWAY01_DETECTOR/ETUDE.md)
identifie déjà ce binding comme prédécesseur probable du contrôleur central
actif. Il n'est ni effacé du témoin, ni remplacé par un script inventé, ni
ignoré par une exception silencieuse. Le contrôle de laboratoire garde son
refus. Aucun ZIP A/B n'est produit pour ces trois profils.

## Validation restante

1. Résoudre explicitement la baseline de laboratoire avec ce binding fossile,
   sans second écrivain de l'objectif 4 ni de la valeur 40.
2. Observer chaque garde commercial après ouverture et fermeture répétées de la
   porte, sans mélanger les trois variantes.
3. Comparer pas, cadavre visible, tirs et dégâts avant activation, après signal
   1, après signal 2 et après retour d'alarme.
4. Pour 02/03, surveiller conversation, valeur 32 et interruption de l'animation;
   pour 01, surveiller suspension au-delà de 100 m et réveil ultérieur.
5. Tester mort, sauvegarde/reprise et fin de mission. Refuser une IA bloquée,
   une conversation relancée en double ou un objectif divergent.

Toutes les validations de jeu restent **pending**. Le refus de laboratoire
n'empêche pas de vérifier les trois scripts isolément, mais interdit de les
présenter comme trois nouvelles missions prêtes à charger.
