# MG 34 portative — reconstruction additive

État : **fiche de tir et ressources partielles, reconstruction moderne**, 26 septembre 2026.
Aucune entrée Weapon ni modèle n'est créé et rien n'est compilé.

La munition `AMMO MG 34`, des icônes et des sons associés subsistent. Ils
n'établissent ni modèle portable, ni animation FPV, ni entrée Weapon
fonctionnelle. La chaîne `AMMO MG 34 - tank version` et le MG34 monté actif sont
un système différent ; aucun modèle, réglage ou binding du char ne doit être
renommé ou détourné pour fabriquer la version portative.

La ligne 32 de `item_shoot.tbl`, offsets **4656–4791**, conserve une fiche de
tir de 135 octets. Le [parseur complet](../RECONSTRUCTION_BACKLOG/TABLES_EDITEUR.md)
en fixe les limites. Les paramètres restent bruts et le slot natif 32 est
occupé par un casque ; ni cette fiche ni le montage de char n'autorisent sa reprise.

Une reconstruction additive exige d'abord des modèles nouveaux FPV/tiers/sol,
une série d'animations, puis un slot libre audité. Cadence, alimentation,
dispersion, recul, bipied, rechargement, sons, IA et réseau sont des choix
modernes. Le premier banc autorisé est statique et muet, sous préfixe `TEST_`.

Tests ultérieurs : coexistence avec le TANK MG34, inventaire, dépôt/reprise,
bipied éventuel, tir soutenu, animation IA, sauvegarde et hôte/client. Toute
collision de nom, de munition ou de son avec la version montée bloque le cas.
