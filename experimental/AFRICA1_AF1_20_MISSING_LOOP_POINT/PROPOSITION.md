# Africa 1 — point 01 manquant de la boucle d’AF1_20

État : **branche de patrouille conservée mais non activable**, 14 septembre
2026. La branche release reste sélectionnée ; aucun checkpoint n’est ajouté.

## Verdict

OnAlarmDone contient une boucle complète commentée, de AF1_20_01 à _08, avec
quatre appels LOOKAROUND. Le check2 ne possède que les noms _02 à _08. Le point
_01 ne peut pas être identifié de façon unique.

La proposition conserve deux variantes exclusives :

- **release** : les rotations gauche/droite actuelles, sans déplacement ;
- **patrouille** : la boucle historique, seulement après création et validation
  de AF1_20_01.

Le fichier VARIANT_SELECTOR.scr.disabled documente le remplacement. Il n’est ni
compilable ni installé tel quel et garde RELEASE comme choix.

## Points commerciaux attestés

| Nom | Position (x, y, z) |
| --- | --- |
| AF1_20_02 | 94.473633, 0.512365, 17.566032 |
| AF1_20_03 | 114.824249, 0.253651, 20.922476 |
| AF1_20_04 | 123.319962, 0.193441, 40.057735 |
| AF1_20_05 | 133.124817, 0.253651, 23.268465 |
| AF1_20_06 | 143.033249, 0.192390, 23.458580 |
| AF1_20_07 | 138.303986, 0.069155, 41.311558 |
| AF1_20_08 | 113.343231, 0.253654, 28.826727 |

La route minimale _08 vers _02 passe par _03 puis par un point sans nom
(103.970070, 0.253653, 18.327888). Ce candidat ferait revisiter _03 avant son
tour normal et ne prouve pas _01.

Près du milieu géométrique _08/_02, deux autres points sans nom sont presque à
égalité : (103.709152, 0.197839, 21.241714) à 1.973503 unité et
(105.617294, 0.186956, 22.214397) à 1.980640. Cette ambiguïté interdit un
renommage automatique.

## Contrat des variantes

Le choix se fait avant de copier la mission. Il ne doit pas changer en cours de
partie et aucun test ne mélange script release et check2 de patrouille.

La variante PATROL exige un point nommé, relié et testé. Tant que ce prérequis
n’est pas satisfait, sélectionner PATROL est une erreur de préparation.

## Test de la future variante

1. Vérifier le chemin _08 -> _01 -> _02 dans les deux sens dans l’éditeur.
2. Faire dix tours sans alarme et noter tout retour prématuré vers _03.
3. Déclencher une alarme sur chaque segment, puis laisser OnAlarmDone reprendre.
4. Tester mort, blocage joueur, sauvegarde avant _01 et reprise après _01.
5. Comparer la durée et la couverture à la rotation release.
6. Retour arrière : remettre le script release et le check2 commercial ensemble.

