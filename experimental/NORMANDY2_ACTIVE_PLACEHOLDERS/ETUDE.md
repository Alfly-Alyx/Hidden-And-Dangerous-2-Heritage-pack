# Normandy 2 — trois familles de commentaires inachevés

État : triage sourcé, 26 septembre 2026. Les commentaires ne sont pas des appels
restaurables; aucun nouveau comportement n'est introduit.

## Red31 : intention sans implémentation

`R_N2_Red_31.scr` est lié à Red_31. Le détecteur 8 envoie le signal 8 qui réveille
le soldat, règle vue/ouïe 50/60 et mode sniper. La ligne « panique et peut-être
mort sur OnSee » n'est qu'un commentaire : pas de corps OnSee à réactiver, pas
de condition de mort ni animation officielle pour cette idée.

Le repli existant `DeAlarm` vise `Red31_1`, puis `dummy_Red31_turn`; les deux noms
existent. `OnAlarm` arrête le mouvement et termine le script; `OnAlarmDone`
contient le raccord de repli, dont l'exécution réelle doit être observée sans
supposer que `EndScript` conserve tous les événements. Une nouvelle panique
serait MODERNE et devrait préserver combat, mort et progression. Ne pas tuer le
soldat à la première vue du joueur sur la seule base de cette note.

Source Scripts.dta : 927 octets, SHA-256
`01656052cf8b9380c17555de702d760a6471b42b56fc41f141b8843e4264aadb`.

## Tiger : cible existante, tir déjà actif

`R_N2_Ger_Tank_Driver.scr` est lié à `GerTank_driver`. La cible
`la_N2_balkon` existe; l'annotation demande un ajustement, pas la recherche
d'une frame absente. Après le trajet GerTank1/2/3, le conducteur passe au siège
2, attend 2500 ms et appelle déjà `HUMAN_Attack(Target, 10000)` avant de réarmer
les alarmes. Ce n'est donc pas un simple regard commenté à déverrouiller.

Il faut observer l'axe du canon, la hauteur de cible et les obstacles depuis
l'arrêt du char. Ne pas déplacer le balcon partagé, forcer une seconde attaque
ou inventer un repère avant cette mesure. Source Scripts.dta : 1575 octets,
SHA-256 `6a611197fb114adcb34088c4baaacc855b002a736d1955fb9a5aaf059f92fb31`.

## Blue : orientation de repli et cibles de combat distinctes

Les dix-sept scripts Blue définissent `turn` vers `Ally_1` avec une annotation
provisoire. Quinze acteurs sont présents et liés; Blue12/16 restent absents.
Le regard est employé dans le repli `DeAlarm`, après le mouvement propre au
soldat. Les gestionnaires 1..5 choisissent déjà séparément les cinq alliés et
déclenchent des échanges de tirs; changer `turn` ne reconstituerait pas tout
ce protocole. Exemple Blue1 : 2780 octets dans Scripts.dta, SHA-256
`658d5467e2b21788bb25506ffc9508a568b74b46e295706b979a17e2c9aa3f81`.

Une variante d'orientation exige une direction mesurée à chaque poste, pas un
remplacement global d'Ally1 par un autre allié. Les corrections Heritage déjà
installées dans les quinze Blue concernent une autre chaîne et doivent être
conservées; l'audit commercial les exclut explicitement, sans les écraser.

## Contrôle et essais

L'[audit commun](../../tools/audit_normandy2_vestiges.py) vérifie présences,
liaisons, routes et les dix-sept orientations; il ne joue pas la mission. La
reconstruction du [coordinateur](../NORMANDY2_FAKE_DEFENCE_COORDINATOR/ETUDE.md)
est indépendante. Pour chaque famille : témoin en jeu, observation du défaut,
un seul delta moderne, mort/alarme/sauvegarde, puis retour byte-identique au
témoin. Aucun de ces trois commentaires ne justifie une activation automatique.
