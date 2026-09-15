# Inventaire des armes et véhicules retirés

Premier balayage lexical des archives. Les nombres comptent des noms ou sous-chaînes et ne prouvent ni une liaison exacte à une mission ni une jouabilité complète.

| Élément | Correspondances lexicales | Ressources modèle/animation exactes | Scripts | Tables | Classement |
|---|---:|---:|---:|---:|---|
| Benelli M4 | 27 | 18 | 0 | 9 | reconstruction additive prioritaire |
| Deux lance-flammes | 5 | 1 | 0 | 4 | effet seul ; armes à reconstruire |
| FG 42 | 4 | 0 | 0 | 4 | catalogue incomplet |
| MG 34 portative | 6 | 0 | 0 | 6 | armement de char actif ; portative incomplète |
| Vickers K | 1 | 1 | 0 | 0 | arme montée active sur Jeep SAS |
| MG 15 | 6 | 0 | 0 | 6 | armement monté seulement |
| MG 81 | 6 | 0 | 0 | 6 | armement monté seulement |
| Garota | 0 | 0 | 0 | 0 | aucune ressource locale |
| ZK-383 | 0 | 0 | 0 | 0 | aucune ressource locale |
| Me 323 | 6 | 2 | 0 | 0 | modèle présent, non placé et non pilotable |
| Aichi Val | 3 | 2 | 0 | 0 | modèle présent, non placé et non pilotable |
| Fa 223 | 2 | 2 | 0 | 0 | modèle présent, non placé et non pilotable |
| La-5 | 24 | 2 | 5 | 0 | modèle présent, non placé et non pilotable |
| Ju 52 | 24 | 2 | 4 | 0 | décor scénarisé actif, non pilotable |
| Fw 200 | 2 | 2 | 0 | 0 | modèle présent, non placé et non pilotable |
| Li-2 | 16 | 2 | 8 | 0 | modèle présent, non placé et non pilotable |
| DFS 230 | 2 | 2 | 0 | 0 | modèle présent, non placé et non pilotable |

Lecture manuelle recoupée :

- le Ju 52 est le seul aéronef retiré dont un usage exact dans une mission soit prouvé : il reste un décor scénarisé dans Africa 1 ;
- les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS/DSF 230 sont réellement présents et articulés, mais aucune chaîne commerciale de placement ou de pilotage ne subsiste ;
- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;
- les correspondances lexicales La-5 dans `posila5`, par exemple, sont des faux positifs distincts : elles ne remettent pas en cause la présence du vrai modèle `la_La-5.4ds` ;
- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.

## Armes déjà actives ou faussement présentées comme retirées

Le Garand et le fusil juxtaposé Stevens disposent de leurs modèles monde et FPV, animations, entrées Weapon et munitions : ils sont déjà jouables. Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck de Sabre Squadron sont eux aussi complets et actifs. Le Flak 38 et le canon de 17 mm sont déjà employés comme armes fixes.

Le Vickers K n’est pas une arme portative oubliée. `w_vickerKFPV.4ds` est l’arme montée de la Jeep SAS : le modèle de Jeep conserve ses sièges, caméras et l’ancrage `BARREL01_00`, et une mission CMP relie encore exactement cet ancrage au modèle FPV. MG 15 et MG 81 n’ont pas de modèles portatifs démontrés ; leurs entrées correspondent à des armements montés.

## Benelli M4

La Benelli est le candidat expérimental le mieux conservé. Neuf couples d’animation `#FPVBeneli*.4ds/.5DS`, les textures et icônes, les sons de tir et de rechargement, le bloc `FpvAnims.sav` et la munition 179 subsistent. En revanche, l’ancien rang Weapon est occupé par la boussole et aucun modèle extérieur/posé ni paramètres originaux complets n’ont été retrouvés.

Une restauration doit donc ajouter une nouvelle entrée sans écraser la boussole, recréer un modèle monde et signaler comme reconstruits la capacité, la cadence, les dégâts et la dispersion. Elle reste hors du lot stable jusqu’à validation en jeu.

## Armes incomplètes

Les deux lance-flammes conservent icônes, munitions, sons et effet. `flame1.4ds` ne pèse que 471 octets et contient seulement `fire01` : c’est un effet, pas une arme. Modèle, animations et comportement doivent être créés.

La MG 34 portative conserve une munition, des icônes et des sons, mais ni modèle portatif, ni animations FPV, ni entrée Weapon autonome. Il ne faut pas la confondre avec la MG 34 de char active. Le FG 42 ne subsiste que comme texte désactivé et munition. Garota et ZK-383 nécessitent des sources nouvelles ou une création moderne explicitement annoncée.

## Aéronefs

Les modèles exacts La-5, `la_aici`, `LA_M323`, Li-2, `la_Fa 223`, Fw 200 et DFS 230 sont présents avec leurs LOD et plusieurs pièces articulées. Cela permet un banc décoratif et des essais de collision, pas de revendiquer un véhicule jouable : commandes, physique de vol, HUD, dégâts, IA et synchronisation réseau manquent.

Le prochain ordre de travail reste : Benelli additive, test du Vickers K monté, banc décoratif Ju 52/La-5/Aichi, puis seulement lance-flammes, FG 42, MG 34 portative, Garota, ZK-383 et pilotage complet.
