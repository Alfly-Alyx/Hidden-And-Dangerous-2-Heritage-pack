# Poses partielles et mélange natif : objet synthétique

**27 septembre 2026.** Après le [calcul des canaux](CALCUL_ANIMATION_NATIF.md),
un second banc examine leur assemblage et leur écriture sur un **objet inventé**.
Il ne charge pas de modèle, de squelette, de scène ou de ressource commerciale.

## Domaine effectivement exécuté

Même `LS3DF.dll` épinglée, même contrôle x87 synthétique `0x027f`.
Départ `0x1001eed0`, parcours des huit emplacements de canaux, puis arrêt
`0x1001fac7` **avant le traitement des événements**. L'objet possède déjà sa
rotation sous forme de quaternion, drapeau `0x08`. Le pointeur de pose
supplémentaire est nul. Le chemin de reconstruction depuis une matrice,
les callbacks et les autres instructions non examinées sont refusés.

Le domaine accepte zéro à huit emplacements, chacun actif/inactif, poids
float32 entre 0 et 2, jusqu'à trois clés par canal. Les transformations
initiales sont fournies explicitement. Le poids 2 contrôle le branchement
« supérieur à 1 » : il ne prouve pas que le jeu l'utilise normalement.
Seuls les drapeaux `0x08` et `0x88` sont admis ; cette borne n'est pas une
description exhaustive des types de nœuds du moteur.

Les entrées sont en lecture seule ; les seules écritures hors pile autorisées
sont les champs de transformation et de drapeaux de l'objet synthétique.
Le budget est de 12 000 instructions et une seconde par pose. Les compteurs,
la pile, les entrées et les champs non concernés sont contrôlés.

## Règles établies sur ce domaine

1. Un emplacement inactif ou de poids nul ne contribue pas.
2. Chaque canal — position, rotation, échelle — possède son propre accumulateur.
   Son premier contributeur de poids strictement positif est copié, **même
   si ce poids est très petit** : il n'est pas mélangé avec la pose initiale.
3. Un contributeur suivant de poids inférieur à 1 mélange le résultat courant
   vers sa valeur. Les positions/échelles sont linéaires ; les rotations utilisent
   Slerp. À partir de 1, il remplace le résultat. **L'ordre des emplacements compte.**
4. En l'absence de contributeur, les octets du canal de l'objet sont conservés.
   Le code ne remet pas automatiquement le canal au repos et ne lui injecte
   ni identité ni première clé d'une autre animation.
5. Le bit `0x80` empêche l'écriture de la position dans ce chemin, sans empêcher
   les canaux de rotation ou d'échelle. Son nom fonctionnel global n'est pas deviné.
6. Une rotation écrite passe par la normalisation native `0x10030540`, avec
   choix de l'antipode à W non négatif. Si plusieurs contributions de rotation
   restent accumulées, une normalisation supplémentaire précède la copie.
   Une rotation absente reste intacte, même si son W initial est négatif.

La non-normalisation de Slerp et la normalisation lors de l'application sont
**deux étapes différentes**, pas des conclusions contradictoires.
Une contribution de rotation qui remplace les précédentes remet son compteur
à 1 ; les compteurs de position et d'échelle, eux, comptent les contributions.
L'écriture d'échelle copie aussi un quatrième mot voisin depuis la pile ; le
banc ne lui attribue pas de signification géométrique.

## Preuve et limites

Le corpus comprend **586 poses** : deux objets sans contributions, 480
variantes d'un emplacement parmi les huit, 80 mélanges de deux emplacements,
16 ensembles partiels de huit et huit ensembles de huit rotations.
Il couvre les deux drapeaux admis, les canaux absents, les poids nuls/petits/
unitaires/supérieurs à un, l'ordre inverse, les clés et leurs frontières.
Les **168 cas écrivant une rotation** passent par l'auxiliaire de normalisation.
Le premier rapport privé `ls3d-native-pose-20260927.json` constate un résidu nul.
La reprise `ls3d-native-pose-v2-20260927.json` retrouve ces résultats en ajoutant
le comptage exact des appels de normalisation et la comparaison octet par
octet des canaux absents ou verrouillés.

Douze tests du dépôt portent sur des données inventées : absence, ordre,
verrouillage de position, normalisation, compteurs, conservation des entrées,
bornes et refus des chemins hors périmètre. Ils ne lisent pas la bibliothèque.

**Ce résultat ne prouve pas encore l'héritage Benelli en situation réelle.**
Il manque notamment l'initialisation de l'objet par le chargeur, le choix et
la durée de vie des emplacements, les éventuelles poses supplémentaires et
le chemin matrice. Il serait donc incorrect de compléter les pistes manquantes
avec le modèle au repos en prétendant reproduire le moteur. Le skin, la caméra,
les événements et les interactions entre états d'arme restent séparés.

```powershell
.\.venv\Scripts\python.exe tools/ls3d_pose_audit.py --library 'D:\Games\Hidden and Dangerous 2\LS3DF.dll' --json-output '.analysis/poses-natives-nouveau.json'
```

Rapport neuf obligatoire, aucune modification ou exécution de l'installation.
