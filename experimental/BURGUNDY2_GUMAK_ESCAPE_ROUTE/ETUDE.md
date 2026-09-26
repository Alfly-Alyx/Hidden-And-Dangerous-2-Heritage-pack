# Burgundy 2 — itinéraire de fuite de Gumak

État : alternatives séparées, géométrie à vérifier, 26 septembre 2026.
Aucun parcours ou objectif modifié.

Le script solo `gumak.scr` est lié à l'acteur homonyme. Source SabreSquadron.dta,
6798 octets, SHA-256
`a0aa3631badec52686ba0b06cd0f28ed28f2f42d1e2a635cd65929d962ba5a84`.

La branche moto embarque au siège 0 de `bmw`, désactive les événements et
active la mauvaise musique. Elle conserve `HUMAN_Drive("citron1",40)`;
`bmv1` à 40 avant cet appel et `bmv4` à 30 après sont commentés. Dans les
checkpoints solo et coop, bmv1/bmv2/citron1 existent, **bmv4 est absent**.
La branche voiture utilise la Citroën puis bmv2 à 50 : le nom des parcours ne
suffit donc pas à attribuer une route exclusivement à un type de véhicule.

Une restauration des deux lignes n'est pas complète. Ajouter bmv1 tout en
laissant citron1 allongerait le trajet, au lieu de sélectionner une alternative;
ajouter bmv4 viserait un nom inexistant. Il faut d'abord mesurer les points,
virages, sorties et collisions dans l'éditeur, puis choisir une seule route.
Un nouveau bmv4 serait MODERNE et son nom ne lui donnerait pas une provenance
officielle.

## Coop : comportement retiré, véhicules encore présents

Le constat initial « véhicules retirés en coop » est corrigé. actors.bin coop
contient bien les records de modèle `bmw -> la_BmwR75` et
`la_citroen -> la_citroen`, tous deux de type 9. Ce sont les recherches de
véhicules et les branches auto/moto de **Gumak** qui ont été retirées du script
coop. D'autres scripts coop recherchent encore ces véhicules.

Le Gumak coop reste lié, mais son script de 5270 octets (SHA-256
`7c9be0b9f28bd6af082f30005d7345bbdad35de3de8ed334aaa62cc56dde3465`)
utilise une réaction et des valeurs de progression différentes : valeur 16
pour sa mort, contre 15 en solo; attente à 30 unités contre 15. Copier le solo
sur la coop n'est donc pas une simple restauration de route. La surcharge
Heritage installée est encore une baseline distincte, à préserver.

## Contrat à tester

Le détecteur solo `detect_motopryc` surveille déjà Gumak à moins de 20 unités
et envoie le signal 4 aux objectifs. Le choix auto/moto dépend aussi des valeurs
5/6/7/8/9 et de l'état des véhicules; les autres soldats consultent la valeur 9.
Ne pas ajouter une seconde détection d'évasion ou remettre les événements à
true sans analyser toute la chaîne.

Essais obligatoires : chaque véhicule disponible/volé/détruit, joueur près des
deux accès, types d'alarme distincts, conducteur tué pendant embarquement,
route bloquée, franchissement du détecteur, sauvegarde et objectif d'évasion.
La variante commerciale citron1 reste le défaut; la reconstruction de route
et l'adaptation coop devront rester deux options exclusives et séparées.
