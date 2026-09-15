# Reconstruction — Ardennes1 Objectifs solo

Statut : **wrapper étudié, non lançable**.

## Origine

- treize fichiers complets, registre Sabre de quatre bindings ;
- 35 acteurs structurants, 32 spawns et zones 1 à 5 ;
- deux Sherman, un Tiger, trois canons, jeep et explosifs dans la scène Sabre ;
- initialiseur d'objectif plus trois scripts de canon ;
- textes MP 15020/15030, 15021/15031 et 15022/15032.

La composition Base à trois Sherman et deux Tiger est séparée dans
[`ARDENS1_OBJ_LEGACY_ROSTER`](../../ARDENS1_OBJ_LEGACY_ROSTER/ETUDE.md), avec
son wrapper dans
[`VARIANTE_SOLO_RECONSTRUCTION.md`](../../ARDENS1_OBJ_LEGACY_ROSTER/VARIANTE_SOLO_RECONSTRUCTION.md).

## Wrapper

- **ORIGINE** : scène Sabre, trois objectifs et scripts de canons ;
- **DÉDUCTION** : choisir le camp allié comme équipe solo et conserver l'ordre
  des trois objectifs ;
- **CRÉATION** : point de départ unique, IA de remplacement des joueurs AXIS,
  échecs, textes solo et fin.

Tester chaque canon, chaque char vivant/détruit, objectifs hors ordre, absence
de respawn et sauvegarde avant/après chaque validation. Spéculation : **2/3**.

