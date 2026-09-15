# Étude expérimentale — variante legacy à trois véhicules d'Alps3_Obj

État : conception d'une seconde entrée multijoueur, 14 septembre 2026. Seuls
cette étude et son inventaire de création sont produits. Aucun script jouable,
registre, scène, installateur ou fichier du jeu n'est créé ou remplacé.

Cette proposition applique le
[`principe de reconstruction additive`](../PRINCIPE_RECONSTRUCTION_ADDITIVE.md) :
la mission Sabre reste la release ; une éventuelle reconstruction devient une
mission séparée nommée provisoirement `ALPS3_OBJ_LEGACY_THREE_VEHICLES`.

Une déclinaison solo distincte est préparée dans
[`VARIANTE_SOLO_RECONSTRUCTION.md`](VARIANTE_SOLO_RECONSTRUCTION.md). Elle ne
remplace ni l'entrée Sabre ni la future reconstruction multijoueur du convoi.

Sa fiche transversale figure aussi dans
[`MP_ONLY_TO_SOLO_MATRIX`](../MP_ONLY_TO_SOLO_MATRIX/ALPS3_OBJ/FICHE.md).

## Verdict

Les quatre scripts Base décrivent sans ambiguïté une ancienne règle de jeu :
amener l'un de deux Opel à moins de 15 m du détecteur d'arrivée et protéger
trois véhicules, suivis par les objectifs 2, 3 et 4. Ils ne suffisent pourtant
pas à reconstruire une mission : la scène et le registre effectifs appartiennent
à la variante Sabre au char, les deux Opel ont disparu, le troisième véhicule
n'est pas identifié et aucune condition de réussite finale des trois objectifs
de survie n'est conservée.

La variante legacy doit donc être traitée comme une **création moderne fondée
sur des règles commerciales partielles**, jamais comme quatre scripts à
réinjecter dans `missions/alps3_obj`.

## Baseline Sabre à préserver

Le registre effectif provient de `SabreSquadron.dta` et contient quatre
bindings, tous résolus :

| Acteur | Script actif |
| --- | --- |
| `dummy_objective` | `Alps3_obj_car_detect.scr` |
| `most_01` | `Alps3_drop.scr` |
| `dummy_zasrtank` | `Alps3_tankdetect.scr` |
| `la_Pak_` | `Alps3_delo.scr` |

Le script Sabre homonyme `Alps3_obj_car_detect.scr` suit `panzer`, initialise
les objectifs 1 à 3, gère leur échec à la destruction du char et valide
l'objectif d'arrivée. `Alps3_drop.scr`, `Alps3_tankdetect.scr` et
`Alps3_delo.scr` fournissent les autres conditions et valeurs 50/51. Aucun
script attaché ne manque.

La scène effective contient `panzer` et ses contrôleurs. Elle ne contient ni
`La_OpelE_` ni `La_OpelE_2`. Les trois scripts Base de protection sont
disponibles mais non liés, sans porteur homonyme libre. Remplacer le script
Sabre homonyme par le détecteur Base détruirait la logique release ; c'est
explicitement interdit.

## Contrat commercial survivant

| Fragment Base | Règle attestée | Lacune |
| --- | --- | --- |
| `Alps3_obj_car_detect.scr` | objectif 1 actif ; réussite si `La_OpelE_` ou `La_OpelE_2` arrive à moins de 15 m | position du détecteur et textes absents |
| `Alps3_obj_car_01.scr` | objectif 2 actif ; échec à la mort de son porteur | identité, placement et réussite finale absents |
| `Alps3_obj_car_02.scr` | objectif 3 actif ; échec à la mort de son porteur | identité, placement et réussite finale absents |
| `Alps3_obj_car_03.scr` | objectif 4 actif ; échec à la mort de son porteur | troisième véhicule inconnu ; commentaire erroné, code sans ambiguïté sur l'objectif 4 |

Deux véhicules seulement sont nommés par le détecteur, alors que trois scripts
attendent chacun un porteur. Rien ne prouve si le troisième était un autre Opel,
un char, un véhicule allié différent ou un objet de mission. Assigner les trois
scripts aux deux Opel produirait soit un doublon, soit un véhicule non protégé.

De même, les scripts mettent les objectifs de survie à l'état actif et savent
uniquement les faire échouer. Ils ne disent pas si ces objectifs réussissaient
à l'arrivée du premier Opel, à l'arrivée de chaque véhicule, à la fin d'un
compte à rebours ou à une fin de manche externe.

## Architecture additive proposée

L'option recevable est une **seconde entrée multijoueur** avec son propre
répertoire de mission, son propre `mpscripts.dta`, sa scène, ses textes et son
identifiant d'affichage. Elle peut réutiliser des modèles commerciaux présents
dans les archives, mais pas les frames ni le registre de la mission Sabre.

Le sélecteur de carte doit présenter séparément :

| Entrée | Contenu | Statut |
| --- | --- | --- |
| `Alps3_Obj` | char `panzer`, objectifs 1–3, scripts Sabre | release inchangée |
| `Alps3_Obj — Legacy trois véhicules` | convoi reconstruit, objectifs 1–4 | prototype moderne, désactivé par défaut |

Cette séparation évite les collisions de noms, d'objectifs, de valeurs 50/51,
de zones de spawn et de scripts homonymes. Elle permet aussi de supprimer la
branche expérimentale sans restaurer de fichier release.

## Questions bloquantes avant prototype

1. Identifier le troisième véhicule à partir d'une scène, d'un registre ou
   d'une build antérieure.
2. Retrouver ou redessiner explicitement les trois placements de départ, la
   route carrossable et la zone d'arrivée.
3. Retrouver les quatre textes d'objectifs ou les écrire comme contenu
   `MODERNE`, sans les présenter comme commerciaux.
4. Fixer la réussite des objectifs 2–4 : survie jusqu'à quelle condition ?
5. Définir les règles de manche si un véhicule est abandonné, immobilisé,
   retourné, occupé au changement d'hôte ou détruit simultanément à l'arrivée.
6. Déterminer si « n'importe quel Opel » réussit seulement l'objectif 1 ou
   termine toute la mission alors que les deux autres véhicules survivent.

Tant que ces réponses manquent, un prototype de script donnerait une fausse
précision et figerait des choix de level design non commerciaux.

## Protocole futur

La première version jouable devra tracer séparément arrivée et état de chacun
des trois véhicules. Les objectifs de protection ne pourront réussir qu'une
fois, après une condition documentée ; une destruction et une arrivée dans la
même fenêtre réseau devront produire un résultat déterministe. Les tests
couvriront hôte/client, changement d'hôte, joueurs tardifs, destruction
simultanée, véhicule vide, véhicule immobilisé et fin de manche.

L'entrée Sabre sera testée avant et après installation : ses quatre bindings,
ses trois objectifs et ses valeurs 50/51 devront rester strictement identiques.

## Sources internes

- registre effectif `missions/alps3_obj/mpscripts.dta` de
  `SabreSquadron.dta` ;
- scène effective `scene2.bin`, `actors.bin` et `sounds.bin` ;
- scripts Base `Alps3_obj_car_01/02/03.scr` et
  `Alps3_obj_car_detect.scr` ;
- scripts Sabre `Alps3_obj_car_detect.scr`, `Alps3_drop.scr`,
  `Alps3_tankdetect.scr` et `Alps3_delo.scr`.
