# Test — reconstruction — Normandy3 Zone

Statut : **RESTE MULTIJOUEUR ; wrapper solo non lançable**.

## Origine et lacunes

Le dossier non publié possède treize fichiers propres, mais `loader.4ds`,
`map.4ds`, `scene.4ds` et `tree.klz` ne sont que des marqueurs de 16–19 octets,
et `volumy.bin` manque. `actors.bin` conserve 25 noms liés aux véhicules,
échelles et armes ; `scene2.bin` ne livre qu'un nom exploitable à l'audit. Il
n'existe ni entrée de catalogue, ni registre, ni spawn, ni objectif.

Le prototype MP existant complète huit bases depuis `Normandy3_MP` et demeure
une exploration Occupation. Cette fusion est une **DÉDUCTION**, non une carte
solo commerciale.

## Wrapper réservé

- **ORIGINE** : les six fichiers propres conservés; les fragments dégradés restent des preuves, pas des conteneurs jouables ;
- **DÉDUCTION** : les huit bases empruntées à Normandy3_MP, dont les remplacements complets de `actors.bin`, `scene2.bin` et `sounds.bin` ;
- **CRÉATION** : point de départ, équipe, acteurs, objectifs, volumes, textes et
  fin.

Nom réservé : `Test — reconstruction — Normandy3 Zone`. Aucun `scripts.dta`
n'est créé avant qu'une version fusionnée charge en solo avec collision et
volume. Tester d'abord la parité du prototype MP, puis seulement un départ solo
instrumenté. Spéculation : **3/3**.

La [comparaison des préfixes](../../NORMANDY3_MP_ZONE_TRUNCATED_CONTAINERS/ETUDE.md)
du 25 septembre 2026 refuse une simple concaténation avec les fichiers MP : les
trois fragments divergent, tailles déclarées comprises. Aucun fichier installé
n'a été modifié par cette étude.
