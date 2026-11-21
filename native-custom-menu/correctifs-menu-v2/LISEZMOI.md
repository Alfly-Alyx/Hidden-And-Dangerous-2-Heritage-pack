# Correctifs du menu natif (v2)

Sources du module `HD2.CustomMenu.asi` avec 5 correctifs supplémentaires, basées sur la
branche `main` : le moteur du jeu ne prévoit de la place que pour 2 catalogues de
missions, ce qui faisait planter les catalogues 2 à 5 (adaptations solo, missions
de joueurs, exploration libre).

- `HookCleanupSlot`, `HookGroupStartA`, `HookGroupStartB` : évitent les écritures hors tableau.
- `HookRecordStore` et `HookGetSlot` : les fiches au-delà de 120 sont rangées dans une
  table de secours (`HookExtraSlots`) et relues par `HookGetSlot`.

Compilation (TinyCC) : `tcc.exe -shared -o HD2.CustomMenu.asi CustomMenu.c Hooks.S`.
À intégrer dans `native-custom-menu/` quand la branche aura été rapprochée de `main`.
