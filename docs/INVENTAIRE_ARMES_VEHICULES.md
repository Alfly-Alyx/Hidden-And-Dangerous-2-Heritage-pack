# Inventaire des armes et véhicules retirés

Premier balayage lexical des archives. Les nombres comptent des noms ou sous-chaînes et ne prouvent ni une liaison exacte à une mission ni une jouabilité complète.

| Élément | Correspondances lexicales | Ressources modèle/animation exactes | Scripts | Tables | Classement |
|---|---:|---:|---:|---:|---|
| Benelli M4 | 29 | 18 | 0 | 11 | reconstruction additive prioritaire |
| Deux lance-flammes | 5 | 1 | 0 | 4 | effet seul ; armes à reconstruire |
| FG 42 | 6 | 0 | 0 | 6 | catalogue incomplet |
| MG 34 portative | 8 | 0 | 0 | 8 | armement de char actif ; portative incomplète |
| Vickers K | 1 | 1 | 0 | 0 | arme montée active sur Jeep SAS |
| MG 15 | 8 | 0 | 0 | 8 | armement monté seulement |
| MG 81 | 8 | 0 | 0 | 8 | armement monté seulement |
| Modèle `w_m1gran` | 1 | 1 | 0 | 0 | modèle orphelin, fonction exacte non démontrée |
| Anciennes mines | 5 | 5 | 0 | 0 | variantes techniques sans chaîne d'objet complète |
| Garota | 0 | 0 | 0 | 0 | aucune ressource locale |
| ZK-383 | 0 | 0 | 0 | 0 | aucune ressource locale |
| Me 323 | 6 | 2 | 0 | 0 | modèle présent ; pilotage non démontré |
| Aichi Val | 3 | 2 | 0 | 0 | modèle présent ; pilotage non démontré |
| Fa 223 | 2 | 2 | 0 | 0 | modèle présent ; pilotage non démontré |
| La-5 | 24 | 2 | 5 | 0 | modèle présent ; pilotage non démontré |
| Ju 52 | 24 | 2 | 4 | 0 | décor scénarisé actif ; pilotage non démontré |
| Fw 200 | 2 | 2 | 0 | 0 | modèle présent ; pilotage non démontré |
| Li-2 | 16 | 2 | 8 | 0 | modèle présent ; pilotage non démontré |
| DFS 230 | 2 | 2 | 0 | 0 | modèle présent ; pilotage non démontré |

Lecture manuelle recoupée :

- le Ju 52 est le seul aéronef retiré dont des usages exacts dans des missions soient prouvés : il reste un décor scénarisé actif dans Africa 1 et Africa 2 ;
- les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DSF 230 sont réellement présents et articulés, mais aucune liaison par identifiant exact ne subsiste dans les 3 059 scènes, registres et scripts commerciaux examinés ;
- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;
- les correspondances lexicales La-5 dans `posila5`, par exemple, sont des faux positifs distincts : elles ne remettent pas en cause la présence du vrai modèle `la_La-5.4ds` ;
- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.
- aucun des 49 `car_table.dat` commerciaux ni des 105 tables libres actuellement installées ne contient sous forme lisible les identifiants exacts de ces aéronefs ; leur format binaire n’étant pas décodé, ce résultat n’exclut pas une ancienne liaison numérique ou indirecte.

## Armes déjà actives ou faussement présentées comme retirées

Le Garand et le fusil juxtaposé Stevens disposent de leurs modèles monde et FPV, animations, entrées Weapon et munitions : ils sont déjà jouables. Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck de Sabre Squadron sont eux aussi complets et actifs. Le Flak 38 et le canon de 17 mm sont déjà employés comme armes fixes.

Le Vickers K n’est pas une arme portative oubliée. `w_vickerKFPV.4ds` est l’arme montée de la Jeep SAS : le modèle de Jeep conserve ses sièges, caméras et l’ancrage `BARREL01_00`, et une mission CMP relie encore exactement cet ancrage au modèle FPV. MG 15 et MG 81 n’ont pas de modèles portatifs démontrés ; leurs entrées correspondent à des armements montés.

## Benelli M4

La Benelli est le candidat expérimental le mieux conservé. Neuf couples d’animation `#FPVBeneli*.4ds/.5DS`, les textures et icônes, les sons de tir et de rechargement, le bloc `FpvAnims.sav` et la munition 179 subsistent. Surtout, `others.DTA::TABLES/item_shoot.tbl` conserve un record balistique complet `Benelli` de 135 octets, aux offsets 1547–1682, dont le SHA-256 est `56A60C8F6846A86E24137BAE21877935EA4F0D113F94F73B0CE6750F951ED7E7`.

Le record de 135 octets occupé par la boussole dans `SabreSquadron.dta::Tables/item_base_items.tbl` conserve simultanément `M4`, `_benelliFPV` et `lli` autour de `KOMPAS` et `ii_compas`. Son empreinte exacte est `3E040CBC5BFE0A4D3DBE8728F484928E4081636FBBE7A7D13DD3B15C583E115F`. Ces fragments confirment que l’ancien emplacement Benelli a été réemployé ; les valeurs numériques actuelles appartiennent toutefois à la boussole et ne sont pas des réglages d’arme récupérables.

Une restauration doit donc créer une nouvelle entrée sans écraser la boussole. L’ID 359 est le premier candidat après la plage commerciale publiée et était libre dans les 80 `items.dat` commerciaux et 144 communautaires inspectés ; il reste provisoire et toute collision devra être refusée explicitement. Aucun modèle extérieur/posé complet n’est conservé, et les liaisons numériques vers `FpvAnims.sav`, le record de tir et la munition 179 doivent encore être démontrées. Le modèle monde, ces liaisons et toute valeur non prouvée restent une reconstruction moderne, hors du lot stable jusqu’aux essais solo et réseau.

`tools/item_id_collision_audit.py` rend cette vérification reproductible. Sur l’installation inspectée, il a décodé 149 462 enregistrements dans les 80 fichiers commerciaux et 144 missions installées, contrôlé 7 135 déclarations de `mpmaplist.txt` et n’a trouvé aucun ItemID 359. Pour les neuf fichiers anciens ou tronqués que le parseur ne peut finir, le verdict n’est accepté que si les octets candidats sont absents ou entièrement situés dans le préfixe déjà décodé ; une occurrence ambiguë ferait échouer le contrôle.

## Armes incomplètes

Le Flammenwerfer conserve un record d'arme complet comme référence, mais ses modèles `w_flmwrFPV` et `w_flmwr` sont absents. Le record britannique a été remplacé par `Flak TMP` et ne conserve que les fragments `_FlameFPV` et `_Flame`. Les deux munitions, vingt ressources d'icônes et l'effet 25 subsistent. `flame1.4ds` ne pèse que 471 octets et contient seulement `fire01`, huit sommets et quatre faces : c'est un effet, pas une arme. Les libellés sonores retrouvés sont deux réactions vocales, pas les sons de tir ou de recharge. Aucune table de tir, animation FPV ou logique de script n'est reliée ; modèles, animations et comportement doivent donc être créés.

`tools/flamethrower_evidence_audit.py` vérifie ces preuves et leurs empreintes exactes sans exporter les données commerciales dans le dépôt.

Le FG 42 et la MG 34 portative conservent chacun un record de tir complet et une munition. Leurs anciens emplacements d'objet 27 et 32 ont cependant été réemployés par des casques, malgré les fragments résiduels `_42FGfpv` et `_34mgFPV`. Le FG 42 n'a plus de modèle, d'icône de munition ni de son identifiable ; la MG 34 portative conserve icônes et sons, mais ni modèle ni animations FPV. La munition 211 appartient à la MG 34 de char active et ne constitue pas une preuve portative.

MG 15 et MG 81 conservent quatre entrées d'armement monté, des icônes et des sons. L'emplacement 55 est incohérent entre la table de tir MG 15 et l'objet MG 81, signe d'un réemploi ; aucun modèle portatif n'est démontré. `tools/orphan_weapon_evidence_audit.py` contrôle ces records et interdit de réutiliser les IDs 27/32. Garota et ZK-383 nécessitent des sources nouvelles ou une création moderne explicitement annoncée.

`w_m1gran.4ds` conserve un modèle et une référence de texture `W_GRANATUS.BMP`, mais aucune entrée d'objet, animation FPV, occurrence de mission ou fonction explicitement nommée. Le trou 1065 du catalogue textuel n'est pas une preuve suffisante de son identité. Les cinq modèles `w_mine*`/mine technique n'ont eux non plus ni chaîne d'objet complète ni placement commercial attesté ; ils restent séparés des mines finales actives.

## Aéronefs

Les modèles exacts La-5, `la_aici`, `LA_M323`, Li-2, `la_Fa 223`, Fw 200 et DSF 230 sont présents avec leurs LOD et plusieurs pièces articulées. Le M323 est le vestige le plus fourni avec six moteurs, plusieurs sièges, caméras et ancrages d’arme ; Fa 223, Li-2 et DSF 230 conservent eux aussi des sièges et caméras, tandis que le Fw 200 est plus proche d’un décor animé. Cela permet un banc décoratif et des essais de collision, pas de revendiquer un véhicule jouable : commandes, physique de vol, HUD, dégâts, IA et synchronisation réseau manquent.

`tools/aircraft_scenic_audit.py` vérifie les modèles et empreintes des huit types d’aéronefs, les 49 `car_table.dat` commerciaux, les 105 tables libres, les 3 059 ressources de mission pertinentes et les deux chaînes Ju 52 encore actives. Africa 1 utilise `CUTjunkers` et `CUTjunkersB` dans sa cinématique ; Africa 2 anime `HoriciJunkers` sur `fight_stage01`, tourne ses trois hélices, crée la fumée 16 puis masque et fait exploser l'appareil. La liaison vers `AF2_particle_junkers.scr` subsiste, mais le fichier manque dans Base, Patch et Sabre ; son rôle ne doit pas être inventé dans le paquet stable puisque `AF2_actprelet.scr` assure déjà la fumée et son nettoyage.

Le prochain ordre de travail reste : Benelli additive, test du Vickers K monté, banc décoratif Ju 52/La-5/Aichi, puis seulement lance-flammes, FG 42, MG 34 portative, Garota, ZK-383 et pilotage complet.
