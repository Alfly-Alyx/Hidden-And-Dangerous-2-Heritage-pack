# Ju 52 — décor fidèle et pilotage séparé

État : **décor commercial attesté ; pilotage non reconstruit**, 15 septembre
2026. Aucun asset n'est copié et rien n'est compilé.

## Décor

Le Ju 52 possède le meilleur contrôle positif : `la_Ju52`, `la_Ju52Af`, leurs
LOD et pièces sont conservés, et Africa 1 utilise activement `CUTjunkers` /
`CUTjunkersB` via `CUT_af1Ju52.scr` et `CUT_af1velit.scr`. Le premier banc est
la scène commerciale rejouée inchangée, avec capture des hélices, poussières,
animation, bascule d'acteur et nettoyage.

Le second banc `TEST_LOCAL_JU52_DECOR` instancie un décor séparé uniquement
après cette baseline. Son placement et son éclairage sont modernes ; il ne doit
pas remplacer ni perturber la scène Africa 1.

## Pilotage

La géométrie articulée, les sièges et caméras ne constituent pas un avion
pilotable. Modèle de vol, commandes, cockpit/HUD, roulage, décollage,
atterrissage, dégâts, sortie, IA et réseau manquent. `PROTOTYPE_JU52_PILOTAGE`
est un chantier distinct, verrouillé jusqu'à spécification complète et ne peut
être annoncé comme restauration.

Les scripts aéronautiques orphelins consignés dans le laboratoire ne doivent
pas être rattachés au Ju 52 sans propriétaire et séquence attestés.
