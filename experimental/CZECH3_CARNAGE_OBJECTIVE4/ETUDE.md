# Czech3 — objectif Carnage 4

État : **variante de substitution désactivée, fidélité non démontrée**, 14
septembre 2026. La release conserve l'objectif 1 comme autorité de la victoire
Carnage ; aucun fichier actif n'est modifié.

## Verdict

Le catalogue commercial déclare bien quatre objectifs pour Czech3, mais le
quatrième est un doublon sémantique du premier :

| N° | Texte | Libellé anglais |
| ---: | ---: | --- |
| 1 | 6201 | `Kill the enemy.` |
| 2 | 6202 | `Take Freiberg to the villa.` |
| 3 | 6203 | `All team members must survive.` |
| 4 | 6063 | `Kill the enemy.` |

Aucun script commercial Czech3 n'écrit le statut 4. Le moteur ne complète pas
non plus cette entrée implicitement : en modes 3/7, la mission remplace à la
fois le contrôleur d'objectifs et le compteur de morts ; ce compteur envoie le
signal 2 au contrôleur, qui réussit explicitement **l'objectif 1**.

L'objectif 4 ressemble donc à un slot Carnage résiduel abandonné lorsque la
variante finale a réutilisé l'objectif 1. Le réactiver en parallèle produirait
deux lignes « Kill the enemy ». La release ne doit pas être corrigée par ajout.

Une copie laboratoire peut seulement tester une **substitution exclusive** :
en 3/7, masquer l'objectif 1 et employer le n°4 à sa place, sans nouveau
compteur et sans double validation. Ce test ne prouve pas que cette présentation
ait existé historiquement.

## Stabilité du catalogue et des scripts

Les trois couches du catalogue portent exactement la même liste :

- `others.DTA : GameData/Gamedata00.gdt` ;
- `Patch.dta : GameData/Gamedata00.gdt` ;
- `SabreSquadron.dta : GameData/Gamedata00.gdt`.

Dans les trois cas : `6201, 6202, 6203, 6063`. L'entrée 4 n'est donc ni une
addition tardive du patch ni une correction Sabre.

Les copies Base et Patch de `R_Cz3_objectives_carn.scr` sont byte-identiques ;
il en va de même pour `R_Cz3_objectives.scr`. `setobjectives.scr`,
`Mrtvoler.scr` et `Mrtvoler_carn.scr` proviennent de Base et ne sont pas
remplacés par Patch.

## Chaîne Carnage effective

`e_ktable3` est lié à `setobjectives.scr`. Lorsque `_SPGetGameType()` vaut 3 ou
7, ce script :

1. assigne `R_Cz3_objectives_carn.scr` à `objectyves` ;
2. remplace le script de `mrtvoler` par `Mrtvoler_carn.scr` ;
3. remplace aussi le conducteur Opel et `solcar_1` par leurs variantes Carnage.

Après son signal 1, `Mrtvoler_carn.scr` sonde
`_GetCountOfCarnageEnemies()`. Quand le compteur atteint zéro, il envoie le
signal 2 à `objectyves`. Le contrôleur Carnage reçoit ce signal, affiche les
textes de transition, active l'objectif 2, réussit l'objectif 1 et réveille
`Big_boss`.

La condition « tuer tous les ennemis » possède donc déjà un détecteur et une
progression complète. Ce qui manque est uniquement une écriture vers le slot 4.

## Comparaison CMP

La variante CMP `Czech3bco` conserve un `setobjectives.scr` qui cite les mêmes
noms Carnage, mais son dossier ne fournit aucun corps récupéré pour
`R_Cz3_objectives_carn.scr` ou `Mrtvoler_carn.scr`. Son
`R_Cz3_objectives.scr` décrit une autre mission coopérative à deux objectifs.

La variante `Czech3co` définit six objectifs propres. Son objectif 4 demande de
tuer trois snipers ; ce numéro réutilisé n'est pas une copie du slot solo 6063.
Aucune des deux variantes ne fournit donc la logique historique de l'objectif
4 solo.

Sources CMP consultées :

- [sélecteur Czech3bco](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Czech3bco/setobjectives.scr) ;
- [contrôleur Czech3bco](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Czech3bco/R_Cz3_objectives.scr) ;
- [objectif 4 de Czech3co](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Czech3co/objct4.scr).

## Comparaison des missions voisines

Czech2 et d'autres missions commerciales écrivent explicitement chaque statut
d'objectif, y compris les objectifs de survie et les variantes Carnage. Le
catalogue ne suffit donc pas à déclencher une victoire automatique. Les numéros
réservés au Carnage varient selon la mission : aucun invariant moteur ne permet
de déduire que Czech3 devait obligatoirement employer le slot 4.

## Variante laboratoire autorisée

`PROTOTYPE_OBJECTIVE4_EXCLUSIVE.scr.disabled` décrit uniquement le delta à
appliquer à une copie de `R_Cz3_objectives_carn.scr` dans une mission distincte
`Czech3 [Test Carnage — slot 4]` :

1. garde interne stricte `_SPGetGameType() == 3 || 7` ;
2. objectif 1 mis à l'état 4 avant activation du n°4 ;
3. objectif 4 activé au chargement ;
4. compteur officiel `Mrtvoler_carn` conservé ;
5. sur son signal 2, objectif 4 réussi à la place de l'objectif 1 ;
6. tous les textes, délais, signaux vers `Big_boss` et transitions de
   l'objectif 2 conservés.

Cette copie ne doit jamais être installée en même temps que le contrôleur
Carnage release. Si l'état 4 laisse l'objectif 1 visible, barré ou comptabilisé,
le test est rejeté : ajouter une seconde ligne ne satisfait pas le contrat
d'exclusivité.

## Tests

1. Baseline 3/7 : journaliser objectif 1, signal 1 du compteur, compteur à zéro,
   signal 2 et passage vers l'objectif 2.
2. Modes autres que 3/7 : le slot 4 ne doit jamais changer.
3. Variante seule en 3/7 : une seule ligne « Kill the enemy », portant le n°4.
4. Tester ennemis suspendus, renforts non apparus et dernier ennemi mourant au
   moment d'une sauvegarde.
5. Vérifier que Freiberg, `Big_boss`, l'objectif 2 et l'objectif 3 suivent la
   trace release.
6. Recharger avant et après le signal 2 ; aucune double réussite ni réapparition
   de l'objectif 1.
7. Désactiver la variante et retrouver la présentation release au n°1.

Critères d'arrêt : deux objectifs visibles, objectif 4 hors 3/7, progression 2
anticipée, second compteur, perte d'un sous-titre ou dépendance à un fichier CMP.

## Sources internes

- `.analysis/metadata/others/GAMEDATA/Gamedata00.gdt` ;
- `.analysis/metadata/patch/GameData/Gamedata00.gdt` ;
- `.analysis/metadata/sabre/GameData/Gamedata00.gdt` ;
- `.analysis/scripts/base/SCRIPTS/CZECH3/setobjectives.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH3/Mrtvoler_carn.scr` ;
- `.analysis/scripts/base/SCRIPTS/CZECH3/R_Cz3_objectives_carn.scr` ;
- `.analysis/scripts/patch/SCRIPTS/CZECH3/R_Cz3_objectives_carn.scr` ;
- `output/audit/full-game-audit.json`.
