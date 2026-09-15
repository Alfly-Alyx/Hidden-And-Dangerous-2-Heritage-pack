# Laboratoire décoratif d'aéronefs

État : **architecture TEST/PROTOTYPE désactivée**, 15 septembre 2026. Aucun
modèle commercial n'est copié, aucune mission n'est créée ou compilée et aucun
installateur n'est modifié.

## But

Le laboratoire visualise un modèle à la fois comme décor statique. Il sépare
strictement :

- `TEST_LOCAL_*` : chargement, matériaux, échelle, orientation, LOD et
  collision sur une scène locale dédiée ;
- `PROTOTYPE_MP_*` : même modèle dans une autre scène, uniquement après succès
  local, pour vérifier apparition, collision et nettoyage hôte/client.

Il ne crée ni siège utilisable, ni cockpit/HUD, ni moteur de vol, ni armement,
ni trajectoire autonome. Les ressources sont résolues depuis l'installation
possédée du testeur et ne sont jamais redistribuées.

## Ordre

1. Ju 52 : rejouer d'abord la scène Africa 1 officielle comme contrôle positif.
2. Charger en local un seul modèle/LOD par profil.
3. Mesurer bounds, pivot, sol, collision, textures et nœuds nommés sans les
   interpréter comme systèmes fonctionnels.
4. Répéter en MP dans une mission séparée ; aucun basculement de profil à chaud.
5. Retirer le profil et confirmer l'absence de ressource ou état résiduel.

Les positions de laboratoire, socles, éclairages, caméras de visite et scripts
de sélection seraient des créations modernes. Ils doivent porter les préfixes
`TEST_` ou `PROTOTYPE_` et ne jamais reprendre un nom d'acteur commercial.

## Acceptation d'un décor

Chargement stable, textures correctes, échelle et orientation documentées,
collision non bloquante, LOD vérifiable, sauvegarde/reprise propre et état MP
identique sur hôte/client. Cette acceptation ne change jamais le statut
« présent non pilotable ».

[`MANIFEST.md`](MANIFEST.md) inventorie les huit familles de modèles.
[`LAB_SELECTOR.plan.disabled`](LAB_SELECTOR.plan.disabled) fixe les profils.
[`ORPHAN_SCRIPTS.md`](ORPHAN_SCRIPTS.md) met en quarantaine les scripts qui ne
doivent pas servir de raccourci vers le pilotage.
