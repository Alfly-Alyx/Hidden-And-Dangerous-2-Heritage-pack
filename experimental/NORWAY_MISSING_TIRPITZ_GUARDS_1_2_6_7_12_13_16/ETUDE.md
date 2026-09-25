# Étude expérimentale — sept gardes Tirpitz absents de Norway

État : **preuves corrigées, implantation toujours bloquée**, 25 septembre 2026.
Aucun acteur, checkpoint, binding ou script de jeu n'est créé/compilé.

## Correction de l'hypothèse initiale

Les acteurs et bindings 1, 2, 6, 7, **10**, 12, 13, 16 et **17** sont absents de
l'état effectif `actors.bin`/`scripts.dta` du Patch 1.12. Les neuf scripts
subsistent dans `Scripts.dta`. Le nom historique de ce dossier couvre sept
gardes; les deux autres sont maintenant inclus dans l'inventaire.

**Correction de l'étude du 15 septembre : les noms de leurs checkpoints et les
deux points de regard existent.** La recherche antérieure les déclarait à tort
absents. Les noms sont vérifiés avec limite de token et terminaison zéro dans
le `check2.bin` Base effectif; les regards sont des champs nommés de la scène
Patch. Cela ne donne pas une identité, un équipement ou une position initiale
d'acteur, ni une preuve de navigation.

Il ne faut donc pas recréer leurs comportements à partir des neuf voisins : les
scripts propres constituent une preuve plus forte. Le chantier porte sur les
acteurs, la validation géométrique des routes, leur équipement et le sender.

## Inventaire exact

| ID | Acteur exact | Binding exact | Script commercial | Chemins requis |
| ---: | --- | --- | --- | --- |
| 1 | absent | absent | présent | `T1_1`, `T1_2`, `T1_3` présents |
| 2 | absent | absent | présent | `T2_1`, `T2_2` présents |
| 6 | absent | absent | présent | `T6_1`, `T6_2` présents |
| 7 | absent | absent | présent | `T7_1`, `T7_2` présents |
| 10 | absent | absent | présent | `T10_1`, `T10_2` présents |
| 12 | absent | absent | présent | `T12_1`, `T12_2`, `t12_3` présents |
| 13 | absent | absent | présent | `T13_1`, `T13_2` présents |
| 16 | absent | absent | présent | `T16_1`, `T16_2` présents |
| 17 | absent | absent | présent | `T17_1`, `T17_2` présents |

Les recherches sont exactes et terminées par zéro afin d'éviter le faux positif
`tirpic_guard_1` dans `tirpic_guard_11/14/15/18`.

`dummy_see1` et `dummy_see2` existent dans la scène effective. La casse du
checkpoint `t12_3` est conservée dans l'inventaire; sa résolution réelle par le
moteur reste à tester.

## Scripts retrouvés

[`SCRIPTS_SURVIVANTS.md`](SCRIPTS_SURVIVANTS.md) détaille les rayons, routes et
particularités. Ils attestent suspension initiale, ronde, signaux d'ambiance et
signalement d'alarme. Exception explicite : le gestionnaire bouteille 2 du garde
12 est commenté; il ne doit pas être compté comme actif.

Ces scripts ne sont pas pour autant prêts à l'emploi : la bouteille pointe vers
une frame vide, certaines particularités syntaxiques demandent examen et aucune
identité/position initiale d'acteur n'est établie.

## Sender et probabilités

`R_Nor_action_Sender.scr` tire toujours :

- un signal avec `_RandomInt(12)+1`, écrêté à 4 ;
- un numéro avec `_RandomInt(18)+1` ;
- une valeur `waiter` de 7 à 17 secondes, **jamais passée à `Delay`**.

Ses branches actives ciblent 3, 4, 5, 8, 9, 11, 14, 15 et 18. Les sept branches
étudiées sont commentées. Le sender figure lui-même comme non lié dans l'audit,
donc son porteur doit être identifié ou créé dans une copie expérimentale avant
de conclure que les actions aléatoires tournent dans la release. L'audit strict
des dépendances compte 81 scripts racines, 87 accessibles sur 102 présents; le
sender n'est ni lié ni accessible par `#include`/affectation littérale.

Le seul délai actif est celui de 10 secondes **avant** la boucle. Entre son
label et son saut de retour, aucun appel `Delay` n'existe. Une activation brute
pourrait donc marteler les destinataires ou accaparer le moteur; sa cadence
réelle n'a pas été mesurée. Il faut résoudre ce défaut dans une variante
explicitement moderne avant tout test d'intégration du sender.

Le fragment
[`PROTOTYPE_SINGLE_SENDER_EXTENSION.scr.disabled`](PROTOTYPE_SINGLE_SENDER_EXTENSION.scr.disabled)
doit être fusionné dans **l'unique** sender de la variante. Il ne crée aucun
second tirage. Ainsi chaque garde existant conserve exactement sa probabilité
de sélection de 1/18 par tirage; seules sept anciennes issues sans destinataire
deviennent actives. Cela décrit une distribution de tirages, **pas une fréquence
temporelle validée**. Les gardes 10/17 n'ont pas de branche dans ce fragment.
L'ajout de `Delay(waiter)` constitue un changement moderne distinct, nécessaire
à étudier; le fragment d'extension seul n'est pas activable.

## Placement : porte bloquante

Aucune position initiale ni identité historique des acteurs manquants n'a été
établie. Les noms de checkpoints sont présents, mais leur géométrie et leurs
liaisons de navigation ne sont pas validées par cette recherche de noms. Les
numéros voisins ou une zone vide ne suffisent pas à attribuer un acteur.

[`PLACEMENTS.plan.disabled`](PLACEMENTS.plan.disabled) laisse donc les
transformations d'acteurs à `TBD_SOURCE_OR_MODERN_EDITOR`. Deux voies sont admises :

1. source attribuée donnant position/orientation et parcours ;
2. implantation moderne en éditeur, explicitement annoncée comme telle.

Sans l'une de ces voies, aucun acteur ne doit être ajouté.

## Intégration graduée

1. Réserver une copie de mission et mesurer les neuf gardes release, sender
   inclus ou absent.
2. Implanter un seul garde pilote, avec ses chemins et son point de regard,
   sans modifier aucun acteur 3/4/5/8/9/11/14/15/18.
3. Lier son script commercial propre ; ne dériver un script que pour renommer
   un checkpoint moderne, avec diff et source indiqués.
4. Tester ronde, quatre signaux, alarme, retour, décès, modes 3/7 et sauvegarde.
5. Ajouter les gardes un par un. Le sender complet n'est activé qu'après
   validation des acteurs, du délai de boucle et des gestionnaires du garde 3.
6. Comparer les probabilités de sélection des neuf gardes existants sur un grand
   nombre de tirages : chacune doit rester 1/18. Mesurer séparément la cadence.

Critères d'arrêt : chemin manquant, acteur bloqué, double sender, modification
d'une probabilité existante, équipement inventé présenté comme officiel,
régression d'objectif ou divergence Base/Patch inexpliquée.

## Retour arrière

Retirer les sept nouveaux bindings, acteurs et chemins, puis restaurer le sender
commercial avec ses sept branches commentées. Les neuf gardes existants et
leurs fichiers ne sont jamais modifiés.

## Sources internes

Audit reproductible, sans écriture ni extraction :

```powershell
.\.venv\Scripts\python.exe tools\audit_norway_guard_chain.py --game "D:\Games\Hidden and Dangerous 2" --archives-only
```

Il fournit les empreintes des 106 fichiers lus. Repères de l'état effectif :

| Source | SHA-256 |
|---|---|
| Registre Patch | `622dec8d57c7080e744ebf5c4be27f92169d97b185b81fe196cd7f5832a2a1e0` |
| Acteurs Patch | `71c532bb13710dd5229671fcc7eef47b5108911b148f0295b0179662e79a96bc` |
| Scène Patch | `583f6f6e9bb9e57ba690e9f60ee5d3d21f733c8a8a337c8196b0776e80248289` |
| Checkpoints Base | `12a42fd25dada8e1237fc6bf1c18ec855123824a4411f06c0acd43d4fe4ea996` |
| Sender Base, 2222 octets | `ae1e9261fae7d09d301aa1eedac2858dba8fbdda5fe7211d016d8439c369d733` |

- scripts Base `NORWAY/R_Nor_action_Sender.scr` et
  `R_Nor_Tirpic1/2/3/4/5/6/7/8/9/11/12/13/14/15/16/18.scr` ;
- Base/Patch `MISSIONS/NORWAY/actors.bin`, `scene2.bin`, `scripts.dta` ;
- `output/audit/script-bindings.json` et
  `.analysis/script-bindings-refresh.json`.
