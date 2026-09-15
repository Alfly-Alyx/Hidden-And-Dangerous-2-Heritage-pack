# Reconstruction — Alps3 Objectifs solo

Statut : **wrapper étudié, non lançable**.

## Origine

- onze fichiers complets, dont `mpscripts.dta`, `check2.bin`, items et véhicules ;
- 17 acteurs structurants, 42 spawns (`spawn01xx`, `02xx`, `03xx`) et zones
  1, 2, 6 ;
- quatre bindings : détecteur de véhicule, pont, détecteur de char et canon ;
- trois objectifs MP AXIS avec textes 15011/15003, 15010/15004 et 15002/15001.

La variante Sabre active au char reste intacte. L'ancienne branche Base à deux
Opel et trois véhicules est documentée dans
[`ALPS3_OBJ_LEGACY_THREE_VEHICLES`](../../ALPS3_OBJ_LEGACY_THREE_VEHICLES/ETUDE.md).
Son vrai wrapper solo est déjà spécifié dans
[`VARIANTE_SOLO_RECONSTRUCTION.md`](../../ALPS3_OBJ_LEGACY_THREE_VEHICLES/VARIANTE_SOLO_RECONSTRUCTION.md).

## Wrapper

- **ORIGINE** : carte Sabre, véhicule, pont, canon et détections ;
- **DÉDUCTION** : convertir le camp attaquant en progression solo et supprimer
  score/respawn ;
- **CRÉATION** : équipe, catalogue solo, règles d'échec du véhicule et fin.

Tester véhicule bloqué/détruit, pont avant/après passage, canon neutralisé,
ordre alternatif, sauvegarde et fin unique. Spéculation : **2/3**.

