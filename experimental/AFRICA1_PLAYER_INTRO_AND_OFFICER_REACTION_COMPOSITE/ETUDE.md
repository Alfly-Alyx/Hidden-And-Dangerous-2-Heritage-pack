# Africa 1 — introduction et réaction des joueurs à l'officier

État : deux générations de scripts séparées, 26 septembre 2026. Aucun script
de joueur réaffecté et aucune introduction remplacée.

Les quatre `AF1_player01..04` sont libres et non atteints par les dépendances
littérales. Ils résolvent AF1_21 et, pendant OnCutscene(10), tournent le joueur
vers lui si sa distance est **strictement inférieure à 10**. Les quatre
OnCutsceneDone(10) sont vides. Ils ne contiennent ni l'introduction 3 ni sa
gestion des doubles.

La chaîne commerciale actuelle lie Spawnsingle01..04 à PL1..4assign_af1;
OnUse affecte CUTSAS1..4_af1. Ces quatre scripts identifient ensuite leur
propriétaire avec FRM_GetMyFrame, gèrent l'introduction **3**, leurs doubles,
les places de Jeep pour 2/3/4 et les jumelles du premier joueur. Tous terminent
par EndScript après OnCutsceneDone(3). Ajouter OnCutscene(10) après cette fin
ne garantit donc pas un gestionnaire encore vivant.

Les assigners déclarent une frame player sans initialisation explicite dans
leur texte. Leur contexte spécial OnUse doit être observé; remplacer cette
frame par le dummy de spawn serait une identité différente, pas une correction
évidente. Deux ScriptAssign successifs ne composent pas deux comportements :
le second peut remplacer le premier et perdre son nettoyage.

## Composition moderne à établir

Conserver l'introduction commerciale ou Heritage choisie comme baseline.
Après nettoyage complet de la cinématique 3, transférer une seule fois chaque
joueur effectivement présent vers un récepteur 10 persistant, ou intégrer les
deux événements dans un contrôleur explicitement conçu pour rester vivant.
Ce sont deux architectures alternatives à comparer, pas à cumuler.

Avant implantation : vérifier 1..4 membres, absence de double restant, joueur
mort, cinématique sautée/interrompue, changement de personnage, sauvegarde et
autre ScriptAssign ultérieur. Le récepteur doit conserver le seuil historique
`<10`, ne pas créer de nouveau joueur et ne pas déplacer les personnes hors
champ. La restauration du
[mouvement de l'officier](../AFRICA1_OFFICER_21_CUTSCENE_MOVE/ETUDE.md)
est un autre profil, à tester séparément avant composition.

## Provenance Patch.dta

| Groupe / premier fichier | Octets | SHA-256 |
|---|---:|---|
| AF1_player01 | 444 | `909835023716d0bd9339b785ca966055e7d5d90ae30de1ee8aed7e67c4f24f43` |
| AF1_player02 | 444 | `2377d0fc648c312658bf5fe58689319d31ef9339b420a0911c948afc7ca38ed5` |
| AF1_player03 | 446 | `9f808e319a074ae41a5bbf534b97a774b62db3654dfb3e0848a813fbe56a5095` |
| AF1_player04 | 446 | `69a18fd4e0a0e40ac86ac00959d4b0b13a53347062f7f08a922010ef71904b31` |
| PL1assign_af1 | 81 | `b8b1d4277c5d419626afa033d63b774ea0101e9198e12ae3057f855e1cd9f09e` |
| CUTSAS1_af1 | 1531 | `58b850ef31e7077c6e472316ebbb797393906a3a35062989269f5fae65861c7d` |
| CUTSAS2_af1 | 833 | `0d8ac65937d64d0a786bba0861c031e42025868962efcd1c7b4042bb8a0bde62` |
| CUTSAS3_af1 | 825 | `2f6b66d4914e44fa62f93395284cd35ab6e32389c321ff877b30dcc92a0c0ff1` |
| CUTSAS4_af1 | 830 | `555e8b9d208b205e2a31b77486936ead4445d85fba371dc7181578d86db4952c` |

Chemins internes : scripts/africa1/<nom>.scr. Ces données n'autorisent aucune
écriture sur l'installation actuelle, dont le registre Heritage est distinct.
