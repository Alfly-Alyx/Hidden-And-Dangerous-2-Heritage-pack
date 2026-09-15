# Arctic 1 — cinématiques 3 et 4 du guide

État : **deux variantes exclusives avant mission**, 14 septembre 2026. Les
fragments sont désactivés ; aucune mission n’est compilée ou installée.

## Verdict

R_Arc1A_rebel.scr conserve deux cinématiques complètes, mais force leurs
variables SKIP_CSC3 et SKIP_CSC4 à 99 avec le commentaire qu’elles ont reçu
l’ordre d’être supprimées. Les anciennes lectures des sauvegardes 29 et 30 sont
encore présentes juste au-dessus, commentées.

Les assets requis existent : K3/K3a/K4/K4a/K4b dans scene2, Roof_walker dans
actors, kanisternik dans scene2, et les pistes « kamera 3 » / « kamera 4 » dans
tracks.dat. Les scripts référencent aussi Auti_Bad, présent sous cette casse dans
leurs contrats de mission.

La solution sûre n’est pas un interrupteur en cours de partie. Elle produit deux
copies de mission choisies **avant** le démarrage :

- RELEASE_NO_CAMERA garde les constantes à 99 ;
- HERITAGE_CAMERAS restaure _LoadGameValue(29/30).

Un paquet ne doit contenir qu’une des deux versions de R_Arc1A_rebel.scr.

## Équivalence des effets de jeu

Pour la scène 3, la branche release envoie dabing 9 puis Roof_walker signal 1.
La cinématique envoie les mêmes deux événements dans le même ordre, autour des
plans K3a/K3 et de la piste kamera 3.

Pour la scène 4, la release envoie dabing 10, vyprostovani signal 1 et
kanisternik signal 5. La cinématique envoie les mêmes trois effets, avec
kanisternik avant vyprostovani, pendant les plans K4a/K4/K4b et kamera 4. Cette
différence temporelle est historique et ne doit pas être normalisée.

## Sauvegardes et interruptions

Le guide initialise les valeurs 29/30 à 0. Plusieurs scripts de gardes/toit
mettent 29 à 99 lorsque la scène du toit doit être sautée. Les scripts des roues
et l’organisateur du camion mettent 30 à 99 quand la scène véhicule n’est plus
valide. La variante Heritage doit donc **lire** ces valeurs au moment prévu ;
elle ne doit jamais forcer la caméra si le monde a invalidé sa cible.

Les deux fichiers disabled documentent les deux substitutions exclusives. Aucun
nouvel identifiant de sauvegarde, frame, piste ou signal n’est ajouté.

## Tests

1. Nouvelle mission release : confirmer zéro caméra 3/4 et tous les dialogues,
   signaux et objectifs habituels.
2. Nouvelle mission heritage : confirmer scène 3 après le marais et scène 4
   après la route du camion, caméra rendue au joueur à chaque fin.
3. Tuer/alarmer Roof_walker et les autres écrivains de 29 avant la scène : elle
   doit suivre la branche release sans caméra.
4. Détruire roues/camion et déclencher les écrivains de 30 : même exigence pour
   la scène 4.
5. Vérifier Auti_Bad et kanisternik, les pistes audio, le skip manuel, mort du
   guide, sauvegarde/reprise avant/pendant/après chaque cinématique.
6. Vérifier qu’aucun signal dabing/Roof/vyprostovani/kanisternik n’est doublé.

Retour arrière : replacer la copie RELEASE_NO_CAMERA. Les valeurs 29/30 déjà
inscrites dans une sauvegarde ne sont pas migrées et les tests utilisent des
sauvegardes jetables distinctes.

