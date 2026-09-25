# Quarantaine — scripts aéronautiques et véhicules orphelins

Ces scripts restent des objets d'étude. Aucun n'est lié aux profils décoratifs.

## Africa 2

- `AF2_aa_spit01.scr` cible `opelsflakem` ou un joueur avec
  `AirAttack_SetTarget`, mais ne fournit ni modèle de vol ni binding restauré ;
- `AF2_airfight.scr` cible immédiatement `HoriciJunkers` ;
- `AF2_mes05.scr` attend un signal 1, choisit un joueur puis une destination
  `dummy_afterattack` ;
- `AF2_act_fly_mes.scr` lance la piste `flying_mes` sur `dummy_letka_mes`, alors
  que son déclencheur de proximité est commenté.

Les scripts Base/Patch existent, mais leurs acteurs, leurs séquences complètes
et leur autorité par rapport aux avions Africa 2 actifs doivent être prouvés.
Ils ne correspondent pas aux bancs La-5, Aichi, M323, Li-2, Fa 223, Fw 200 ou
DFS 230.

## Africa 6 et Africa 1

`AF5_airanim.scr` saute directement à `END`; les six appels
`#aircraft1.I3D..#aircraft6.I3D` sont inatteignables. L'audit du 26 septembre a
retrouvé les six supports 4DS/pistes 5DS et la hiérarchie
`#aircraftdum.airdummy -> ju88` dans Africa6. Le Ju 88 actif est déjà lié à sa
chaîne native : retirer le saut ne serait pas un simple ajout décoratif et
pourrait doubler son pilotage. Voir l'
[étude du support et de la séquence](../AFRICA6_AIRANIM_OWNER_AND_SEQUENCE/ETUDE.md).

`AF1_snd_aircraft.scr` boucle seulement `PlaySound(1,8)` toutes les quatre
secondes et n'a pas de propriétaire démontré. Ne pas l'attacher au Ju 52 ou à
un banc sur la seule base du nom.

## Co_Libye3 et Tutorial

`Co_Libye3/Opel.scr` met le carburant de son propriétaire à zéro. Les candidats
`la_OpelAfK_` et `la_OpelFAf_1` restent deux variantes exclusives documentées
dans `experimental/CO_LIBYE3_OPEL_OWNER/`; ne rattacher ce script à aucun banc.

La séquence véhicule du Tutorial attend un `ControlorTwo` capable de convertir
les signaux 1/2 en 4/5 et de consommer le retour 4. Ce contrôleur manque et le
pilote vestigial n'est pas lié. Le dossier
`experimental/TUTORIAL_CONTROLORTWO_SEQUENCE/` reste l'autorité de cette étude.

## Règle

Un nom d'avion ou de véhicule dans un script ne vaut ni instance du modèle, ni
physique, ni autorisation de binding. Toute réouverture exige propriétaire,
dépendances, ordre, rollback et test séparés du laboratoire décoratif.
