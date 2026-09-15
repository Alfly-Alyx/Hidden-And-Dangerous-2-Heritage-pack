# Normandy 2 [Prototype — défense élargie]

État : **quinze modules d'acteurs définis, placements/items manquants**, 14
septembre 2026. Normandy2 release reste le choix par défaut.

## Verdict

Quinze scripts substantiels sont orphelins et leurs acteurs ont disparu :
`Blue_12`, `Blue_16`, `Red_6`, `Red_9`, `Red_11`, `Red_12`, `Red_18`,
`Red_21`, `Red_24`, `Red_34`, `Red_37`, `Wave1_2`, `Wave1_4`, `Wave2_4` et
`Wave2_5`. Tous les chemins réellement nommés par ces scripts survivent.

La composition retirée est confirmée plus fortement pour Blue12/16 et les
quatre Wave : `R_N2_fake_defence_sender`, `R_N2_Waves`, le pilote du char allié
et `R_N2_End_Killer` commentent explicitement leurs déclarations ou émissions.
Les neuf Red ont des scripts et plusieurs émetteurs commentés, mais leurs
placements restent à déduire.

La variante additive s'appelle
`Normandy 2 [Prototype — défense élargie]`. Chaque acteur est activable
séparément ; aucun groupe ne remplace le roster release.

## Coordination avec le réseau Legacy

Le dossier `../NORMANDY2_LEGACY_GO_NETWORK/ETUDE.md` étudie les contrôleurs
`R_N2_Go_1..14` retirés. Cette route déplaçait les cinq alliés et n'est pas
requise pour recréer les défenseurs. Les deux options doivent être testées
séparément avant une combinaison, car `fake_defence_sender` choisit justement
un allié comme destinataire du signal 25.

## Chemins conservés

`check2.bin` contient une occurrence de chacun des repères suivants :
`Red11_1/2/3/END`, `Red12_1/2`, `Red18_1`, `Red21_1`,
`Red24_1/2/3`, `Red34_1`, `Red35_1`, `Red37_1`, `Red6_1`, `Red9_1`,
`W1man2_1`, `W1man4_2/4`, `W1manX_1/3`, `X10`, `X13`.

La présence d'une route ne fixe ni le transform initial, ni l'uniforme, ni
l'arme. Leur provenance et leur niveau de déduction sont consignés dans
`MATRICE_ACTEURS.md`.

## Raccords d'activation

### Raccords attestés à rétablir dans la copie

- Blue12 et Blue16 : signal 10 depuis la copie de `R_N2_Waves` ;
- Wave1_2 et Wave1_4 : signal 1 depuis cette même copie ;
- Wave2_4 et Wave2_5 : signal 1 depuis la copie du pilote de char allié ;
- Red6 et Red11 : signal 20 de `Red_5`, commenté ;
- Red12, Red18, Red21, Red34 et Red37 : signaux 1, 4, 5, 8 et 7 des
  détecteurs homonymes, tous commentés ;
- Red24 : signal 30 de son activateur entièrement commenté.

Ces lignes sont des vestiges officiels, mais leur réactivation n'est sûre que
si l'acteur correspondant existe. Chaque émetteur est donc gardé par l'option
de module et ne doit jamais viser une frame vide.

Red9 possède son propre déclencheur de proximité à 18 unités ; aucun émetteur
extérieur n'est nécessaire. Wave2_4/5 contiennent encore deux déplacements
vides commentés : ne pas inventer de route pour ces emplacements.

## Objectifs et fin

Une copie du contrôleur `R_N2_OBJ4` peut ajouter Blue12 et Blue16 à son scan de
pertes. Le seuil release de départ du char (`> 8`) est conservé lors du premier
test ; le relever serait un choix d'équilibrage moderne. Le commentaire final
et le seuil `> 13` sont liés au roster réduit : avec 17 Blue, une proposition
moderne cohérente est `> 15`, à valider par instrumentation.

Les treize autres ennemis ne sont pas des Blue alliés et ne doivent pas être
injectés dans ce compteur. La variante leur réserve un objectif secondaire
moderne « neutraliser les défenseurs supplémentaires », compté par un
contrôleur séparé et désactivable. La fin principale ne dépend pas de ce bonus.

La copie de `R_N2_End_Killer` doit résoudre les quinze frames et neutraliser
les survivants après le signal final, afin qu'aucun acteur suspendu ne continue
après la fin. Le code commercial commenté atteste déjà ce nettoyage pour les
six Blue/Wave ; son extension aux neuf Red est étiquetée `MODERNE`.

## Sauvegarde, IA et équilibrage

Le masque des quinze options, leur état d'activation, le compteur bonus et les
deux seuils Blue doivent être versionnés ensemble. Tester acteur par acteur,
puis par famille et enfin tous ensemble : navigation, collisions, friendly
fire, arrivée des vagues, charge CPU, munitions, difficulté, mort anticipée et
sauvegarde/reprise.

Critère de retrait : désactiver les quinze options doit retrouver la scène, le
graphe de signaux, les objectifs et les seuils release sans résidu.

