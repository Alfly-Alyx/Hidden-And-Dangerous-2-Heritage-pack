# Co_Burgundy1 — acteurs solo retirés

État : **variante additive spécifiée, données de scène à copier**, 14 septembre
2026. Co_Burgundy1 release reste inchangée.

## Verdict

Les scripts coop de John Ashley et du chien ont été livrés, mais ni leurs
acteurs ni leurs bindings. John est le meilleur candidat : ses trois trajets
survivent dans `Co_Burgundy1/check2.bin` et son script coop est cohérent. Le
chien est plus incomplet : son maître `bu1_03` survit, mais ses anciennes routes
ne sont présentes ni sous `dog_1..5` ni sous `pes01..03` dans la carte coop.

Une entrée distincte, `Co_Burgundy1 — Solo actors [Reconstruction]`, peut copier
les acteurs, items et transformations officiels de Burgundy1. John et le chien
doivent rester deux options indépendantes afin de mesurer séparément impact
d'objectif, furtivité, IA et réseau.

## Comparaison des registres

| Élément | Burgundy1 | Co_Burgundy1 |
| --- | --- | --- |
| `JohnAshley` | présent, lié à `bur1_JohnAshley.scr` | acteur absent, script orphelin |
| `pes_03` | présent, lié à `bur1_dog01.scr` | acteur absent, script orphelin |
| `bu1_03` | présent, lié à `bur1_03.scr` | présent, même liaison |
| trajets John 01/02/03 | présents | présents |
| `ja_kolize` | présent | absent |
| trajets chien `pes01..03` | présents | absents |
| trajets commentés `dog_1..5` | absents | absents |

L'audit commercial donne 105 liaisons en solo, contre 91 en coop. Les deux
scripts sont parmi les orphelins coop et aucun acteur homonyme libre n'existe.

## John Ashley

Le script coop attend 15 secondes, parcourt `JohnAshley01`, `02`, `03`, se
suspend, puis devient allié quand un joueur arrive à moins de deux unités. Par
rapport au solo, la coop retire `ja_kolize`, `HUMAN_Stop()` et les deux répliques
57990071/72 ; cette version est donc déjà adaptée aux données coop survivantes.

Le script solo de la dynamite peut aussi choisir John comme locuteur. Les trois
scripts coop de dynamite ne le référencent pas. La première reconstruction doit
respecter cette différence : John est un allié narratif facultatif, pas un
nouvel autorisateur d'objectif. Tout raccord ultérieur à la dynamite sera une
adaptation moderne séparée, après validation multijoueur des sous-titres.

Implantation : copier **exactement** depuis Burgundy1 l'acteur, son item, son
équipement et son transform initial, puis lier le script coop existant. Les
trajets sont conservés par la carte cible ; aucun point n'est inventé.

## Chien `pes_03`

Le noyau des scripts solo et coop est identique : maître `bu1_03`, agressivité,
course et attaque à l'alarme. À la mort du maître, le solo porte vue et ouïe à
120 et patrouille aléatoirement sur `pes01..03`. La coop conserve le bloc de
réaction mais toute la patrouille `dog_1..5` est commentée et aucun de ces
repères n'existe.

La première variante copie exactement l'acteur/item/transform solo et utilise
le script coop **sans décommenter de route**. Le chien reste sur place après la
mort du maître, conformément au code coop livré. Une phase optionnelle pourra
copier `pes01..03` du solo et reprendre la patrouille solo ; elle sera étiquetée
`ADAPTATION OFFICIELLE SOLO VERS COOP`, pas « restauration coop ».

Le chien ne doit pas être ajouté au décompte d'ennemis ou à un objectif avant
preuve. Son autorité IA et son état de maître doivent être vérifiés côté hôte
et client.

## Architecture et non-interférences

Les deux options sont appliquées avant le chargement de la copie de mission,
jamais en cours de sauvegarde :

- `JOHN_ASHLEY=0/1` contrôle acteur, item, binding et transform John ;
- `DOG_03=0/1` contrôle acteur, item, binding et transform chien ;
- les scripts et objectifs release ne sont pas modifiés ;
- chaque configuration possède une signature de sauvegarde distincte.

La matrice complète de test est dans `MATRICE_ACTIVATION_ET_TESTS.md`.

## Porte d'implantation

Avant de produire un registre ou un delta de scène désactivé, comparer dans
l'éditeur les items, inventaires, transformations et affiliations des deux
acteurs solo. Vérifier que la copie n'écrase aucune frame coop de même ID et que
le transform du chien reste valide autour de `bu1_03`. Aucun prototype de
script supplémentaire n'est nécessaire : les scripts coop existent déjà.

