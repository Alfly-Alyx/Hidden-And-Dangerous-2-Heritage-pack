# Czech 4 — destinations incomplètes des trois soldats de cave

État : propriétaires et événement établis, positions manquantes, 25 septembre 2026.

Les trois `CZ4_Sklepers_01..03.scr` sont liés à leurs acteurs présents. Les
détecteurs `CZ4_detector_07`, `08` et `11` leur envoient respectivement les signaux
7, 8 et 11. Dans chacun des trois récepteurs 11, un `HUMAN_Move("???")` est
commenté avec une note demandant de compléter après la refonte des checkpoints.
Ce n'est pas un nom de destination exploitable, et aucune position n'est donnée.

Le reste de 11 est actif : réveil, masque d'alarme 373, choix marche/course selon
la valeur 15, posture accroupie et IA défensive immédiate. Le commentaire associé
au masque est arithmétiquement incohérent : sa somme écrite vaut **371**, pas 373.
Le nombre commercial 373 reste l'autorité; aucune « correction » du masque
n'est incluse dans l'étude des déplacements.

Les trajets des événements 7/8 ne permettent pas de déduire ceux de 11 : les
acteurs 01/02 visent `inj`/`ind` sur 7, utilisent `sklep` puis `sklep2` sur 8;
le 03 n'a pas le même parcours et ne vise que `sklep` sur 8. Les cinq routes
`TheEnd_1..5` appartiennent encore à une autre branche de fin, avec compteur 16.
Réutiliser l'une de ces cibles sous trois nouveaux noms serait une invention
géométrique non démontrée.

| Scripts.dta, `scripts/czech4/` | Octets | SHA-256 |
|---|---:|---|
| `cz4_sklepers_01.scr` | 2750 | `bbb669f29c5cdc31505e75ec33137c7857387cabcff8c63a24781871d144249e` |
| `cz4_sklepers_02.scr` | 3007 | `dafc00d2bf6e6f10716d92eb9be66bf4aabc6234d7b94f7155ce7d04ffcb0565` |
| `cz4_sklepers_03.scr` | 2904 | `68dcf72d1d220ad9e64988477c7a3e4243468f556e34ccddf2819a42dca80903` |

Suite : relever les trois positions au signal 11 et la géométrie traversable,
choisir trois destinations **MODERNES** distinctes, vérifier portes, hauteur,
croisements et temps d'exposition, puis construire une variante exclusive.
Le profil commercial garde la réaction défensive immédiate. Tester alarme,
mort pendant déplacement, séquences 7/8/11, signal répété et sauvegarde/reprise.
Aucun checkpoint n'est créé avant cette preuve géométrique.
