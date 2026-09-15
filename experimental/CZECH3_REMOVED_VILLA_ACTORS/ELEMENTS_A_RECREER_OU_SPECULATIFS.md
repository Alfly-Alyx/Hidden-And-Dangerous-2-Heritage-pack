# Czech 3 Villa — éléments à recréer ou à valider

| Élément | Preuve | Statut avant prototype |
| --- | --- | --- |
| `InViller_1` | script et `dummy_sit_vila1` | copier la pose du dummy ; transformation de départ à valider |
| `Plotman_01` / `02` | scripts et routes | acteurs, transformations, modèles et déclencheurs manquants |
| `SAS_1` | script et destination `BFD_1` | position de départ, modèle, équipement et source du signal 2 manquants |
| `Shocker_1` | cible explicite de `SAS_1` | acteur, transformation et état initial manquants |
| sous-titres 20994007–009 | appels dans le script | texte rendu, langue et synchronisation à tester |
| fin par signal 6 | appel officiel, récepteur absent | remplacer par un contrôleur propre étiqueté `MODERNE` |
| compteur de morts | anciens signaux vers `dummy_reinforcement` | isoler ; ne pas réutiliser le seuil release `> 18` |
| `la_bar_1` / `2` / `3` | scripts de barils seulement | placements et acteurs absents ; option séparée |

## Ordre de travail

1. retrouver des transformations historiques ou choisir des placements
   modernes explicitement documentés ;
2. copier des modèles et équipements depuis des acteurs release comparables de
   la villa, sans les qualifier d'originaux ;
3. créer le contrôleur et le compteur propres à la variante ;
4. valider les textes et sons avant d'autoriser la séquence ;
5. seulement ensuite produire des scripts `.scr.disabled`.

