# Propositions MODERNES — lance-flammes et aéronefs

État : architecture de laboratoire, non intégrée, 14 septembre 2026. Toutes les
fonctions décrites ici sont des **RECONSTRUCTIONS MODERNES**. Elles ne doivent
jamais être annoncées comme contenu coupé restauré.

## M1 — lance-flammes visuel

Prérequis : le banc OFFICIEL de l'effet 25 doit avoir établi son orientation,
sa durée et son nettoyage. La première création moderne ajoute seulement :

- un point d'émission porté par une arme factice entièrement nouvelle ;
- un état éteint/allumage/émission/extinction ;
- une durée maximale et une coupure forcée au changement d'arme, à la mort ou
  à la sauvegarde ;
- une jauge de carburant de laboratoire sans prétention historique.

Aucun dégât à ce stade. Le but est de savoir si l'effet suit correctement une
frame animée sans se dupliquer ni traverser visuellement le tireur.

## M2 — volume de dégâts expérimental

Le jet visible ne prouve aucune collision. Un second prototype, séparé, devrait
échantillonner un petit nombre de volumes le long d'un segment borné et appliquer
des impulsions espacées, jamais un dégât illimité à chaque image.

Mesures obligatoires : portée réelle, occultation par les murs, alliés, tireur,
véhicules, accumulation dans le temps, mort de la cible et nettoyage. La portée,
le débit, les dégâts et les réactions IA sont des choix d'équilibrage modernes.
Sans primitives moteur confirmées pour ces quatre points, aucun script exécutable
n'est fourni dans cette étude.

## M3 — chaîne d'arme complète

Une arme testable exige des assets originaux nouvellement créés : modèles tenu
et au sol, vues première et troisième personne, animations, réservoir, sons de
fonctionnement et icône propre si la redistribution des icônes commerciales
n'est pas autorisée. Elle doit ensuite couvrir inventaire, sélection, tir
continu, rechargement/carburant, dépôt, IA, sauvegarde et réseau.

Les entrées `AMMO Flammewer` et `AMMO Flamethrow` peuvent servir de repères lors
d'un test privé sur une installation possédée. Elles ne doivent pas être copiées
dans le prototype distribuable et ne fournissent aucun comportement.

## A1 — banc statique d'aéronef

Créer une mission laboratoire distincte par modèle, résolu depuis l'installation
du testeur : Ju 52, La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS 230. Le banc
ne propose ni siège joueur ni vol. Il mesure seulement :

- chargement, textures, échelle, orientation et collision ;
- LOD principal/simplifié ;
- présence et pivot des nœuds moteur, hélice/rotor, gouvernes, roues, sièges et
  caméras ;
- sauvegarde/reprise avec l'acteur statique.

Pour le Ju 52, ce banc moderne doit rester distinct de la scène Africa 1
officielle. Pour les sept autres, l'instanciation elle-même est moderne puisque
leur liaison à une mission n'est pas démontrée.

## A2 — animation de nœuds sans vol

Après A1, animer un seul nœud à la fois dans une scène privée : hélice, gouverne,
roue ou porte. Employer des vitesses manifestement de test et consigner les axes.
Ne pas déduire de ces pivots une aérodynamique, une commande joueur ou une table
de dégâts.

Le Ju 52 est le meilleur contrôle positif grâce à sa scène officielle. La-5 ou
Aichi peuvent ensuite servir de contrôle moderne simple. M323, Fa 223 et DFS 230
sont reportés tant que moteurs multiples, rotor ou remorquage n'ont pas de
contrat moteur identifié.

## A3 — pilotage libre, non réalisable avec les preuves actuelles

Un prototype de vol demanderait commandes, portance, décrochage, roulage,
atterrissage, collisions, dégâts, caméra, sortie, IA et réplication réseau. Aucun
de ces systèmes n'est déductible des seuls nœuds 4DS. Écrire maintenant un
contrôleur ferait une démonstration communautaire arbitraire, pas une expérience
de restauration bornée. Aucun code A3 n'est donc proposé.

## Éléments sans prototype

- **Garota** : absence de modèle et surtout des deux animations synchronisées
  attaquant/victime ; une maquette actuelle serait entièrement nouvelle.
- **ZK-383** : absence de modèle, animation, son et entrée locale ; réutiliser la
  balistique d'une autre arme ne restaurerait pas le ZK-383.
- **FG 42 et MG 34 portative** : des munitions ou icônes ne suffisent pas à
  produire l'arme manquante.

## Critères de publication

Un résultat moderne ne devient distribuable que s'il contient exclusivement du
code original et des assets nouveaux ou librement redistribuables. Il doit
détecter l'absence des archives commerciales et demander au testeur de les
installer légalement, sans les incorporer au paquet. Toute interface doit
afficher « reconstruction moderne » et séparer le comportement inventé des
identifiants historiques observés.
