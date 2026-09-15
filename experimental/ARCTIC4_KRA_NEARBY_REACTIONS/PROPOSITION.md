# Arctic 4 — réactions voisines aux chutes de glace Kra

État : **intention attestée, destinataires non démontrables**, 14 septembre
2026. Aucune réaction humaine n’est ajoutée au script.

## Verdict

Les trois détecteurs commerciaux sont liés et actifs :

| Détecteur | Rayon joueur | Signaux attestés |
| --- | ---: | --- |
| dummy_Kra1_detektor | 40 | Kra_1, signal 1 |
| dummy_Kra2_detektor | 45 | Kra_2 et Static_Guard_5, signal 1 |
| dummy_Kra3_detektor | 25 | Kra_3, signal 1 |

Chacun conserve le commentaire indiquant qu’il faut aussi compléter les
personnages/animations autour. Ce commentaire prouve une intention de réactions
locales, mais ne nomme aucun destinataire ni signal.

Le seul contrat humain conservé est Static_Guard_5 pour Kra2. Son OnSignal(1)
tourne vers dummy_Kra2_detektor, attend huit secondes, affiche deux messages,
puis reprend sa boucle. L’animation « effrayée et figée » y est elle-même
marquée à compléter : aucun nom d’animation n’est attesté.

## Pourquoi aucune copie vers Kra1/Kra3

Le registre énumère Static_Guard_1 à 6, Walking_Guard_1 à 3 et d’autres acteurs,
mais les binaires de scène Arctic 4 permettant de mesurer leurs positions ne
sont pas présents dans les extractions locales auditées. Un nom de garde ne
prouve pas qu’il se trouve près de Kra1 ou Kra3.

De plus, aucun handler compatible et libre n’est identifié pour ces gardes. Le
signal 1 peut déjà avoir un autre sens. Copier OnSignal(1) de Static_Guard_5
risquerait donc d’interrompre une patrouille ou une activation sans retour sûr.

## Proposition uniquement spéculative

Le fichier REACTION_MATRIX.plan.disabled définit une campagne de mesure, pas un
prototype de script. En éditeur, il faut capturer la position de chaque Kra,
détecteur et humain dans le rayon, puis inspecter son script avant de réserver
un signal. Les candidats ne sont acceptés que si :

- ils sont spatialement dans le rayon de l’événement, pas seulement du joueur ;
- leur script ne consomme pas déjà le signal choisi ;
- une animation compatible existe dans les assets commerciaux ;
- alarmes, mort et reprise de patrouille interrompent proprement la réaction.

Sans ces quatre preuves, la proposition reste une simple liste moderne. Aucun
Sendsignal supplémentaire ne doit être ajouté aux détecteurs.

## Tests futurs

Tester chaque Kra séparément, puis alarmes simultanées, acteur mort, joueur à la
limite du rayon, sauvegarde pendant animation, et répétition du détecteur. Pour
Kra2, vérifier d’abord le comportement commercial de Static_Guard_5 afin de ne
pas attribuer à une nouvelle animation un délai ou une reprise déjà défectueux.

