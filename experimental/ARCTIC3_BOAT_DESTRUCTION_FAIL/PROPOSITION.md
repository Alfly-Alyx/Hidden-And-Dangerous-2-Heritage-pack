# Arctic 3 — échec si la vedette d’extraction est détruite

État : **intention explicite, mécanisme moteur à confirmer**, 14 septembre
2026. Les deux variantes sont désactivées et mutuellement exclusives. Aucune
mission n’a été compilée ou installée.

## Verdict

Le commentaire `DOPLNIT Fail na zniceni lodi` (« compléter l’échec lors de la
destruction du bateau ») atteste clairement la règle voulue. La conséquence la
moins inventive est l’échec critique de l’objectif 3, celui qui demande de
monter dans le bateau. En revanche, le type exact d’événement de destruction
émis par `ELKO` n’est pas démontré pour ce véhicule précis.

Deux essais sont donc proposés : d’abord `OnDeath()` sur le propriétaire
existant du bateau, car cette méthode est active sur plusieurs véhicules ; si
elle ne se déclenche pas, un contrôleur séparé surveille `_ACTOR_GetState`.
Les deux envoient le signal local 20 au contrôleur d’objectifs, sans inventer de
texte ni de son.

## Inventaire des preuves

| Élément | Constat | Portée |
| --- | --- | --- |
| `R_Ar3_objectives.scr` | se termine par le commentaire d’échec manquant | intention directe |
| objectif 3 | activé après la rencontre du pilote et réussi au signal 10, juste avant la cinématique du bateau | cible naturelle de l’échec |
| objectif 2 | utilise déjà `SetObjectiveStatus(2, 3)` quand le pilote meurt | précédent local d’échec critique |
| registre de mission | `ELKO` est lié à `R_Ar3_Amik_Boat.scr` | propriétaire exact vérifié |
| `R_Ar3_Amik_Boat.scr` | masque puis révèle `ELKO`, `la_BoatGun_`, `la_BoatGun_2` et `la_A3_lavka_` au signal 1 | aucun détecteur de dégâts |
| `CUTclun_ar3.scr` | masque `ELKO` au début de la cinématique 1 | un test de visibilité serait un faux positif |
| précédents véhicules | `AF3b_axiscar01.scr` et `AF3b_repairedcar.scr` emploient `OnDeath()` ; `AF1_opelflak.scr` emploie `_ACTOR_GetState` | deux mécanismes attestés, pas encore sur `ELKO` |
| signaux Arctic 3 | le signal 20 n’apparaît pas dans les scripts Base/Patch de la mission | canal candidat, à réauditer lors d’une intégration |
| retour joueur | aucun identifiant de sous-titre, voix ou son n’est associé à cette destruction | ne rien réutiliser arbitrairement |

## Niveaux de spéculation

- **Faible** : la destruction devait provoquer un échec ; le commentaire est
  explicite.
- **Faible à moyenne** : faire échouer l’objectif 3. Il décrit l’embarquement,
  mais le commentaire ne donne pas lui-même le numéro.
- **Moyenne** : `OnDeath()` sur `ELKO`. La commande fonctionne pour des voitures,
  mais le bateau n’a pas été testé.
- **Moyenne à forte** : `_ACTOR_GetState(ELKO) == 0`. Le précédent véhicule est
  réel, mais il faut distinguer destruction, état initial et transition de
  cinématique.
- **Exclue** : ajouter un message, un son, une explosion ou un modèle non
  attesté.

## Variantes de laboratoire

### A — événement `OnDeath()` du propriétaire, préférée

`PROTOTYPE_OBJECTIVE_RECEIVER.scr.disabled` contient le verrou partagé et
l’échec de l’objectif 3. `PROTOTYPE_ONDEATH.scr.disabled` ajoute seulement le
signal 20 envoyé par `ELKO` à sa mort. Le verrou est armé au signal 1 et désarmé
dès le signal 10, avant que la cinématique masque le bateau.

Cette variante ne crée ni acteur ni scrutation permanente. Elle est rejetée si
la destruction visible du bateau ne déclenche jamais `OnDeath()`.

### B — état acteur surveillé par un contrôleur séparé

`PROTOTYPE_STATE_MONITOR.scr.disabled` doit être attaché à un nouveau dummy
uniquement dans une copie de la mission. Il ne commence à considérer l’état 0
comme une mort qu’après avoir observé `ELKO` vivant au moins une fois. Le signal
2 le désarme avant la cinématique.

Cette variante est rejetée si l’état acteur passe à 0 lors d’un simple
masquage, d’un changement de niveau de détail, d’une sauvegarde/reprise ou de la
cinématique. Elle ne doit jamais être activée avec la variante A.

## Activation et retour arrière

1. Dupliquer la mission sous un nom de test distinct.
2. Copier les scripts effectifs, appliquer le récepteur partagé, puis **un seul**
   des deux détecteurs.
3. Pour A, conserver le binding `ELKO -> R_Ar3_Amik_Boat.scr` et modifier sa
   copie ; aucun nouveau propriétaire.
4. Pour B, créer un dummy de laboratoire, lui assigner le moniteur et lui
   envoyer 1 depuis le signal 1 des objectifs, puis 2 au début du signal 10.
5. Réauditer le signal 20 dans la copie complète avant le premier lancement.
6. Désactivation : remettre les deux scripts release ; pour B, supprimer aussi
   le binding et le dummy de test.

Le retour arrière ne touche pas aux objectifs 1, 2, 4, 5 ou 6, ni aux trois
Américains, au pilote, au pont ou à la cinématique.

## Risques

- `OnDeath()` peut ne pas être émis par ce type de bateau.
- L’état 0 peut signifier « masqué » plutôt que « détruit ».
- Une destruction pendant le délai d’apparition peut précéder l’armement.
- Le signal d’échec peut arriver en même temps que le signal 10 de réussite.
- Une reprise de sauvegarde peut perdre le verrou si le moteur ne sérialise pas
  les variables du script comme attendu.
- Le statut 3 peut suffire à terminer la mission ou seulement marquer la ligne ;
  cela doit être observé en jeu, sans ajouter `EndMission` à l’aveugle.

## Protocole de test en jeu

1. Baseline release : rejoindre le pilote, faire apparaître le bateau, embarquer
   et noter l’ordre des signaux 1 et 10.
2. Variante A seule : détruire le bateau avant son apparition, juste après son
   apparition, pendant l’approche et au seuil d’embarquement.
3. Vérifier qu’une destruction après armement produit une seule écriture
   `SetObjectiveStatus(3, 3)` et qu’aucun texte ou dialogue sans rapport ne joue.
4. Terminer normalement : le signal 10 doit désarmer l’échec avant la
   cinématique ; le masquage de `ELKO` ne doit rien déclencher.
5. Si A ne reçoit aucun événement, revenir entièrement à la baseline, puis
   essayer B seule.
6. Avec B, vérifier explicitement l’état initial masqué, l’apparition retardée,
   la destruction, le masquage de cinématique et la reprise après sauvegarde.
7. Tester le décès du pilote et des Américains pour confirmer que leurs chaînes
   existantes restent inchangées.
8. Recharger avant et après l’apparition, avant le tir fatal et juste avant le
   signal 10.

Critères d’arrêt : faux échec au chargement ou à la cinématique, double statut,
collision de signal, dialogue réutilisé, ou différence dans la fin normale.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC3/R_Ar3_objectives.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC3/R_Ar3_Amik_Boat.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC3/CUTclun_ar3.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC3/R_Ar3_TheEndOBJ.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_axiscar01.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA4/AF3b_repairedcar.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA1/AF1_opelflak.scr` ;
- registre `Missions/ARCTIC3/Scripts.dta` de `missions.dta`.
