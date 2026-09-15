# Étude expérimentale — lightmap du feu de camp d'Arctic 1

> Réévaluation du 15 septembre 2026 : la création du propriétaire est désormais
> **bloquée**. `Object155` est sérialisé comme bloc `LMAP` sans transform monde
> autonome et aucun contrôleur de feu comparable ne justifie la cadence moderne.
> Le dossier autoritatif est
> [`ARCTIC1_FIRE_OBJECT155_LMP`](../ARCTIC1_FIRE_OBJECT155_LMP/ETUDE.md). La
> maquette ci-dessous est conservée comme historique non promotable.

État : reconstruction visuelle désactivée, 14 septembre 2026. La maquette ne
possède aucun binding actif et attend un signal d'un contrôleur expérimental
séparé. Le script commercial brut n'est jamais activé.

## Verdict

`R_Arc1A_ohen_LMP.scr` vise la frame existante `Object155` et sélectionne
aléatoirement ses lightmaps 0, 1 et 2. Son principe visuel est récupérable, mais
sa boucle finale ne contient plus aucune attente : les deux lignes qui auraient
calculé puis exécuté un délai sont commentées. Lier ce fichier tel quel créerait
une boucle serrée illimitée, avec changements visuels et charge processeur non
bornés.

La maquette
[`PROTOTYPE_CAMPFIRE_LIGHTMAP_CONTROLLER.scr.disabled`](PROTOTYPE_CAMPFIRE_LIGHTMAP_CONTROLLER.scr.disabled)
conserve seulement les trois indices attestés et ajoute :

- un démarrage explicite par signal 1 ;
- une temporisation moderne aléatoire de 150 à environ 300 ms ;
- un arrêt par signal 2 avec retour à la lightmap 0 ;
- un porteur de contrôle distinct, sans binding sur `Object155`.

Cette cadence est un choix **MODERNE**, pas une valeur commerciale retrouvée.
Elle limite la boucle à environ 3,3–6,7 évaluations par seconde ; les répétitions
aléatoires d'un même indice réduisent encore le nombre de transitions visibles.

## État commercial

Le script dormant contient trois indices de lightmap et deux indices de temps
contradictoires :

```text
wait = 100                    // initialisé, jamais utilisé
// wait = _RandomInt(20)+10   // calcul commenté
// delay(wait)                // attente commentée
```

La valeur 100 laisse supposer qu'une attente avait été envisagée, tandis que
10–29 ms serait trop rapide pour une restauration prudente. Aucun autre script
ne lance `R_Arc1A_ohen_LMP.scr`; il est non relié, sans acteur homonyme.

`Object155` existe dans la scène et ne possède pas de binding de script. Cette
absence ne transforme pas l'objet en contrôleur : lui attacher la boucle
mélangerait ressource visuelle et logique d'option. Le design proposé ajoute un
acteur distinct, par exemple `dummy_exp_ar1_campfire_lmp`, uniquement dans une
copie de test. Un sélecteur expérimental lui envoie le signal 1 quand l'effet
est choisi et le signal 2 avant arrêt/rechargement.

## Contrat additif

| Élément | Release | Option expérimentale |
| --- | --- | --- |
| `Object155` | objet présent, sans ce script | cible visuelle inchangée |
| binding d'`Object155` | aucun | aucun |
| contrôleur | absent | nouvel acteur séparé, désactivé par défaut |
| indices | état commercial courant | choix aléatoire 0/1/2 |
| cadence | aucun animateur actif | 150–300 ms, moderne |
| arrêt | état statique | signal 2 puis lightmap 0 |

La suppression du nouvel acteur et de son binding suffit à revenir à la
baseline ; aucun script release n'est remplacé.

## Sécurité et validation visuelle

1. Mesurer la baseline d'`Object155` pendant au moins cinq minutes.
2. Envoyer un seul signal 1 : vérifier une seule boucle et au maximum sept
   évaluations par seconde.
3. Envoyer de nouveau le signal 1 : le contrôleur ne doit pas dupliquer la
   boucle ; ce cas devra être instrumenté avant toute activation.
4. Envoyer le signal 2, effectuer un skip, sauvegarder/recharger et quitter la
   mission : aucune boucle ne doit survivre et la lightmap doit revenir à 0.
5. Contrôler scintillement, visibilité à distance, variation de luminosité et
   confort visuel. Allonger la cadence si l'effet paraît agressif.
6. Vérifier que l'effet est purement local/visuel et ne modifie ni collision,
   IA, objectifs, ombres de gameplay ni synchronisation multijoueur.

La maquette contient un verrou `running` contre un second signal 1, mais reste
non activable tant qu'un test ne confirme pas son caractère réellement
monostable dans le moteur. Si le dialecte permet malgré ce verrou deux entrées
concurrentes dans la boucle, le contrôleur devra être remplacé par un séquenceur
à tick unique.

## Exclusion de `R_Arc1A_Rebel_Test.scr`

Ce fichier orphelin ne doit pas être reconstruit. `Rebel` est déjà lié à
`R_Arc1A_rebel.scr`, qui contient `swampYesNo`, les réactions à l'alarme et au
signal 17, les signaux internes 10/11/12, toute la route du marais et toute la
route de contournement. Réactiver le test externe créerait une seconde autorité
pour un choix déjà intégré.

## Sources internes

- registre effectif `missions/arctic1/scripts.dta` ;
- script Base `R_Arc1A_ohen_LMP.scr` ;
- scripts Base `R_Arc1A_Rebel_Test.scr` et `R_Arc1A_rebel.scr` ;
- `scene2.bin` et `actors.bin` confirmant `Object155` et `Rebel`.
