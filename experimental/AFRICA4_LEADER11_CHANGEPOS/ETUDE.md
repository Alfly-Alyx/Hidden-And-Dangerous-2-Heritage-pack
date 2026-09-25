# Africa 4 — sous-routine de posture du chef 11

État du 25 septembre 2026 : **vestige documenté, point d'appel non attesté**.
Ne pas confondre ce cas avec les réservistes 27–30 déjà traités par Heritage.
Aucun prototype ni nouveau comportement ajouté ici.

## Comparaison des 18 scripts effectifs Patch

| Scripts | Sous-routine CHANGEPOS | Appel actif dans les archives |
|---|---|---|
| AF3b_11 | entièrement commentée; tirage debout/accroupi | aucun |
| AF3b_16 à 25 | corps présent, réveil puis tirage debout/accroupi | aucun |
| AF3b_27 à 30 | corps présent; appel commenté avant leur déplacement | aucun; cet appel est réactivé par le module Heritage |
| AF3b_31 à 33 | corps présent, sans réveil dans la sous-routine | aucun |

Analyse après retrait des commentaires. Un label actif ne prouve pas que la
sous-routine s'exécute. Pour 27–30, `Africa4DormantInfantryInstaller.cs` et
`docs/OBJECTIFS_ET_CHEMINS.md` décrivent le site d'appel historique exact déjà
traité. Il ne doit pas devenir une seconde reconstruction expérimentale.

## Pourquoi le chef est différent

Le chef crée une formation de cinq membres, parcourt `AF3b_c1_01` à `05` avec
un état `AtPos`, puis dissout la formation, notifie le coordinateur et les
membres et termine dans une boucle accroupie de visée vers le joueur, délai
1500 ms. Sa mort possède aussi une dissolution conditionnelle et des signaux.
Le bloc `CHANGEPOS` commenté ne contient pas de déplacement : il s'agit d'une
posture, pas d'un parcours perdu.

Réactiver le corps sans appel n'aurait aucun effet démontré. Ajouter un `gosub`
avant chaque segment, au signal 1 ou dans la boucle finale serait moderne.
Avant la posture accroupie finale, le résultat serait aussitôt écrasé; pendant
la marche, il pourrait modifier le comportement de formation. Aucun de ces
moments n'est attesté dans le script du chef 11.

## Décision

Conserver le commercial et observer allures, formation, interruption/reprise
avec `AtPos` et posture finale. Ne choisir un point d'appel moderne qu'après
avoir identifié un besoin visuel précis et ses effets sur les cinq membres.
Retraite 22, compteurs et objectifs restent hors périmètre. Ne pas importer les
appels des réservistes ni dissoudre une seconde fois la formation.

Source : `af3b_11.scr`, Patch.dta, 4733 octets, SHA-256
`1a5e7e786f80e38cac148efa5c994cf0fe0793201209daaf58f1e8344339a44c`.
Acteur et liaison présents. Provenance des fichiers de mission :
[étude du passager 09](../AFRICA4_PASSENGER09_ORIENTATION/ETUDE.md).
Aucun essai en jeu n'est déclaré réalisé par cette étude.
