# Tutoriel — troisième passage SW2

État : chaîne documentée, variante à trois actions non activable, 25 septembre 2026.

## Propriétaire existant, protocole incomplet

Les quatre frames `dummy_SW1`, `dummy_SW2`, `dummy_SW3`, `dummy_SW_counter`
existent dans `scene2.bin`. SW1/SW3 sont liés et envoient 1/3 au compteur. SW2
n'a aucune liaison; son script libre détecte le joueur à une unité puis envoie 2.
Le compteur commercial ne reçoit que 1 et 3, positionne deux drapeaux puis envoie
1 à `TUT_Instructor1_aid` quand ils sont réunis. Le nom `counter2` correspond
donc au troisième passage, pas à un récepteur historique de signal 2.

SW2 n'est pas une position inutilisée : `TUT_Instructor1.scr` l'utilise comme
cible de caméra pendant la cinématique 1. Lui ajouter une liaison ne donne pas
le droit de déplacer cette frame ou de modifier cette caméra. L'accessibilité
du rayon d'une unité sur le parcours réel n'a pas été testée.

| Scripts.dta, `scripts/tutorial/` | Octets | SHA-256 |
|---|---:|---|
| `tut_dummy_sw1.scr` | 227 | `5d4c0ffa5f2f43ac6ba6dbf753186cd1ea5df6f1b4bf1d9fd0ed13315bd11204` |
| `tut_dummy_sw2.scr` | 212 | `73c10108e74fedbbff6208af6754fe4083aad3ea6dc56d859eb3cf0d2d6c9950` |
| `tut_dummy_sw3.scr` | 226 | `bda594bcb8f6b87ca5e81db381d049fb0ec7cccd75b9bc0bc0429be0e22ada9e` |
| `tut_dummy_sw_counter.scr` | 418 | `b70056790c9c6af69cbc39d83bd11a352fadc8cc59e1022d4296570277248054` |

## Architecture proposée, explicitement moderne

Deux copies exclusives avant chargement : commerciale 1+3 inchangée, laboratoire
1+2+3 avec une liaison SW2 et un compteur modifié **ensemble**. Trois indicateurs
distincts mémoriseraient les passages, un quatrième empêcherait une seconde
validation; compter seulement le nombre de signaux autoriserait les répétitions
d'un passage à remplacer une étape manquante. La barrière devrait être posée
avant l'émission finale vers l'instructeur.

Ne pas ajouter un second compteur à côté du commercial, ni conditionner le
parcours commercial à SW2. Ne pas exporter le compteur à trois actions sans
la liaison et la preuve d'accessibilité du détecteur : cela pourrait bloquer le
tutoriel. Aucun registre, objectif ou numéro de sauvegarde n'est modifié ici.

Essais requis : parcours 1+3 commercial, tous les ordres de 1/2/3 dans la variante,
passages répétés, entrée pendant l'introduction, sortie du rayon, reprise entre
chaque étape et déclenchement final unique. Si le rayon historique n'est pas
accessible, une position/règle moderne doit être étudiée sans déplacer la cible
de caméra partagée. Aucun prototype complet n'est fourni avant cette vérification.
