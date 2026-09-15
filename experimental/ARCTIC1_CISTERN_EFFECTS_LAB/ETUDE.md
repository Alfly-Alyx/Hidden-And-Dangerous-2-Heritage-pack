# Arctic 1 — laboratoire d'effets des six citernes

État : **A/B requis avant option**, 15 septembre 2026. Aucun des six scripts
release n'est modifié.

## Verdict

Les six `R_arc1A_cisterna*.scr` possèdent les mêmes deux lignes commentées avant
`MakeExplosion` : particule 53 sur `MyFRM` et `PlaySound(6, 2)`. Les six
citernes Arctic 3 conservent la même paire commentée. Les quatre contrôleurs
Arctic 1 MP se limitent à `MakeExplosion`. Cette convergence propre à la famille
de citernes impose de supposer un risque de double effet jusqu'à preuve visuelle
et audio contraire.

La paire n'est pas invalide en soi. D'autres missions l'emploient activement ;
certains scripts remplacent alors `MakeExplosion`, d'autres cumulent les trois
appels. Ces précédents démontrent l'effet, pas le bon mix pour les réservoirs
Arctic ni la décision historique finale.

## Matrice commerciale

| Famille | Particule 53 | Son 6/2 | `MakeExplosion` | Observation |
| --- | --- | --- | --- | --- |
| Arctic 1 SP, 6 citernes | commentée | commenté | actif sur `EXPL00` | sauvegarde 101–106 |
| Arctic 3, 6 citernes | commentée | commenté | actif sur `EXPL00` | reprend l'état Arctic 1 |
| Arctic 1 MP, 4 citernes | absent | absent | actif sur la citerne | choix simplifié confirmé |
| Africa 1, citernes | actif | actif | commenté | paire utilisée en remplacement |
| Africa 2, explosions | actif | actif | actif | cumul possible dans un autre contexte |

## Expérience autorisable

Le plan [`SINGLE_CISTERN_PROBE.plan.disabled`](SINGLE_CISTERN_PROBE.plan.disabled)
limite l'essai à une seule citerne dans une copie de test et conserve exactement
les dégâts, la cible `BUUUM` et la valeur de sauvegarde. Les profils sont testés
séparément : baseline, particule seule, son seul, puis les deux seulement si les
essais unitaires ne doublent pas l'effet de `MakeExplosion`.

Une option sur les six citernes est interdite tant que l'essai unitaire et une
explosion en chaîne n'ont pas été comparés. Aucune ligne ne doit être ajoutée à
Arctic 3 ou au MP par symétrie.

## Mesures

- nombre de flashes, boules de feu, fumées et débris par destruction ;
- niveau crête, durée et nombre d'attaques audio à proximité et à distance ;
- différence entre cible `MyFRM` et point `EXPL00` ;
- destruction simple puis chaîne de deux et six citernes ;
- sauvegarde/reprise avant/après, valeurs 101–106 inchangées ;
- aucune répétition au chargement d'Arctic 3.

## Sources internes

- scripts `R_arc1A_cisterna1..6.scr` ;
- scripts `R_Ar3_cisterna1..6.scr` ;
- scripts `A1_mp_cisterna*.scr` ;
- comparables Africa 1/2 utilisant la particule 53 et le son 6/2.
