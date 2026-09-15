# Objectifs, actions et chemins

## Quatorze ensembles d'objectifs fragiles confirmés

### Africa 1 - Airfield (mode Carnage)

Le catalogue commercial conserve un huitième objectif, « Tuez l'ennemi », prévu pour les types de partie Carnage 3 et 7. L'acteur `dummy_carnage` est toujours relié à `AF1_obj_carnage.scr`; ce script contient encore l'initialisation de l'objectif 8, le comptage officiel `_GetCountOfCarnageEnemies()` et sa validation, mais toutes les lignes utiles sont commentées dans la version de base comme dans le patch 1.12.

Le paquet retire uniquement les marques de commentaire de ce bloc officiel. L'objectif reste limité aux deux types Carnage prévus et ne modifie pas la campagne normale.

### Arctic 3 - Mole in a Hole

Le script suit deux hommes du bateau, mais l'un est tué par une autre séquence. Selon le trajet choisi, le joueur peut parfois éviter le déclencheur problématique. Le bon diagnostic est donc : objectif mal scripté et dépendant de la route, pas impossible dans tous les cas.

Le correctif remplace la référence inexistante Amik_2 par le survivant Amik_1. Les deux routes doivent être testées.

### Arctic 2 - Scout in the Arctic

Les cinq emplacements de dynamite possèdent chacun leur acteur, leur script et une paire de signaux vers le gestionnaire. Quatre charges suffisent à l'objectif principal 3 « Poser des explosifs aux emplacements appropriés » ; les cinq doivent valider l'objectif optionnel 6 « Explosifs posés dans tous les emplacements appropriés ».

Lorsque le compteur atteint cinq, le script écrit pourtant 99 dans l'état 5, réservé à l'alarme et à l'objectif de discrétion, au lieu de l'état 6. Le contrôleur final initialise explicitement l'état 6 en indiquant qu'il doit être alimenté par ce gestionnaire, puis ne valide l'objectif 6 que si cette valeur vaut 99. Le paquet remplace donc uniquement cette écriture 5 par 6. Les cinq charges valident de nouveau leur objectif et ne font plus échouer à tort la discrétion.

### Lumière de l'interrupteur d'Arctic 2

Le même niveau conserve une lumière dynamique nommée `1sut-vratnice`. L'acteur `g_zasuv47` est toujours relié à `R_Arc1B_Vypinac.scr`, et la version 1.12 de `scene2.bin` contient encore exactement ce cadre. Le script bascule déjà les deux modèles d'ampoule `m_svet_3` et `m_svet_4`, la lightmap `Blikni_si` et l'état sauvegardé 21, mais ses cinq commandes de la lumière dynamique ainsi que sa déclaration ont été commentées ensemble.

Le paquet réactive ces lignes à leur emplacement d'origine. La lumière dynamique complète donc le rendu existant sans remplacer la lightmap ni modifier les signaux envoyés aux gardes lorsque la pièce est plongée dans le noir.

### Boutons d'alarme de Sicily 1

Les six boîtiers `M_ALAR_` à `M_ALAR_6` sont placés une fois chacun et reliés aux six scripts `Sic1_alarm_buton1.scr` à `Sic1_alarm_buton6.scr`, aussi bien en solo qu'en coopération. Le modèle commercial `M_ALAR01.4ds` conserve son nœud `Cylinder01`. Les scripts d'Arctic 2 et de Czech 6 confirment le même usage actif : le bouton disparaît quand l'alarme est enclenchée et réapparaît lorsqu'elle est coupée.

Dans Sicily 1, la déclaration du nœud et les quatre changements d'état visuel étaient commentés ensemble dans les douze scripts, alors que les sons, l'état de l'alarme et le distributeur global restaient actifs. Le paquet réactive uniquement cette animation de bouton ; il ne change ni les sons ni le déroulement de l'alerte.

### Africa 2 - Airshow

La destruction du blindé existe, mais le signal ne rejoint pas correctement la validation optionnelle. Le correctif relie cette condition au gestionnaire qui neutralise déjà le véhicule.

### Normandy 2 - Blade Dancer

Le compteur de survivants n'est recalculé qu'après une première mort. Si les cinq alliés survivent, l'état parfait n'existe pas. Le correctif refait donc le décompte des cinq acteurs au moment de la validation finale.

### Libye 3 - Sitting Duck

Le catalogue officiel contient un quatrième objectif optionnel, « Tous les membres de l'unité doivent survivre », mais le gestionnaire de fin ne le valide jamais. La mission voisine Libye 2 emploie déjà la même fonction de contrôle au moment de l'extraction. Le paquet rétablit donc cette validation à la réception du signal final, hors mode où cet objectif n'est pas applicable.
### Africa 6 - Flying Fish

L'objectif 2 officiel, « Tous les membres doivent survivre », est initialisé comme caché. Au moment où le vol dans le canyon est réussi, les quatre lignes qui vérifient la survie de l'équipe et valident cet objectif sont encore présentes, mais entièrement commentées dans les versions de base et 1.12. Le paquet réactive exactement ce bloc, hors mode où la règle de survie n'est pas applicable.

### Africa 5 - Operation Challenger

L'objectif 8 dépend de cinq avions distincts. Le gestionnaire initialise bien les états 21 à 24, puis initialise une seconde fois l'état 24 au lieu de l'état 25. Les cinq scripts d'avion sont reliés, chacun met à zéro son état propre de 21 à 25 et avertit ce gestionnaire. Cette faute fait donc compter le cinquième avion comme déjà détruit.

Le correctif remplace uniquement la seconde initialisation de 24 par 25. L'objectif exige de nouveau les cinq destructions prévues, sans créer de condition ni de cible.

### Burgundy 1 - Business

Après le contact avec la Résistance, la version solo active le sabotage du dépôt de munitions mais laisse entièrement commenté le bloc qui révèle le second sabotage, le dépôt de carburant. La variante coopérative conserve exactement ce même bloc actif, tandis que le script solo du dépôt de carburant est complet : pose de l'explosif, destruction, sauvegarde et validation de l'objectif 3.

Le paquet réactive uniquement ces quatre lignes officielles. Il ne crée ni objectif, ni cible, ni condition nouvelle.

### Libye 2 coopératif - parc automobile

La liste multijoueur commerciale ne déclare que les deux objectifs principaux 15520 et 15521. Le contrôleur coopératif conserve pourtant l'objectif 3 complet : `AF2_obj3.scr` surveille cinq Opel, deux Opel Flak et le Kübelwagen, puis envoie le signal 1 lorsque les huit véhicules ennemis sont détruits ; `AF2_objective.scr` reçoit ce signal, valide l'objectif 3 et affiche son texte de réussite. Le texte officiel 15523 « Provoquez le plus de dégâts possibles aux véhicules ennemis » est présent dans toutes les langues du jeu.

Le paquet ajoute uniquement l'entrée 15523 au bloc `Co_Libye2` de la liste multijoueur. Les acteurs, le compteur, la condition et la validation restent ceux de Sabre Squadron. Les deux Jeeps ne font pas partie de ce compteur, car elles servent aussi de véhicules de sortie et leur destruction totale fait échouer la mission.

L'objectif 4 de survie est différent : son nom 15524 et son initialisation commentée subsistent, mais la version coopérative n'a plus la vérification de fin présente en solo. Comme les joueurs coopératifs peuvent mourir et réapparaître, son sens et son mécanisme ne peuvent pas être déduits par une simple copie. Il reste donc dans le module expérimental.
### Brest coopératif - explosifs sur les générateurs

Le catalogue solo déclare l'objectif 5, texte 15504 « Placez des explosifs sur les générateurs ». La variante coopérative conserve `obj_gener.scr` à l'identique : elle vérifie les deux explosifs `explgen` et `explgen2`, valide l'objectif 5 et retire la validation si l'une des charges disparaît. L'acteur libre `OBJ_gener` est présent dans la scène, mais aucune liaison n'existe dans les deux registres coopératifs et le bloc multijoueur ne déclare que les quatre premiers objectifs.

Le paquet ajoute l'entrée 15504 et relie `OBJ_gener` à `obj_gener.scr` dans `Scripts.dta` et `MPScripts.dta` de la mission. Aucune condition n'est inventée : après correction, la chaîne est strictement celle du solo officiel.

### Burgundy 1 coopératif - infiltration et pose discrètes

La liste coopérative s'arrête aux quatre objectifs principaux, alors que `bu1_objective_05.scr` est déjà relié et conserve deux validations distinctes tant que l'état d'alarme 70 reste nul : entrer dans la zone de l'entrepôt valide l'objectif 5, et poser les trois explosifs valide l'objectif 6. Les textes officiels 15566 et 15567 décrivent exactement ces deux actions.

La copie coopérative du contrôleur diffère de la copie solo active par un seul caractère : la branche `obj6done` valide par erreur une seconde fois l'objectif 5. Le paquet remplace ce 5 par 6, ce qui rend les deux fichiers identiques, puis ajoute les deux textes au bloc `Co_Burgundy1`. L'objectif 7 de survie reste séparé : sa vérification est commentée et sa sémantique en présence de réapparitions coopératives doit être reconstruite avant activation.
### Burgundy 3 coopératif - chaîne des prisonniers

La liste multijoueur déclare en premier l'objectif « Sauvez le plus de prisonniers possible ». Son contrôleur conserve pourtant l'activation de l'objectif 1 à l'état caché, cinq validations commentées autour du compteur `done==3` et l'échec commenté si moins de quatre prisonniers restent en vie. Les trois sous-objectifs qui alimentent ce compteur — contacter le premier SAS, contacter le commandant et libérer le dernier groupe — sont tous actifs. Le paquet réactive donc l'objectif principal, ses cinq points de validation possibles selon l'ordre des rencontres et son échec officiel.

Le dernier groupe de quatre prisonniers avait aussi une condition logique incohérente : il fallait sauver une paire complète, tandis que la perte d'une paire complète provoquait l'échec. Deux survivants répartis entre les paires ne validaient ni succès ni échec, et la récompense optionnelle « tous les prisonniers » pouvait être attribuée après une perte isolée. La version solo fournit la règle de référence : le groupe réussit si au moins un des quatre survit et échoue seulement si les quatre meurent. Le correctif aligne la coopération sur cette règle et ajoute un signal interne lorsque le sauvetage est partiel, afin que l'objectif optionnel « tous les prisonniers » ne soit plus validé à tort.
### Czech 2 - sortie avec Freiberg

Le catalogue commercial contient l'objectif 2 « Quittez la zone ». Après la capture du colonel Freiberg, le contrôleur valide bien l'objectif 1, mais n'active jamais l'objectif 2. Le déclencheur endgame.scr vérifie pourtant que tous les joueurs et Freiberg se trouvent dans la zone de sortie, puis envoie le signal 2 au contrôleur ; celui-ci ne possède aucun gestionnaire pour ce signal.

Le paquet active donc l'objectif 2 au moment exact où la capture est validée, puis utilise le signal 2 commercial pour le terminer. La zone, Freiberg, la condition collective et le signal sont tous conservés ; aucune nouvelle condition n'est créée.

## Emplacements Carnage triés

- **Africa 3, objectif 6** : l’acteur `dummy_carnage` est relié et le script conserve le test `_AllEnemiesDead()`, l’activation et la validation, mais tout le bloc est commenté. Surtout, la garde qui limite normalement ce type d’objectif aux modes Carnage 3 et 7 n’existe plus dans ce fichier. Une simple décommentation afficherait un doublon de l’objectif 2 en campagne normale. La restauration est donc réalisable, mais reste expérimentale tant que cette garde reconstituée n’a pas été testée.
- **Czech 3, objectif 4** : le texte générique « Tuez l’ennemi » duplique sémantiquement l’objectif 1. Les variantes normale et Carnage emploient toutes deux les objectifs 1 à 3 et aucun corps de validation de l’objectif 4 ne subsiste. Il s’agit d’un emplacement de catalogue obsolète, pas d’un objectif secondaire prouvé.
- **Libye 3, objectif 6** : il répète exactement le texte de l’objectif 5. Le contrôleur actif initialise et valide déjà l’objectif 5 dans les modes Carnage ; aucun appel à l’objectif 6 n’est conservé. Ce sixième emplacement est donc classé comme doublon technique.

## Objectifs composés et actions désactivées

Le cas le plus net est CASTLE2 : quatre objectifs structurés subsistent et un cinquième, récupérer les armes saisies, est entièrement commenté. Les scripts secondaire et de réussite existent encore. Cela confirme qu'une action complète a été retirée de la chaîne avant la version finale.
Africa 5 conserve également une étape officielle « Forcer Hans Schumann à coopérer ». Son activation exacte est commentée après la découverte de Schumann, mais sa validation a disparu : la conversation complète passe directement de l'objectif 1 à l'évasion. Le point de validation le plus logique est la fin de cette conversation, mais l'ajout de cette ligne serait une reconstruction minimale. Le cas est donc transmis au module expérimental et n'entre pas encore dans la restauration stable.

L'hypothèse d'un objectif jadis validé par trois actions puis réduit à une doit être traitée mission par mission. Un texte, un objet ou un script résiduel ne suffit pas. Il faut réunir :

- les trois déclencheurs ;
- leur état persistant ;
- le gestionnaire qui les compte ;
- le texte d'objectif ;
- une route praticable pour chaque action.

### Chaînes à plusieurs actions vérifiées

- **Arctic 2** : les cinq poses de dynamite et leurs dix signaux sont actives ; seule l'écriture finale vers le mauvais état empêchait l'objectif optionnel des cinq charges.
- **Norway** : deux mines magnétiques sur le Tirpitz alimentent une première étape, la mine du chalutier une deuxième et l'Enigma, objet 253, une troisième. Les trois signaux 5, 6 et 7 alimentent bien le compteur central ; les commentaires annonçant une rupture sont périmés.
- **Normandy 2** : les trois tireurs d'élite envoient tous leur validation et les cinq alliés envoient tous le signal de survie. L'état parfait absent lorsque personne ne mourait est réparé ; les erreurs de riposte Blue sont traitées séparément car elles n'altèrent pas le compteur de l'objectif.
- **Sicily 2** : le déminage vérifie simultanément les six charges du pont, les trois chars alimentent l'objectif optionnel correspondant et la défense finale attend à la fois la sécurisation et le déminage. Aucun maillon obligatoire n'est absent. Les `SendSignal(MyFRM, 1)` commentés dans les neuf scripts de charge sont explicitement encadrés par `Test - start/end` ; les réactiver ferait exploser les charges automatiquement. Une branche historique distincte subsiste toutefois : la deuxième vague peut partir lorsque trois charges atteignent l'état 3, et les six scripts conservent la transition 0→3 commentée. Cette transition ne peut pas être rétablie seule, car l'objectif de déminage attend les six états 0. Le laboratoire doit donc compter les charges retirées sans modifier leur état, afin de préserver à la fois ce déclencheur et la réussite de l'objectif.
- **Africa 3** : la découverte du véhicule par le mécanicien et l'élimination des ennemis incrémentent séparément le compteur qui autorise la radio. Le détecteur de véhicule restauré ne double pas ce compteur.
- **Burgundy 1 solo** : les trois explosifs du sixième objectif sont tous suivis ; les deuxième et troisième partagent un gestionnaire et le premier possède le sien.
- **Burgundy 2 solo** : l'officier, le collaborateur et l'élimination du groupe alimentent encore les trois indicateurs attendus avant la sortie.
- **Burma 1** : les conditions du pont, des documents et de l'extraction sont actives, avec une exigence supplémentaire d'élimination en mode Carnage.
- **Burma 2** : la prise du bunker attend toujours la mort des deux gardes `BU2_06` et `BU2_22`, chacun relié au même compteur.
- **Burma 2, mise en scène du bunker** : l'approche de `BU2_22_A2` signalait encore au garde `BU2_22` de se lever et de passer en alerte, mais son tir vers `BU2_22_shoot01` était commenté. La cible et le déclencheur existent ; le tir est restauré sans réduire ni remplacer les deux morts requises pour l'objectif.
- **Libye 2 coopératif** : les huit véhicules ennemis surveillés alimentent encore l'objectif optionnel 3 ; seule sa déclaration dans la liste multijoueur manquait.
- **Libye 3 coopératif** : l'officier, l'équipement du Liberator et les réserves de carburant alimentent chacun `last_objectives`; le rassemblement final ne s'active qu'à trois.
- **Brest coopératif** : les deux charges des générateurs sont encore vérifiées par le script solo recopié à l'identique ; l'acteur et l'objectif 15504 manquaient seulement de liaison et de déclaration.
- **Burgundy 1 coopératif** : l'infiltration sans alarme et la pose des trois explosifs sans alarme sont deux validations distinctes ; le second gestionnaire écrivait seulement dans le mauvais numéro d'objectif.
- **Burgundy 3 coopératif** : les trois rencontres alimentent encore `done`; l'objectif principal qui les regroupait était complet mais commenté et est maintenant restauré.

### Faux signaux écartés

Dans Africa 1, le détecteur de portée de `AF1_23` double une activation autonome déjà présente et le dialogue `dummy_dabing_01` est lancé par la même cinématique globale que son émetteur. Dans Libye 3, le second occupant du camion est déjà embarqué comme tireur et suit physiquement le véhicule ; l'absence de gestionnaire pour le signal de mouvement n'est pas une action d'objectif manquante.

Dans Libye 1 coopératif, `AF1_obj2_succ_sender.scr` et l'ancien gestionnaire du signal 3 appartiennent à une première version de l'objectif 2 où les deux prisonniers devaient survivre. Le fichier se désactive explicitement et le contrôleur indique que cette condition a été remplacée par l'élimination des trois officiers, dont la validation est complète et active. Réactiver le signal 3 écraserait donc le sens de l'objectif livré au lieu d'ajouter une action secondaire. La conversation voisine des gardes reste, elle, une reconstruction expérimentale distincte : ses douze répliques sont commentées et son compteur de synchronisation n'a plus qu'un seul émetteur.

Dans Libye 2, `AF2_obj3.scr` envoie aussi un signal 2 lorsque tous les véhicules, y compris les moyens d'extraction, sont détruits. Le contrôleur ne le reçoit pas, mais il surveille déjà directement la même condition et fait échouer l'extraction : ajouter un second gestionnaire doublerait cette conséquence. Dans Burgundy 2 coopératif, les signaux 3 et 4 de `detect_motopryc.scr` proviennent au contraire des anciennes fuites solo ; les scripts coopératifs des deux fugitifs ne conservent plus leurs trajets en voiture ou à moto. Ces signaux sont donc inatteignables sans recréer d'abord les routes supprimées.

Ces cas restent documentés, mais ne sont pas modifiés dans la restauration stable.

L'audit continue sur les autres compteurs, en exigeant la même chaîne de preuve avant toute activation stable.

## Route française restaurée

Operation Overlord - Lighthouse se déroule en France. La version commerciale garde cinq caméras, deux trajectoires et les deux accès souterrains, mais la liaison qui devait lancer le guidage est absente. Le paquet reconnecte Spawnsingle01 à X_N1_player01.scr.

Cette restauration ne crée pas un tunnel. Elle rétablit le choix visuel d'origine entre les accès déjà présents.

Les autres fichiers X_N1_*_A* isolés ne prouvent pas de nouvelles routes complètes. Le registre commercial conserve déjà les approches N12_A1 à N12_A4, N14_A1 à N14_A3 et N17_A1/N17_A2 en les reliant à des scripts communs fonctionnels. N14_A2 est un doublon, tandis que l'ancien N17_A2 envoie un signal que son destinataire ne traite pas. Les activateurs N12_A5, N13_A2, N13_A3, N24_A1 et N25_A1 n'ont plus d'acteur ni de position. Les gardes N24 et N25 restent néanmoins activés en solo par l'alarme de N01, et leurs chemins sont présents. Un réveil direct de proximité en solo est donc étudié comme variante additive expérimentale, pas comme correction stable prouvée.

## Seconde route de Brest restaurée

La mission Brest conserve deux détecteurs d'approche, `detectorzone3aktiv1` et `detectorzone3aktiv2`, à deux emplacements distincts. La version commerciale relie toutefois les deux au premier script. Le second script original est encore complet et envoie au soldat `z3_ven4` le signal 2, qui lance sa patrouille `z3ven4_01` puis `z3ven4_02`; le signal 1 du premier passage le laisse dans son autre comportement.

La même erreur de liaison subsiste dans les deux registres de la variante coopérative `Co_brest`. Le paquet corrige donc le second détecteur en solo et dans les deux registres coopératifs. Il ne déplace aucun acteur et ne crée aucune logique : il restaure l'embranchement déjà présent dans les données commerciales.

La variante coopérative conserve aussi l'acteur `hint` exactement à la position solo et le même script `hint.scr`, mais sans la liaison solo `hint → hint.scr`. Le paquet la rétablit afin que le conseil contextuel officiel 15600 apparaisse de nouveau à cet emplacement.

## Seconde approche du civil 03 dans Alps 1

Alps 1 contient deux petits détecteurs placés à des coordonnées distinctes devant le civil bûcheron. `ci03alarmer` est relié et agit à trois mètres ; `ci03alarmer1`, placé un peu plus loin sur l'autre approche, était resté sans liaison malgré son script complet à deux mètres. Les deux envoient le signal 8 à `ci_03`, dont le script conserve le comportement d'alarme correspondant.

## Gardes de forge dormants dans Alps 1

Les détecteurs `detector_forge16`, `detector_forge20` et `detector_forge30` contiennent quatre envois commentés vers `ge_10`, `ge_11` et `ge_43`. Ces trois soldats sont présents et reliés ; leurs signaux 1 ou 2 les sortent de suspension, les conduisent dans leurs boucles existantes et utilisent quinze points encore présents dans `check2.bin`. Le paquet réactive exactement ces quatre envois.

Deux autres envois apparaissent dans `detector_forge24`, mais ce script ne déclare ni `ge10` ni `ge11`. Ils sont donc classés en reconstruction additive : les activer directement produirait des références invalides.

## Route alternative du maître-chien en Carnage dans Alps 1

Pour les types Carnage 3 et 7, `setobjectives.scr` remplace explicitement le script normal `ge_08.scr` par `ge_08_car.scr`. La version normale, au signal 10, conduit le maître-chien vers `ge08_01` puis envoie le signal 2 qui suspend le chien. La variante Carnage conserve exactement la même branche mais ses deux actions sont commentées et son point est différent : `ge08_02`. Le paquet réactive ces deux lignes uniquement dans la variante Carnage. Les deux routes restent donc disponibles selon le mode prévu par le jeu, sans que l'une remplace l'autre.

## Postes de combat oubliés dans Alps 1

Les scripts reliés des gardes `ge_16`, `ge_17` et `ge_23` conservent leurs réactions d'alarme et leurs déplacements. Seules les actions finales étaient commentées : le garde 16 n'atteignait plus `ge16_sniper` et ne passait plus en mode tireur, tandis que les gardes 17 et 23 ne prenaient plus place sur `w_mg42Crouch_` et `w_mg42Crouch_3`. Les soldats, les armes fixes et les trois points existent encore dans la mission. Le paquet réactive uniquement ces quatre instructions officielles, sans modifier les itinéraires ni créer de poste. La boucle du garde `ge_18` retrouve également `ge18_01` : le point existe et l'ordre commenté placé avant `ge18_02` rétablit le trajet symétrique `01-02-03-04-05-04-03-02` avant son recommencement. Dans la réaction visuelle du garde `ge_34`, le script alerte déjà `ge_33`, sort l'arme et tourne le soldat ; l'acteur cible `ge34attack` est toujours dans `actors.bin`. La commande `HUMAN_Attack(atak,5000)` était la seule étape commentée et est réactivée à son emplacement d'origine. Le détecteur `detector_forge30` envoie par ailleurs le signal 1 aux huit soldats `ge_30` à `ge_37` : sept exécutent activement `HUMAN_Suspend(0)`, mais cette ligne était commentée dans `ge_35.scr` juste avant l'activation de ses événements d'écoute. Le paquet restaure aussi ce réveil isolé ; le compteur de tirs/explosions et ses conséquences de cinématique demeurent ceux du jeu.

## Conséquence temporisée des renforts dans Alps 1

Le contrôleur `ridiccasovac.scr` reçoit trois types d'événements déjà actifs : mort du conducteur, coupure de la ligne téléphonique et alarme. Dès que deux ont eu lieu, il attend 60 secondes, réveille les deux renforts `ge_38` et `ge_39` avec leurs trajets complets, puis attend 30 secondes supplémentaires. Sa dernière instruction vers `objectyves` était commentée. Le récepteur du signal 18 est pourtant actif : il affiche le sous-titre officiel 14992813 et fait échouer l'objectif 1 des documents. Le paquet réactive cette seule liaison finale ; il ne change ni les trois conditions, ni les délais, ni les limites de la carte.

Le paquet reconnecte le second détecteur à son script homonyme. Il n'ajoute ni acteur, ni position, ni comportement.

## Alarme de proximité d’Alps 2 restaurée

La carte conserve l’acteur `shotalarmdetector`, son script complet et le contrôleur actif `shotalarm`. La liaison du détecteur avait disparu. Une fois reconnecté, l’entrée du joueur dans la zone prévue envoie le signal officiel 2 : la chaîne cesse de traiter les tirs comme un échec critique et passe à la réaction d’alarme prévue par les scripts.

Cette restauration n’ajoute ni zone ni règle nouvelle. Son effet exact sur les différentes approches furtives doit encore être confirmé en jeu.

### Résultat de l'audit complet d'Alps 2

Les chaînes d'objectifs principales et Carnage sont complètes dans les scripts effectifs. Les lignes commentées qui envoient les objectifs 2 et 5 sont d'anciens émetteurs remplacés : les soldats du magasin envoient déjà l'objectif 2, et l'agent envoie l'objectif 5 après sa réplique de départ. Dans Carnage, l'objectif 8 est déjà initialisé après la cinématique puis validé par le compteur de tous les ennemis ; sa seconde initialisation commentée ne constitue pas une action supplémentaire.

Les vestiges restants demandent une reconstruction séparée : le détecteur `AL2_13_A1` n'a plus les scripts des gardes 13 et 14, l'accessoire `k_leo_` n'a plus son point d'attache actif, et l'ancien échec automatique après 90 secondes contredirait le comportement d'exploration retenu. La course de l'agent et les trois anciens détecteurs d'alarme Carnage sont également des variantes concurrentes. Ils ne seront proposés que sous forme additive ou optionnelle, sans remplacer les branches release.

## Découverte du véhicule d’Africa 3 restaurée

La mission conserve l’acteur `AF3a_obj2` exactement sur l’Opel utilisable, ainsi que son script officiel non relié. Ce détecteur reconnaît l’arrivée du joueur à moins de huit mètres, affiche le message conservé et valide l’objectif de découverte du véhicule.

Le paquet restaure uniquement cette liaison. Il ne redirige pas le détecteur vers le compteur `pocet_splnenych` : ce compteur reste alimenté par le signal 4 que le mécanicien envoie après la conversation, comme dans la logique commerciale. On évite ainsi un double comptage tout en rétablissant l’action secondaire présente dans la carte.

## Deux identifiants de voix d’Africa 3 corrigés

Dans `AF3a_rozhovor_05.scr`, les commentaires officiels associent les deux dernières répliques d’`AF3a_02` aux identifiants `07991601` et `07991604`. Les appels actifs utilisent par erreur `079915601` et `079915604`, avec un chiffre 5 supplémentaire. Le registre commercial relie bien `dummy_rozhovor_05` à ce script ; le paquet remplace donc uniquement ces deux nombres.

Cette réparation interne ne réactive pas la conversation. Aucun émetteur du signal 1 attendu n’est encore démontré pour les conversations 03, 04 et 05 : leur déclenchement reste une reconstruction expérimentale séparée.

### Barrière de Burgundy 1

Dans les variantes solo et coopérative, le garde ouvre la barrière avec le signal 1, attend vingt secondes, puis lui envoie le signal 0. Or le script officiel de la barrière ne gère que le signal 1 pour ouvrir et le signal 2 pour fermer. La barrière restait donc ouverte après le passage du camion.

Le paquet remplace ce signal 0 par la commande de fermeture 2 dans les deux variantes. Il réactive aussi le déplacement immédiatement suivant vers `04_01` : ce checkpoint subsiste et mène le garde à sa position de conversation avant l'écriture de la valeur 61. Le conducteur attend ensuite la valeur 2 produite par cette conversation avant de poursuivre `path01_05…09` ; aucune nouvelle route n'est inventée.

### Reprise de ronde dans Burgundy 2

`ge_cesticka` enregistre l'étape 5 après `ge_cesticka4`, puis possède un `label 5` complet qui rejoint `ge_cesticka2`. Le répartiteur utilisé après une alarme traite les étapes 1 à 4 mais garde sa cinquième branche commentée. Le paquet réactive uniquement `if(a==5) goto 5` en solo et en coopération, afin que le garde reprenne le segment interrompu au lieu de recommencer toute sa ronde.

La fuite de `gumak` en BMW reste séparée : `bmv1` subsiste, `citron1` reste actif, mais `bmv4` n'existe plus dans les checkpoints. Restaurer le trajet complet demande donc une reconstruction géométrique et n'entre pas dans ce correctif stable.

## Deux chemins possibles

### Vague 7 de Normandy 2

Le détecteur 7 envoie le signal 7 à douze combattants. Onze le reçoivent correctement ; Red 26, pourtant explicitement placé dans cette même liste, attend encore le signal 6 d'un autre groupe auquel il n'appartient pas. La même incohérence existe dans la démo officielle, ce qui indique une erreur ancienne restée dans la version commerciale.

Le paquet remplace uniquement le numéro du signal reçu par Red 26, de 6 à 7. Son comportement complet — réveil, déplacement jusqu'au mur opposé et réaction au joueur — reste inchangé.

### Riposte au cinquième allié dans Normandy 2

Les quinze soldats Blue réellement placés possèdent cinq gestionnaires de riposte, un pour chacun des alliés. Dans chaque fichier, la cinquième branche trouve `Ally5`, attaque cette cible et porte le label `loop_A5`, mais le saut final retourne vers `loop_A1`. Les quinze sauts sont corrigés vers leur propre boucle A5. Les autres branches, les durées et les cibles restent inchangées.

Le réseau libre de quatorze zones `Dummy_Go_*` et des détecteurs 9–11 forme une route d'escorte/retour plus ambitieuse. Ses acteurs sont encore placés, mais aucune liaison ni impulsion initiale ne subsiste, et les signaux 9/11 ne correspondent plus aux récepteurs Blue. Il reste une variante de reconstruction, pas une activation stable.

Plusieurs missions finales conservent des approches multiples. Pour identifier un chemin réellement désactivé, il faut distinguer :

- terrain existant mais rendu punitif par une limite de zone ;
- passage fermé seulement par une collision ou une porte ;
- navigation IA manquante ;
- branche de script coupée ;
- simple décor sans secteur jouable.

Le mode exploration libre permet d'examiner le premier cas. Il ne transforme pas automatiquement un décor en route fonctionnelle.

### Deux zones d'approche de Norway

Les scripts `detect_player1` et `detect_player2` forment une paire symétrique : chaque zone enregistre l'arrivée du joueur, lance le signal 10 vers le garde `small7`, puis désactive l'autre zone. La seconde cible correctement `detect_player1` avec le signal 1, que celui-ci gère. La première envoie le signal 2, que `detect_player2` gère, mais sa variable cherche par erreur `detect_player1` : le signal repart donc vers elle-même et reste sans effet.

Le paquet corrige uniquement ce nom de cible, de `detect_player1` vers `detect_player2`. Les deux acteurs, leurs scripts, les signaux croisés et la scène du garde sont tous présents dans les données commerciales.

### Ambiance du Tirpitz et minuteur du garde 3

La couche Base relie `R_Nor_action_Sender.scr` au cadre `m_tirpitz low.t_kotva41`. Le Patch 1.12 retire seulement cette liaison : le cadre, le script et les neuf gardes visés restent présents. Huit scripts de garde — 4, 5, 8, 9, 11, 14, 15 et 18 — conservent leurs quatre réactions complètes aux signaux chapeau, bouteille, froid et regard vers la mer. Le paquet restaure la liaison commerciale du contrôleur sans changer son tirage, ses délais ni la probabilité de chaque garde.

Le garde 3 est lui aussi encore visé, mais son script ne conserve aucun `OnSignal(1..4)`. Ses réactions ne sont pas inventées dans le lot stable et sont confiées à la reconstruction additive. Les gardes 1, 2, 6, 7, 10, 12, 13, 16 et 17 ont perdu leurs acteurs et liaisons ; leurs scripts et tous leurs checkpoints `T1…T18` subsistent, ce qui réduit la reconstruction aux acteurs, positions initiales, identités, équipements et finitions de script.

Séparément, `R_nor_man3.scr` démarre `small3_timer` lors d'une fausse alerte. Sa branche de blessure conserve un arrêt commenté adressé à l'ancien nom `timer`, tandis que la variable active s'appelle `timer2` et que le contrôleur lié possède encore `OnSignal(3)`. Le paquet réactive cet arrêt sous le nom exact `timer2`, afin qu'une attente ancienne ne renvoie plus le garde à sa ronde après sa blessure.

### Seconde approche de la place dans Czech 4

Le détecteur 4 envoie le signal 4 aux trois soldats `CZ4_Plazzars_01`, `02` et `03`. Le premier possède un gestionnaire 4 qui l’envoie vers son itinéraire `cor3`. Les deux autres ne possèdent pas ce gestionnaire, mais leur signal 3 officiel les réveille et leur fait suivre les chemins `hop2`, `DDP` et `RRR`, comme lors de l’approche déclenchée par le détecteur 3.

Le paquet laisse intact le signal 4 et la route distincte du premier soldat. Il remplace uniquement les deux signaux 4 ignorés par `Plazzars_02` et `03` par le signal 3 qu’ils gèrent déjà. Les trois acteurs, les deux détecteurs, les scripts et les chemins sont présents dans la mission commerciale.

### Second garde de la porte dans Czech 2

Le script actif `LMswitchdoors.scr`, relié à la porte `dobytcak146`, déclare séparément les variables `ger24` et `ger25`. Lors de l'utilisation de la porte, il envoyait pourtant deux fois le signal 3 à `ger24`. Les deux soldats sont présents dans le registre commercial et leurs scripts possèdent chacun une réaction complète au signal 3, avec leur déplacement propre.

Le paquet conserve le premier envoi vers `ger24` et remplace uniquement le second destinataire par `ger25`. Aucun chemin ni comportement n'est inventé : le deuxième garde reçoit simplement enfin la commande déjà prévue pour lui.

### Réaction complète du groupe Wood dans Arctic 3

Le chef `Wood_1` constitue une formation avec `Wood_2` et `Wood_3`. Lorsqu’il meurt, il doit libérer ses deux équipiers vers leur réaction défensive `Dealarm`, déjà entièrement présente sous le signal 5. Le script envoyait pourtant deux fois ce signal à `Wood_2`.

Le paquet conserve le premier envoi vers `Wood_2` et adresse le second à `Wood_3`. Les trois soldats, la formation, les chemins défensifs et les gestionnaires sont reliés dans la mission commerciale.

### Réaction du convoi touché dans Arctic 3

Le camion `Opel_01` transporte les six acteurs `Car_1` à `Car_6`. Le script officiel non relié `R_Ar3_CarHit.scr` possède un gestionnaire `OnHit` qui leur envoie à tous le signal 4. Chacun des six scripts de soldat est actif et traite ce signal en interrompant le trajet, en quittant le véhicule et en passant au 

### Échec manquant à la destruction du bateau dans Arctic 3

L'objectif 3 demande l'embarquement et est validé par le signal 10 juste avant la cinématique d'extraction. Le contrôleur se termine par une note explicite demandant de compléter l'échec si le bateau est détruit. Le bateau `ELKO` et son script sont présents, mais aucun gestionnaire de destruction, message ou son spécifique n'a survécu.

Ce cas n'est donc pas activé par simple décommentage. Le laboratoire expérimental arme l'échec seulement après l'apparition du bateau et le désarme avant la cinématique, avec deux variantes mutuellement exclusives à éprouver : événement `OnDeath()` du propriétaire ou transition d'état observée. Le statut proposé est l'échec critique de l'objectif 3, sans inventer de dialogue.

Le paquet relie uniquement le camion libre à ce script. Le véhicule, les six occupants, leurs liaisons et leurs réactions sont tous présents ; aucun trajet, déclencheur ou comportement n'est créé.

### Effet de destruction de l’Opel dans Czech 5

La mission conserve le camion `La_OpelE_1`, employé par `CUTSCENE_cz4B.scr`. Cette cinématique le masque temporairement puis le remet explicitement en jeu. Le script officiel non relié `Opel_1_OnDeath.scr` ne contient qu’une réaction à la destruction : créer la particule 79 sur le véhicule.

Le paquet relie uniquement `La_OpelE_1` à ce script. L’autre camion `La_OpelE_5` reste relié à `OpelOD.scr` ; aucune commande de cinématique, route ou réaction existante n’est remplacée.

### Réveil groupé du magasin dans Africa 5

La porte du magasin utilise `AF4_sklad_activator.scr` et envoie le signal 1 aux sept hommes `AF4_sklad01` à `07`. Six scripts possèdent déjà ce gestionnaire. Seul `AF4_sklad04`, le mécanicien, restait suspendu malgré un label `ACTIVATE` complet qui le réveille, le place en garde et lance son animation de travail.

Le paquet ajoute à `AF4_sklad04.scr` le même gestionnaire que chez les cinq voisins comparables : activation du type d'alarme 2, puis branchement vers `ACTIVATE`. Son détecteur autonome à vingt unités, son déplacement, son animation `!manipul1` et toutes ses réactions d'alarme restent inchangés.

### Recherche d’alarme du garde 06 dans Africa 5

Le garde `AF4_sklad06` écoute déjà les types d’alarme généraux, sauf les catégories 512 et 4 réservées à son comportement intérieur. Sa branche complète pour le type 256 — arrêter l’alarme courante, passer en course et rejoindre sa source avec `HUMAN_MoveToAlarm()` — est pourtant entièrement commentée. Les gardes voisins `AF4_sklad02`, `03`, `05` et `07` conservent exactement cette réaction active.

L’acteur est relié à `AF4_sklad06.scr` dans le registre officiel et sa réaction distincte au signal intérieur 2 reste complète. Le paquet réactive donc seulement la branche 256, sans modifier le point de couverture du magasin, les animations de recherche ni la priorité de l’alarme intérieure.

### Cigarette du garde d’entrée dans Africa 5

Après avoir salué puis fait signe au convoi d’entrer, `AF4_03.scr` conserve exactement deux lignes commentées : redémarrer `HUMAN_ACTIVITY_Smoke(true)`, attendre une seconde, puis rejoindre `AF4_03_04`. Le même script arrête déjà la cigarette dans `OnAlarm()`. Huit gardes de la mission utilisent activement la même paire démarrage/arrêt, l’acteur `AF4_03` est relié au script et les quatre points `AF4_03_01` à `04` sont présents dans la carte.

Le paquet réactive uniquement le démarrage et son délai déjà écrits. Le salut, le geste de circulation, la ronde, les réactions d’alarme et le point final restent inchangés.
### Reprise du polissage dans Burgundy 2

Dans l’atelier solo, `ge_motorka.scr` envoie explicitement le signal 2 « ne polis pas » avant le dialogue, puis le signal 3 « polis » après la dernière réplique. `ge_dilna.scr` possédait bien le gestionnaire d’arrêt sur 2, mais son second gestionnaire écoutait lui aussi 2 et ne conservait plus que le commentaire de reprise. L’animation exacte `%%lestisamopal`, avec ses paramètres 500/500/1, subsiste dans l’initialisation du même acteur.

Le paquet fait écouter le second gestionnaire au signal 3 et y relance uniquement cette animation officielle. Il ne rejoue pas la pose assise, ne réactive aucun signal coupé par une alarme et ne modifie ni les déplacements ni les réactions de combat.

### Mise en place de Schumann pendant l’embuscade d’Africa 5

Le détecteur `dummy_attack_schumann` lance encore la cinématique 20 lorsque le joueur approche de Schumann et que le tireur `AF4_31` est disponible. Le tireur possède son gestionnaire actif : il rejoint sa position, vise Schumann, tire puis poursuit l’attaque après la scène.

Le gestionnaire correspondant d’`AF4_23` était entièrement commenté. Il arrête son activité, le fait rejoindre `AF4_blesz_end`, l’accroupit et termine son script à la fin de la cinématique. Ce point existe une fois dans la carte, et les trois acteurs sont toujours reliés. Le paquet restaure ce bloc sans modifier la conversation facultative de Schumann, le déclencheur de l’embuscade ni le comportement du tireur.

### Ronde du garde 32 dans Burgundy 3

Dans la mission solo, `BUR03_32` rejoint bien son label de ronde, arme au bras et en mode garde, mais les deux déplacements vers `32_01` et `32_02` sont commentés. Ces deux points sont présents une seule fois dans la carte solo. La version coopérative de Burgundy 3 contient le même script avec les deux lignes actives dans le même ordre.

### Phrase d'ouverture du premier SAS dans Burgundy 3

Le prisonnier `BUR03_SAS01` conserve en solo les cinq lignes de son dialogue, mais l'appel de la première voix 59990052 est commenté alors que 59990053 à 59990056 restent actifs. La variante coopérative joue les cinq appels dans cet ordre exact. La voix anglaise et son animation labiale 59990052 sont présentes dans l'archive commerciale ; le paquet réactive donc uniquement cette phrase, sans modifier le déclencheur à six mètres ni les objectifs des prisonniers.

L'audit des neuf objectifs et des 78 checkpoints actifs de Burgundy 3 ne montre pas d'autre action secondaire démontrable laissée inactive. Les signaux de gestes de l'interrogatoire, la fuite en Jeep privée de `car05` et le son partagé entre les deux branches d'explosion nécessitent des raccords nouveaux. Ils restent dans la reconstruction expérimentale afin de conserver simultanément les comportements release et historiques.

Le paquet réactive donc uniquement cette boucle 01-02. Le trajet `32_dth` puis `32_ad`, utilisé après une alarme pour combattre près des prisonniers, ainsi que les cibles SAS et les réglages d’alarme, ne sont pas modifiés.

### Partie de cartes des soldats 24 et 25 dans Africa 1

`AF1_24.scr` et `AF1_25.scr` conservent la même séquence commentée dans leur label d’activation : `HUMAN_ACTIVITY_Card(1)` sort les cartes, puis `Card(2)` se répète toutes les 1,5 seconde. Les deux soldats sont placés et reliés, mais leur déclencheur de proximité n’exécutait plus aucune activité.

Les commandes 1 et 2 sont actives dans les séquences de cartes de Czech 3 et Castle 2. Les deux scripts Africa 1 arrêtent déjà leur animation dès une alarme ou le signal 10. Le paquet réactive donc leurs boucles identiques sans modifier leur placement assis, leur distance d’activation ni leurs réactions de combat.

### Inspection d'arme de la ronde 08 dans Africa 3

La branche `PATH_CWEAPON` d'`AF3a_08.scr` est complète : le soldat rejoint son point, s'assoit, attend, doit inspecter son arme deux fois, attend encore, puis se relève et reprend sa ronde. Seules les deux commandes `HUMAN_ACTIVITY_CheckWeapon()` ont été commentées avec la mention qu'elles devaient attendre le fonctionnement de l'animation.

Cette commande est pourtant active dans les archives commerciales pour `AF2_06`, `AF2_09`, `AF2_11` et deux gardes d'Arctic 1. Le paquet réactive donc exactement les deux appels d'Africa 3, sans changer la cadence, le trajet, la pose assise ni la réaction aux alarmes. Les autres vestiges voisins — sommeil d'`AF3a_26` et emploi de l'arme statique par `AF3a_07` — restent expérimentaux, faute d'un exemple actif permettant d'en garantir les paramètres.

### Mise à couvert du mécanicien dans Africa 3

Le mécanicien `AF3a_21` active déjà le type d'alarme 64, correspondant à sa blessure, mais la branche entière qui le faisait se réfugier sous l’Opel était commentée. Cette branche fixe `below_car`, interrompt son travail, rejoint `AF3a_21_01`, passe couché puis gagne `AF3a_21_bcar`. Les quatre points employés par le comportement, y compris `AF3a_21_below`, sont présents une seule fois dans la carte et l’acteur est toujours relié à son script.

La conversation active teste encore `below_car == 1` et contient le trajet inverse pour le faire ressortir avant de parler au joueur. Le paquet réactive donc le bloc de mise à couvert sans inventer de transition, sans déplacer de point et sans modifier la conversation ni les autres réactions d’alarme.

### Geste de chaleur du garde 03 dans Africa 3

Pendant sa ronde, `AF3a_03` rejoint déjà son point de repos, range son arme, fume et utilise l’animation assise `%%sedimL`. Un unique appel `HUMAN_ACTIVITY_Hot()` était commenté entre le début de cette pause et son attente de 25 secondes.

Le garde 16 de la même mission combine activement `HUMAN_ACTIVITY_Sit`, `Hot` puis `Smoke` dans son propre repos. Le paquet réactive donc ce geste sans changer les déplacements, la cigarette, le temps de pause ni les réactions aux signaux et alarmes.

### Repos assis du garde 24 dans Africa 3

Le commentaire d’`AF3a_24.scr` décrit à l’origine un soldat endormi, mais le cadre provisoire `some_bed` n’existe plus et l’activité de sommeil n’est pas réactivable fidèlement. En revanche, le remplacement assis est complet : `dummy_24_sit`, `AF3a_24_01`, `AF3a_24_sit` et `AF3a_24_alert` existent, tandis que le script conserve deux appels à `HUMAN_ACTIVITY_Sit(sit)` et le retour au siège après alarme.

Le radio-opérateur 19 de la même mission utilise déjà cette activité avant suspension et après alarme. Le paquet réactive donc le repos assis du garde 24 et son retour, mais laisse le sommeil dans le dossier expérimental faute de lit officiel.

### Alerte globale des gardes 22 et 23 dans Africa 3

Le distributeur `AF3a_dummy_alarm.scr` avertit déjà douze gardes par le signal 20 lorsque l'alarme globale est déclenchée. Les déclarations d'`AF3a_22` et d'`AF3a_23`, puis les deux envois correspondants, sont les seules lignes de cette liste restées commentées.

Les deux acteurs sont toujours placés et reliés à leurs scripts. Chacun possède exactement un gestionnaire `OnSignal(20)` complet qui abandonne son activité, augmente sa portée de vue et le replace en défense. Aucun autre script ne leur envoie déjà ce signal. Le paquet réactive donc ces quatre lignes sans toucher aux réactions locales d'alarme ni aux itinéraires des deux soldats.

### Vapeur de la cinématique Jeep dans Africa 3

`CUTPARTICLES.scr` pilote déjà deux particules de fumée pour la variante Opel et deux autres pour la variante Jeep. Dans la branche Jeep, seule l’activation puis l’arrêt du cadre sonore `cut_para` étaient commentés ; les particules, les délais et la cinématique 3 sont toujours actifs.

Le cadre `cut_para` existe une fois dans le registre sonore, les quatre ancres de particules sont présentes une fois dans la scène et `CUTparticle1` reste relié au contrôleur. La variante Opel utilise le même son aux mêmes instants. Le paquet réactive donc uniquement les deux commandes sonores de la Jeep, sans modifier les caméras, les fumées, les conditions de choix du véhicule ni la durée de la scène.

### Cigarettes des gardes de Libye 1 coopératif

Les scripts coopératifs `AF1_33`, `AF1_50`, `AF1_52` et `AF1_53` conservent chacun exactement un démarrage et un arrêt de `HUMAN_ACTIVITY_Smoke`, commentés avec une ancienne note indiquant que la commande ne passait pas encore. Les quatre acteurs sont bien reliés à ces scripts par `Co_Libye1/mpscripts.dta`.

La même syntaxe booléenne est active dans la mission solo Libye 1 et dans Libye 3 de Sabre Squadron, en plus de nombreux scripts du jeu de base. Le paquet réactive donc ces huit lignes : `AF1_33` fume pendant la pause de deux minutes déjà prévue dans sa boucle, tandis que les trois gardes de rempart reprennent la cigarette à leur poste. Tous l'arrêtent avant leur traitement d'alarme ; aucun déplacement ni réglage de difficulté n'est modifié.

### Marche de la patrouille au chien dans Arctic 4

Dans `R_Arc3_walking_guard_3.scr`, le mode marche placé juste après le mode garde est commenté avec la note tchèque « remettre plus tard — seulement pour le test avec le chien ». Les deux autres gardes conservent une ronde comparable et la branche de retour d'alarme du troisième utilise déjà `HUMAN_SETMODE_Walk()`.

Le registre lie `Walking_Guard_3` à ce script et `pes_1` à `R_Arc3_dog_1.scr`. Le chien désigne ce garde comme propriétaire, et la mort du garde lui envoie déjà le signal 1. Le paquet réactive seulement l'ordre de marche avant la boucle de patrouille ; l'attaque, l'errance du chien, la portée de perception et la réaction d'alarme restent inchangées.

### Marqueur de proximité des documents dans Arctic 4

`R_Arc3_Documents.scr` masque d’abord son propre cadre `k_vykricnik_`, puis active la surveillance de l’objet 254 lorsque le joueur s’approche à moins de 10 mètres. L’apparition du marqueur dans cette zone et son masquage après la collecte étaient les deux seules commandes visuelles commentées ; les signaux 24, 25, 26 et 30 ainsi que les transitions de l’objectif 2 restent actifs.

Le cadre est présent une fois dans la scène et lié au script. Le signal 24 atteint le contrôleur d’objectifs assigné par la mission. Le paquet réactive donc ce repère historique, sans toucher à l’objet, au délai de récupération après perte ni au marqueur `vykricnik_man` de l’officier, dont la ligne porte au contraire une note explicite demandant son retrait.

### Impact de la chute de glace dans Arctic 4

`R_Arc3_ulomek4_sender.scr` détecte le joueur à douze mètres et envoie le signal 1 au contrôleur `dummy_bouchni`. Ce dernier est lié à `R_Arc3_bouchni.scr`, vise le fragment existant `ulomek_4` et active déjà son état. L'appel d'explosion placé immédiatement avant cette activation est complet mais commenté.

Le paquet réactive exactement `MakeExplosion(FRM, 5000000, 3500)` sans modifier la distance de déclenchement, la puissance, le rayon ou le fragment. Il s'agit d'un danger de décor restauré, pas d'un nouvel objectif ni d'une limite d'exploration.

### Météo et éclairs de Czech 5

Le registre de Czech 5 relie encore `3crib144` à `R_Cz4B_pocasi.scr` et `light_lightnings` à `R_Cz4B_lightnings.scr`. Les deux fichiers sont complets mais chaque ligne exécutable a été commentée : quantité, couleurs, vitesse, taille, espacement et direction de la météo d'une part ; boucle aléatoire d'éclairs d'autre part.

Toutes les commandes utilisées sont actives ailleurs dans les archives, notamment dans les scripts météo de l'easter egg du Tutorial. Le paquet réactive les paramètres officiels et la boucle d'éclairs sans en changer les valeurs. La ligne `THUNDERSTORM_SetOn(-integer-, -frame-)` reste commentée, car il s'agit d'un gabarit de développeur invalide et non d'une instruction destinée au jeu.


### Alerte vocale du garde 36 dans Alps 2

Dans la version commerciale, `al2_36.scr` avertit le contrôleur `AL2_alarm` par le signal 6 puis joue `PlaySound(9,49)` dès que le garde donne l'alarme. La mise à jour 1.12 conserve toute cette branche et la liaison `AL2_36 → al2_36.scr`, mais commente seulement l'appel vocal sans le remplacer.

Le même appel `PlaySound(9,49)` reste actif dans la réaction d'alarme du garde `ge_14` d'Alps 1. Le paquet réactive donc cette unique ligne dans Alps 2. Le signal vers le contrôleur, la perte du déguisement, les réactions de mort et les déplacements dans l'archive restent inchangés.

### Troisième changement d'éclairage de l'Enigma dans Norway

`R_Nor_OBJ_3.scr` déclare trois éléments visuels de l'Enigma et applique déjà la lightmap 1 aux deux premiers lors de la prise de l'objet. La même instruction pour `LMP3`, relié à `Mesh46`, est conservée juste après mais commentée dans la version de base comme dans la mise à jour 1.12.

Le paquet réactive seulement `FRM_SetLightMap(LMP3, 1)`. Le registre commercial relie bien `r_nor_obj3` à ce script et `Mesh46` existe dans les deux arbres de scène officiels vérifiés. La validation de l'objectif, sa musique et la logique de reprise en cas de perte de l'Enigma restent inchangées.

### Deux trajets ambiants complets dans Africa 1

`AF1_16.scr` conserve le déplacement du mécanicien vers `af1_16_06` et son orientation vers l'avion immédiatement avant sa boucle de réparation. `AF1_19.scr` conserve, dans le retour d'une fausse alerte, une ronde fermée passant par `AF1_18_02`, `AF1_19_01`, `AF1_19_02` et `AF1_18_03`.

Les deux acteurs sont reliés à leurs scripts et les cinq checkpoints existent encore exactement une fois dans `check2.bin`. Le paquet réactive uniquement ces instructions. Les autres trajets commentés d'Africa 1 ne sont pas mélangés à ce lot : `AF1_04_g06`, `AF1_04_g07`, `AF1_20_01` et `dummy_22_sit` manquent réellement et sont confiés à la reconstruction expérimentale.

### Second détecteur de patrouille dans Czech 3

Le contrôleur `ovladacblockeru` déclare `detector_blockerz` et `detector_blockerz1`. Lorsqu’il lance la patrouille, il adressait néanmoins deux fois le signal 1 au premier. Les deux acteurs sont reliés au même script officiel, qui active leur détection du joueur à trente mètres.

Le paquet remplace seulement la cible du second envoi par `detector_blockerz1`. La seconde zone retrouve ainsi la fonction déjà prévue sans ajout de comportement.

### Czech 3 : stationnement complet et réactions de garde

Le camion `opel_2` suit toujours sa route d'arrivée, charge les prisonniers puis repart dans la mission normale. Quatre commandes de sa manœuvre de stationnement avaient cependant été commentées : passage par `BMW_16`, approche de `couvej1`, puis recul par `couvej1` et `couvej3`. Tous ces points sont encore dans `check2.bin`; surtout, `opel_driver_carn.scr` exécute déjà l'intégralité de cette même géométrie. Le paquet rétablit les quatre appels dans `opel_driver.scr` et conserve toutes les étapes release autour d'eux.

Le mécanicien possède un contrôleur de parole séparé, `mechanik_kecac`, qui gère déjà le signal 2 en coupant ses déclencheurs de proximité. Son script principal déclarait ce contrôleur mais avait commenté l'envoi exactement dans `OnDeath`. Le signal est réactivé afin qu'un cadavre ne continue pas à parler.

Le radio-opérateur rejoint déjà `spojar1`, s'accroupit, arme son personnage et se tourne vers `spojarcum` pendant l'alarme. Son passage en poste de précision était l'unique instruction commentée de cette branche. La variante communautaire `co_czech3` conserve la même instruction active au même emplacement ; le paquet la remet donc en service sans modifier ses distances ni ses réactions d'alarme.

### Czech 4 : second combattant absent du compteur principal

Le contrôleur `CZ4_OD.scr` déclare bien les deux combattants `CZ4_Chatter_01` et `CZ4_Chatter_02`, liés chacun à leur propre script. Sa seconde recherche de cadre utilisait toutefois encore le nom `CZ4_Chatter_01`. Les deux variables pointaient donc sur le même acteur, tandis que `CZ4_Chatter_02` ne pouvait jamais être compté dans la chaîne de l'objectif 1 « Tuez tous les ennemis ».

Le paquet remplace uniquement le nom de cette seconde recherche par `CZ4_Chatter_02`. Les objectifs 2, 3 et 4 restent inchangés : trois signaux distincts alimentent la destruction des réservoirs, `dummy_treasure` valide la découverte du trésor et le contrôleur de fin vérifie la survie de l'équipe. Les trois trajets `???` des soldats de cave ne sont pas confondus avec ce correctif : leurs checkpoints ont réellement disparu et leur reconstruction est isolée.

### Czech 5 : trois objectifs et convoi complets

Le catalogue déclare trois objectifs et le contrôleur corrigé par le Patch les utilise tous. La disparition du dernier ennemi Carnage valide l'élimination et l'interdiction de fuite, puis la survie de l'équipe est accordée si aucun équipier n'est mort. À l'inverse, le détecteur `dummy_PD` lance la cinématique de fuite lorsqu'un ennemi ou le Tiger atteint son rayon, puis envoie le signal 16 qui désactive le compteur et fait échouer le second objectif.

Les cinq passagers de l'Opel reçoivent tous leur signal de débarquement depuis le conducteur ou depuis le contrôleur de destruction `OpelOD`. Les quatre postures debout commentées chez les passagers 16 à 19 précédaient l'appel de sortie du véhicule ; les mêmes sièges sont évacués sans cette préparation dans les scripts commerciaux d'Africa 4, et tous ces soldats définissent ensuite leur mode de déplacement ou de combat. Leur retour n'ajouterait ni trajet, ni action, ni objectif.

### Czech 6 : objectifs complets et route remplacée de l'ISU-152

La récupération des documents active les vingt soldats russes, lance la transition de carte et ouvre le second objectif. Le contrôleur de documents distingue encore trois actions : première collecte, perte de l'objet 252 puis récupération. Le compteur central surveille séparément les vingt acteurs `C5_R01..20`. La capture du Tiger et le sabotage du poste radio disposent chacun de leur objet utilisable et de leur signal de validation ; la survie de l'équipe est évaluée après le dernier Russe, tandis que la variante Carnage active son sixième objectif propre.

Le Patch simplifie en revanche une route de véhicule. La version Base faisait passer l'ISU-152 de `C5_isu01` par `C5_tank11` avant `C5_isu02`, alors que la version effective le conduit directement au dernier point à vitesse 30. Comme le char est déjà téléporté sur `C5_isu01`, réactiver la première commande seule serait redondant et rétablir les trois commandes remplacerait la route corrigée. Les deux tracés, tous encore présents, sont donc préparés comme choix expérimental distinct.

Le sabotage radio illustre la même règle. La Base attendait que le radio-opérateur `C5_G11` donne l'alarme avant d'autoriser l'interaction ; le Patch retire l'envoi et le verrou, rendant l'action immédiate. Une éventuelle branche historique doit conserver cette possibilité release. Enfin, l'alerte de `C5_G40` vise toujours `G11` et `G43`, mais leurs gestionnaires 1 ne subsistent pas : aucune simple décommentation ne peut réparer ce raccord.

### Normandy 1 : objectifs complets et anciens déclencheurs

Les huit objectifs de Lighthouse restent actifs et reliés : les trois canons en tir, les quatre autres canons, le générateur, le phare déverrouillé après le générateur, les cinq gardes de la Flak, le rassemblement, la survie de l'équipe et l'élimination Carnage. Les 144 checkpoints appelés par les scripts et les 204 cibles principales de scène sont tous présents.

La cinématique libre `X_N1_kamera-ya.scr` montre les deux accès souterrains avec cinq caméras et deux trajectoires encore présentes ; son lanceur commercial est reconnecté au point d'apparition solo. Les activateurs libres `N13_A2/A3` et `N24_A1/N25_A1` n'ont plus de positions, tandis que l'ancien `N17_A2` vise un signal sans récepteur. Leur remise en place exige une reconstruction géométrique additive qui préserve les activations release déjà fonctionnelles.

### Conséquence du radio-opérateur entre Africa 3 et Africa 4

Africa 3 enregistre explicitement la valeur 20 à zéro au début de la scène du radio-opérateur, puis à un seulement si sa transmission aboutit. Africa 4 conserve ensuite deux variantes complètes : les conducteurs reçoivent les signaux 20 ou 21, dix-huit fantassins et deux chefs de char les signaux 1 ou 2, cinq réservistes n'apparaissent que si l'alerte a été envoyée, et les délais ainsi que le journal changent selon ce choix.

Dans le seul organisateur de l'attaque, la valeur sauvegardée était cependant remplacée juste après sa lecture par `odvysilali = 1;`, ce qui condamnait systématiquement la variante « ennemis non avertis ». Le paquet retire uniquement cette affectation. Les deux branches restent entièrement constituées de scripts commerciaux et la correction 1.12 des soldats 24 et 25 est conservée.

### Réactions coordonnées des gardes dans Africa 2

Le groupe initial utilise deux commandes d'alerte déjà complètes : le signal 20 rejoint directement la route `ALERT`, tandis que le signal 5 interrompt l'animation puis conduit vers le chemin d'alerte propre à chaque soldat. Deux envois officiels sont croisés : l'activateur adresse le signal 5 à `AF2_02`, qui ne gère que 20, et l'alarme générale adresse 20 à `AF2_05`, qui ne gère que 5. `AF2_03` est pour sa part retiré des trois émetteurs par sept lignes commentées : les déclarations de son acteur, deux activations au signal 1, l'alerte directe 5 et l'alarme générale 20.

Le paquet remplace uniquement les deux numéros croisés et réactive les sept lignes officielles d'`AF2_03`. Ses gestionnaires 1, 5 et 20, sa ronde `AF2_03_01` à `AF2_03_06`, son trajet `AF2_03_alert`, son acteur et les trois émetteurs sont tous présents dans les données commerciales. Aucun comportement n'est inventé.

Le même lot réactive la scène rapprochée des gardes `AF2_14` et `AF2_15`. À 130 mètres, `AF2_15` envoie le signal 10 déjà géré par `AF2_14`, puis suit les trois points `AF2_14_01` à `AF2_14_03`. Le script commercial contient aussi l'arrêt de ce détecteur dans `OnAlarm`; les cinq lignes commentées sont remises ensemble afin que la séquence ne détourne pas les gardes après une alerte.

### Alerte croisée du groupe de commandement dans Africa 1

Les gardes `AF1_07`, `08`, `09` et `10` se préviennent mutuellement lorsqu'un membre du groupe détecte une alarme. Dix envois utilisent pourtant le signal 10, absent des quatre destinataires concernés. Chacun possède en revanche un signal 20 complet qui rejoint sa route `ALERT`, change sa posture, l'envoie vers son emplacement défensif et arme le soldat.

Le paquet remplace ces dix signaux 10 par 20 dans les quatre émetteurs. La conversation d'ambiance entre `07`, `08` et `09`, qui utilise le signal 1, reste intacte. Tous les acteurs, scripts et chemins sont présents dans la mission commerciale.

### Czech 2 : branche Freiberg propre au Carnage

Le sélecteur commercial différencie déjà les types Carnage 3 et 7, et déclare l'acteur `boss`, mais il n'affectait plus le script `carn_Big_Boss.scr`. Ce script libre est une variante complète de Freiberg : comportement agressif, réveil à quinze mètres, arme en main et alarmes actives. Le paquet rétablit son unique affectation dans la branche Carnage. La mission normale conserve le prisonnier, les cinq répliques, le ligotage, la capture puis l'objectif de sortie déjà réparé.

Cette restauration ne change pas le compteur « Tuez l'ennemi » : `mrtvoler.scr` surveille toujours `_GetCountOfCarnageEnemies()` et avertit le contrôleur lorsque le total atteint zéro. Elle rétablit seulement le comportement qui empêche Freiberg de rester un captif passif dans ce mode.

### Czech 1 : chaîne complète, anciens doublons

Les deux officiers `SS1` et `SS2` alimentent encore le compteur à deux actions qui libère le sauvetage de Trebissky. La conversation avec le cheminot `vechtr` valide séparément l'objectif optionnel, puis le contrôleur active la sortie, rassemble l'équipe et vérifie ses survivants. Aucune des cinq étapes n'est réduite à une action unique.

Les états d'objectifs commentés en tête des deux contrôleurs sont remplacés par le sélecteur du patch et les transitions actives. De même, les deux signaux commentés de la conversation `speech4` sont déjà émis par le détecteur d'approche commun aux deux gardes. Leur retour doublerait un comportement existant au lieu de restaurer une seconde voie.

## Signaux anciens déjà remplacés

- Africa 3, paire 14/15 : le registre vise encore un `AF3a_1415synchronizer.scr` absent depuis la version de base, en l'attachant au simple cadre de regard `AF3a_14_lookAF15`. La conversation complète 14/15 est déjà lancée par `AF3a_rozhovor_02_activator.scr` et son contrôleur actif ; recréer un second synchroniseur risquerait un double déclenchement.
- Africa 5 : le registre conserve encore `dummy_runway01 -> AF4_runway01_detector.scr`, mais le script a disparu. Le contrôleur actif `AF4_runway_detector.scr` surveille déjà les trois points de piste, reçoit le signal de démarrage prévu et met à jour l'objectif 4 ainsi que la valeur sauvegardée 40. L'ancien détecteur unitaire a donc été remplacé par cette version centralisée.
Un écart du graphe ne doit pas être réactivé :

- Libye 2 envoie un signal 2 seulement après la destruction de tous les véhicules, jeeps comprises. La réussite optionnelle est déjà validée par le signal 1 après les huit véhicules du parc, tandis que la perte de tous les véhicules est contrôlée séparément et fait échouer l'extraction. Le signal 2 est donc un doublon sans fonction distincte.
- Czech 3 : à leur mort, les deux civils envoient un signal 2 à `e_ktable3`, acteur utilisé uniquement pour lancer `setobjectives.scr`. Ce script d'initialisation n'a aucun récepteur et le vrai contrôleur d'objectifs emploie déjà son signal 2 pour la sécurisation de la zone. La conversion coopérative publique retire ces deux envois tout en conservant la mort, l'arrêt des voix et la séquence d'évacuation ; ils sont donc classés résidus d'un ancien protocole, sans correctif à ajouter.

- Libye 3 : le cargo envoie uniformément le signal 1 à plusieurs membres du groupe Panzer, dont le servant `Li3_German_Con_2`. Celui-ci est pourtant déjà actif et embarqué au siège 1, exactement comme le servant du siège 2 qui ne reçoit aucun signal ; seuls le conducteur et les fantassins suspendus ont besoin d'un réveil. La variante coopérative officielle conserve la même répartition des rôles. Ajouter un récepteur au servant serait donc une invention sans effet démontré.

## Vestiges de signaux confiés à la reconstruction

- Africa 3, paire 22/23 : le registre attend `AF3a_2223synchronizer.scr`, mais aucun fichier ni gestionnaire correspondant ne subsiste. Les deux soldats déclarent chacun l'autre sans utiliser cette référence, ce qui confirme un lien perdu sans révéler son comportement. La coordination doit être reconstruite comme variante expérimentale.
- Tutoriel : l'instructeur envoie cinq fois le signal 17 à dummy_BA_counter lorsque les cinq groupes sont terminés, mais ce compteur ne gère que les signaux 1 à 5. Un ancien compteur montre un arrêt complet possible, sans conserver le gestionnaire exact du signal 17. Un arrêt ou une remise à zéro peut être prototypé, mais doit rester étiqueté reconstruction moderne.
- Tutoriel : les signaux vers dummy_WI et T_HR_Check réactivent des détecteurs déjà actifs ; ils sont classés redondants. Les deux signaux du piquet visent en revanche un contrôleur de route qui ne les gère plus, sans assez de données pour choisir la réaction d'origine.
- Czech 2 : les signaux 1, 3 et 4 adressés à Big_Boss, le signal 1 vers Ger20 et les signaux 2 vers Ger24/Ger25 restent sans gestionnaire démontré. La conversion communautaire actuelle en conserve elle-même plusieurs comme opérations sans effet ; ils ne sont donc pas transformés en correctifs stables.

- Czech 2 : l'ancien contrôleur libre `bigboskecac.scr` peut rejouer les voix 19993810 et 19993811 depuis la porte, mais la cinématique active joue déjà les mêmes répliques. Son éventuel retour doit préserver les deux mises en scène sous forme de variante choisie, sans doublage simultané.
- Alps 2 : `al2_13_a1.scr` et son acteur libre savent encore avertir `AL2_13` et `AL2_14`, mais les deux soldats ont perdu leurs scripts de réaction. Leur réveil nécessite de reconstruire ces comportements avant de relier le détecteur.
- Alps 2 : l'ancien accessoire de lecture d'`AL2_11` conserve son objet `k_leo_`, mais la référence de main `al2_11.hw1` et le téléport de l'objet sont tous deux commentés. Sa remise en scène doit être reconstruite et testée avec l'animation active `%%ctuneco`.
- Alps 2 : le délai d'échec de 90 secondes, la course de l'agent et les anciens envois Carnage vers `detectoral204`, `_2` et `_3` sont des branches remplacées. Leur étude doit préserver simultanément le comportement release, sous forme de mode historique ou de variante choisie.
- Tutoriel : `t_dummy_speech.scr` et `TUT_Talker_01` conservent une conversation d'ambiance complète, tandis que `TUT_Talker_02` n'est plus placé et que sa position d'origine n'est pas prouvée. La scène est confiée à la reconstruction.
- Co_Libye3 : `Opel.scr` immobilise son véhicule en mettant son carburant à zéro, mais aucun propriétaire exact ne subsiste et deux Opel sont plausibles. Deux variantes de test doivent être comparées avant toute intégration.
- Co_Burgundy3 : dix scripts d'ambiance et leurs cadres sonores survivent à l'identique du solo, mais les dix contrôleurs qui les portaient ont disparu. Ils doivent être recréés avec des positions vérifiables.
- Arctic 2 : plusieurs émetteurs de lightmap de portes sont orphelins et les gestionnaires de leurs secondes portes ont été commentés lorsque les portes ont été réunies pour fermer les portails. Leur retour exige une variante additive avec portails et portes indépendants, pas une simple liaison.
- Czech 3 : quatre comportements humains, une victime `Shocker_1` et trois barils explosifs subsistent sous forme de scripts, alors que leurs acteurs et leur déclencheur ont disparu. Plusieurs chemins de villa sont encore présents ; l'événement complet est confié à une reconstruction séparée.
- Normandy 2 : quinze scripts de défenseurs Red, Blue et Wave ont perdu leurs acteurs, mais tous les chemins qu'ils référencent subsistent. Quatorze zones d'escorte, trois détecteurs de retour et un coordinateur sans propriétaire complètent ce système coupé ; leurs signaux de démarrage et certains raccords ont disparu. Une défense élargie pourra être reconstruite en variante distincte, sans augmenter silencieusement la mission commerciale.

## Éléments à ne pas surinterpréter

- La présence d'une porte utilisée par l'IA ne prouve pas une pièce supprimée.
- Un objectif dans un ancien briefing ne prouve pas que ses acteurs et scripts ont survécu.
- Le supposé dépôt de bombes de Whisky Bar n'apparaît pas comme objectif dans le script inspecté.
- Les modifications officielles de Burma 1, Czech 6 et Alps 1 prouvent que des accès ont changé entre versions, sans fournir une liste complète des routes alpha supprimées.

Chaque restauration future devra indiquer la preuve, la part reconstruite et les tests réalisés.
