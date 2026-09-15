# Étude expérimentale — objectif Carnage 6 d'Africa 3

État : reconstruction désactivée, 14 septembre 2026. Aucun script actif,
registre de mission ou installateur n'est modifié ; aucun fichier n'est compilé.

## Verdict

L'acteur `dummy_carnage` est relié à `AF3a_obj_carnage.scr` et le catalogue
conserve l'objectif 6 « Kill the enemy », textuellement identique à l'objectif
2. Le contrôleur conserve, entièrement commentés :

- `DisableSignals(true)` ;
- le Whenever `_AllEnemiesDead()` ;
- le sous-titre 20994001 et son délai de deux secondes ;
- `SetObjectiveStatus(6, 1)` à la victoire ;
- `SetObjectiveStatus(6, 0)` à l'initialisation.

Le corps fonctionnel est donc **OFFICIEL 4/4**. Ce qui manque est son confinement
au mode Carnage. Décommenter les lignes telles quelles activerait l'objectif 6
dans la campagne normale, où `AF3a_obj.scr` active déjà l'objectif 2 « tuer tous
les ennemis ».

`PROTOTYPE_CARNAGE_ONLY.scr.disabled` rétablit le corps conservé et ajoute une
garde 3/7 copiée comme motif des missions voisines. Classification globale :
**reconstruction expérimentale 3/4**. La garde est fortement attestée par
analogie, mais n'est pas conservée dans ce fichier Africa3.

## Copies et état des sources

Les versions Base et Patch de `AF3a_obj_carnage.scr` ont le même contenu ligne
à ligne. La couche Patch possède aussi `AF3a_all_dead.scr`, identique à sa copie
de `AF3a_obj_carnage.scr`; ce doublon ne fournit pas la garde manquante. Le
corpus coopératif consulté ne contient pas d'autre corps Africa3 équivalent.

L'audit statique recense bien quatre opérations d'objectif 6 commentées dans
Africa3 et aucune opération active pour ce numéro. Le contrôleur normal
`AF3a_obj.scr` initialise et valide l'objectif 2 avec
`_GetCountOfCarnageEnemies() == 0`.

## Motif des contrôleurs Carnage voisins

| Mission | Activation limitée à 3/7 | Désactivation hors 3/7 | État du corps |
| --- | --- | --- | --- |
| Africa1 | oui | oui | bloc complet mais commenté |
| Africa2 | oui | oui | actif |
| Africa4 | oui | oui | actif |
| Africa5 | oui | non | actif, avec boucle de diagnostic |
| Burgundy3 | oui | oui | actif |

Tous réservent donc **l'activation** de leur objectif aux types 3 ou 7. Quatre
sur cinq désarment explicitement le Whenever dans la branche `else`; Africa5
omet cette seconde protection mais n'active tout de même son objectif qu'en
3/7. Le prototype Africa3 retient la forme majoritaire et plus sûre : activation
en 3/7, `SetWhenever(alldead, false)` ailleurs.

Cette analogie justifie la garde, pas le numéro d'objectif ni la condition de
victoire. Ces deux derniers éléments viennent exclusivement du fragment local.

## Reconstruction proposée

Le prototype suit l'ordre des contrôleurs Africa2/Africa4/Burgundy3 :

1. lire `_SPGetGameType()` ;
2. désactiver les signaux du dummy ;
3. déclarer la détection de victoire locale ;
4. en 3/7, rendre l'objectif 6 actif ;
5. dans tout autre mode, désactiver le Whenever.

Il conserve `_AllEnemiesDead()` au lieu de le moderniser vers
`_GetCountOfCarnageEnemies() == 0`. La seconde forme domine chez les voisins et
dans le contrôleur normal Africa3, mais remplacer la condition locale ajouterait
une hypothèse supplémentaire. Leur équivalence doit être mesurée en jeu avant
toute promotion.

## Risque principal : doublon 2/6 en Carnage

`AF3a_obj.scr` ne contient pas lui-même de garde excluant 3/7 lorsqu'il active
l'objectif 2. Selon la sélection d'objectifs opérée par le moteur et le registre
du mode, le prototype peut donc faire apparaître deux objectifs « Kill the
enemy » même en Carnage.

Ce dossier ne neutralise pas l'objectif 2 : cela modifierait un second
contrôleur et dépasserait la restauration locale. Si les deux objectifs sont
visibles ou se valident ensemble, le prototype reste refusé et le problème doit
être reclassé comme conflit de sélection d'objectifs/registre, non comme simple
bloc commenté.

## Matrice de test

1. Modes campagne ordinaires : confirmer que l'objectif 6 ne s'affiche jamais,
   que `alldead` est désarmé et que l'objectif 2 reste inchangé.
2. Modes 3 et 7 : vérifier l'activation unique de l'objectif 6 au chargement.
3. Comparer `_AllEnemiesDead()` au compteur Carnage avec ennemis actifs,
   suspendus, renforts non apparus et dernier ennemi mourant.
4. Vérifier le sous-titre 20994001, le délai de deux secondes et une seule
   validation de l'objectif 6.
5. Tuer le dernier ennemi pendant une sauvegarde/reprise et juste avant
   l'apparition éventuelle d'un renfort.
6. Relever séparément les statuts et l'affichage des objectifs 2 et 6.

Critères d'arrêt : objectif 6 visible hors 3/7, double objectif visible en
Carnage, victoire avant les renforts, validation répétée ou divergence entre
`_AllEnemiesDead()` et le compteur Carnage.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_obj_carnage.scr`
- `.analysis/scripts/patch/SCRIPTS/AFRICA3/AF3a_obj_carnage.scr`
- `.analysis/scripts/patch/SCRIPTS/AFRICA3/AF3a_all_dead.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_obj.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA1/AF1_obj_carnage.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_obj_carnage.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_obj_carnage.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_obj_carnage.scr`
- `.analysis/scripts/sabre/Scripts/Burgundy3/bur3_obj_carnage.scr`
- `.analysis/objective-audit.json`

