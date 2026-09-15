# Audit des easter eggs

## Résultat

Sept easter eggs du jeu de base sont identifiables. Six sont documentés publiquement. Le septième, dans Africa 4, est complet dans les fichiers d'origine mais neutralisé par le patch 1.12.

L'entretien du studio de 2004 indique qu'aucun nouvel easter egg de ce type n'a été ajouté à Sabre Squadron, notamment à cause des problèmes de classification causés par les scènes macabres.

Sources publiques :
- https://hd2.fandom.com/wiki/Easter_eggs
- https://gamefaqs.gamespot.com/pc/451072-hidden-and-dangerous-2/cheats
- https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/

## Tutorial

Le lingot d'or, l'interrupteur, les cibles et le déclencheur subsistent. L'audit reproductible `tools/tutorial_easter_egg_audit.py` confirme onze liaisons actives : le bouton alimente `la_Bedford_1` et révèle l'objet 245, l'activateur exige cet objet, puis lance quatre cibles successives et cinq feux d'artifice. `T_EE_Weather.scr` et `T_EE_Light.scr` sont des vestiges distincts sans liaison commerciale au secret ; les ajouter ici serait une reconstruction non attestée.

La route historique utilise le capot et le toit du Bedford pour atteindre le garage. La comparaison des correctifs officiels montre que le 1.06 ne livre que des binaires moteur, alors que le 1.12 remplace aussi le moteur et ajoute `Patch.dta`. Les témoignages d'époque attribuent précisément la rupture à la désactivation de l'escalade des véhicules. Remplacer le moteur 1.12 par celui du 1.06 sacrifierait la compatibilité Sabre Squadron et les correctifs ultérieurs : cette méthode est exclue. Le paquet ne déplace pas encore le lingot ; une adaptation physique locale, clairement étiquetée, reste confiée au laboratoire expérimental.

## Africa 1 - Spaghetti Airport

Le script exige quatre morts liées à l'officier et au jeep. La version d'origine met mrtvi_panaci à 1 ; le patch 1.12 force cette valeur à 0, ce qui rend l'activation impossible. Les trois personnages, l'armure rouge, le portail de feu et la caméra sont encore présents. Le paquet restaure la valeur d'origine.

Les deux tonneaux rouges parfois cités dans les guides ne sont pas exigés par le déclencheur officiel inspecté.

## Burma 1 - Anthill

Trois crânes envoient chacun un signal. L'activation ne part que si tous les ennemis sont déjà morts au moment où le troisième crâne est détruit. L'ordre est donc essentiel.

## Alps 1 - Babes in the Wood

Quatre membres de l'équipage du half-track doivent être réunis à moins de deux mètres du point caché sur le rocher. Le script ne teste pas explicitement leur état, mais la procédure prévue consiste à y porter les quatre corps.

## Alps 2 - Estate Agent

Un lingot doit entrer successivement dans trois zones : bibliothèque, pièce secrète des tableaux et archives. Les déclencheurs s'enchaînent ; déposer les lingots dans un autre ordre ne suffit pas.

## Normandy 1 - Lighthouse

Chaque bouteille bleue détruite incrémente le compteur. À dix, le garde ivre reçoit le signal. Il doit être abattu après la dernière bouteille.

## Africa 4 - septième easter egg

Les clés A, B et C portent les identifiants 240, 241 et 242. Le script d'origine vérifie qu'elles sont toutes dans un rayon de trois mètres. Le patch 1.12 redirige alors l'exécution vers la fin au lieu du bloc ACTIVATED. La scène contient toujours meteor01, sa trajectoire et l'effet de particules. Le paquet restaure ce saut.

Positions relevées :

- clé A : 11,21 ; 0,26 ; -5,25, secteur sud-ouest de l'enceinte ;
- clé B : 31,57 ; 0,33 ; 14,57, secteur central-est ;
- clé C : 37,45 ; 0,64 ; 35,17, secteur nord-est.

Le guide joueur traduit ces coordonnées en repères visuels et explique comment réunir les trois clés.
