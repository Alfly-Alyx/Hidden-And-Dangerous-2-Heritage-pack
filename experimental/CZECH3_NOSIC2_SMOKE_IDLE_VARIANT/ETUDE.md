# Czech 3 — pause fumée longue de nosic2

État du 25 septembre 2026 : profil reproductible désactivé
`czech3-nosic2-long-smoke`, comportement moteur non validé.

Le propriétaire `nosic2` est lié à `R_cz3_nosic2.scr`; le Patch fournit le script
effectif (8376 octets, SHA-256
`21acdd547b2eb96fa5c20b7759e530e553064b83e11386482b4f5b3b948d7b50`).
L'acteur est sérialisé. La frame `ja_patnik17`, déjà résolue par la variable
`smoker_eyeball_point`, existe dans la scène commerciale. Les quatre sources
nécessaires sont verrouillées dans le [catalogue](../reconstruction-variants.json).

## Variante exclusive

Après sa promenade autour du camion et son retour à `Chest16`, le porteur fume
déjà. Deux lignes historiques commentées le tournent vers `ja_patnik17` et
attendent 42 secondes; la version commerciale attend seulement 5 secondes.

La variante réactive ces deux lignes **en remplaçant** les 5 secondes, sans
addition des délais. La cigarette est arrêtée par l'appel existant juste après.
La manipulation des quatre caisses, leurs états physiques, les alarmes, la mort,
les signaux et la partie de cartes ne sont pas modifiés.

La pause et la rotation sont des vestiges **OFFICIELS**; leur restitution comme
comportement final voulu reste une **INFÉRENCE**. La pause augmente de 37 secondes
(plus la rotation) le délai avant les étapes suivantes. Le coordinateur actif
attend les deux signaux de disponibilité, sans délai maximal déclaré; cela ne
constitue pas une preuve que tout scénario de mission restera fluide.

## Essais requis

- Comparer témoin et variante depuis la même sauvegarde, avant la troisième caisse.
- Vérifier orientation, fumée, reprise au bout de 42 secondes et dépôt des quatre
  caisses sans duplication; observer ensuite les deux porteurs aux cartes.
- Déclencher alarme, mort et cinématique pendant la pause. Aucun geste ou son
  ne doit survivre anormalement à l'interruption.
- Sauvegarder/recharger avant, pendant et après la pause; terminer la mission.
- Refuser la promotion si la rotation vise un mauvais objet, si la cigarette
  reste attachée ou si le coordinateur attend indéfiniment.

La sélection se fait par deux [copies A/B séparées](../RECONSTRUCTION_BACKLOG/LABORATOIRES_DESACTIVES.md),
jamais par un second script sur le même acteur. Retrait : retirer la copie de
laboratoire; l'installation commerciale n'est pas touchée par les générateurs.
