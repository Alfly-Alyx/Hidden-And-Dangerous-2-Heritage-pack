# Burgundy 2 — ébauche caméra et scripts de passage

État : vestiges classés, 26 septembre 2026. Aucun raccord ajouté.

## Camery est une ébauche concurrente, pas huit plans manquants

Dans le solo, `camery.scr` est non lié/non accessible, 764 octets,
SHA-256 `0e7fc3228bd10f535009285036988718e83d8f052eb771fe6edf6e10878cd665`.
Il résout K1..K8, masque french1/2, lance la cinématique 1, attend 60000 ms,
ne joue que K1 puis attend 9900 ms. La déclaration des sept autres caméras
n'est pas une séquence à décommenter : leurs appels n'existent pas ici.

`panaci.scr` déroule déjà les huit plans K1..K8 avec leurs animations, voix et
nettoyage. `objectyves.scr` valide l'objectif 5 sur `OnCutsceneDone(1)`.
Une liaison de camery lancerait une seconde cinématique de même numéro,
masquerait des personnages et pourrait valider la progression au mauvais
moment. Elle reste exclue de l'
[adaptation du garde coop](../BURGUNDY2_COOP_GUARD_TO_SOLO/ETUDE.md).

Sources Sabre : panaci, 6223 octets, SHA-256
`095f2a406f43b522c828d04923844eb26ebef5b96dd5706699d24a9ca98e6834`;
objectyves solo, 3542 octets, SHA-256
`88f355e706dbb5137fed3090bd8bfc050110cae65b22915eb0421f71bb2a55a0`.

## Ge_pruchod n'a pas le même contenu selon la variante

Solo : 352 octets, SHA-256
`9bf2cccaecb9a38768c98af517826dff4d82290252a3014aca00e877b0033f57`.
Sans acteur ni liaison, il n'a pas de patrouille; il peut seulement suspendre
son propriétaire et désarmer événements/signaux selon la valeur 3. Le terme
« no-op » ne signifie donc pas qu'on peut l'attacher sans conséquence.

Coop : 1619 octets, SHA-256
`fc1715a025d3405a468f06a58429c93774baef4904061f8798240c4055cf076b`.
Acteur et liaison existent, avec la boucle `%%nuda` et pause 7000 ms. C'est un
script différent. Son import en solo est une ADAPTATION OFFICIELLE COOP VERS
SOLO, déjà étudiée, pas la reconstitution d'une patrouille solo connue.

## Ge_pruchod2 est une chaîne déjà raccordée

Les deux variantes possèdent acteur, liaison, `ge_pruchod2_1/_2` et les regards
correspondants. En coop, le contrôleur lié `detector_gepruchod` envoie signal 1
à ge_pruchod2 et trois autres gardes sur proximité 120. Il n'y a pas de nouvel
émetteur à inventer. Le script coop remplace la fumée solo par `%%nuda`;
les arrêts Smoke commentés ne prouvent pas une activité Smoke encore à lancer.

Sources Sabre : ge_pruchod2 solo 3318 octets,
`26c615ca1589c70be5397d9988b01299b7f5e90974e13951ca5ebdc00540a90b`;
coop 3353 octets,
`e8bc8c1cc289a7958d2661686f96005dddb90b8afbefafd4d13fcbcc1369cdde`;
détecteur coop 526 octets,
`0c7852e461409f001ef16635dfdee1d2d90f940bbf8caddc584147af8f064969`.

Les boucles d'animation et leurs interruptions restent à observer. Toute
alternative Smoke sera isolée des ajouts de
[sons animaux](../CO_BURGUNDY2_ANIMAL_AMBIENCE/ETUDE.md); aucune activation
collective des commentaires n'est justifiée.
