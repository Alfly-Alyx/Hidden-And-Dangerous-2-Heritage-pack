# Matrice officielle propriétaire → script

| Propriétaire solo à copier | Transform solo `(x, y, z)` | Script coop existant | Frames cibles |
| --- | --- | --- | --- |
| `snd_vrabec01` | `(-70.359, -1.356, -137.514)` | `bur3_SND_bird1.scr` | `S_ptacek1..3` |
| `snd_vrabec02` | `(-70.525, -1.360, -138.959)` | `bur3_SND_bird2.scr` | `S_ptacek4..6` |
| `snd_vrabec03` | `(-70.872, -1.363, -140.342)` | `bur3_SND_bird3.scr` | `S_ptacek7..9` |
| `snd_vrabec04` | `(-71.180, -1.375, -141.674)` | `bur3_SND_sisky.scr` | `S_siska1..3` |
| `snd_vrabec05` | `(-71.525, -1.378, -143.078)` | `bur3_SND_stromy.scr` | `S_strom1..3` |
| `snd_vrabec06` | `(-71.881, -1.392, -137.515)` | `bur3_snd_bunkr.scr` | `S_bunkr1..3` |
| `snd_vrabec07` | `(-72.035, -1.396, -138.771)` | `bur3_snd_door1.scr` | `F_door_wood01` → `S_door02` |
| `snd_vrabec08` | `(-72.259, -1.349, -140.112)` | `bur3_snd_door2.scr` | `F_door_wood00` → `S_door03` |
| `snd_vrabec09` | `(-72.513, -1.405, -141.363)` | `bur3_snd_door3.scr` | `F_door_wood02` → `S_door04` |
| `snd_vrabec10` | `(-72.784, -1.410, -142.703)` | `bur3_snd_vrzik.scr` | `S_vrzik1..3` |

Les valeurs arrondies documentent le contrôle ; l'import doit reprendre les
champs binaires complets du record solo, pas ressaisir ces décimales.

## Interdictions

- ne pas redistribuer les dix scripts sur moins de propriétaires ;
- ne pas ajouter les bindings à un acteur coop existant ;
- ne pas copier une deuxième fois `sounds.bin` ou les frames `S_*` ;
- ne pas modifier les cadences avant test comparatif solo/coop.

