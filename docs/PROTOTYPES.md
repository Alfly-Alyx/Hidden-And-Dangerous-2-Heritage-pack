# Prototypes et données incomplètes

## Classement

- Restaurable : données presque complètes, manque limité et non spéculatif.
- Variante déjà active : anciens scripts ou ressources remplacés par une version finale complète.
- Démonstration possible : assez de matière pour un prototype, mais création moderne nécessaire.
- Fragment historique : insuffisant pour être rendu jouable fidèlement.

## Prototypes installés

### Normandy3 Zone

Variante officielle absente de la liste finale. Treize fichiers lui sont propres, mais quatre fichiers de décor ou de chargement ne sont que des marqueurs de 16 à 19 octets et `volumy.bin` manque. Trois autres conteneurs sont réellement tronqués : `actors.bin` annonce 21 970 octets mais n'en conserve que 3 768, `scene2.bin` en annonce 6 309 393 mais n'en conserve que 2 814, et `sounds.bin` en annonce 8 603 mais n'en conserve que 70. Ces longueurs internes incohérentes expliquent le blocage du client multijoueur.

Le pack reprend donc exactement huit bases correspondantes de `NORMANDY3_MP` : les cinq fichiers absents ou factices et ces trois conteneurs incomplets. Il conserve les six données propres encore structurellement valides de la zone. Les quatorze fichiers obtenus sont tous déployés dans un dossier autonome ; le jeu ne dépend ainsi d'aucun mélange implicite entre ce dossier et `missions.dta`. Elle est ajoutée sous le nom `PROTOTYPE - Normandy3 Zone (exploration libre)` dans le mode **Occupation**.

### Africa5 Prototype

`AFRIKA5_MP` conserve sept fichiers propres. Six ressources manquantes peuvent être reprises d'`AFRICA5_MP`. Le pack déploie les treize fichiers de la carte complétée dans un dossier autonome. Ses sept scripts de citernes subsistent sous `Scripts/AFRICA5_MP` ; le pack les rend aussi disponibles sous l'orthographe attendue par le prototype, `Scripts/AFRIKA5_MP`, et leurs sept propriétaires sont présents dans la scène propre du vestige. La carte est déclarée sous le nom `PROTOTYPE - Africa5 (exploration libre)` dans le mode **Deathmatch**.

Ces vestiges ne sont pas ajoutes au menu solo natif : ils ne contiennent ni definition complete de mission solo, ni objectifs, ni fin de mission. Ils sont accessibles directement dans le jeu par Multijoueur > Creer > LAN : Africa5 en Deathmatch et Normandy3 Zone en Occupation.

Le contrôle indépendant `tools/prototype_deployment_audit.py` vérifie deux états
distincts : la possibilité de reconstruire les dossiers complets depuis les
archives commerciales, puis leur présence réelle sur le disque. La validation
finale exigera `13/13` fichiers et sept scripts pour Africa5, `14/14` fichiers
pour Normandy3 Zone, l'intégrité déclarée de `actors.bin`, `scene2.bin` et
`sounds.bin`, les deux entrées correctement nommées dans leur mode
multijoueur et zéro drapeau ou objet `border` dans leurs collisions. Un simple
nom visible dans le menu ne suffit donc plus à déclarer un prototype installé.

## Combien existe-t-il de cartes prototypes ?

Dans l'installation commerciale 1.12 étudiée, **deux dossiers de cartes distinctes sont actuellement assez complets pour être restaurés et explorés sans inventer une nouvelle géométrie** : `NORMANDY3_MP_ZONE` et `AFRIKA5_MP`.

Le jeu conserve davantage de vestiges historiques, mais ils ne constituent pas d'autres cartes autonomes immédiatement jouables : `ENGLAND`, `CASTLE1` et `CASTLE2` sont surtout des ensembles de scripts ; `ALPS3_OBJ` et `ARDENS1_OBJ` sont d'anciennes variantes de missions ensuite finalisées dans Sabre Squadron. Ils restent des pistes de reconstruction, pas trois ou cinq cartes supplémentaires déjà prêtes à activer.

## Dossiers officiels non activés automatiquement

### ENGLAND

Quatorze scripts : ennemis, otage, gardes, sniper, appels HELP et détecteurs de tranchée. Aucune carte complète correspondante n'a été retrouvée. Une démonstration sur une carte existante serait possible, mais ce ne serait pas la mission anglaise d'origine.

### CASTLE1

Soixante scripts d'une branche ancienne. Ils montrent une architecture de mission, sans paquet autonome complet.

### CASTLE2

Cinquante-cinq scripts plus substantiels, plusieurs personnages et quatre objectifs. Un cinquième objectif de récupération des armes est commenté alors que ses auxiliaires subsistent. Une reconstruction jouable est envisageable sur la géométrie apparentée, mais devra séparer les données conservées des raccords modernes.

### ALPS3_OBJ

La mission Objectifs livrée par Sabre Squadron est complète, déclarée dans le catalogue et déjà active : elle fait franchir le pont puis la gorge à un char endommagé. Les quatre scripts du jeu de base appartiennent toutefois à une génération antérieure distincte, fondée sur au moins deux Opel et trois véhicules à protéger, avec quatre objectifs au lieu de trois. Cette branche ancienne a perdu sa scène, ses acteurs, son registre de scripts, l'identité du troisième véhicule et plusieurs règles de victoire. Elle doit donc être reconstruite comme une seconde carte clairement marquée `PROTOTYPE/LEGACY`, sans remplacer la variante Sabre actuelle.

### ARDENS1_OBJ

La carte Objectifs de Sabre est complète, publiée et déjà active. Le script Base est identique à son initialiseur final et ne conserve aucune ancienne route ni action de validation ; la scène Base est seulement une composition antérieure et inachevée de la même carte. Elle contient néanmoins trois Sherman et deux Tiger, contre deux Sherman et un Tiger dans la version finale. Une conservation de ce roster ne peut prendre que la forme d'une seconde variante `PROTOTYPE/LEGACY`, avec une logique d'objectifs à recréer, sans remplacer la carte Sabre.

### PROLEZACKA

Ce nom ne désigne pas une troisième carte cachée. Les archives ne contiennent
aucun dossier `Missions/PROLEZACKA`, aucune entrée de catalogue, aucun registre
de scripts, aucune scène, aucun acteur ni aucun checkpoint associé. Il ne reste
que neuf scripts `German1.scr` à `German9.scr` : huit décrivent des rondes et
réactions d'alarme vers des points `G1_01` à `G9_04`, tandis que
`German4.scr` joue une boucle de cigarette. Aucun de leurs acteurs ou trajets
n'est placé dans une mission commerciale.

Ces fichiers peuvent servir de référence à un banc d'essai moderne de gardes,
clairement étiqueté comme reconstruction, mais pas à la restauration fidèle
d'une carte perdue. Leur cas est confié au laboratoire expérimental sans être
ajouté au menu multijoueur stable.

## Aéronefs et véhicules

La recherche exacte dans Models.dta corrige plusieurs faux négatifs :

- MODELS\LA_M323.4ds et sla_m323.4ds ;
- la_La-5.4ds et sa version simplifiée ;
- la_aici.4ds et sa version simplifiée, nom interne vraisemblablement fautif pour Aichi ;
- la_Fa 223.4ds et sa version simplifiée ;
- modèles Fw 200, Li-2 et DSF 230 ;
- douze ressources Ju 52, avec variantes et sous-éléments.

Les modèles M323, La-5, Aichi et Fa 223 contiennent moteurs, hélices ou rotors, surfaces mobiles, sièges et caméras. Cela les place au-dessus d'un simple dessin. En revanche, aucune mission, physique, commande et interface de véhicule pilotable complète n'est démontrée. Le bon statut est : modèle de véhicule présent, jouabilité annoncée historiquement, véhicule pilotable fini non prouvé.

Le Ju 52 est explicitement appelé dans une scène d'Africa 1. Il est présent et utilisé comme élément de scène ; il n'est pas absent.

## Faisabilité de finition

- Objectif commenté avec acteurs et carte existants : élevée après test.
- Variante de carte complète non déclarée : élevée.
- Mission avec scripts mais sans géométrie propre : moyenne, avec forte part de création.
- Aéronef orphelin pilotable : faible à moyenne ; commandes, physique, cockpit, dégâts, IA et mission manquent.
- Campagne Angleterre ou Gary Bristol fidèle : faible sans build ancienne, dialogues et cartes.
- Démonstration inspirée de ces concepts : élevée, à condition de l'étiqueter comme création communautaire.

La règle du projet est de compléter au maximum sans masquer la part spéculative.
