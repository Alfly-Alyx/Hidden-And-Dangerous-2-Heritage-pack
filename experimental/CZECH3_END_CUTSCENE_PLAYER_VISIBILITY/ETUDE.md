# Czech 3 — visibilité des joueurs à la fin

État : contrat de doubles documenté, prototype bloqué par les sorties et la
sélection des joueurs, 25 septembre 2026.

## Une dépendance dynamique, pas un simple script orphelin

`CUTplayer1_cz3.scr` n'a pas de liaison directe au registre. Il est néanmoins
atteignable par l'affectation littérale de `R_Cz3_Com1.scr`, qui est lié. Le graphe
commercial compte 67 racines, 76 scripts accessibles et 84 disponibles. Cette
accessibilité statique ne prouve pas à quel moment `OnUse` s'exécute : l'assigner
déclare une frame `player` sans l'initialiser explicitement. Observer le mécanisme
réel avant de créer un second propriétaire ou de corriger l'affectation.

## Tous les joueurs n'ont pas un double créé

Dans `OnCutscene(2)`, le script calcule le nombre de membres moins un, choisit
le premier joueur via `CSC_GetPlayerNumNoNPC(0, ...)` et crée son double. Il crée
le second seulement dans la branche `num_players > 1`. Les branches suivantes
retrouvent et téléportent les joueurs 3/4, **sans appel de duplication pour eux**.
Les quatre anciens `FRM_SetOn(playerN, false)` sont commentés.

La fin appelle pourtant libération/réaffichage pour quatre variables de doubles.
Une animation du second double est aussi demandée après 15 secondes hors du bloc
conditionnel de création. Ne pas interpréter cela comme preuve que quatre doubles
valides existent. Les conventions du compteur d'équipe et des frames vides restent
à tester; aucune correction d'indice automatique n'est justifiée ici.

Les repères `Com1..4` existent dans le Check2 commercial. Leur présence ne justifie
ni un masquage global, ni une suppression de téléportation. La cinématique 1 du
même fichier cache et réaffiche déjà le premier joueur : elle doit rester distincte.

## Sources

- Scripts.dta, `scripts/czech3/cutplayer1_cz3.scr`, 6620 octets,
  SHA-256 `e755588c0eda6ac12ca339c43d3f799ea4f69ea873314033eb9a155fb73ca6cf`.
- Scripts.dta, `scripts/czech3/r_cz3_com1.scr`, 79 octets,
  SHA-256 `0695d290138f5c8c88ef1bea96785107f718c85a1cb0ac198e4dc0dd3e97697d`.
- missions.dta, `missions/czech3/check2.bin`, 164478 octets,
  SHA-256 `a0b6db1acaf50dbfba19e90933d322dccbda186d18d68f5a9de70ca4d1894cba`.

## Avant un prototype

Définir un état par couple joueur/double : joueur obtenu, double créé, joueur
masqué, nettoyage effectué. Le masquage n'est autorisé qu'après une création
confirmée. Le nettoyage ne touche que les couples réellement créés et doit être
idempotent lors d'une fin normale, annulation, mort, reprise ou changement de scène.
Ne pas inventer une primitive de validité de frame : confirmer son API dans une
source commerciale ou un essai isolé. Tester un à quatre survivants et préserver
caméra, accessoires, positions et progression dans le profil commercial.
