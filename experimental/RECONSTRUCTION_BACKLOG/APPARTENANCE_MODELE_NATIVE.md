# Appartenance native des nœuds à un modèle

Vérifications du **10 octobre 2026**, en émulation privée de LS3DF 1.12.
Elles complètent la [collecte compilée](COLLECTE_MODELE_MAINS.md), sans prétendre
résoudre la création ou la destruction des objets dans le client.

## Trois relations distinctes

| Champ du nœud | Relation examinée | Effet observé |
| --- | --- | --- |
| `+100` | Modèle propriétaire de l'entrée de collection | Modifié par ajout / retrait natifs |
| `+108` | Parent de la hiérarchie de transformations | Inchangé par ces ajouts / retraits |
| `+168` | Visuel propriétaire du joint diagnostique | Utilisé par le rafraîchissement ; distinct des deux précédents |

Le compteur de références natif est un **mot de 16 bits à `+e4`**. L'entrée
virtuelle `+4` n'est pas un `AddRef` : la création d'une référence dans le chemin
étudié est une incrémentation directe du mot. Cette distinction interdit de
traiter les objets comme une interface COM supposée.

Pour la table du modèle `0x1009ba50`, ajout `+7c` / `0x100341c0` et retrait
`+80` / `0x10034260` ont été lus puis exécutés. L'ajout incrémente la référence,
retire le nœud de son ancien propriétaire via `0x1001c3d0`, l'ajoute au vecteur
de destination et écrit `+100`. Le retrait comble une case intérieure avec la
dernière entrée, diminue le nombre, efface `+100` et libère une référence si son
compteur est positif. La case hors du nouveau nombre n'est pas remise à zéro.
Le retrait d'un nœud absent renvoie `0x80000006` sans modification.

## Domaine effectivement exécuté

Deux scénarios de onze et 128 nœuds, vecteurs préalloués à 128 places, conservent
toujours une référence de l'appelant. Les transferts aller / retour, réajout au
même modèle plein, retrait intérieur / dernier / unique et retrait absent font
**562 opérations**. Ils entraînent 419 appels d'ajout, 423 appels de retrait
(y compris les retraits imbriqués) et 419 diminutions de référence positives.

Chaque opération est comparée à un modèle indépendant des vecteurs, compteurs
et propriétaires. Les pages complètes des objets, noms, liens de parenté et
gardes ainsi que l'image de bibliothèque sont vérifiées. Les registres
préservés et la pile sont contrôlés. Les branches d'allocation, d'erreur de
référence et de destruction finale sont **interdites** par le garde d'exécution.
Leur comportement n'est donc pas qualifié par ce banc.

Le collecteur compilé est appelé douze fois sur ces mêmes objets : succès
après assemblage / réordonnancement / retour, refus de collection incomplète,
et refus après transfert complet vers le second modèle car les parents des
racines désignent encore le premier. Aucun reliaisonnement de parents n'est
injecté par le banc entre les opérations natives.

## Conséquences pour l'intégration

La liaison de correction ne doit pas survivre sans contrôle à un ajout, retrait,
transfert, redimensionnement du vecteur ou remplacement du modèle. Un compteur
positif seul ne prouve pas que la hiérarchie est encore celle attendue. Le
client observé dans `0x491130` retire les anciennes pièces avant de libérer son
modèle composé : invalider uniquement après cette libération serait trop tard.

Il reste à raccorder une invalidation avant mutation, reconnaître l'équipement,
qualifier les allocations et les destructions finales, puis tester le cycle
complet du client. Aucun hook de durée de vie n'est installé, aucun modèle du
jeu personnel n'est modifié et aucune bibliothèque Windows n'est chargée.

La [garde compilée de retrait](RETRAIT_LIAISON_MAINS.md) réalise maintenant le
retrait du registre sur notification explicite. La livraison de ces notifications
depuis les opérations du moteur demeure une étape distincte non implémentée.

Reproduction : `tools/model_membership_audit.py --library <LS3DF 1.12>`, avec
`--compiled-collection <image désactivée>` et `--json-output <rapport neuf>`.
Rapport privé : `.analysis/native-model-membership-v1-20261010.json`.
