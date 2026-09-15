# Armes et équipements retirés

## Deux lance-flammes

Les noms Flamethrower Portable No. 2 et Flammenwerfer 35, ainsi que leurs
munitions, subsistent dans les listes historiques et identifiants d'objets.

L'examen local corrige toutefois une interprétation fréquente :

- la table Sabre conserve un record allemand de 135 octets nommé
  `Flammewerfer`, qui référence `w_flmwrFPV`, `wi_ge-flmwr35`,
  `w_flmwr` et le texte 1044 ;
- les deux modèles référencés par ce record sont absents ;
- le record britannique suivant a été réemployé par `Flak TMP`, le texte 1046
  et l'icône `wi_flak38`, mais conserve encore les fragments `_FlameFPV` et
  `_Flame` de l'ancienne arme ;
- les deux records de munition de 508 octets sont intacts et identiques entre
  le jeu de base et Sabre Squadron : textes 1207/1208, masse 5, catégorie 2,
  modèle générique `w_ammo` et icônes propres ;
- les quatre icônes principales d'arme et de munition, avec leurs seize
  variantes de texture, subsistent dans `maps.dta` ;
- flame1.4ds ne pèse que 471 octets ;
- il ne contient qu'un objet `fire01`, huit sommets et quatre faces ;
- le bloc 25 `plamenomet` d'effet est identique dans les tables Base et Sabre ;
- aucune entrée correspondante n'existe dans `item_shoot.tbl` ou
  `FpvAnims.sav`, et aucun script commercial ne pilote ces armes ;
- les deux mentions sonores retrouvées sont des réactions vocales face au
  lance-flammes, pas un son de tir ou de rechargement.

Il n'existe donc pas une option cachée qu'il suffirait de cocher. Une version jouable demanderait de créer le modèle tenu et posé, les animations, le réservoir, les sons, la portée, les dégâts, les réactions de l'IA et les règles multijoueurs. Elle serait une reconstruction communautaire inspirée d'une arme annoncée.

`tools/flamethrower_evidence_audit.py` contrôle automatiquement les quatre
records, les vingt ressources d'icônes, le modèle et l'effet, les textes
anglais/français, ainsi que l'absence des liaisons nécessaires à une arme
jouable. Les empreintes servent à empêcher qu'une future archive différente
soit prise pour cette version commerciale.

Sources contemporaines :
- https://www.gamespot.com/articles/hidden-and-dangerous-2-qanda/1100-2713950/
- https://games.tiscali.cz/preview/hidden-dangerous-2-preview-51655
- https://hidden-and-dangerous.net/articles/interview-with-illusion-softworks-2004-10-26/

## Benelli M4 Super 90

C’est le vestige d’arme le plus complet retrouvé. Les archives conservent neuf couples d’animations FPV `#FPVBeneli` (visée, tir, rechargement, enrayage, armement et désarmement), avec les bras, le chargeur, la culasse et les points d’éjection. Les textures, l’icône, la munition ID 179 et les sons officiels de tir `f_bene_a.wav` et de rechargement `bene_r.wav` sont également présents. `others.DTA::TABLES/item_shoot.tbl` contient en plus un record balistique complet `Benelli` de 135 octets, dont l’empreinte et les premiers champs sont désormais contrôlés automatiquement.

La table d’animations place ce bloc exactement entre le Mosin et le Garand. Le record d’objet correspondant est devenu la boussole, mais conserve encore les fragments `M4`, `_benelliFPV` et `lli` mêlés à `KOMPAS`, `ii_compas` et `d_compas` : l’entrée Weapon d’origine a donc été remplacée, pas simplement masquée. Aucun modèle extérieur ou posé `w_benelli*` n’est conservé, et les clés reliant le record balistique, les animations et la munition ne sont pas encore prouvées.

L’ID additif 359, premier numéro après la plage commerciale publiée, était libre dans les 80 catalogues commerciaux et 144 catalogues communautaires locaux inspectés. Il reste une proposition expérimentale : le prototype devra vérifier sa disponibilité au moment de l’installation et refuser toute collision, sans numéro de repli silencieux. Toute capacité, cadence, dispersion, liaison ou géométrie non démontrée doit rester marquée comme création moderne. Une activation stable écraserait un objet livré ou inventerait encore des données ; seule cette reconstruction additive isolée est acceptable.

## Garrote

La Garota est citée par le concepteur principal dans l'arsenal de préproduction. Aucune chaîne locale complète de modèle, animation et comportement n'est démontrée. Statut : arme annoncée puis retirée, implémentation récupérable non prouvée.

## ZK-383

Le ZK-383 apparaît dans l'iconographie alpha/bêta communautaire. Aucun ensemble local complet et identifiable n'a encore été relié à cette arme. Statut : représentation ancienne crédible, restauration directe non disponible.

## Traces orphelines

Le FG 42 est explicitement marqué `DISABLED` dans un catalogue ancien et conserve une munition, mais ni modèle ni icône. La MG 34 portative conserve une munition et des icônes, sans modèle portatif identifiable. MG 15 et MG 81 possèdent des entrées, icônes et sons compatibles avec des montages de véhicule, mais aucune chaîne d’arme portative démontrée. Ces traces ne sont pas activables seules.

`w_m1gran.4ds` est un petit modèle monde dont la texture interne se nomme
`W_GRANATUS.BMP`. Il n'a toutefois ni entrée d'objet, ni animation FPV, ni
texte explicite, ni comportement et n'apparaît dans aucune mission
commerciale. L'identifiant de texte libre 1065, placé près des grenades et
équipements, ne suffit pas à lui attribuer un nom ou une fonction. Il reste un
modèle orphelin de reconstruction, pas une grenade cachée réactivable.

Les modèles `w_mine`, `w_specmine`, `w_mineg`, `w_minedecor` et
`w_mdtank` sont également des variantes anciennes ou techniques sans chaîne
complète d'objet, d'animation, de comportement et de placement. Les mines
antipersonnel, antichar et magnétique livrées sont déjà actives ; ces cinq
modèles ne doivent pas les remplacer.

## Faux positifs

- Le M1 Garand est présent dans le jeu final.
- Le Flak 38 existe comme arme stationnaire.
- Le Stevens 311 est rare mais récupérable.
- Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck sont des éléments livrés avec Sabre Squadron.
- Le Vickers K est le composant monté de la jeep SAS déjà active, pas une arme portative dormante.
- Le canon de 17 mm est utilisé activement dans `Ardens1_obj` ; sa mention désactivée dans une ancienne liste ne décrit pas son état final.
- Les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DSF 230 sont bien
  présents. Aucun identifiant exact n'apparaît dans les 3 059 scènes,
  registres et scripts commerciaux examinés. Les 49 `car_table.dat` ne
  contiennent pas non plus ces noms lisibles, mais leur format binaire reste
  indécodé : aucune chaîne pilotable complète n'est démontrée.

## Décision actuelle

Aucune arme incomplète n'est activée dans le paquet stable. La Benelli est prioritaire pour un démonstrateur FPV utilisant uniquement ses ressources officielles, puis pour une entrée additive qui ne remplace jamais la boussole. Les lance-flammes restent des prototypes isolés ; aucune de ces créations ne doit être présentée comme une arme officielle simplement réactivée.
