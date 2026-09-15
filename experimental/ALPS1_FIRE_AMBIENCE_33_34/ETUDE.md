# Ge33/ge34 — ambiance du feu sans doublage

État : **couche additive non matérialisée**, 15 septembre 2026. Le système
release garde l'autorité sur la particule et les animations ; rien n'est
compilé.

## Constat

`ge_33.scr` conserve deux déclarations alternatives et commentées du même
handle `ohen`, vers `MR_PARTICLE - 39-OHEN A KOUR` et `partico`. Ces deux frames
sont absentes. Les anciens `FRM_SetOn(ohen,...)` et
`HUMAN_ACTIVITY_Sit(sit)` sont également commentés.

Le système actif est plus précis : `detector_forge30.scr` résout la frame
existante `ohen` et y crée la particule indexée 40. Ge33 emploie
`%%sedimtak`, puis une ronde détaillée et une activité assise au retour. Ge34
joue une boucle assise avec gobelet, `%%sedilavice1`, `%%priklohen` et
`%%sedila1`.

Réactiver les anciens fragments doublerait ou concurrencerait donc la particule
et remplacerait des animations release plus riches.

## Variante additive autorisable

[`AMBIENCE_CONTRACT.plan.disabled`](AMBIENCE_CONTRACT.plan.disabled) réserve :

- particule 40 et frame `ohen` à `detector_forge30.scr` ;
- animations humaines à `ge_33.scr` et `ge_34.scr` ;
- une éventuelle couche `TEST_FIRE_AMBIENCE_AUX` uniquement pour un son ou une
  lumière distincte, après identification d'un asset commercial ou création
  explicitement moderne.

Cette couche auxiliaire ne possède aucun `FRM_CreateIndexedParticle`, ne
commande pas `FRM_SetOn(ohen,...)` et ne lance aucune activité humaine. Aucun
script prototype n'est produit tant que son/éclairage, position et durée ne sont
pas attestés ou spécifiés.

## Tests futurs

Baseline de création unique de la particule 40, entrée/sortie du rayon, alarmes,
ronde ge33, boucle du gobelet ge34 et sauvegarde/reprise. Une éventuelle couche
auxiliaire doit ensuite être testée seule puis avec la release : une particule
totale, animations inchangées, arrêt propre et aucune réapparition après reload.

Rejet : usage des frames absentes, second feu/fumée, remplacement de
`%%sedimtak` ou de la boucle ge34, ou asset sonore/lumineux inventé sans étiquette
moderne.

## Sources

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_33.scr`, `ge_34.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forge30.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/scene2.bin`.
