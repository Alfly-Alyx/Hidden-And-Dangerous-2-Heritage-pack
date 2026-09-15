# Étude expérimentale — poste de sniper partagé ge16/ge24

État : **propriété exclusive de ge16 ; branche ge24 conditionnelle et
désactivée**, 15 septembre 2026. Aucun script actif, checkpoint, binding ou
installateur n'est modifié et rien n'est compilé.

## Verdict

Le seul poste de sniper commercial nommé dans ce secteur est
`ge16_sniper`. `ge_16.scr` conserve la paire commentée complète : déplacement
vers ce point puis `HUMAN_SetSniper(1,1)`. Sa restauration fidèle appartient au
paquet principal et donne à ge16 la propriété exclusive du poste.

`ge_24.scr` conserve seulement `//HUMAN_Move("ge16_sniper");` dans la même
famille d'alarme. L'activer en parallèle enverrait deux soldats au même point.
Il est donc interdit d'utiliser `ge16_sniper` pour ge24, que ge16 soit déjà
arrivé, en route, mort ou momentanément absent.

La variante ge24 n'est pas un second propriétaire du poste. Elle reste une
branche additionnelle facultative, disponible uniquement si une source
commerciale future atteste un checkpoint distinct près de ge24.

## Preuves et limites

- `ge16_sniper` existe dans `check2.bin` ; les autres noms ge16 trouvés sont
  `ge16_01` et `ge16_02`.
- aucun checkpoint `ge24_*` ou autre poste local associé à ge24 n'est présent
  dans la table commerciale. `ge24sit` est une frame d'activité assise, pas une
  destination de déplacement attestée.
- la position relevée de ge16 est à environ 1,24 unité de `ge16_sniper` ; ge24
  en est distant d'environ 77 unités.
- le vestige ge16 possède déplacement **et** mode sniper. Le vestige ge24 ne
  possède que le déplacement : lui ajouter `HUMAN_SetSniper` serait une
  invention supplémentaire.
- `ge_17.scr` contient aussi un ancien téléport commenté dont une borne est
  `ge16_sniper`. Il reste inactif et ne justifie aucun partage du point.

La destination et la paire de commandes de ge16 sont **OFFICIELLES**. Une
réaction locale de ge24 est une **INFÉRENCE**. Tout nouveau checkpoint, son
placement, sa navigation et sa ligne de tir seraient une **CRÉATION MODERNE**
tant qu'une donnée commerciale ne les atteste pas.

## Contrat de variante

[`SNIPER_POST_OWNERSHIP.plan.disabled`](SNIPER_POST_OWNERSHIP.plan.disabled)
définit deux profils :

- `GE16_FAITHFUL` est le profil par défaut : ge16 reçoit sa paire restaurée et
  ge24 conserve son commentaire ;
- `GE16_PLUS_GE24_DISTINCT` n'est déverrouillable qu'avec le nom, le transform
  et la navigation d'un second point attesté. Ge16 conserve alors son propre
  poste et ge24 reçoit uniquement le mouvement prouvé vers le point distinct.

Le prototype ge16 déjà isolé dans
`experimental/ALPS1_GE16_GE24_SHARED_SNIPER_POINT/` peut servir au profil
fidèle. Il n'est pas dupliqué ici et aucune ligne ge24 n'est produite avant la
porte de preuve.

## Tests

1. Valider d'abord ge16 seul : alarmes 2/16/256, déplacement court, mode
   sniper, répétitions, mort et sauvegarde/reprise.
2. Confirmer pendant toute la baseline que ge24 reste à sa réaction release et
   ne tente jamais `ge16_sniper`.
3. Si un point ge24 est retrouvé, vérifier son identité dans la mission, sa
   distance, son parent, sa navigation, sa couverture et sa ligne de tir.
4. Tester ensuite ge16 et ge24 simultanément : destinations distinctes, aucun
   croisement bloquant, aucune occupation mutuelle et aucun téléport.
5. Retirer seulement la branche ge24 et confirmer que le poste fidèle de ge16
   reste inchangé.

Critères d'arrêt : point ge24 inventé par simple commodité, réutilisation de
`ge16_sniper`, ajout non attesté du mode sniper à ge24, conflit de navigation ou
nécessité de désactiver la restauration ge16.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_16.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_24.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_17.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/check2.bin` et
  `actors.bin` ;
- `experimental/ALPS1_GE16_GE24_SHARED_SNIPER_POINT/PROPOSITION.md`.
