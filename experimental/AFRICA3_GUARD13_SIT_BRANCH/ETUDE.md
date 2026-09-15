# Étude expérimentale — branche assise du garde AF3a_13

État : **siège et placement modernes requis**, 15 septembre 2026. Aucun
checkpoint, décor, script commercial ou installateur n'est modifié/compilé.

## Verdict

Dans la branche active `rnd == 1`, AF3a_13 joue déjà `%%sedimL4`, subit la
chaleur pendant 15 secondes, efface l'animation puis repart debout. Trois lignes
commentées devaient auparavant le déplacer vers `AF3a_13_sit`, résoudre
`dummy_13_sit` et appeler `HUMAN_ACTIVITY_Sit`.

Ni le checkpoint ni le dummy ne subsistent dans `check2.bin`/`scene2.bin`.
Réactiver les lignes ferait donc référence à deux frames absentes. La ronde
active `AF3a_13_01 -> _02 -> _03`, les conversations, le rally point et les
alarmes doivent rester intacts.

## Analogues commerciaux 14 et 15

AF3a_14 et AF3a_15 fournissent le patron, pas le placement :

1. déplacement vers un checkpoint `AF3a_14_sit` ou `AF3a_15_sit` ;
2. court délai de 200/500 ms ;
3. `HUMAN_ACTIVITY_Sit` sur `dummy_14_sit` ou `dummy_15_sit` ;
4. activité secondaire et délai ;
5. retour à la station debout ou reprise de route ;
6. `OnAlarm()` efface l'animation, arrête l'acteur et le remet debout.

Ces points et dummies existent pour 14/15. Les copier à leurs coordonnées pour
13 créerait une superposition et ne prouverait rien historiquement.

## Reconstruction additive

Créer dans une copie de mission :

- `AF3a_13_sit_modern`, checkpoint relié à la ronde sans modifier `_01..03` ;
- `dummy_13_sit_modern`, siège aligné au même mobilier ;
- un script dérivé ne modifiant que les trois lignes de la branche `rnd == 1`.

Les suffixes `modern` rendent visible l'origine actuelle des transforms. Le
fragment
[`PROTOTYPE_SIT_BRANCH.scr.disabled`](PROTOTYPE_SIT_BRANCH.scr.disabled)
conserve l'animation chaleur et toute la suite commerciale.

[`PLACEMENT_SEAT.plan.disabled`](PLACEMENT_SEAT.plan.disabled) bloque les
coordonnées tant qu'un emplacement cohérent n'a pas été choisi dans l'éditeur.
Le mobilier doit être réellement présent, accessible, hors trajectoire des
autres acteurs et compatible avec la silhouette des sièges 14/15.

## Tests

1. Baseline : journaliser 100 tirages et la ronde complète sans variante.
2. Valider navmesh aller/retour entre `_01` et le nouveau checkpoint, pivot du
   siège, pieds/sol, collision et absence de superposition.
3. Exécuter au moins dix branches `rnd == 1` : déplacement, assise, chaleur,
   lever et reprise vers `_02`/`_03` sans changement de probabilité.
4. Déclencher chaque alarme pendant mouvement, transition Sit, animation
   `%%sedimL4`, chaleur et lever ; l'acteur doit se détacher et suivre le chemin
   commercial.
5. Tester signaux 1/2/4/10/20, mort et sauvegarde/reprise à chaque phase.
6. Retirer la variante et comparer la ronde, les dialogues et les alarmes.

Critères d'arrêt : siège introuvable, acteur attaché, alarme retardée, route
altérée, conflit avec 14/15 ou transform présenté comme officiel sans source.

## Retour arrière

Restaurer `AF3a_13.scr` Patch dans la copie et retirer les deux frames modernes.
Les points `_01..03`, les scripts 14/15 et tous les handlers restent inchangés.

## Sources internes

- scripts Base/Patch `AFRICA3/AF3a_13.scr`, `AF3a_14.scr`, `AF3a_15.scr` ;
- `missions.dta : MISSIONS/AFRICA3/check2.bin`, `scene2.bin`, `scripts.dta`.
