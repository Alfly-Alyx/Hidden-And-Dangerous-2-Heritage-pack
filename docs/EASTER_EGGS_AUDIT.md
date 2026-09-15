# Audit des easter eggs

## Résultat

Sept easter eggs du jeu de base sont identifiables. Six sont documentés publiquement. Le septième, dans Africa 4, est complet dans les fichiers d'origine mais neutralisé par le patch 1.12.

L'entretien du studio de 2004 indique qu'aucun nouvel easter egg de ce type n'a été ajouté à Sabre Squadron, notamment à cause des problèmes de classification causés par les scènes macabres.

Sources publiques :
- https://hd2.fandom.com/wiki/Easter_eggs
- https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats
- https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/

## Repérage spatial reproductible

`tools/easter_egg_position_audit.py` relit les couches commerciales effectives et
consolide 36 cadres utiles dans
`output/audit/easter-egg-world-positions.json`. Le lecteur distingue désormais
le champ `0x20`, position locale relative au parent, du champ `0x2C`, position
mondiale. Cette distinction corrige notamment les bouteilles 2 à 10 de Normandy 1
et les trois volumes d'Alps 2, dont les valeurs locales proches de l'origine ne
représentaient pas leur emplacement réel sur la carte.

## Tutorial

Le lingot d'or, l'interrupteur, les cibles et le déclencheur subsistent. L'audit reproductible `tools/tutorial_easter_egg_audit.py` confirme onze liaisons actives : le bouton alimente `la_Bedford_1` et révèle l'objet 245, l'activateur exige cet objet, puis lance quatre cibles successives et cinq feux d'artifice. `T_EE_Weather.scr` et `T_EE_Light.scr` sont des vestiges distincts sans liaison commerciale au secret ; les ajouter ici serait une reconstruction non attestée.

La route historique utilise le capot et le toit du Bedford pour atteindre le garage. La comparaison des correctifs officiels montre que le 1.06 ne livre que des binaires moteur, alors que le 1.12 remplace aussi le moteur et ajoute `Patch.dta`. Les témoignages d'époque attribuent précisément la rupture à la désactivation de l'escalade des véhicules. Remplacer le moteur 1.12 par celui du 1.06 sacrifierait la compatibilité Sabre Squadron et les correctifs ultérieurs : cette méthode est exclue. Le paquet ne déplace pas encore le lingot ; une adaptation physique locale, clairement étiquetée, reste confiée au laboratoire expérimental.

Les ancres mondiales survivantes sont le Bedford
(-17,804197 ; -1,512808 ; 80,766449), le modèle d'alarme contenant
l'interrupteur (-52,354725 ; 1,906093 ; -2,890001) et le volume où apporter le
lingot (57,962864 ; 1,353687 ; 41,821579). Le bouton
`M_ALAR_1.Cylinder01` est un sous-nœud du modèle `M_ALAR_1` : il hérite de
sa transformation au lieu de porter une position autonome dans `scene2.bin`.

## Africa 1 - Spaghetti Airport

Le script exige quatre morts liées à l'officier et au jeep. La version d'origine met mrtvi_panaci à 1 ; le patch 1.12 force cette valeur à 0, ce qui rend l'activation impossible. Les trois personnages, l'armure rouge, le portail de feu et la caméra sont encore présents. Le paquet restaure la valeur d'origine.

Les deux tonneaux rouges parfois cités dans les guides ne sont pas exigés par le déclencheur officiel inspecté.

Le propriétaire `dummy_ee` du déclencheur se trouve en
(183,752380 ; 0,113866 ; 87,638565). L'officier `AF1_21` commence en
(6,329951 ; 0,543395 ; 71,905884) et le jeep en
(-48,694279 ; 0,261597 ; -205,161865). Ces positions confirment que le script
teste leur arrivée auprès de son propre volume caché ; elles ne remplacent pas
la procédure joueur, qui les y conduit en déplaçant le corps et le véhicule.

## Burma 1 - Anthill

Trois crânes envoient chacun un signal. L'activation ne part que si tous les ennemis sont déjà morts au moment où le troisième crâne est détruit. L'ordre est donc essentiel.

L'audit reproductible `tools/burma1_easter_egg_audit.py` confirme les quatre liaisons du registre (`BU1_EE`, `lebka`, `lebka2`, `lebka3`), le compteur à trois, la garde sur le nombre d'ennemis et les trois silhouettes déclenchées. Il décode aussi les positions exactes dans `scene2.bin` du Patch 1.12 :

- `lebka` : 12,628406 ; 3,475543 ; -18,529207 ;
- `lebka2` : -109,692360 ; -3,072645 ; 106,144691 ;
- `lebka3` : -135,529770 ; -4,413265 ; 49,811054.

Le premier est proche du centre de l'étendue de scène ; les deux autres occupent son bord occidental. Ces coordonnées permettront une carte annotée exacte. Les repères visuels définitifs restent à confirmer par captures en jeu avant de remplacer dans le guide joueur la consigne générale « cherchez les trois crânes ».

## Alps 1 - Babes in the Wood

Quatre membres de l'équipage du half-track doivent être réunis à moins de deux mètres du point caché sur le rocher. Le script ne teste pas explicitement leur état, mais la procédure prévue consiste à y porter les quatre corps.

Le centre mondial exact du volume `kwdet` est
(156,910172 ; 1,257552 ; 15,105836).

## Alps 2 - Estate Agent

Un lingot doit entrer successivement dans trois zones : bibliothèque, pièce secrète des tableaux et archives. Les déclencheurs s'enchaînent ; déposer les lingots dans un autre ordre ne suffit pas.

Les centres mondiaux, dans l'ordre imposé, sont :

- `eggdetect1` : -13,254289 ; 3,046833 ; 20,740532 ;
- `eggdetect2` : 5,695766 ; 6,016600 ; -7,736698 ;
- `eggdetect3` : 19,067347 ; 6,579298 ; 27,229118.

## Normandy 1 - Lighthouse

Chaque bouteille bleue détruite incrémente le compteur. À dix, le garde ivre reçoit le signal. Il doit être abattu après la dernière bouteille.

Les positions mondiales des dix bouteilles, dans l'ordre de leurs noms
internes, sont :

- `bottle` : -5,417812 ; 3,665698 ; 95,444359 ;
- `bottle2` : 2,530323 ; 4,526854 ; 86,612473 ;
- `bottle3` : 16,911974 ; 5,123803 ; 75,043686 ;
- `bottle4` : 18,080017 ; 4,478304 ; 54,560055 ;
- `bottle5` : 14,906191 ; 5,661610 ; 38,712833 ;
- `bottle6` : -0,291585 ; 4,926290 ; 48,978054 ;
- `bottle7` : -9,968625 ; 3,660000 ; 37,328491 ;
- `bottle8` : -12,101370 ; 5,661610 ; 37,737965 ;
- `bottle9` : -19,799259 ; 3,817951 ; 49,910294 ;
- `bottle10` : 16,675560 ; -0,301945 ; 74,891029.

Le garde `N48` se trouve initialement en
(-5,672054 ; 4,121909 ; 95,740288).

## Africa 4 - septième easter egg

Les clés A, B et C portent les identifiants 240, 241 et 242. Le script d'origine vérifie qu'elles sont toutes dans un rayon de trois mètres. Le patch 1.12 redirige alors l'exécution vers la fin au lieu du bloc ACTIVATED. La scène contient toujours meteor01, sa trajectoire et l'effet de particules. Le paquet restaure ce saut.

L'audit reproductible `tools/africa4_key_trigger_audit.py` décode les trois
enregistrements de placement de `items.dat`, contrôle leurs rotations et
vérifie les liaisons exactes du registre. Positions relevées :

- clé A, objet 240 / instance 317 : 11,214910 ; 0,264778 ; -5,249491,
  secteur sud-ouest de l'enceinte ;
- clé B, objet 241 / instance 318 : 31,565689 ; 0,334397 ; 14,565742,
  secteur central-est ;
- clé C, objet 242 / instance 319 : 37,451393 ; 0,644349 ; 35,168266,
  secteur nord-est.

Le futur guide joueur traduira ces coordonnées en repères visuels après le
test en jeu des deux propriétaires du déclencheur. Tant que ce test n'est pas
fait, aucun point de dépôt unique n'est présenté comme certain.

Le registre commercial contient une particularité jusque-là non documentée :
`AF3b_ee_activator.scr` est affecté à deux propriétaires,
`w_mg42Lie_00` (49,037258 ; 6,798772 ; -22,116121) et
`dummy_ee_activator` (0,377980 ; -4,089648 ; 2,210202). Comme
`_ItemInRange` est évalué relativement au propriétaire du script, la formule
« réunir les clés n'importe où » n'est pas suffisamment démontrée. Le
rétablissement du saut original conserve les deux liaisons officielles ; un
essai en jeu doit encore dire si les deux volumes sont actifs ou si l'un est un
vestige inerte avant de figer le repère dans la prochaine édition du guide
joueur.
