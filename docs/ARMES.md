# Armes et équipements retirés

## Deux lance-flammes

Les noms Flamethrower Portable No. 2 et Flammenwerfer 35, ainsi que leurs munitions, subsistent dans les listes historiques et identifiants d'objets.

L'examen local corrige toutefois une interprétation fréquente :

- les entrées de modèles d'arme attendues entre le MG 81 et le Flak 38 sont absentes ;
- flame1.4ds ne pèse que 471 octets ;
- il ne contient qu'un objet fire01 ;
- c'est un effet de flamme, pas le modèle du lance-flammes.

Il n'existe donc pas une option cachée qu'il suffirait de cocher. Une version jouable demanderait de créer le modèle tenu et posé, les animations, le réservoir, les sons, la portée, les dégâts, les réactions de l'IA et les règles multijoueurs. Elle serait une reconstruction communautaire inspirée d'une arme annoncée.

Sources contemporaines :
- https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/
- https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655
- https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/

## Benelli M4 Super 90

C’est le vestige d’arme le plus complet retrouvé. Les archives conservent neuf couples d’animations FPV `#FPVBeneli` (visée, tir, rechargement, enrayage, armement et désarmement), avec les bras, le chargeur, la culasse et les points d’éjection. Les textures, l’icône, la munition ID 179 et les sons officiels de tir `f_bene_a.wav` et de rechargement `bene_r.wav` sont également présents.

La table d’animations place ce bloc exactement entre le Mosin et le Garand. Cependant, l’emplacement d’objet correspondant est devenu la boussole : l’entrée Weapon d’origine a donc été remplacée. Aucun modèle extérieur ou posé `w_benelli*` n’est conservé, et les paramètres originaux de chargeur, cadence, dégâts et dispersion manquent. Une activation stable écraserait un objet livré ou inventerait ces valeurs ; seule une entrée additive expérimentale est acceptable.

## Garrote

La Garota est citée par le concepteur principal dans l'arsenal de préproduction. Aucune chaîne locale complète de modèle, animation et comportement n'est démontrée. Statut : arme annoncée puis retirée, implémentation récupérable non prouvée.

## ZK-383

Le ZK-383 apparaît dans l'iconographie alpha/bêta communautaire. Aucun ensemble local complet et identifiable n'a encore été relié à cette arme. Statut : représentation ancienne crédible, restauration directe non disponible.

## Traces orphelines

Le FG 42 est explicitement marqué `DISABLED` dans un catalogue ancien et conserve une munition, mais ni modèle ni icône. La MG 34 portative conserve une munition et des icônes, sans modèle portatif identifiable. MG 15 et MG 81 possèdent des entrées, icônes et sons compatibles avec des montages de véhicule, mais aucune chaîne d’arme portative démontrée. Ces traces ne sont pas activables seules.

## Faux positifs

- Le M1 Garand est présent dans le jeu final.
- Le Flak 38 existe comme arme stationnaire.
- Le Stevens 311 est rare mais récupérable.
- Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck sont des éléments livrés avec Sabre Squadron.
- Le Vickers K est le composant monté de la jeep SAS déjà active, pas une arme portative dormante.
- Le canon de 17 mm est utilisé activement dans `Ardens1_obj` ; sa mention désactivée dans une ancienne liste ne décrit pas son état final.
- Les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS 230 sont bien présents, mais sans chaîne de pilotage complète.

## Décision actuelle

Aucune arme incomplète n'est activée dans le paquet stable. La Benelli est prioritaire pour un démonstrateur FPV utilisant uniquement ses ressources officielles, puis pour une entrée additive qui ne remplace jamais la boussole. Les lance-flammes restent des prototypes isolés ; aucune de ces créations ne doit être présentée comme une arme officielle simplement réactivée.
