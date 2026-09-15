# Prototype — reconstruction — Ardennes2 Frontline

Statut : **BLOQUÉ, mission entièrement créée sur carte officielle**.

## Origine

- entrée Teamplay `FRONTLINE` ;
- dix fichiers complets, sans registre ni script ;
- 22 acteurs structurants : `dummy_multispawn`, zones 1 à 4, sept MG42,
  deux caisses de munitions et six échelles ;
- 32 spawns de camp (`spawn0101..16`, `spawn0201..16`) et sous-repères de zones.

## Wrapper

- **ORIGINE** : géométrie, armes fixes, munitions, zones et spawns ;
- **DÉDUCTION** : assaut allié zone1 → zone4 et défense allemande autour des
  MG42 ;
- **CRÉATION** : acteurs, chemins, activation, objectif, échecs, extraction et
  textes.

Aucune mission solo Ardens2 ne fournit un contrôleur direct. Utiliser seulement
des patrons génériques d'arme fixe après adaptation des frames.

Tester maniement IA/joueur des sept MG, secteurs de tir, zone contournée,
équilibrage avec 1–4 membres et sauvegarde. Spéculation : **3/3**.

