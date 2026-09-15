# Burgundy 2 [Alternative — garde coop]

État : **adaptation officielle coop vers solo, implantation de scène à faire**,
14 septembre 2026. Burgundy2 release reste intacte.

## Verdict

`ge_pruchod.scr` est un stub sans acteur ni route dans Burgundy2. Dans
Co_Burgundy2, le même nom désigne au contraire un acteur présent, lié à un
script complet. La reconstruction ne rétablit donc pas un garde solo prouvé :
elle importe dans une copie du solo un élément officiel conçu pour la coop.

Nom de l'entrée : `Burgundy 2 [Alternative — garde coop]`.
Étiquette obligatoire : **ADAPTATION OFFICIELLE COOP VERS SOLO**.

## Données attestées

| Élément | Burgundy2 | Co_Burgundy2 |
| --- | --- | --- |
| `ge_pruchod` | absent ; script stub orphelin | acteur/item/transform présent, script lié |
| `ge_pruchod2` | présent et lié | présent et lié |
| `k_topol_4` | présent | présent, visé par le script du garde |

Le script coop configure les alarmes, une IA zombie en garde, une portée de vue
70, une ouïe 100, l'animation `%%nuda`, une texture de visage, puis ferme sa
routine à l'alarme ou à la mort. Il ne déplace pas `ge_pruchod2` et ne doit pas
être fusionné avec lui.

Le compteur coop `pocitadlo_picusu.scr` scanne séparément `ge_pruchod` et
`ge_pruchod2`. Ce compteur n'est pas portable tel quel : il appartient à la
progression coop et ne doit pas être copié dans le solo.

## Import minimal

Dans une copie de Burgundy2 uniquement :

1. copier exactement l'acteur, l'item, l'équipement, l'affiliation et le
   transform `ge_pruchod` depuis Co_Burgundy2 ;
2. copier le script coop `ge_pruchod.scr` et créer son binding homonyme ;
3. ne modifier ni acteur, ni binding, ni script de `ge_pruchod2` ;
4. conserver `k_topol_4` comme repère de regard existant ;
5. ne pas importer le compteur coop.

La position est officielle dans la coop, mais son adéquation à la navigation
solo est une adaptation à valider. Aucun repositionnement ne doit être fait
silencieusement : toute correction de transform porte l'étiquette `MODERNE`.

## Cinématique explicitement exclue

`camery.scr` ne joue que le premier plan K1, attend puis lance la cinématique 1.
La release possède déjà `panaci.scr`, qui déroule K1 à K8. Comme
`objectyves.scr` valide l'objectif 5 sur `OnCutsceneDone(1)`, lancer l'ébauche
en parallèle peut produire un succès prématuré. `camery.scr` reste donc
orphelin et hors de la variante.

## Objectifs et sauvegarde

Le garde importé ne devient pas une condition de victoire. Le solo ouvre
l'objectif de regroupement après ses trois états principaux et valide
l'objectif 5 à la fin de la cinématique ; il ne scanne pas tous les ennemis.
La variante conserve ce contrat.

Si une sauvegarde est créée avec l'option active, sa signature de variante doit
empêcher son chargement dans Burgundy2 release. La mort, l'alarme et l'état
d'animation du garde doivent reprendre sans relancer une seconde routine.

## Tests

- superposer les scènes dans l'éditeur et vérifier le transform exact ;
- contrôler alignement du regard vers `k_topol_4`, collisions et navmesh ;
- tester approche furtive à plusieurs angles, pas, tir proche et explosion ;
- tester alarme globale, blessure, mort et corps bloquant le passage ;
- terminer chaque objectif avec le garde vivant puis mort ;
- sauvegarder avant l'approche, pendant `%%nuda`, après alarme et après mort ;
- désactiver la variante et comparer Burgundy2 à la baseline.

Il n'existe pas de nouveau `.scr.disabled` : le script source coop complet est
la pièce à copier après validation du delta de scène.

