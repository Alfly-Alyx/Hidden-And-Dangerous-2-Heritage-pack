# Alps 2 — livre tenu par AL2_11

État : **prototype désactivé, validation runtime obligatoire**, 15 septembre
2026. Aucun fichier de mission n'est modifié.

## Vestiges et ressources

`AL2_11.scr` résout encore `k_leo_` et son enfant logique
`k_leo_.rectangle01`. Dans `mode1`, le personnage suit
`AL2_11_01 -> AL2_11_02`, regarde `al211cum1`, attend 400 ms et lance la boucle
`%%ctuneco`. La ligne immédiatement suivante est l'ancien
`FRM_TeleportNearFrame(leo, ruka, 1)` ; seule la résolution de
`al2_11.hw1` est commentée.

L'inventaire de `scene2.bin` confirme une frame exacte `k_leo_`. Le nom
hiérarchique `k_leo_.rectangle01` et le socket `al2_11.hw1` ne sont pas des
frames statiques sérialisées séparément. Cela est cohérent avec le moteur :
des scripts actifs Alps 2 résolvent leurs sockets `<acteur>.hw1` au moment de
l'animation (`AL2_01`, `AL2_05`, `AL2_21`, `AL2_22`, `AL2_34`, `AL2_37`).
Cette convention atteste le type de point, mais **pas encore sa présence sur
AL2_11 au runtime**.

Un analogue ancien, `R_nor_man10.scr`, utilise le même objet `k_leo_`, résout
`small10.hw1` juste avant l'attache puis vide la référence. Il confirme que le
vestige correspond bien à un livre/objet de lecture tenu en main.

## Proposition bornée

Le profil `LEO_HAND_PROP_TEST` ne remplace ni ne relance `%%ctuneco`. Il ajoute
uniquement, juste après cette animation, une résolution locale du socket, le
téléport officiel, puis la libération de la référence. Le fragment se trouve
dans `PROTOTYPE_MODE1_DELTA.scr.disabled`.

La release reste le profil par défaut. Le fragment est bloqué tant que la
console runtime n'a pas confirmé les trois résolutions :

1. `k_leo_` non nul dans la scène chargée ;
2. `al2_11.hw1` non nul après l'activation de l'acteur ;
3. `k_leo_.rectangle01` cohérent avec la géométrie attendue.

Si le socket manque, aucune frame de substitution ne doit être inventée. Si
l'objet est déjà parenté, partagé ou manipulé par un autre script, le test est
abandonné.

## Tests d'acceptation

- observer l'objet avant, pendant et après `mode1` ;
- vérifier la main, l'orientation et l'absence de clipping pendant toute la
  boucle `%%ctuneco` ;
- déclencher l'alarme et tuer AL2_11 pendant la lecture ;
- sauvegarder/recharger avant et après l'attache ;
- confirmer qu'une seconde entrée dans `mode1` ne duplique pas l'objet ;
- vérifier que `leo1` reste enfant du même objet et qu'aucune autre copie de
  `k_leo_` n'est déplacée.

Sans point de retour officiel pour le livre, le premier essai reste visuel et
jetable : aucune promotion n'est autorisée tant que les sorties alarme/mort et
rechargement ne sont pas propres.
