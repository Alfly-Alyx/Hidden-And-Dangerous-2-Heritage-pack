# Norway — garde 3 et chaîne d'ambiance dormante

État du 25 septembre 2026 : **documenté, activation bloquée**. Aucun prototype
installable ni nouveau propriétaire; ne pas copier les quatre gestionnaires
voisins dans le seul but de faire disparaître un avertissement statique.

## Faits commerciaux

`tirpic_guard_3` existe dans les acteurs Patch et possède une liaison unique
vers `R_Nor_Tirpic3.scr`. Ses checkpoints `T3_1` et `T3_2` sont nommés dans le
fichier Base. Le script de 1167 octets a l'empreinte
`d8f1da063b3cc5b89f1ade520b48a18cdc8faf4873490910ab9926b67baf2471`.
Il est accessible depuis le registre commercial.

Il n'a aucun gestionnaire `OnSignal(1..4)`. Il désactive explicitement les dix
catégories d'alarme, fixe la vue à 400, suspend l'acteur et possède un réveil à
60 m. Sa mort désactive les signaux et termine le script; les modes 3/7
neutralisent l'acteur. Aucune de ces particularités ne doit être remplacée par
le profil d'alarme du garde 4.

Le sender contient une émission vers le garde 3, mais **n'est ni lié ni
accessible** dans la fermeture statique des scripts : 81 racines, 87 scripts
accessibles sur 102. L'absence de récepteur ne démontre donc pas un bug visible
de la mission commerciale. En outre, le sender attend 10 secondes au départ,
puis calcule `waiter` dans sa boucle sans jamais attendre cette valeur.

## Comparaison utile, pas transplantation automatique

Le garde 4 fournit les primitives chapeau, bouteille, froid et regard, mais il
possède aussi un compteur de segment et des labels de retour que le garde 3
n'a pas. Sa bouteille utilise une frame vide. Copier les handlers avec leurs
`goto go_back` produirait donc une variante structurellement incomplète.
Les deux frames de regard `dummy_see1/2` existent; choisir laquelle pour le
garde 3 reste une décision moderne non justifiée par son script actuel.

## Conditions avant reconstruction

1. Observer le garde commercial : réveil, ronde effective, comportement pendant
   les événements de mission et raison éventuelle de ses alarmes neutralisées.
2. Résoudre un propriétaire unique du sender et sa cadence dans une copie de
   test. Ne pas relier le sender brut, qui n'attend pas dans sa boucle.
3. Définir une reprise de ronde propre au garde 3, sans importer le compteur ou
   les alarmes d'un autre garde; vérifier interruptions, mort et sauvegarde.
4. Pour une variante moderne minimale, étudier d'abord le froid générique seul.
   Chapeau, bouteille et regard exigent des vérifications supplémentaires.
5. Mesurer séparément cadence et probabilités; l'émission 4 a une probabilité
   de 9/12 par tirage de signal, chacun des autres 1/12, si l'API aléatoire a
   le domaine habituel observé dans le corpus. Ce n'est pas une cadence mesurée.

L'[audit en lecture seule](../../tools/audit_norway_guard_chain.py) reproduit les
faits de liaison, de dépendances, de noms et de délai. Sept tests sur données
inventées empêchent notamment de prendre un délai commenté pour un délai actif
ou un nom de checkpoint pour une identité d'acteur. Il ne simule pas le jeu.
Voir aussi l'[étude des gardes absents](../NORWAY_MISSING_TIRPITZ_GUARDS_1_2_6_7_12_13_16/ETUDE.md),
corrigée pour les checkpoints réellement présents et les gardes 10/17.
