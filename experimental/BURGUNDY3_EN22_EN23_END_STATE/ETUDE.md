# Burgundy 3 — état final des gardes 22 et 23

État : variante historique reproductible désactivée, 25 septembre 2026.
Le jeu installé n'est pas modifié. Aucun résultat moteur n'est acquis.

## Preuve et portée

Le contrôleur `bur3_vybuch.scr`, lié à `la_bu3_FuelStorage_01`, retrouve les
acteurs `bur03_22` et `bur03_23`. La branche commerciale `DESTROY_DMG` tue
explicitement chacun lorsque `_FrameInRange` est strictement inférieur à 15,
puis produit les explosions. Dans `OnCutscene(4)`, les mêmes huit lignes sont
commentées : les explosions à forte valeur de dégâts restent actives.

La différence ne démontre pas un défaut. Les dégâts commerciaux peuvent déjà
produire la mort souhaitée, avec une mise en scène différente d'un appel direct.
La portée est évaluée par le contrôleur commercial; aucun nouveau centre ni
rayon physique d'explosion n'est déduit de ce seuil.

Les deux scripts de gardes, `bur3_22.scr` et `bur3_23.scr`, terminent leur script
sur `OnDeath`. Ils participent aussi aux gestes de dialogue (signaux 10/11), à
l'attaque du maquis (22) et aux événements de cinématique 4. Le fait de ne pas
voir d'objectif dans ces handlers ne prouve pas l'absence de toute conséquence
ailleurs dans la mission, ni l'ordre de livraison des événements moteur.

## Variante construite

Le profil `burgundy3-cutscene-nearby-guard-deaths` du
[catalogue](../reconstruction-variants.json) retire uniquement les huit préfixes
`//`. Les deux conditions `< 15` sont conservées, y compris l'exclusion de la
borne exacte 15. Explosions, caméra, délais, particules, signal 10, branche
directe et objectifs sont inchangés. Aucun récepteur ou compteur n'est ajouté.

Ce profil est **exclusif** de
[`burgundy3-direct-explosion-sound`](../BURGUNDY3_DEPOT_EXPLOSION_SOUND/ETUDE.md) :
ils modifient le même contrôleur pour deux expériences différentes. La présente
variante n'ajoute pas le signal sonore moderne 11. Ne pas empiler les sorties.

Trois sources Sabre sont épinglées :

| Source | Octets | SHA-256 |
|---|---:|---|
| `scripts/burgundy3/bur3_vybuch.scr` | 3316 | `c5fd6d7c3d30f84dd193209d5615b85cb443be2f06a995ed089e9fc9d48b71ba` |
| `missions/burgundy3/scripts.dta` | 3421 | `606d7a312b600d9e3b15060d3faa32c27ef6ebe73c1ca38c0f78f899b4b98ac5` |
| `missions/burgundy3/actors.bin` | 22645 | `669dbf9a0902601e9e8e2a1b832f27dfbe300578750d8879655061a61c67bcae` |

La sortie complète locale fait **3300 octets**, SHA-256
`34d3a527c2e4105195e6b57fe045412f39c2ac1456248401e75bf21ba0f3ff97`.
Les 16 octets retirés sont exactement les marqueurs de commentaires. Le
laboratoire inerte contient 105 fichiers par branche, 87 racines, 89 scripts
accessibles et neuf objectifs commerciaux conservés. Aucun binaire commercial
n'est versionné. Trois tests vérifient le delta, les deux conditions strictes
et la conservation de la branche directe; ils ne simulent pas les dégâts.

## Essais requis avant toute activation

1. Comparer d'abord les dégâts seuls et la variante pendant la cinématique 4,
   avec chacun des gardes vivant à distance inférieure, égale et supérieure à 15.
2. Tester un garde déjà mort, absent du voisinage ou engagé dans un dialogue;
   observer les événements de mort, animations, ragdoll et interruptions audio.
3. Vérifier la route directe inchangée et la course tir joueur/attaque du maquis.
4. Interrompre la cinématique, sauvegarder/reprendre avant et après l'explosion;
   vérifier caméra, contrôles, progression et fin de mission.
5. Si les dégâts commerciaux suffisent, classer le résultat comme alternative
   de mise en scène, pas comme correction nécessaire. Au moindre effet de mort
   doublé ou changement de progression, conserver le comportement commercial.
