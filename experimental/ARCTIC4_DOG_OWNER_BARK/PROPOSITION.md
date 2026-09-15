# Arctic 4 — jappement du chien après la mort du maître

État : **primitive plausible mais non prouvée à l’exécution**, 14 septembre
2026. Deux variantes de script et un plan sonore restent désactivés. Aucune
mission n’a été compilée ou installée.

## Verdict

La scène et la chaîne de signal sont complètes : `Walking_Guard_3` envoie 1 à
`pes_1` dans `OnDeath()`, puis le chien parcourt aléatoirement `dog_1..5`. Entre
les deux, trois lignes commentées demandent exactement cinq secondes de
`DOG_HafHaf(True)` puis `False`.

Le nom de primitive n’apparaît activement dans aucun autre script commercial.
Une recherche dans les exécutables et bibliothèques n’est pas concluante : ni
`DOG_HafHaf`, ni des primitives pourtant actives comme `DOG_Attack` ou
`DOG_Move` n’y figurent en clair. Sans compilation ni essai moteur, l’existence
réelle de la commande ne peut donc pas être certifiée.

La première branche rétablit les trois lignes exactes. La seconde ajoute
seulement un arrêt de sécurité si une alarme interrompt les cinq secondes. Si la
primitive est refusée, le seul repli sonore attesté est l’émetteur `S_haf`
d’Alps 1 ; son portage dans Arctic 4 reste une adaptation moderne et n’est pas
réalisable avant extraction de son record complet et choix d’un placement.

## Inventaire des preuves locales

| Élément | Constat | Portée |
| --- | --- | --- |
| registre Arctic 4 | `pes_1 -> R_Arc3_dog_1.scr` | propriétaire exact |
| maître | `Walking_Guard_3` référence `Pes_1` et lui envoie 1 à sa mort | émetteur actif |
| chien, signal 1 | commentaire de mort du maître, `DOG_HafHaf(True)`, délai 5000, `DOG_HafHaf(False)` commentés | séquence directe |
| suite du signal 1 | choix aléatoire d’un point `dog_1..5`, course ou marche | comportement actuel à préserver |
| données de navigation | les cinq points existent dans `Missions/ARCTIC4/check2.bin` | aucune route à créer |
| corpus commercial | aucune occurrence active de `DOG_HafHaf` | exécution non éprouvée |
| remplacement sonore | Alps 1 possède `S_haf`, lié au contrôleur `stekani -> V_a1_pes.scr` | jappement audio officiel, autre mission |
| données Arctic 4 | aucun `S_haf` ou contrôleur `stekani` | pas de repli sonore local immédiat |

Arctic 4 ne possède pas de remplacement Patch de `R_Arc3_dog_1.scr` ou du
maître : les scripts Base inspectés sont effectifs.

## Données manquantes et hypothèses

- **Manquant** : preuve de résolution/compilation de `DOG_HafHaf` par le moteur
  final.
- **Manquant** : comportement de la primitive — son, animation, boucle, portée
  et interruption.
- **Hypothèse faible** : les booléens activent puis arrêtent un jappement ; la
  forme des trois lignes et le commentaire le suggèrent directement.
- **Hypothèse moyenne** : `OnAlarm()` peut interrompre le délai sans laisser le
  chien en état de jappement.
- **Manquant pour le repli audio** : record complet de `S_haf`, parent,
  transform, volume, portée et autorité réseau applicables à Arctic 4.
- **Hypothèse moderne** : un `S_haf` transplanté et placé sur ou près de
  `pes_1` restituerait convenablement le jappement du chien mobile.

## Niveaux de spéculation

- **Faible** : le chien devait japper cinq secondes après la mort du maître.
- **Moyenne à forte** : `DOG_HafHaf` existe et fonctionne encore dans le moteur
  livré ; aucun appel actif ne le démontre.
- **Moyenne** : l’arrêt ajouté au début de l’alarme est nécessaire et inoffensif.
- **Forte** : importer `S_haf` d’Alps 1 dans Arctic 4 ; l’asset est officiel,
  mais le placement et le déclenchement seraient modernes.
- **Exclue** : choisir un `PlaySound(groupe, index)` ou une animation au hasard.

## Branches conservables

### A — vestige exact

`PROTOTYPE_HAFHAF_EXACT.scr.disabled` rétablit uniquement les trois lignes dans
`OnSignal(1)`. La patrouille commence ensuite exactement comme dans la release.
Cette branche est la meilleure mesure de compatibilité de l’API.

### B — vestige avec arrêt d’alarme

`PROTOTYPE_HAFHAF_GUARDED.scr.disabled` ajoute un verrou local et appelle
`DOG_HafHaf(False)` avant l’attaque de `OnAlarm()`. Elle ne doit être testée
qu’après que A a prouvé la primitive. Elle est plus sûre, mais moins fidèle au
texte survivant.

### C — repli sonore conditionnel

`PROTOTYPE_S_HAF_IMPORT.plan.disabled` décrit un portage séparé de l’émetteur
Alps 1. Aucun script exécutable n’est fourni : tant que son record et un
placement mobile sûr ne sont pas établis, une référence `S_haf` dans Arctic 4
serait nulle ou spatialement fausse.

## Activation et désactivation

1. Dupliquer Arctic 4 et partir du script Base effectif.
2. Tester A seule, sans importer `S_haf`.
3. Si A fonctionne mais laisse un jappement après alarme, restaurer la baseline
   puis essayer B seule.
4. Si la primitive ne compile pas ou ne produit aucun comportement, restaurer
   immédiatement le script et n’étudier C qu’après extraction du record sonore.
5. Désactivation de A/B : remettre `R_Arc3_dog_1.scr` release. Désactivation de
   C : retirer le nouveau porteur, le record sonore et son unique binding.

Le maître, son signal 1, les cinq routes, les modes du chien et son attaque ne
sont modifiés par aucune branche.

## Risques

- symbole inconnu ou primitive retirée du moteur final ;
- boucle sonore/animation non arrêtée après une alarme ou une mort ;
- délai de cinq secondes empêchant la réaction immédiate du chien ;
- jappement joué sans son, sans animation ou deux fois ;
- repli `S_haf` fixe alors que le chien se déplace ;
- duplication réseau du son chez chaque client.

## Protocole de test en jeu

1. Baseline : tuer `Walking_Guard_3`, confirmer le signal, l’absence de
   jappement scripté et le départ vers `dog_1..5`.
2. Branche A : contrôler d’abord le chargement, puis mesurer précisément cinq
   secondes de comportement avant la même patrouille.
3. Déclencher une alarme avant la mort du maître, pendant le jappement, à sa fin
   et pendant le premier déplacement.
4. Tuer le chien pendant le jappement et vérifier l’absence de son persistant.
5. Comparer A et B sur les mêmes cas ; rejeter B si son arrêt change l’attaque
   ou la navigation.
6. Sauvegarder/reprendre avant le signal 1, pendant les cinq secondes et après
   le premier point aléatoire.
7. Tester hôte et client : une seule source, même durée, même transition.
8. Pour C seulement après extraction, comparer spatialisation près du chien,
   déplacement pendant les cinq secondes et retrait complet de l’émetteur.

Critères d’arrêt : erreur de symbole, crash, attaque retardée, jappement infini,
double son, source fixe incohérente ou divergence hôte/client.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_dog_1.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_walking_guard_3.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/pes.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/V_a1_pes.scr` ;
- `Missions/ARCTIC4/check2.bin`, `actors.bin` et `Scripts.dta` de
  `missions.dta` ;
- `Missions/ALPS1/actors.bin`, `sounds.bin` et `Scripts.dta` de `missions.dta`.
