# Alps3_Obj legacy — variante solo `RECONSTRUCTION`

État : conception non jouable, 14 septembre 2026. Nom de travail :
`Alps3_Obj — Convoi legacy [Reconstruction Solo]`.

Cette entrée est indépendante de la carte multijoueur Sabre et de la future
variante multijoueur legacy. Aucun fichier de ces deux cartes n'est remplacé.

## Données officielles réutilisées

- la géométrie générale d'Alps3_Obj, issue de la scène Sabre tant qu'aucune
  scène Base legacy n'est retrouvée ;
- les noms commerciaux `La_OpelE_` et `La_OpelE_2` conservés dans le détecteur
  Base ;
- la règle d'arrivée à moins de 15 m avec réussite de l'objectif 1 ;
- trois objectifs 2, 3 et 4 qui passent en échec à la mort de leur véhicule ;
- les quatre scripts Base comme spécification partielle ;
- les modèles de véhicules commerciaux, s'ils sont présents dans les archives
  et compatibles avec cette scène.

Les placements, le troisième véhicule et la réussite finale des objectifs de
survie ne sont pas des données officielles réutilisables : ils manquent.

## Logique solo créée

La proposition solo transforme la règle fragmentaire en mission de convoi :

1. le joueur choisit et conduit l'un des deux Opel nommés ;
2. les deux autres véhicules sont confiés à des conducteurs IA et suivent une
   route reconstruite ;
3. l'objectif 1 réussit lorsque l'un des deux Opel nommés atteint la zone ;
4. les objectifs 2–4 réussissent uniquement quand la zone est atteinte et que
   leur véhicule respectif est encore vivant ;
5. la mission réussit quand les quatre objectifs sont résolus sans échec.

Ces règles de réussite et les conducteurs IA sont **MODERNES**. Elles donnent
un sens solo testable aux fragments, mais ne prétendent pas restituer la manche
multijoueur d'origine.

Pour éviter une escorte autonome incontrôlable, la première maquette devra
permettre au joueur de donner un ordre simple « avancer/attendre » au convoi.
La forme de cette commande et son interface restent à choisir.

## Choix spéculatifs

| Choix | Proposition initiale | Alternative possible |
| --- | --- | --- |
| troisième véhicule | camion allié distinct | troisième Opel |
| véhicule du joueur | l'un des deux Opel | marche à pied avec convoi IA |
| succès survie | tous vivants à la première arrivée | chaque véhicule doit arriver |
| échec | mort d'un véhicule protégé | mission continue avec score réduit |
| ennemis | positions Sabre adaptées | nouvelle défense de route |
| fin | succès immédiat des quatre objectifs | courte extraction à pied |

La proposition par défaut minimise les règles nouvelles, mais aucun de ces
choix n'est commercialement attesté.

## Éléments encore bloquants

- identité et modèle du troisième véhicule ;
- trois placements de départ, conducteurs et points de formation ;
- route IA complète et zone d'arrivée ;
- volumes de blocage, retournement et remise en route ;
- textes/briefing solo et condition de fin du moteur ;
- réaction si le joueur abandonne, retourne ou détruit son véhicule ;
- nombre et position des ennemis, munitions et renforts ;
- sauvegarde de la formation et restauration des conducteurs.

Ces éléments doivent être créés en tant que tels. Le dossier
`ELEMENTS_CREES_OU_SPECULATIFS.md` reste l'inventaire de provenance commun aux
variantes multijoueur et solo.

## Protocole de test

1. Confirmer que `Alps3_Obj` Sabre garde ses quatre bindings et ses valeurs
   50/51.
2. Tester chacun des trois véhicules comme premier détruit, y compris à
   l'instant exact où un Opel entre dans les 15 m.
3. Tester le joueur dans chaque Opel, à pied, mort, déconnecté/rechargé et avec
   véhicule immobilisé.
4. Vérifier attente/reprise du convoi, croisements, collision entre véhicules
   et passage des points étroits.
5. Sauvegarder/recharger avant départ, à mi-route, après un échec et dans la
   zone d'arrivée.
6. Confirmer une seule résolution par objectif et une seule fin de mission.
7. Désinstaller l'entrée solo et vérifier que les deux cartes multijoueur
   restent inchangées.

Acceptation : une mission solo identifiable comme reconstruction, terminable
et déterministe, sans modification de la carte Sabre ni confusion avec le
roster commercial incomplet.
