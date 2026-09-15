# Alps 1 — signal 10 Carnage de GE08

État : **branche complète proposée pour essai isolé**, 14 septembre 2026.
Le fragment est désactivé, réservé à la variante Carnage et non compilé.

## Verdict

GE_07 envoie le signal 10 à GE_08 après son dernier déplacement, attend deux
secondes, détruit la formation puis signale le téléporteur. GE08 reçoit bien ce
signal, mais son handler actif ne fait que FORMATION_DelMember(me) ; deux lignes
immédiatement suivantes sont commentées : déplacement vers ge08_02 et signal 2
au chien.

Le signal 2 du script pes.scr est actif : il déclenche le cadre de jappement,
suspend le chien et retourne à son état de fin. Il s’agit donc du partenaire
exact, pas d’un signal inventé.

## Reconstruction

PROTOTYPE_GE08_SIGNAL10_CARNAGE.scr.disabled exécute :

1. retrait de GE08 de la formation ;
2. déplacement vers ge08_02 ;
3. signal 2 au chien ;
4. remise de SaveGameValue(7) à 0 ;
5. suspension de GE08 ;
6. retour au label end.

Les étapes 1 à 3 proviennent directement du handler et de ses commentaires.
Les étapes 4 et 5 sont des **invariants de cycle de vie inférés** : la valeur 7
est mise à 1 lors des activations et remise à 0 à l’initialisation et à la mort,
tandis que le personnage est suspendu dans l’état inactif. Elles ferment la
branche sans recopier aveuglément une autre scène.

## Géométrie et séparation de variante

ge08_01 se trouve vers 114.246323, 2.338546, 115.774345 et ge08_02 vers
121.218475, 2.555223, 85.686256, soit environ 30.89 unités. Le mouvement est
donc visible et doit finir avant la suspension.

Cette branche remplace uniquement le handler signal 10 de la copie Carnage de
ge_08_car.scr. Elle ne doit pas être ajoutée à la mission release ni changer le
binding normal de ge_08.

## Test

1. Lancer la variante Carnage et vérifier la formation GE07/GE08.
2. Observer l’ordre : signal 10, retrait, déplacement, chien suspendu, puis
   destruction de formation et téléport de GE07.
3. Tester le chien en attaque, mort et déjà suspendu avant le signal 2.
4. Déclencher une alarme de GE08 pendant le trajet vers ge08_02.
5. Vérifier la valeur 7 avant/après et à la reprise d’une sauvegarde.
6. Contrôler que le signal 10 répété ne relance pas un acteur suspendu.

Rejeter la variante si le déplacement dépasse la fenêtre de GE07, si la
suspension interrompt HUMAN_Move ou si la valeur 7 est utilisée ailleurs comme
preuve de survie plutôt que d’activité.

