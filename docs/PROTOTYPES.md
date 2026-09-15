# Prototypes et données incomplètes

## Classement

- Restaurable : données presque complètes, manque limité et non spéculatif.
- Variante déjà active : anciens scripts ou ressources remplacés par une version finale complète.
- Démonstration possible : assez de matière pour un prototype, mais création moderne nécessaire.
- Fragment historique : insuffisant pour être rendu jouable fidèlement.

## Prototypes installés

### Normandy3 Zone

Variante officielle absente de la liste finale. Treize fichiers lui sont propres, mais quatre fichiers de décor ou de chargement ne sont que des marqueurs de 16 à 19 octets et `volumy.bin` manque. Trois autres conteneurs sont réellement tronqués : `actors.bin` annonce 21 970 octets mais n'en conserve que 3 768, `scene2.bin` en annonce 6 309 393 mais n'en conserve que 2 814, et `sounds.bin` en annonce 8 603 mais n'en conserve que 70. Ces longueurs internes incohérentes expliquent le blocage du client multijoueur.

La comparaison binaire écarte une réparation par simple concaténation. Les 25
noms de cadres lisibles dans l'`actors.bin` Zone existent dans la base MP, mais
les enregistrements sont supprimés, déplacés ou ajustés avec des décalages
variables. `scene2.bin` saute déjà environ 6,4 Ko de la base alors que sa taille
finale déclarée devait la dépasser de 37 316 octets. Dans `sounds.bin`, le seul
nom Zone conservé correspond à un enregistrement situé presque à la fin du
conteneur MP. Les parties perdues ne sont donc pas un suffixe récupérable.

Faute d'une seconde copie dans les archives commerciales ou d'époque, le pack
emploie un **fallback de compatibilité** : il reprend huit fichiers complets de
`NORMANDY3_MP`, dont les trois conteneurs, et conserve les six fichiers Zone
encore structurellement valides. Cela produit un dossier autonome susceptible
d'être chargé, mais ce n'est pas la reconstruction fidèle de la variante
originale. Toute fusion de ses enregistrements serait une création moderne et
devra rester une variante A/B additive. La carte est ajoutée sous le nom
`PROTOTYPE - Normandy3 Zone (exploration libre)` dans le mode **Occupation**.

La préparation des deux prototypes s'exécute après l'éventuelle installation
de la CMP, puis avant le dernier nettoyage des collisions. Un fichier
communautaire de même nom ne peut donc plus remplacer silencieusement la
version préparée, et leurs `tree.klz` reçoivent toujours le
traitement final d'exploration libre.

### Africa5 Prototype

`AFRIKA5_MP` conserve sept fichiers propres. Six ressources manquantes peuvent être reprises d'`AFRICA5_MP`. Le pack déploie les treize fichiers de la carte complétée dans un dossier autonome. Ses sept scripts de citernes subsistent sous `Scripts/AFRICA5_MP` ; le pack les rend aussi disponibles sous l'orthographe attendue par le prototype, `Scripts/AFRIKA5_MP`, et leurs sept propriétaires sont présents dans la scène propre du vestige. La carte est déclarée sous le nom `PROTOTYPE - Africa5 (exploration libre)` dans le mode **Deathmatch**.

Le registre repris d'`AFRICA5_MP` contient exactement sept liaisons, de
`m_nadrz_` à `m_nadrz_7`, vers `AF5_mp_cisterna1.scr` à
`AF5_mp_cisterna7.scr`. L'audit vérifie désormais ces paires, la présence des
sept propriétaires dans les données propres d'`AFRIKA5_MP` et l'intégrité
interne des conteneurs `actors.bin`, `scene2.bin` et `sounds.bin`.

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

Dans l'installation commerciale 1.12 étudiée, **deux dossiers de cartes
distinctes peuvent actuellement être rendus chargeables sans inventer une
nouvelle géométrie** : `AFRIKA5_MP` par complément de ressources appariées et
`NORMANDY3_MP_ZONE` au moyen du fallback de compatibilité décrit ci-dessus.

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

Le Ju 52 est explicitement appelé dans deux scènes actives. Africa 1 utilise
`CUTjunkers` et `CUTjunkersB` dans sa cinématique ; Africa 2 fait suivre
`fight_stage01` à `HoriciJunkers`, anime ses hélices, crée sa fumée puis le
masque et le fait exploser. Il est donc présent et utilisé comme élément de
scène ; il n'est pas absent. La liaison Africa 2 vers le fichier manquant
`AF2_particle_junkers.scr` reste un vestige incomplet, pas une fonction à
réactiver aveuglément.

## Faisabilité de finition

- Objectif commenté avec acteurs et carte existants : élevée après test.
- Variante de carte complète non déclarée : élevée.
- Mission avec scripts mais sans géométrie propre : moyenne, avec forte part de création.
- Aéronef orphelin pilotable : faible à moyenne ; commandes, physique, cockpit, dégâts, IA et mission manquent.
- Campagne Angleterre ou Gary Bristol fidèle : faible sans build ancienne, dialogues et cartes.
- Démonstration inspirée de ces concepts : élevée, à condition de l'étiqueter comme création communautaire.

La règle du projet est de compléter au maximum sans masquer la part spéculative.
