# Alps3_Obj legacy — éléments créés, attestés et spéculatifs

État au 14 septembre 2026. Cette liste empêche de confondre une preuve
commerciale avec le contenu qu'une future mission devrait inventer.

## Créé dans ce lot

| Élément | Nature |
| --- | --- |
| `ETUDE.md` | analyse et architecture additive |
| `ELEMENTS_CREES_OU_SPECULATIFS.md` | présent inventaire |
| `VARIANTE_SOLO_RECONSTRUCTION.md` | conception de l'entrée solo distincte |

Aucun script `.scr`, registre, binaire de scène, texte, modèle, son ou package
de mission n'est créé.

## Attesté par les sources commerciales

- deux noms de véhicules : `La_OpelE_` et `La_OpelE_2` ;
- une zone d'arrivée évaluée à 15 m du porteur de
  `Alps3_obj_car_detect.scr` ;
- un objectif d'arrivée 1 ;
- trois objectifs de protection 2, 3 et 4 qui échouent à la mort de leur
  porteur ;
- quatre scripts Base conservant ces règles partielles ;
- une variante Sabre actuelle complète, active et indépendante, centrée sur
  `panzer`.

## À créer ou retrouver — donc spéculatif

| Élément futur | Ce qui manque | Étiquette obligatoire si créé |
| --- | --- | --- |
| troisième véhicule | identité, modèle, nom de frame | `MODERNE` |
| scène legacy | placements, terrain utile, collisions, route | `MODERNE` ou `RECONSTRUIT` selon les preuves |
| détecteur d'arrivée | position et volume exacts | `MODERNE` si redessiné |
| registre legacy | porteurs des quatre scripts et autres contrôleurs | `MODERNE` |
| textes objectifs 1–4 | libellés et traductions | `MODERNE` s'ils sont rédigés |
| succès des objectifs 2–4 | événement final et ordre de résolution | `MODERNE` |
| logique multijoueur | réplication, arrivée simultanée, changement d'hôte | `MODERNE` |
| métadonnées de carte | nom affiché, description, miniature, identifiant | `MODERNE` |

Les noms de travail proposés pour la mission et son menu sont eux aussi
provisoires ; ils ne constituent pas des identifiants commerciaux retrouvés.

## Éléments interdits dans cette branche

- remplacer `missions/alps3_obj` ou son registre Sabre ;
- reprendre les valeurs 50/51 sans vérifier leur portée dans la nouvelle
  mission ;
- présenter le troisième véhicule ou les textes rédigés comme des restaurations
  officielles ;
- distribuer la branche avant qu'elle possède un identifiant et un répertoire
  distincts de la release.
