# Étude expérimentale — réactions de signaux manquantes dans Czech 2

État : analyse documentaire, 14 septembre 2026. Aucun prototype et aucun script
commercial modifié.

## Hors périmètre explicite

La restauration stable de l'objectif « Quittez la zone » appartient à la tâche
principale : activation après la capture et signal 2 envoyé par l'endgame. La
présente étude ne la recopie pas, ne la renumérote pas et ne réétudie pas non
plus le correctif `LMswitchdoors`.

## Synthèse

| Chaîne | Intention | Corps exact | Décision |
| --- | ---: | ---: | --- |
| Ger21/Freiberg → Big_Boss 1/3/4 | 4/4 | 0/4 | réactions perdues ; aucun prototype |
| Ger16 → Ger20 signal 1 | 4/4 | analogue interne 3/4 | documenter, aucun prototype |
| morts Ger22/23 → Ger24/25 signal 2 | 4/4 | 0/4 | réaction distincte du signal 3 ; aucun alias |

## `Big_Boss` — trois canaux absents

`R_Cz2_Ger21.OnDeath()` envoie le signal 1 à `Big_Boss`.
`Freiberg_attack01.scr` et `Freiberg_attack02.scr`, commentés comme activateurs
pour faire tirer Freiberg, envoient respectivement 3 et 4 au même acteur.
`R_Cz2_Big_Boss.scr` ne reçoit pourtant que le signal 19 pendant la cutscene :
il arrête alors son animation et passe vers la pose ligotée.

La table de checkpoints conserve quatre noms inutilisés par son script,
`Big_Boss_01` à `_04`. Ils renforcent l'hypothèse de plusieurs déplacements ou
positions perdus, mais ne donnent aucune correspondance entre 1/3/4 et ces
quatre points. L'activateur `Ger_22_activator01`, apparemment non relié dans le
registre effectif, mentionne lui aussi Freiberg et envoie 1 au boss : c'est un
indice d'une version antérieure, pas un corps de réaction.

La variante coopérative publique redéfinit le contrat : elle supprime l'émission
1 de Ger21, réemploie le signal 1 comme fin de dialogue/ligotage dans Big_Boss,
et conserve les émissions 3/4 des deux activateurs sans récepteur correspondant.
Ce choix mêle retrait d'un no-op, conservation de deux autres et nouvelle
sémantique du même numéro : il ne fournit aucun corps fidèle pour la mission
solo. [Variante `co_czech2`](https://github.com/ehylla93/had2-cmp/tree/main/Scripts/co_czech2).

**Décision : aucun prototype.** Associer arbitrairement les quatre checkpoints
aux trois signaux inventerait routes, délais, cible de tir et ordre de scène.

## Ger16 → Ger20 — réveil précoce probable

`R_Cz2_Ger16.OnAlarm()` envoie systématiquement 1 à Ger20. Ger20 est un sniper
suspendu, déjà armé et accroupi, que son Whenever `range` réveille à 50 unités.
Il ne possède pas de handler 1.

Deux chaînes homologues de la même mission fournissent le même corps : Ger9
réveille Ger11 et Ger13 réveille Ger16 avec le signal 1 ; les récepteurs
exécutent `HUMAN_Suspend(false)`, désactivent leur proximité, puis reviennent à
`end`. Ger20 possède bien une proximité `range`, mais ce parallélisme ne prouve
pas que son handler perdu était identique.

Le CMP 2.6.5 conserve l'émission Ger16→Ger20 et laisse encore Ger20 sans handler
1 ; il ajoute seulement un handler 19 de désactivation des alarmes. Cette
conservation d'un no-op n'est pas une restauration. **Décision : aucun
prototype tant que le corps exact n'est pas retrouvé.**

## Ger22/Ger23 → Ger24/Ger25 — ne pas confondre 2 et 3

Les morts de Ger22 et Ger23 diffusent toutes deux le signal 2 aux deux gardes
Ger24 et Ger25. Ceux-ci ne gèrent que le signal 3, lié à la commande de porte :
ils regardent, se déplacent vers `ger24_01` ou `ger25_01`, puis reprennent une
posture adaptée. Leur réveil normal se fait par proximité à 18 et 12 unités.

Le canal 2 est donc un fan-out symétrique de décès ; le canal 3 est une
instruction de porte et de positionnement. La répétition des deux émetteurs
prouve qu'une **réaction différente** était prévue, mais aucune source ne dit
s'il s'agissait d'un simple réveil, d'un changement d'alarme, d'une orientation
ou d'une route. Le CMP 2.6.5 conserve les quatre émissions 2 et ne donne aux
récepteurs 24/25 que leurs handlers 3 et un nouveau signal 19 ; la rupture reste
donc entière.

**Décision : ne pas convertir 2 en 3, ne pas créer d'alias et ne pas proposer de
delta.** Un test dynamique peut montrer que la réaction manque, pas la
reconstituer.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/CZECH2/R_Cz2_Big_Boss.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH2/R_Cz2_Ger21.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH2/Freiberg_attack01.scr` et `02.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH2/cut2.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH2/R_Cz2_Ger9.scr` à `Ger25.scr`
- `.analysis/scripts/base/SCRIPTS/CZECH2/Ger_22_activator01.scr`
- registre effectif et table de checkpoints de `.analysis/mission-assets/czech2/`
- CMP public 2.6.5, commit `793d979748b27a9924fccc30fa0fba6edb7cd70f`,
  `Scripts/co_czech2/`
