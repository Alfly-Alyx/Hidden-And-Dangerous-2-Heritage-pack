# Proposition expérimentale — objectif 2 de Whisky Bar

État : étude non intégrée, 13 septembre 2026. Cette proposition ne modifie
aucune archive commerciale ni aucun script actif. Elle est limitée à la remise
en scène de l'objectif catalogue 2 d'Africa 5 : « Force Hans Schumann to
cooperate ».

## Classification

**Reconstruction minimale.** L'activation réutilise une ligne officielle encore
présente mais commentée. La validation exige en revanche d'ajouter une ligne
absente des archives auditées. Le résultat ne doit donc pas être présenté comme
une simple réactivation.

| Aspect | Niveau | Motif |
| --- | ---: | --- |
| Faisabilité technique | 4/4 | deux changements de statut, sans nouvel acteur ni signal |
| Fidélité de l'activation | 4/4 | ligne exacte conservée dans `AF4_obj.scr` |
| Fidélité de la validation | 3/4 | point déduit de la fin de la conversation officielle |
| Risque de régression | faible à moyen | ordre des objectifs, sauvegardes et morts à vérifier |

## Preuves officielles

### Objectif conservé

`AF4_init_obj.scr` initialise explicitement :

```text
SetObjectiveStatus(1, 0);  // Find and capture Hans Schumann
SetObjectiveStatus(2, 4);  // Force Hans Schumann to cooperate
SetObjectiveStatus(3, 4);  // Hans Schumann must survive
SetObjectiveStatus(4, 4);  // Eliminate enemy resistance near runway
SetObjectiveStatus(5, 4);  // Fly away in JU88 with Hans Schumann
```

Dans cette API, les usages cohérents de la mission indiquent : `0` en cours,
`1` réussi, `3` échoué et `4` caché/inactif.

### Point d'activation conservé

Au début de la conversation, `AF4_23.scr` envoie le signal 1 à
`dummy_gigant`. `AF4_obj.scr` le reçoit et rejoint `OBJ1_COMPLETE`, qui :

- fixe `schuman_found = 1` ;
- contient encore `// SetObjectiveStatus(2, 0);` ;
- active les objectifs 3 et 4 ;
- valide l'objectif 1.

La ligne exacte d'activation de l'objectif 2 est présente dans les versions base
et patch. Les scripts base et patch comparés sont identiques après normalisation
des fins de ligne.

### Conversation et transition suivantes

`AF4_23.scr` conserve sept répliques, identifiants 09991951 à 09991957. Après la
dernière réplique, il :

1. valide de nouveau l'objectif 1 ;
2. active directement l'objectif 5 ;
3. envoie le signal 1 au détecteur de piste `dummy_runway` ;
4. rend Schumann membre NPC de l'équipe ;
5. termine son script.

Aucun `SetObjectiveStatus(2, 1)` n'a été trouvé dans les scripts Africa 5 base
ou patch. L'objectif catalogue est donc toujours caché et jamais validé dans la
branche commerciale auditée.

## Hypothèses

### H1 — moment de l'activation

**INFÉRENCE forte.** La ligne commentée dans `OBJ1_COMPLETE` est le point prévu
pour rendre « Force Hans Schumann to cooperate » visible. Ce label est atteint
au moment où Schumann est trouvé et où la conversation commence. L'objectif 2
devient ainsi l'étape en cours pendant l'échange, tandis que l'objectif 1 vient
d'être réussi.

### H2 — moment de la validation

**INFÉRENCE forte.** La coopération est acquise après la dernière réponse de
Schumann, juste avant que la mission demande de rejoindre le Ju 88 et active la
piste. C'est le seul point où convergent :

- la fin complète du dialogue ;
- l'activation de l'objectif d'évasion avec Schumann ;
- l'activation du détecteur de piste ;
- le passage de Schumann au statut de NPC allié.

Valider l'objectif 2 plus tôt, au premier signal vers `dummy_gigant`,
confondrait capture et coopération. Le valider au départ de l'avion serait trop
tardif, car l'objectif 5 suppose déjà sa coopération.

### H3 — absence de nouvelle branche d'échec

**INFÉRENCE prudente.** La mission possède déjà l'objectif 3 « Hans Schumann
must survive » et `AF4_Schummandead.scr` le marque échoué lorsque Schumann
meurt. Aucune preuve ne montre que l'objectif 2 devait aussi être marqué échoué.
La reconstruction minimale n'ajoute donc aucune règle d'échec à l'objectif 2.
Ce choix doit être observé en test, notamment si une mort interrompt le dialogue.

## Delta proposé

### 1. `Scripts/AFRICA5/AF4_obj.scr`

Réactiver la ligne officielle, sans autre changement :

```diff
 Label OBJ1_COMPLETE:
   schuman_found = 1;
-//  SetObjectiveStatus(2, 0);
+  SetObjectiveStatus(2, 0);
   SetObjectiveStatus(3, 0);
   SetObjectiveStatus(4, 0);
   SetObjectiveStatus(1, 1);
```

Classification de cette ligne : **OFFICIEL, réactivé**.

### 2. `Scripts/AFRICA5/AF4_23.scr`

Ajouter une seule validation après la dernière réplique et entre les objectifs
1 et 5 :

```diff
   FRM_MorphSpeechDelayed(pl, 09991957, 3, 9);

   SetObjectiveStatus(1, 1);
+  SetObjectiveStatus(2, 1);
   SetObjectiveStatus(5, 0);
   SendSignal(runway, 1);
```

Classification de cette ligne : **RECONSTRUCTION MINIMALE**. Sa valeur et sa
position sont cohérentes avec l'API et la narration officielles, mais la ligne
n'existe dans aucune archive auditée.

### Pourquoi conserver la validation redondante de l'objectif 1

La supprimer serait un troisième changement sans nécessité fonctionnelle. La
proposition vise le delta le plus petit : une ligne décommentée et une ligne
ajoutée. La redondance existante reste donc intacte.

## Chronologie attendue

| Moment | Objectif 1 | Objectif 2 | Objectif 3 | Objectif 4 | Objectif 5 |
| --- | --- | --- | --- | --- | --- |
| Début de mission | en cours | caché | caché | caché | caché |
| Schumann trouvé, conversation lancée | réussi | en cours | en cours | en cours | caché |
| Dernière réplique terminée | réussi | réussi | en cours | en cours | en cours |
| Conditions de piste et d'évasion remplies | réussi | réussi | réussi | selon détecteur | réussite finale |

Cette chronologie est l'effet attendu de la proposition, pas une preuve que
tous ces états étaient affichés ainsi dans une version historique.

## Protocole de test

### Instrumentation minimale

Consigner à chaque transition : statut des objectifs 1 à 5, valeur de
`schuman_found`, signal 1 vers `dummy_gigant`, signal 1 vers `dummy_runway`,
valeurs de jeu 40, 77 et 88, état de `AF4_23` et état de `AF4_31`.

### Parcours nominal

1. Démarrer une nouvelle mission avec la proposition active.
2. Vérifier que l'objectif 2 reste caché avant Schumann.
3. Approcher à 20 unités : aucun succès anticipé.
4. Approcher à deux unités et lancer la conversation.
5. Vérifier que l'objectif 1 réussit et que les objectifs 2, 3 et 4 deviennent
   actifs au début de l'échange.
6. Vérifier que l'objectif 2 reste en cours pendant les répliques 09991951 à
   09991957.
7. Après la dernière réplique, vérifier dans cet ordre : objectif 2 réussi,
   objectif 5 actif, détecteur de piste activé, Schumann allié.
8. Terminer la mission et vérifier que la cinématique d'évasion et l'objectif 5
   restent inchangés.

### Variantes et échecs

- alarme avant la rencontre, puis retour à Schumann ;
- Schumann tué avant le signal de capture ;
- Schumann tué pendant la conversation ;
- Schumann tué après sa coopération ;
- sniper `AF4_31` vivant, neutralisé tôt ou géré par sa scène ;
- résistance de piste déjà éliminée avant la conversation ;
- entrée et sortie répétées des rayons 20 et 2 ;
- modes de jeu pris en charge, notamment les branches `game_type` 2, 3 et 7 ;
- sauvegarde/reprise avant la rencontre, pendant l'objectif 2 et après sa
  validation ;
- chargement d'une sauvegarde commerciale antérieure à la proposition.

### Critères d'acceptation

- l'objectif 2 apparaît une seule fois et ne réussit jamais avant la dernière
  réplique ;
- aucun dialogue, signal ou objectif 1/3/4/5 n'est déclenché deux fois ;
- la mort de Schumann conserve l'échec de l'objectif 3 ;
- aucun blocage n'est créé si la conversation est interrompue ;
- la logique de piste, le statut NPC et la cinématique finale sont inchangés ;
- une sauvegarde créée sous la proposition restitue les mêmes états au
  chargement.

Une sauvegarde commerciale déjà située après `OBJ1_COMPLETE` peut ne pas
réexécuter l'activation de l'objectif 2. La proposition n'annonce donc pas de
compatibilité rétroactive sans test dédié.

## Réversibilité et limites

La réversion des fichiers consiste uniquement à recommenter la ligne
`SetObjectiveStatus(2, 0)` dans `AF4_obj.scr` et à retirer la nouvelle ligne
`SetObjectiveStatus(2, 1)` de `AF4_23.scr`. Aucun acteur, frame, son, texte ou
identifiant nouveau n'est requis.

Retirer la proposition ne réécrit pas les statuts déjà enregistrés dans une
sauvegarde. Les essais doivent donc utiliser des sauvegardes jetables et une
nouvelle mission pour la comparaison avant/après.

Cette proposition reste hors du paquet stable jusqu'à validation complète. Elle
ne doit pas être copiée dans l'installation du jeu par ce dossier expérimental.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_init_obj.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_obj.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_23.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_Schummandead.scr`
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_schumann_detector.scr`
- équivalents de la couche Patch, identiques après normalisation des fins de
  ligne pour les trois scripts principaux

## Sous-cas — mise en scène de Hans pendant la cinématique 20

État : **cycle de vie non prouvé ; aucun correctif proposé pour intégration**.

Le détecteur AF4_schumann_detector.scr lance toujours activement la cinématique
20 lorsque le joueur se trouve à moins de 20 unités de Hans, que la valeur 88
est nulle et que le sniper AF4_31 est vivant. AF4_31 possède la scène complète :
il se place, vise AF4_23, tire pendant la scène, puis l’attaque encore pendant
10 s et 60 s avant d’écrire la valeur 88.

AF4_23 conserve en commentaire sa réaction complémentaire exacte : arrêt,
déplacement vers AF4_blesz_end, posture accroupie, puis EndScript dans
OnCutsceneDone(20). Le checkpoint AF4_blesz_end est présent dans le check2
commercial.

Cette apparente restauration n’est pourtant pas sûre. Après la conversation,
AF4_23 exécute SetNPCTeamStatus(this,true) puis EndScript. L’usage de cette paire
ailleurs atteste un transfert au contrôle NPC, mais ne prouve pas si un handler
de cinématique du script terminé peut encore être distribué. Inversement, si
EndScript du OnCutsceneDone(20) termine réellement l’instance avant la
conversation, Hans peut perdre son rayon de dialogue. Le sens exact doit être
mesuré dans le moteur, pas déduit du nom de la primitive.

### Relation avec les objectifs 2 et 3

Le rayon 20 du détecteur précède normalement le rayon 2 de la conversation.
La scène du sniper peut donc arriver alors que l’objectif 3 « Hans must survive »
est encore caché ; AF4_Schummandead peut néanmoins le marquer échoué. Restaurer
le déplacement accroupi peut modifier directement la probabilité de survie et
donc le moment où l’objectif 2 devient accessible.

Aucun essai ne doit valider l’objectif 2 si Hans meurt pendant cette scène. Le
succès de l’objectif 2 reste lié à la dernière réplique ; l’objectif 3 conserve
son détecteur de mort et son succès au départ avec Hans.

### Stratégie sûre

Le plan PROTOTYPE_HANS_CUTSCENE20.plan.disabled impose d’abord un essai
instrumenté de la réaction historique exacte. Une réassignation secondaire
n’est pas retenue : aucune primitive commerciale de réassignation dynamique de
script n’a été trouvée, et un contrôleur tiers ne peut pas appeler HUMAN_Move
dans le contexte de Hans sans ajouter un nouveau contrat de signal.

Si EndScript coupe la conversation ou si le statut NPC bloque les callbacks,
la reconstruction reste classée incomplète. Une adaptation moderne ne pourra
être étudiée qu’avec un contrat explicite « avant coopération / après
coopération » et sans remplacer le détecteur de survie.

### Tests supplémentaires obligatoires

1. Tracer l’entrée/sortie des deux handlers 20 et les deux EndScript de Hans.
2. Déclencher la scène avant la conversation, puis vérifier les sept répliques.
3. Terminer la conversation avant un lancement retardé et vérifier si le handler
   est encore reçu sous statut NPC.
4. Tester sniper vivant, mort, alarme interrompue et valeurs 77/88 restaurées.
5. Tuer Hans avant, pendant et après la scène ; relever les objectifs 1, 2, 3 et
   5 ainsi que le détecteur AF4_Schummandead.
6. Sauvegarder/reprendre entre rayon 20, tir, déplacement AF4_blesz_end, rayon 2
   et passage NPC.

Tant que ces tests ne prouvent pas le cycle, ce sous-cas ne doit être ni promu,
ni compilé, ni combiné au delta minimal de l’objectif 2.
