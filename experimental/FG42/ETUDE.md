# FG 42 — reconstruction lourde moderne

Le [contrôle des paramètres du 27 septembre](../RECONSTRUCTION_BACKLOG/PARAMETRES_TIR.md)
conserve explicitement `FG42_F` et `FG42_R` comme références symboliques
non résolues. Aucune conversion silencieuse en numéros ou en zéro.

Deux [effets synthétisés originaux](../RECONSTRUCTION_BACKLOG/SONS_MODERNES.md)
sont maintenant construits sous les nouveaux alias `MOD_FG42_F/R`, avec un
ajout privé réversible dans les banques numériques. Ils ne résolvent pas
les symboles historiques et ne sont encore ni écoutés ni raccordés à un Item.

[Mouvements originaux des pièces](../RECONSTRUCTION_BACKLOG/ANIMATIONS_MODERNES.md) :
neuf séquences construites, sans mains ni liaison au personnage. Les besoins
FPV et animations de personnage mentionnés ci-dessous restent ouverts.

État : **fiche de tir attestée, chaîne exploitable absente**, 26 septembre 2026.
Aucun prototype d'arme fonctionnelle n'est activé ni intégré aux tables du jeu.

Le [modèle extérieur moderne](MODELE_MODERNE.md) est maintenant fabriqué :
25 pièces, deux LOD, aperçu et format natif désactivé contrôlés. Il ne change
pas le statut de l'arme fonctionnelle ; les modèles FPV et banques de mains
construits ensuite restent privés, sans cadrage moteur ou gestes qualifiés.

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
