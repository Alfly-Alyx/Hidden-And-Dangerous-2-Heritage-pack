# Ge17 — double route au signal 2

État : **variantes sélectionnables désactivées**, 15 septembre 2026. La séquence
commerciale, son animation de recherche d'arme et sa destination `ge17_04`
restent le socle commun. Aucun script actif n'est remplacé et rien n'est
compilé.

## Chaîne officielle

Au signal 2, ge17 se lève, observe, rejoint `ge17_02`, s'accroupit, joue
`%%manipulzbran`, se relève, se tourne et joue `%%protahovani`. Deux primitives
sont ensuite commentées autour des rotations et avant `%%hledamkulomet` :

- `HUMAN_Move("ge17_03")` ;
- `FRM_TeleportNearCheckpoint(me,"ge17_03","ge16_sniper")`.

Après ce vestige, la release conserve la recherche d'arme durant quinze
secondes, rejoint `ge17_04`, se tourne et joue `%%sedila1`. Les checkpoints
`ge17_03`, `ge16_sniper` et `ge17_04` existent.

## Variantes

[`ROUTE_SELECTOR.plan.disabled`](ROUTE_SELECTOR.plan.disabled) propose trois
profils exclusifs :

- `RELEASE_GE17_04` : aucune primitive restaurée ;
- `MOVE_GE17_03_THEN_GE17_04` : mouvement déterministe vers `ge17_03`, puis
  toute la fin commerciale inchangée ;
- `TELEPORT_RANGE_THEN_GE17_04` : téléport entre `ge17_03` et
  `ge16_sniper`, puis même animation et `ge17_04`. Ce profil est secondaire et
  bloqué lorsque ge16 peut occuper son poste fidèle.

Les deux primitives commentées ne sont jamais actives ensemble. La variante
Move est la meilleure candidate : ge17 démarre près de ces points et le trajet
est court. Le téléport ajoute de l'aléatoire et partage une borne avec le poste
réservé à ge16 ; son existence textuelle ne garantit pas qu'il doive coexister
avec la restauration ge16.

[`PROTOTYPE_ROUTE_OPTIONS.scr.disabled`](PROTOTYPE_ROUTE_OPTIONS.scr.disabled)
conserve les deux deltas séparés et répète explicitement le tronc final commun.

## Tests

1. Capturer la release complète du signal 2, notamment la continuité de
   `%%hledamkulomet` et l'arrivée à `ge17_04`.
2. Tester Move seul dix fois, avec alarmes avant/pendant/après `ge17_03` et
   sauvegarde pendant le déplacement.
3. Tester Téléport séparément, ge16 fidèle d'abord désactivé puis actif ; tracer
   position choisie, collisions et occupation de `ge16_sniper`.
4. Vérifier dans chaque profil que les animations, délais, rotations,
   `ge17_04`, `%%sedila1` et la réaction d'alarme restent identiques.
5. Revenir à Release sans modifier checkpoints ni acteur.

Rejet : activation simultanée Move/Téléport, disparition de l'animation,
absence de `ge17_04`, collision avec ge16, position aléatoire invalide ou
différence après reprise.

## Recette complète — 26 septembre 2026

`alps1-ge17-move-before-final-post` reconstruit le script de 2511 octets depuis
la source de 2513 octets, SHA-256
`9222687af260c0af902f470922d2e8f67f81bb8473bca9edae86d23992281314`.
Seuls les deux octets de commentaire devant le mouvement vers `ge17_03`
sont retirés. Acteur, liaison et points 02/03/04 sont vérifiés. Le téléport
reste commenté; tous les octets de la recherche d'arme et de la fin sont
conservés. La variante téléport n'est pas promue par cette recette.

## Sources

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_17.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/check2.bin` ;
- `experimental/ALPS1_GE17_AMBIGUOUS_REPOSITION/` ;
- `experimental/ALPS1_GE24_SHARED_SNIPER_POST/`.
