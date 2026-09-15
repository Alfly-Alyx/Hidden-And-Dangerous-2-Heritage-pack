# Africa 3 — sommeil et arme statique

État : **trois essais indépendants et réversibles**, 14 septembre 2026. Les
fragments sont désactivés ; aucune mission n’a été compilée ou installée.

## Verdict

Les trois commentaires ne présentent pas le même degré de récupérabilité :

- AF3a_24 possède un dummy assis valide et une activité `Sit` abondamment
  attestée. Un « assoupissement assis » est testable, mais ce n’est pas une
  restitution du sommeil sur un lit.
- AF3a_26 nomme un lit réellement présent, `m_postel_a7`, mais
  `HUMAN_ACTIVITY_Sleep` n’a aucun appel actif dans le corpus inspecté. Son
  essai reste à haut risque.
- AF3a_07 omet la déclaration de `biggun`, mais la mission contient bien
  l’acteur statique `AF3a_MG42`. Plutôt que réactiver `HUMAN_Use`, lui aussi sans
  précédent actif, le repli le moins spéculatif emploie la commande
  `HUMAN_BoardVehicle` utilisée par d’autres servants de mitrailleuse, dont
  AF3a_02 dans la même mission.

Ces trois pistes ne doivent pas être fusionnées. Chacune doit être évaluée sur
une copie distincte ou activée seule.

## Inventaire des preuves

| Script | Vestige | Actif ou présent ailleurs | Conclusion |
| --- | --- | --- | --- |
| `AF3a_24.scr` | `some_bed` commenté, puis deux appels `HUMAN_ACTIVITY_Sit(sit)` commentés | `dummy_24_sit` existe dans `scene2.bin` ; `Sit` est actif dans plusieurs scripts Africa 3 | repli assis testable ; aucun lit nommé `some_bed` |
| `AF3a_26.scr` | `m_postel_a7` et `HUMAN_ACTIVITY_Sleep(bed)` commentés | le cadre `m_postel_a7` existe ; aucun `Sleep` actif Base/Patch | intention précise, API non éprouvée |
| `AF3a_07.scr` | `HUMAN_Use(biggun, true)` commenté et `biggun` non déclaré | `AF3a_MG42` figure dans `actors.bin` et `items.dat` ; `AF3a_02` monte `AF3a_MG_02` avec `HUMAN_BoardVehicle` | cible récupérée, commande d’origine non fiable |

Les bindings effectifs relient respectivement `AF3a_07`, `AF3a_24` et
`AF3a_26` à leurs scripts homonymes. Les variantes Patch sont les sources à
copier pour les essais.

### Priorité des alarmes conservée

AF3a_24 et AF3a_26 possèdent déjà des `OnAlarm()` qui arrêtent l’animation,
stoppent l’acteur et le réveillent ou le remettent debout. AF3a_07 ne tente
l’arme statique qu’à l’intérieur de son `OnAlarm()`. Aucun prototype n’ajoute
`DisableAlarms`, un nouveau rayon d’activation ou une attente infinie avant le
traitement de l’alarme.

## Niveaux de spéculation

- **Faible** : `dummy_24_sit`, `m_postel_a7` et `AF3a_MG42` sont des noms de
  scène/acteur réellement présents.
- **Faible à moyenne** : `HUMAN_ACTIVITY_Sit(dummy_24_sit)` ; la commande et le
  point d’ancrage sont attestés, mais l’effet est une pose assise, pas un sommeil.
- **Forte** : `HUMAN_ACTIVITY_Sleep(m_postel_a7)` ; seule la ligne commentée en
  donne la signature.
- **Forte et écartée** : `HUMAN_Use(biggun, true)` ; aucun appel actif et aucune
  déclaration locale ne subsistent.
- **Moyenne** : monter `AF3a_MG42` par `HUMAN_BoardVehicle(..., true, 0)` ; la
  commande et le type d’usage sont éprouvés, mais la compatibilité de cet acteur
  précis reste à tester.

## Prototypes isolés

### AF3a_24 — assoupissement assis

`PROTOTYPE_AF3A24_SIT_DOZE.scr.disabled` insère l’appel `Sit` exactement au
point prévu par le commentaire, avant la suspension initiale. Il ne prétend pas
transformer le dummy en lit et ne reprend pas automatiquement cette posture
après une alarme.

### AF3a_26 — test de l’API sommeil

`PROTOTYPE_AF3A26_SLEEP_API.scr.disabled` rétablit la déclaration du lit et
l’appel commenté. C’est un test de compatibilité, non une proposition de release.
Le moindre échec de chargement, réveil ou interruption invalide cette piste.

### AF3a_07 — remplacement par l’interface d’arme statique

`PROTOTYPE_AF3A07_STATIC_MG.scr.disabled` remplace uniquement la ligne
`HUMAN_Use` commentée par un embarquement au siège 0 de `AF3a_MG42`. Le modèle
n’est pas inventé : le nom vient des registres Africa 3. La posture initiale
`%%sedimL4`, la visée, le signal 20 et les réactions d’alarme restent inchangés.

## Activation et retour arrière

1. Créer une copie de test d’Africa 3 et partir des scripts Patch effectifs.
2. Activer un seul fichier de prototype à la fois.
3. Ne pas renommer ni dupliquer `dummy_24_sit`, `m_postel_a7` ou `AF3a_MG42`.
4. Pour désactiver, remettre le script Patch original correspondant. Aucun
   nouveau binding ou objet de scène n’est nécessaire.
5. Après chaque essai, recharger une sauvegarde baseline pour éviter qu’un état
   de posture ou de siège ne contamine l’essai suivant.

## Risques

- `Sleep` peut être absent, incomplet ou non interruptible dans le moteur final.
- Suspendre un acteur après `Sit` ou `Sleep` peut figer une transition inachevée.
- Le réveil peut laisser AF3a_24/26 attaché à un point d’activité.
- `AF3a_MG42` peut ne pas exposer de siège compatible malgré sa présence dans
  les registres.
- L’embarquement peut téléporter AF3a_07, bloquer sa rotation, neutraliser son
  `OnAlarmDone` ou empêcher son signal 20.
- Tester plusieurs variantes ensemble rendrait les régressions impossibles à
  attribuer.

## Protocole de test en jeu

### AF3a_24

1. Vérifier la pose initiale et l’alignement exact sur `dummy_24_sit`.
2. Entrer dans le rayon 40, provoquer chaque type d’alarme utile et blesser
   l’acteur pendant la posture.
3. Confirmer que `OnAlarm()` le remet debout, permet ses déplacements et envoie
   toujours le signal au détecteur de morts.
4. Sauvegarder/reprendre avant et après l’activation.

### AF3a_26

1. Commencer par le contrôle de compilation/chargement.
2. Observer l’alignement avec `m_postel_a7`, puis entrer dans le rayon 15.
3. Déclencher tirs, vue, blessure et friendly fire pendant le sommeil ; la
   réponse doit être immédiate et les chemins d’alerte inchangés.
4. Tester le signal 20 pendant le sommeil et après le réveil.
5. Rejeter l’API si l’acteur reste couché, attaché ou non réactif.

### AF3a_07

1. Baseline : relever sa pose `%%sedimL4`, sa réaction à l’alarme et au signal 20.
2. Variante : déclencher une alarme et confirmer un embarquement réel sur
   `AF3a_MG42`, sans téléportation anormale.
3. Vérifier tir, rotation, cible proche/lointaine, mort du servant et destruction
   de la MG42.
4. Envoyer le signal 20 avant et après l’embarquement ; le chemin vers
   `AF3a_07_alert` doit rester disponible.

Critères d’arrêt communs : alarme retardée, acteur figé, siège occupé à tort,
objet inventé, crash, ou changement du détecteur de morts.

## Sources internes

- `.analysis/scripts/patch/SCRIPTS/AFRICA3/AF3a_07.scr` ;
- `.analysis/scripts/patch/SCRIPTS/AFRICA3/AF3a_24.scr` ;
- `.analysis/scripts/patch/SCRIPTS/AFRICA3/AF3a_26.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA3/AF3a_02.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_15.scr` ;
- `Missions/AFRICA3/scene2.bin`, `actors.bin`, `items.dat` et `Scripts.dta` de
  `missions.dta`.
