# Lecture native des tables FPV — preuve hors moteur

**27 septembre 2026.** `tools/fpv_table_oracle.py` vérifie désormais les boucles
natives de lecture des groupes, des treize états, des quatre canaux, des noms
et des valeurs FPV. Cette preuve complète le calcul d'indices déjà établi ;
elle ne charge toujours aucune animation ou scène dans le jeu.

## Exécution bornée

L'image privée du client 1.12 et l'exécutable original sont vérifiés par les
empreintes du [contrat natif](CONTRAT_NATIF.md). L'oracle indépendant valide la
racine et initialise une portée déjà ouverte à l'octet 6. Le parcours natif va
de **0x490e00 à 0x4910ef**, avant la fermeture du fichier.

Les lecteurs natifs de conteneurs, fermeture de portée, chaînes à compteur
de références et scalaires s'exécutent réellement. Seuls lecture, déplacement
dans le fichier et allocation sont remplacés par des opérations **en mémoire**.
Les écritures de fichier sont interdites ; le tampon source est immuable.
Les fonctions natives d'ouverture, les appels système, les chargeurs de
ressources/scènes et la lecture d'animations ne sont pas exécutés.

Les limites sont explicites : tampon d'entrée de 1 Mio maximum, allocations
de chaîne dans une arène de 1 Mio, lectures individuelles au plus 1 024 octets,
budget d'instructions et de temps. Un nom de plus de **998 octets** est refusé
avant exécution : le lecteur natif copie au plus 999 octets avec le zéro final.
Les destinations natives et mémoire non revues sont refusées.

## Résultats privés

| Source contrôlée | Groupes | États | Canaux de conteneur | Noms/valeurs effectivement chargés |
|---|---:|---:|---:|---:|
| Base originale | 255 | 3315 | 13260 | 546 |
| Sabre originale | 277 | 3601 | 14404 | 601 |
| Fragment moderne propriétaire 459 | 1 | 13 | 52 | 13 |
| Sabre avec ajout 459 désactivé | 278 | 3614 | 14456 | 614 |

Pour chaque cas, le curseur final retrouve la taille exacte du fichier et la
profondeur revient à la racine. Les noms, longueurs, compteurs de références,
valeurs brutes et emplacements concordent avec le lecteur indépendant.
Le rapport privé est `.analysis/fpv-table-traversal-20260927.json`.

L'oracle contrôle le tableau entier de **26 000 cellules** à chaque passage,
y compris les cellules non occupées. Les noms initialement vides restent
nuls. Les valeurs vides sont initialisées avec le témoin **0x5a5a5a5a** et
doivent rester identiques : c'est un témoin de contrôle, **pas une valeur par
défaut native démontrée**. Les autres membres du tableau ne changent pas.

## Intégration au laboratoire de tables

Le constructeur de [tables complètes](TRANSACTION_TABLES.md) exécute maintenant
les deux oracles par défaut lors de sa commande de construction : objets et
FPV. Les variantes privées `BenelliTables_Sabre_v2` et
`BenelliTables_PatchX01_v2` contiennent les reçus dans `MANIFEST.json`.

Chaque variante vérifie **500 emplacements / 273 objets**, puis **278 groupes /
614 références FPV**. Leurs quatorze fichiers de contenu conservent les octets
des variantes v1 ; seuls les manifestes de contrôles changent. Aucun fichier
de jeu n'est installé ni activé, et les versions v1 restent conservées.

Onze tests synthétiques supplémentaires couvrent les noms tronqués, les
formes refusées, les lectures/déplacements bornés, les allocations, l'ordre
des groupes, les reçus et l'intégration des deux oracles. Ils ne sont pas
présentés comme une validation en jeu.

## Suites encore nécessaires

Les noms lus ne prouvent pas encore la résolution des ressources, les mains,
la caméra, les poses, les événements, les sons synchronisés ou le gameplay.
L'initialisation réelle du système FPV et l'ouverture effective des fichiers
restent à tester dans le moteur. Les contrats de sauvegarde complète,
d'identifiant et de déploiement isolé restent distincts.

```powershell
.\.venv\Scripts\python.exe tools/fpv_table_oracle.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --json-output '.analysis/fpv-table-traversal-nouveau.json'
```

Le rapport ne peut pas écraser un fichier existant. Les surcharges libres
sont signalées/empreintées, mais ne sont ni fusionnées ni modifiées.
