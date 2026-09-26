# FG 42 — reconstruction lourde moderne

État : **fiche de tir attestée, chaîne exploitable absente**, 26 septembre 2026.
Aucun prototype d'arme fonctionnelle n'est activé et rien n'est compilé.

Le [modèle extérieur moderne](MODELE_MODERNE.md) est maintenant fabriqué :
25 pièces, deux LOD, aperçu et format natif désactivé contrôlés. Il ne change
pas le statut de l'arme fonctionnelle ; la vue FPV reste à créer.

Le catalogue ancien marque explicitement le FG 42 `DISABLED` et la munition
objet 196 subsiste. La ligne 27 de `item_shoot.tbl` conserve aussi une fiche
de 135 octets, noms `FG 42`, `FG42_F`, `FG42_R`. Leurs présences ne prouvent
pas les fichiers audio correspondants. Les [limites exactes](../RECONSTRUCTION_BACKLOG/TABLES_EDITEUR.md)
sont contrôlées par le schéma, non par une fenêtre de texte. Aucun modèle,
icône, animation FPV, son spécifique ni entrée Weapon exploitable n'est identifié.
Le slot natif 27 est devenu un casque : il reste interdit.

L'implémentation doit compléter l'ensemble visuel, audio et fonctionnel, choisir
un slot libre et documenter chaque paramètre comme moderne. Un premier banc ne
peut montrer qu'un modèle original nouvellement créé sous préfixe `TEST_`; il ne
doit pas utiliser l'apparence d'une autre arme comme substitut de restauration.

Avant une arme jouable : modèles FPV/tiers/sol, animations, icône nouvelle si
la redistribution l'exige, sons, balistique, chargeur, cadence, recul,
dispersion, dégâts, inventaire, IA, sauvegarde et réseau.
