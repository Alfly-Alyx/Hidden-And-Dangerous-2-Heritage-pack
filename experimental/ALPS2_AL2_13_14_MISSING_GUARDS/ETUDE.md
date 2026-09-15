# Alps 2 — gardes manquants AL2_13 / AL2_14

État : **reconstruction moderne désactivée, non attestée**, 15 septembre
2026. Ce dossier consolide l'étude antérieure sans dupliquer ses prototypes.

## Correction du périmètre

La frame exacte `AL2_13_A1` existe dans `scene2.bin`, mais elle n'a pas de
binding effectif dans `Scripts.dta`. Son script complet existe et résout
`AL2_13` et `AL2_14`, puis leur envoie le signal 1 lorsque le joueur passe à
moins de deux unités.

En revanche, aucun acteur exact `AL2_13` ou `AL2_14` n'est présent dans
`actors.bin`, `scene2.bin` ou le registre effectif. L'occurrence textuelle
`AL2_13` dans la scène n'est que le préfixe de `AL2_13_A1`. Il ne manque donc
pas seulement deux scripts : il manque les deux acteurs, leurs items, leurs
transforms, leurs bindings et leurs comportements.

Les fichiers `AL2_13.scr` et `AL2_14.scr` sont absents. Les commentaires
`al2_13 neni` / `al2_14 neni` dans les alarmes normale et Carnage confirment
une suppression connue, sans fournir les comportements perdus.

## Ce que les voisins permettent de déduire

| Voisin | Faits utiles | Limite |
| --- | --- | --- |
| `AL2_11` | dialogue/lecture puis réaction à l'alarme | rôle civilisé, pas un patron de garde local |
| `AL2_12` | activation par signal, routes `01..04`, version Carnage distincte | routes et point `05` propres à 12 |
| `AL2_15` | garde agressif, routes `01..04` + `nuda` | dialogues et points privés |
| `AL2_16` | garde défensif/fumeur, routes `1..4,6` | logique de porte/prisonnier privée |
| `AL2_17` | renfort suspendu réveillé par signal 1, aucune route | meilleur patron minimal d'activation |

`AL2_15_A1` porte encore un commentaire « activator for AL2_13 » mais son code
ne résout que 15/16/17. Cela soutient un ancien groupe local ; cela ne fournit
ni position, ni route, ni signal de fin.

La seule variante Carnage voisine est `AL2_12_carn.scr`, et elle change les
types d'alarme, le traitement des documents, le waypoint final et le point de
regard. Cette divergence interdit de supposer qu'un script normal inventé pour
13/14 convient aussi à Carnage.

## Reconstruction autorisée

Le dossier antérieur
[`ALPS2_AL2_13_14_REMOVED_BEHAVIOURS`](../ALPS2_AL2_13_14_REMOVED_BEHAVIOURS/ETUDE.md)
reste l'unique source des deux fragments de garde locale : 13 emprunte le
profil général de 15, 14 celui de 16, sans reprendre leurs routes. Ces profils
sont des **DÉDUCTIONS MODERNES**, pas une restauration attestée.

Le présent dossier fixe les garde-fous :

- aucun waypoint `AL2_13_*` ou `AL2_14_*` ne doit être créé par simple copie ;
- aucun handler autre que l'activation minimale par signal 1 n'est promu ;
- `AL2_13_A1` n'est lié qu'après création et test manuel des deux destinataires ;
- aucun objectif, compteur de morts ou condition de fin n'est ajouté ;
- Carnage reste désactivé tant qu'un comportement dédié n'est pas spécifié et
  testé séparément.

## Ordre d'essai

1. Copier acteurs/items et poser deux transforms dans une **copie de scène** ;
2. lier les prototypes existants et envoyer le signal 1 manuellement ;
3. tester collision, faction, mort, sauvegarde et ligne de tir ;
4. seulement ensuite lier une copie de `AL2_13_A1` à son script officiel ;
5. instrumenter les signaux répétés ; rendre l'activation monostable si le
   moteur réémet à chaque passage ;
6. tester le profil normal ; laisser Carnage coupé.

Tant que les transforms et les handlers restent créés, l'étiquette de sortie
doit rester `Prototype — gardes 13/14`, jamais `restauration`.
