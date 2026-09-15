# Étude expérimentale — assaut de proximité d'Africa 4

État : **variante exclusive désactivée**, 15 septembre 2026. Aucun script actif
ni registre commercial n'est modifié et rien n'est compilé.

## Verdict

`AF3b_activator.scr` conserve un déclencheur complet à 60 unités qui envoie le
signal 1 à `AF3b_16` jusqu'à `AF3b_25` en une seule fois. Le registre lie bien
`dummy_inrange` à ce script, mais son unique `Whenever` est commenté : le
porteur est commercial et actuellement inerte.

Le même registre lie `dummy_organizer` à `AF3b_organizer.scr`. Celui-ci active
ces dix soldats au sein de trois vagues, mélangés à d'autres fantassins, aux
véhicules et aux tankistes. Réactiver l'ancien rayon en parallèle créerait des
doubles signaux et détruirait l'échelonnement.

La solution n'est donc pas un second activateur ajouté à la release, mais deux
profils de mission sélectionnés avant chargement :

| Profil | Propriétaire de `AF3b_16..25` | Reste de l'organisateur |
| --- | --- | --- |
| `WAVES_RELEASE` | organisateur commercial | strictement commercial |
| `PROXIMITY_EXCLUSIVE` | `dummy_inrange`, une seule fois à 60 m | conserve véhicules, tankistes et soldats hors 16–25 ; filtre les dix destinataires |

## Nuance sur la valeur radio 20

Le script charge `_LoadGameValue(20)`, puis la copie Base/Patch inspectée force
immédiatement `odvysilali = 1`. La branche alternative 20/30 secondes et les
signaux 1/2 restent lisibles, mais la release observée choisit de fait le chemin
vrai : signal soldat 1 et délai 30 secondes. Une variante ne doit pas supprimer
ce forçage en prétendant « restaurer » le choix radio sans étude séparée.

## Preuves

- `dummy_inrange -> AF3b_activator.scr` et
  `dummy_organizer -> AF3b_organizer.scr` sont tous deux présents ;
- les acteurs `AF3b_16..25` existent ;
- le vestige de proximité cible exactement ces dix acteurs avec le signal 1 ;
- l'organisateur les répartit dans les vagues 1 à 3 ; Base et Patch échangent
  la place de 24/25 dans deux vagues, sans changer l'ensemble des dix cibles ;
- l'organisateur gère aussi `S_invaze`, deux Opel, deux tankistes, les soldats
  11–15, 26–33 et les délais : il ne peut pas être simplement supprimé.

## Construction additive/exclusive

[`PROTOTYPE_PROXIMITY_OWNER.scr.disabled`](PROTOTYPE_PROXIMITY_OWNER.scr.disabled)
reprend le vestige et ajoute seulement un verrou placé avant les signaux. Le
contrat de préparation est décrit dans
[`VARIANT_SELECTOR.plan.disabled`](VARIANT_SELECTOR.plan.disabled).

Dans `PROXIMITY_EXCLUSIVE`, partir de la copie Patch effective de
l'organisateur et retirer uniquement ses émissions vers 16–25. Ne modifier ni
leur script propre, ni leur binding, ni les signaux destinés aux autres unités.
Le choix est immuable pendant la partie ; aucun basculement à chaud n'est admis.

## Tests

1. Baseline release : tracer chaque signal vers 16–25 et les trois vagues.
2. Profil proximité : entrer/sortir dix fois du rayon ; chaque acteur reçoit
   exactement un signal 1 total, jamais un signal ultérieur de l'organisateur.
3. Déclencher la radio avant/après l'approche et simultanément à la frontière
   des 60 unités ; le verrou doit attribuer une seule autorité.
4. Vérifier que Opel, tankistes, `S_invaze`, groupes 11–15 et 26–33 conservent
   ordre, signal et délais de la copie Patch.
5. Tester mort anticipée des dix soldats, alarme, sauvegarde/reprise, arrivée
   rapide, plusieurs joueurs et hôte/client.
6. Revenir à `WAVES_RELEASE` et comparer journal, objectifs et timing.

Critères d'arrêt : double signal, soldat réveillé par les deux propriétaires,
véhicule manquant, modification de la probabilité/valeur radio, réarmement après
sauvegarde ou différence réseau.

## Retour arrière

Sélectionner `WAVES_RELEASE`, remettre l'organisateur Patch complet et le
script `AF3b_activator.scr` commercial inerté. Aucun acteur ni frame n'est créé.

## Sources internes

- scripts Base/Patch `AFRICA4/AF3b_activator.scr` et
  `AF3b_organizer.scr` ;
- `missions.dta : MISSIONS/AFRICA4/scripts.dta`, `actors.bin`, `scene2.bin`.
