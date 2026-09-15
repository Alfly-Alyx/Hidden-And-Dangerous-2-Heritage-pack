# Ardennes1 Base — variante solo `RECONSTRUCTION/PROTOTYPE`

État : conception non jouable, 14 septembre 2026. Nom de travail :
`Ardennes1 [Reconstruction Solo — Prototype Base]`.

La carte multijoueur Sabre `Ardens1_obj` reste intacte. La future entrée
multijoueur `Ardennes1 [Prototype Base]` et cette entrée solo possèdent chacune
leur répertoire, leur registre et leur identifiant.

## Données officielles réutilisées

- la scène Base de 3 549 755 octets et ses frames commerciales ;
- trois canons `la_kan17mmw_`, `la_kan17mmw_2`, `la_kan17mmw_3` ;
- trois Sherman `la_shermanw_`, `_2`, `_3` ;
- deux Tiger `la_tigerw_`, `_2` ;
- une Jeep `la_JeepW_` ;
- `dummy_obj` et l'initialisation commerciale des objectifs 1–3 ;
- `dummy_obj1/2/3`, présents mais sans script Base propriétaire ;
- `sounds.bin` Base, après audit des frames réellement exploitables ;
- la géométrie, les collisions et les acteurs déjà contenus dans la scène.

Le `volumy.bin` Sabre, ses charges et ses scripts `Ardens1_delo*` ne sont pas
des données Base. Ils servent de référence de design seulement.

## Logique solo créée

La proposition est une mission de sabotage séquentielle mais à ordre libre :

1. insertion du joueur à un nouveau spawn sûr ;
2. activation simultanée des trois objectifs de canon ;
3. réussite individuelle de chaque objectif par le mécanisme de destruction
   choisi pour la branche ;
4. activation d'une extraction après les trois réussites ;
5. fin de mission lorsque le joueur vivant atteint l'extraction.

Le spawn, l'extraction, la fin de mission, la sauvegarde, le briefing et les
réactions ennemies sont **MODERNES**. Les six véhicules restent présents,
mais leur camp et leur disponibilité sont réglés pour le solo plutôt que
déduits automatiquement d'une manche compétitive.

La première conception propose les Sherman comme véhicules alliés accessibles
et les Tiger comme menaces ennemies. Le rôle de la Jeep reste à choisir. Ces
attributions sont des choix de jouabilité, pas des règles Base attestées.

## Choix spéculatifs

Le principal embranchement reste celui de la validation :

| Option | Avantage solo | Risque historique |
| --- | --- | --- |
| mort directe du canon | toute arme lourde ou charge du joueur fonctionne | aucun `OnDeath` Base conservé |
| charges inspirées de Sabre | objectif de sabotage lisible et contrôlé | importe un design Sabre absent de la scène Base |

Pour la première maquette, aucune option n'est choisie tant que les volumes et
le placement des charges n'ont pas été évalués. Les autres choix spéculatifs
sont : camp des six véhicules, munitions, densité ennemie, renforts après
chaque canon, ordre du briefing et position de l'extraction.

Chaque choix retenu devra apparaître dans le nom/version ou dans une section
« Reconstruction moderne » visible du joueur.

## Éléments encore bloquants

- un spawn solo hors collision et une route d'approche ;
- le choix OnDeath/charges et les trois scripts correspondants ;
- `volumy.bin` pour interactions, limites et extraction ;
- propriétaire des explosions et sons associés ;
- textes localisés des objectifs, briefing et débriefing ;
- règle d'échec en cas de mort du joueur et stratégie de sauvegarde ;
- camp, équipage et IA des six véhicules ;
- condition de victoire du moteur hors session multijoueur.

La scène peut être préparée conceptuellement malgré ces blocages, mais aucun
script exécutable ne doit les masquer par des valeurs arbitraires.

## Protocole de test

1. Vérifier que la carte multijoueur Sabre conserve ses quatre bindings, trois
   charges et son `volumy.bin` d'origine.
2. Tester les trois canons dans les six ordres possibles et deux destructions
   simultanées ; chaque objectif réussit une seule fois.
3. Tester toutes les armes susceptibles de toucher les canons et confirmer la
   règle choisie, notamment tirs des Sherman/Tiger et dégâts collatéraux.
4. Tester chaque véhicule : entrée/sortie, équipage IA, destruction, abandon,
   retournement, munitions et blocage de route.
5. Sauvegarder/recharger avant tout objectif, après chaque combinaison de
   canons et dans la zone d'extraction.
6. Vérifier qu'aucune primitive réseau ou attente de seconde équipe ne bloque
   la partie solo.
7. Comparer les coûts de scène et d'IA avec la release Sabre à quatre véhicules
   (Jeep comprise) ; le Sherman et le Tiger supplémentaires ne doivent pas
   créer de blocage ou de chute de performance non documentée.
8. Retirer l'entrée solo et confirmer l'intégrité binaire de `Ardens1_obj`.

Acceptation : les trois objectifs et l'extraction forment une progression solo
déterministe, les six véhicules ont un rôle explicite, et toutes les créations
restent identifiées comme reconstruction.
