# Arctic 4 — animations ambiantes et sortie du Flak

État : **replis attestés seulement**, 14 septembre 2026. Deux fragments sont
désactivés ; aucune animation au nom supposé n’est créée et aucune mission n’a
été compilée ou installée.

## Verdict

Une activité de froid générique et une commande de sortie de véhicule existent
déjà dans le corpus. Elles permettent deux essais limités : remplacer les deux
emplacements « pied dans la neige » par `HUMAN_ACTIVITY_Cold()`, et ajouter à
`sub_gunner_1` la même sortie que celle déjà active chez `sub_gunner_2`.

En revanche, aucun geste debout de hochement de tête ni aucune posture debout
de stupeur n’est identifié. Les remplacer par une animation de conversation ou
par `%%lezipanica` serait sémantiquement trompeur. Pour ces deux vestiges, le
choix le moins spéculatif est de conserver le regard et la pause release.

## Inventaire des preuves

| Acteur | Vestige ou commande | Éléments attestés | Proposition |
| --- | --- | --- | --- |
| `Static_Guard_2` | hochement après le dialogue ; pied dans la neige dans le tirage aléatoire 3 | `%%kecy3`, `%%nuda`, `%%nuda1` sont actifs localement ; `HUMAN_ACTIVITY_Cold()` est actif en Norway et Arctic 1 | ne pas simuler le hochement ; tester `Cold` pour le geste de froid |
| `Static_Guard_5` | posture effrayée et figée au signal 1 | le script tourne déjà vers `dummy_Kra2_detektor` et attend 8 s ; aucune animation debout de stupeur trouvée | garder cette immobilité comme repli |
| `Static_Guard_6` | pied dans la neige après la bouteille | `HUMAN_ACTIVITY_DrinkBottle` est actif ; `Cold` possède de nombreux précédents | tester `Cold` après la boisson |
| `sub_gunner_1` | commentaire de sortie du Flak dans `OnAlarmDone()` | sa mort appelle déjà `HUMAN_BoardVehicle("", False, 0)` | tester le même appel avant son retour au poste d’observation |
| `sub_gunner_2` | même commentaire | `OnAlarmDone()` contient déjà `HUMAN_BoardVehicle("", 0, 0)` et `OnDeath()` la forme `False` | TODO résiduel : aucune addition nécessaire |

Le registre lie exactement ces cinq acteurs à leurs cinq scripts. Le cadre
`la_flak4x38` est présent dans les données de scène/acteurs. Arctic 4 ne possède
pas de remplacement Patch pour ces fichiers : les versions Base inspectées sont
les sources effectives.

### Commandes et animations disponibles

- `HUMAN_ACTIVITY_Cold()` : appels actifs dans 17 gardes `R_Nor_Tirpic*` et
  dans deux gardes d’Arctic 1 ; activité sans paramètre, suivie de délais courts.
- `HUMAN_BoardVehicle("", 0/False, siège)` : sortie active de voitures et du
  Flak de `sub_gunner_2` ; la chaîne vide et le booléen faux sont des formes
  attestées.
- `%%nuda`, `%%nuda1`, `%%kecy3` : disponibles dans le script de Guard 2, mais
  aucune preuve qu’ils représentent un hochement.
- `%%lezipanica` : animation active ailleurs pour une panique couchée ; rejetée
  pour Guard 5, qui doit rester debout et figé.

## Niveaux de spéculation

- **Faible** : les quatre commentaires d’animation et les deux commentaires de
  sortie sont des vestiges directs.
- **Faible à moyenne** : `HUMAN_ACTIVITY_Cold()` comme remplacement générique du
  pied dans la neige. Le geste exact peut différer, mais le sens et le climat
  correspondent.
- **Faible** : la ligne de sortie de `sub_gunner_2` est déjà active malgré le
  commentaire `DOPLNIT`.
- **Moyenne** : ajouter cette sortie à `sub_gunner_1`, car son embarquement est
  laissé à l’IA après un appel explicite commenté.
- **Forte et écartée** : réutiliser une animation de parole, d’ennui ou de
  panique comme hochement/stupeur sans preuve visuelle.

## Prototypes isolés

`PROTOTYPE_COLD_FALLBACKS.scr.disabled` contient deux fragments indépendants :
un pour la branche aléatoire de Guard 2 et un pour la boucle de Guard 6. Ils ne
touchent pas à `OnAlarm()` ; l’arrêt d’animation, le déplacement et la visée
gardent donc leur priorité release.

`PROTOTYPE_GUNNER1_FLAK_EXIT.scr.disabled` ajoute une seule sortie au début de
`OnAlarmDone()` de Gunner 1. Gunner 2 reste inchangé, puisque sa ligne de sortie
est déjà présente et active.

Aucun prototype n’est produit pour le hochement ou la posture de Guard 5. Cette
absence est volontaire : l’inventaire ne fournit pas d’asset compatible.

## Activation et retour arrière

1. Dupliquer Arctic 4 et copier le script Base correspondant.
2. Pour `Cold`, tester Guard 2 et Guard 6 séparément avant de les combiner.
3. Pour le Flak, modifier seulement Gunner 1 ; ne pas dupliquer la ligne déjà
   active de Gunner 2.
4. Ne jamais décommenter l’embarquement au Flak en même temps que le test de
   sortie : il faut d’abord observer si l’IA monte automatiquement.
5. Désactivation : restaurer les scripts Base originaux. Aucun binding, frame ou
   asset n’est ajouté.

## Risques

- `Cold` peut faire un autre geste de froid que taper du pied.
- L’activité peut être trop longue ou visuellement incompatible avec l’arme en
  main, la bouteille ou la conversation.
- Gunner 1 peut ne jamais être assis dans le Flak ; la sortie serait alors
  inutile ou pourrait déplacer son état interne.
- Une sortie déclenchée par `OnAlarmDone()` peut se produire après une alarme
  sans embarquement effectif.
- Une animation générique ajoutée au hochement ou à la stupeur masquerait la
  lacune sans la restaurer ; ces variantes sont volontairement exclues.

## Protocole de test en jeu

### Ambiances

1. Baseline : observer plusieurs cycles complets de Guard 2 et Guard 6, puis le
   signal 1 de Guard 5.
2. Guard 2 seul : forcer ou attendre la branche aléatoire 3, vérifier le geste
   `Cold`, sa durée, la reprise de patrouille et l’interruption par alarme.
3. Déclencher l’alarme pendant la conversation, pendant `Cold` et pendant
   `%%nuda`/`%%nuda1` ; la chaîne release doit démarrer immédiatement.
4. Guard 6 seul : tester `Cold` juste après la bouteille, puis alarme et mort à
   chaque phase ; aucune bouteille ne doit rester attachée.
5. Guard 5 : confirmer que le regard vers la plaque de glace et les 8 secondes
   d’immobilité restent lisibles sans animation ajoutée.

### Flak

1. Observer si Gunner 1 et Gunner 2 montent réellement `la_flak4x38` après leur
   mouvement `flak`, malgré les appels d’embarquement commentés.
2. Baseline Gunner 2 : déclencher `OnAlarmDone()` et confirmer visuellement la
   sortie déjà active puis le retour aux jumelles.
3. Variante Gunner 1 : répéter avec et sans embarquement préalable ; l’appel de
   sortie ne doit ni téléporter ni figer l’acteur.
4. Tester mort au siège, remplacement par Gunner 2, seconde alarme et reprise
   après sauvegarde.

Critères d’arrêt : alarme retardée, personnage figé, téléportation, occupation
double du Flak, bouteille orpheline ou animation sémantiquement incorrecte.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_static_guard_2.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_static_guard_5.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_static_guard_6.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_sub_gunner_1.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC4/R_Arc3_sub_gunner_2.scr` ;
- `.analysis/scripts/base/SCRIPTS/NORWAY/R_Nor_Tirpic1.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_UnDoorG1.scr` ;
- `Missions/ARCTIC4/scene2.bin`, `actors.bin` et `Scripts.dta` de
  `missions.dta`.
