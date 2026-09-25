# Czech 2 — posture de mort de Ger12

État : **prototype reproductible désactivé**, 25 septembre 2026.

## Preuves et modification

Le registre commercial lie `Ger_12` à `R_Cz2_Ger12.scr`. L'acteur est présent
dans `Patch.dta::missions/czech2/actors.bin`, à
`(2.855754, 0.919533, -8.501865)`. Après détection du joueur à 20 m, le script
réveille le soldat, attend une seconde, joue `%%mrtvolak`, attend une seconde,
puis appelle `HUMAN_KillEx(MyFRM, 2)`.

La ligne `HUMAN_SETMODE_Lie()` située avant l'animation est commentée.
Le profil `czech2-ger12-lie` retire seulement ses deux caractères `//`.
Il ne change ni la détection, ni les délais, ni l'animation active, ni la mort.
Le vestige est **OFFICIEL**; sa compatibilité avec la scène finale est une
**INFÉRENCE** à vérifier, pas une restauration déjà démontrée.

Le dummy `dummy_ger12_sit` existe dans `scene2.bin`, à
`(3.148185, 1.428573, -8.148709)`. Le script le recherche mais ne l'utilise pas.
Ce dummy n'est pas employé dans le prototype : le rapprocher du soldat ou le
faire asseoir serait un second comportement, pas le rétablissement de `Lie`.

## Fabrication et sélection

Le [générateur commun](../RECONSTRUCTION_BACKLOG/VARIANTES_REPRODUCTIBLES.md)
vérifie trois empreintes (script, registre, acteurs), puis fabrique une copie de
380 octets. Le [catalogue](../reconstruction-variants.json) conserve les sources
exactes, tailles, empreintes et la modification unique.

Sélection exclusive avant chargement d'une future copie laboratoire :
`commercial` par défaut, ou `czech2-ger12-lie`. Aucun second acteur ou signal.
Ne pas changer de script dans une sauvegarde en cours; revenir à une mission
neuve avec sa copie commerciale pour le retrait.

## Validation encore requise

- Comparer réveil, posture, position du corps et durée totale sur partie neuve.
- Entrer et sortir des 20 m; vérifier l'absence de répétition de la séquence.
- Provoquer une alarme ou tuer Ger12 avant et pendant l'animation.
- Sauvegarder/reprendre avant détection et pendant chaque délai.
- Contrôler le sol, les collisions et la progression de la mission.

La copie `.scr.disabled` a été construite et son diff contrôlé. Aucun essai
en moteur, aucune installation et aucune validation coop ne sont revendiqués.
