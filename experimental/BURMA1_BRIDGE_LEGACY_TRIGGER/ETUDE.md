# Burma 1 — ancien activateur de renforts du pont

État du 25 septembre 2026 : **documenté, porteur et protocole manquants**.
Aucun script généré, acteur ajouté ni binding modifié. Le réveil commercial à
60 m est conservé; le vestige à 7 m n'est pas présenté comme un correctif sûr.

## Chaîne réellement disponible

`bu1_bridge.scr` existe dans `Scripts.dta` et envoie le signal 1 aux trois
acteurs BU1_32/33/34 lorsque le joueur est à 7 m de son porteur. Il n'est lié
à aucun propriétaire dans le registre effectif Patch et n'est pas accessible
par les dépendances littérales des scripts liés : 115 scripts racines, 117
accessibles sur 118 présents. Aucune frame nommée pour ce détecteur n'a été
identifiée; les objets explosifs du pont ne sont pas des porteurs libres à
lui attribuer par analogie de nom.

Les trois destinataires existent et sont liés. Aucun ne possède de récepteur
du signal 1. Leur réveil à 60 m est actif et possède déjà son comportement :

| Acteur | Source effective | Réveil / alarme commerciale |
|---|---|---|
| BU1_32 | Patch | réveil, embarquement `Type97_18`, optimisation 2; alarme : vue 55 puis fin de script |
| BU1_33 | Base | réveil sur place; certaines alarmes conduisent à `BU1_33_01`, accroupi |
| BU1_34 | Base | même schéma, avec `BU1_34_01` |

Le véhicule/arme `Type97_18` est sérialisé dans les acteurs; les deux checkpoints
33/34 sont nommés dans le fichier Base. Un ajout générique « aller au pont »
aux trois handlers effacerait ces différences, notamment le rôle du garde 32.

## Verdict

Lier le seul script orphelin ne suffirait pas : le porteur n'a pas de placement
établi et les récepteurs sont manquants. Copier les réveils de proximité dans
de nouveaux handlers ne prouverait pas l'intention historique. La redondance
avec les rayons 60 m est plausible, mais **non démontrable par comparaison de
7 et 60 seuls**, puisque le centre du rayon 7 m est inconnu.

Ne pas ajouter de trigger. Rechercher d'abord une source attribuée donnant
porteur et position. En parallèle, une baseline en jeu doit mesurer le réveil
des trois gardes, l'embarquement du 32 et les routes 33/34 selon les approches
du pont. Si tout le rôle attendu est déjà rempli, classer ce vestige comme
protocole abandonné. Toute extension moderne devra être indépendante et
explicitement justifiée, sans doubler l'activation existante.

## Empreintes

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `bu1_bridge.scr` | 701 | `b12c7a300fa03a949e162c752d2247535199c5b4fdce3c09bddd6d579283de47` |
| `bu1_32.scr` | 1420 | `de6a0ad54f1579ab79c006cc53d585d38d2d1476c56afda6b63aaeb4b672a206` |
| `bu1_33.scr` | 1685 | `0344da9d8896a8b2d3e860fd792052d1ab05366551c48b5a7979bfa09a2b027b` |
| `bu1_34.scr` | 1686 | `1a8e2a43b35a9d2f4acd7487aa2c4850bcdaf4fd4e96b3285b4f093fa6c196ad` |
| Registre Patch | 4565 | `087ff71d503e7561b9c2ae9587f05af97e30797f927ab2dc12f7774d3039e254` |
| Acteurs Patch | 21015 | `6cde72833a8a77fd211b23353516aa032b670f5436011e619aaa512b11c709e2` |
| Scène Patch | 2756874 | `a14fdc0555525a8f4c6175c99d28765dd2d37d5c177cf0b6bfa78940b216db7c` |
| Checkpoints Base | 124154 | `79749b9e7de24fc17f2c57c5296a0384b91d9a45dce6cec8703610cfdd7054a6` |

Vérifications de liaison et fermeture effectuées avec les lecteurs d'archives,
`parse_bindings` et `script_closure`; analyse sur commentaires retirés, sans
écriture de fichiers commerciaux. Ces résultats ne sont pas des essais moteur.
