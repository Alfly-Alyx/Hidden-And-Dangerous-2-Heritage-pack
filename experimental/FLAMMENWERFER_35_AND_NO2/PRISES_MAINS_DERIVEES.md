# Poses de prise modernes sur les mains commerciales

**27 septembre 2026. DÉRIVÉ MODERNE, privé, hors moteur.**
Les deux [assemblages animés](ASSEMBLAGES_ANIMES.md) disposent désormais de
poses de mains calculées pour leurs neuf séquences. La géométrie et le
squelette de repos sont ceux des deux [mains commerciales vérifiées](../BENELLI_M4_ADDITIVE/MAINS_ET_CIBLES_FPV.md).
Les positions cibles, orientations de prise, flexions des doigts et calculs
des bras sont modernes. **Aucune animation historique n'est prétendue retrouvée.**

À ce stade, les poses sont calculées et inspectées, mais **pas encore encodées
en clips natifs**. Ce lot ne fournit pas une arme FPV jouable.

## Prises et provenance

La [recette moderne](modern-hand-grips.json) épingle les deux assemblages.
La main droite tient la prise arrière. La main gauche soutient la partie
avant du modèle allemand ; sur le britannique, son orientation et son
décalage sont adaptés à la poignée verticale distincte.

Le solveur calcule coude, avant-bras et poignet en conservant les longueurs
des bras et les positions/échelles locales des articulations. Les cibles
inaccessibles ou singulières sont refusées, jamais compensées par un étirement.
Les quatre doigts longs reçoivent une flexion moderne ; **les pouces restent
dans leur pose source**, sans qualification de leur contact.

La translation générale de l'équipement et les repères de prise sont des
choix d'auteur pour ce banc, pas une calibration de caméra ou de proportions
historiques. Le sac reste fixe. Aucun os de personnage complet, attache IA,
effet, son ou comportement n'est ajouté.

Les modèles, squelettes, positions de repos, poids et textures commerciaux
sont lus sous empreintes. Aucun modèle n'est réécrit. Les aperçus utilisent
une teinte neutre sans textures commerciales ; leur titre indique **mains
dérivées du jeu / poses modernes / privé**. Seuls le code et la recette sont
destinés au dépôt public, pas les modèles, poses sources ou images dérivées.

## Contrôles et aperçu

Deux cent quatre-vingt-cinq poses sont calculées par assemblage et variante
de mains : **1 140 poses**, sans changement des longueurs. Le résidu
géométrique maximal de poignet est inférieur à **4,41 × 10⁻⁸** avant
vérification native. Quatre planches, chacune de six poses et trois vues,
ont été inspectées. La fermeture des doigts a été ajustée et la prise gauche
britannique différenciée après la première inspection.

Les modèles commerciaux contiennent chacun **22 triangles à indices répétés**,
déjà sans surface au repos. Seuls ces triangles sont omis de l'aperçu logiciel
pour éviter une normale indéfinie ; la géométrie commerciale et ses indices
ne sont jamais modifiés. Les 1 526/1 654 triangles sources sont conservés
dans les comptes, et les 1 504/1 632 triangles affichables sont utilisés
uniquement dans les images privées.

Quatorze tests nouveaux, sur données synthétiques ou géométrie moderne,
couvrent le solveur, les longueurs, cibles, orientations, refus, différences
de prise, faces optionnelles et marquages. L'ancien rendu par défaut reste
identique. Aucune ressource commerciale n'est incorporée à ces tests.

L'audit natif de palette et de skin couvre les **1 140 poses, 41 040 poses
d'articulations, 1 178 190 sommets et 2 280 cibles de poignet**. Écarts maximaux :
palette **2,66 × 10⁻⁷**, skin **0**, position de poignet **1,15 × 10⁻⁷**.
Chaque pose est injectée indépendamment : la lecture temporelle d'une
animation n'est pas exécutée. Aucun résultat en jeu n'est annoncé.

Rapport privé : `.analysis/modern-hand-grips-native-20260927.json`.
La suite locale passe **922 tests**, avec un test optionnel ignoré (923 exécutés).

## Reproduction privée

```powershell
.\.venv\Scripts\python.exe tools/build_equipment_hand_grips.py --case F35 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name F35_HandGrips_nouveau
.\.venv\Scripts\python.exe tools/build_equipment_hand_grips.py --case F2 --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name F2_HandGrips_nouveau
.\.venv\Scripts\python.exe tools/hand_grip_native_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/modern-hand-grips-native_nouveau.json'
```

Sans nom de sortie, seuls les calculs sont effectués. Les lots actuels
`F35_HandGrips_v3` et `F2_HandGrips_v2` sont privés sous `.analysis/modern-assets/`.
Chacun contient douze images de poses, deux planches et un manifeste, aucun
modèle commercial ni clip. Les versions d'aperçu précédentes restent conservées ;
le premier dossier F35 refusé avant rendu est vide.

Empreinte de la recette normalisée :
`181b7c2b8895cb88ac97594aeddd4d488b7297835bc87b1be04fbe3e53d7ce31`.

## Suites nécessaires

Encoder les mouvements natifs, vérifier leurs poses entre clés et les raccorder
aux modèles chargés. Affiner pouces et contacts, transitions, caméra et
visibilité ; traiter séparément la tenue joueur/IA et les gestes fonctionnels.
Effets, sons, fonctionnement, tables additives et sauvegardes restent aussi
à réaliser. Les poses seules ne signifient pas qu'il ne reste que des tests.
