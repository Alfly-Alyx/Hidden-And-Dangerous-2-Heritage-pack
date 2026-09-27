# Garota et ZK-383 : deux extérieurs modernes distincts

**27 septembre 2026.** Ressources originales autorisées par l'utilisateur,
`MODERNE`, `pending`. Aucune ressource commerciale retrouvée n'est revendiquée.
Les deux recettes restent indépendantes ; aucune arme jouable n'est installée.

## Provenance et références

La Garota est un **accessoire de jeu inventé** : deux poignées, un cordon
décoratif relâché, couleurs et proportions choisies ici. Ce n'est ni la copie
d'une ressource de préproduction ni une restitution historique établie. Les
deux repères de présentation ne sont pas des os ou des cibles d'interaction.

Pour le ZK-383, le catalogue du Vojenský historický ústav Praha décrit un
chargeur latéral gauche incliné, un manchon ajouré et un bipied repliable ;
la longueur totale indiquée est 875 mm. Ces éléments guident la silhouette
moderne, présentée avec bipied ouvert. [Jan Skramoušský, « Samopal ZK 383 »,
7 novembre 2018](https://www.vhu.cz/samopal-zk-383/), consulté le 27 septembre 2026.

La référence utilisée est **textuelle** : aucune photographie n'a été copiée,
redistribuée ni utilisée pour mesurer la géométrie. Les proportions détaillées,
formes des ouvertures, couleurs et repères sont des choix artistiques modernes.
Ce modèle n'est pas un relevé de l'exemplaire du musée ou un plan technique.
Les caractéristiques mécaniques de la notice ne sont pas transformées en
paramètres de gameplay non démontrés.

## Livrables reproductibles

| Recette | Pièces / matériaux / repères | Triangles LOD haut / bas | SHA-256 du 4DS désactivé |
| --- | --- | --- | --- |
| `modern-garota-world.json` | 7 / 4 / 2 | 732 / 388 | `f51cfaf83e947527849c056538206dc7a7feaa840ffbd7c14ba06d9ae64a5cd4` |
| `modern-zk383-world.json` | 33 / 5 / 5 | 1120 / 720 | `1730926a7468d5a91ec4ae19467ee2613905146caa329f7c0a163f09a9c30032` |

Le générateur existant `tools/build_modern_asset.py` ne lit pas le jeu. Il
produit un 4DS v41 désactivé, un OBJ, un MTL, une planche et un manifeste dans
un répertoire neuf ignoré par Git. Les sorties contrôlées sont
`.analysis/modern-assets/GarotaWorld_v1` et `ZK383World_v1` : cinq fichiers chacune.
Les trois vues des deux planches ont été inspectées. Le profil de la Garota
superpose les poignées ; les vues oblique et supérieure les distinguent.

Six tests nouveaux vérifient les deux recettes, les empreintes, deux lecteurs
de format indépendants, les deux niveaux de détail, les surfaces fermées et
orientées, les particularités de chaque modèle, les sorties désactivées et le
refus d'écraser une génération existante. Ces tests n'utilisent aucune archive
commerciale. Ils ne constituent pas des essais du chargeur de modèles en jeu.

```powershell
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/GAROTA_AND_ZK383/modern-garota-world.json --output-name GarotaWorld_Nouveau
.\.venv\Scripts\python.exe tools/build_modern_asset.py --recipe experimental/GAROTA_AND_ZK383/modern-zk383-world.json --output-name ZK383World_Nouveau
```

## Travail restant, non masqué par les extérieurs

- Mains, animations FPV et raccords aux personnages ; les repères statiques
  ne suffisent pas à réaliser une prise.
- ZK-383 : animation des pièces, événements, icône, sons, descripteurs additifs,
  comportement, sauvegarde et réseau.
- Garota : conception et réalisation de l'interaction à deux personnages,
  animations synchronisées, interruption et états sauvegardés/réseau.
- Chargement, rendu et qualité visuelle en moteur pour les deux ressources.

Ni Item/Weapon ni munition ne sont créés ou réservés. Aucun fichier du jeu
personnel, table centrale, installateur ou mission n'est modifié.

La [banque de mouvements ZK-383](ANIMATIONS_ZK383_MODERNES.md) est maintenant
réalisée séparément : neuf clips de pièces, modèle statique inchangé, sans mains,
événements ni comportement fonctionnel. La liste précédente décrit les limites
de ces extérieurs ; l'état courant de l'animation est détaillé dans cette suite.
