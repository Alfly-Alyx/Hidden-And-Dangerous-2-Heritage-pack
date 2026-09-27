# FG42 / ZK-383 : effets originaux et banque sonore privée

**27 septembre 2026 — ressources créées, aucune écoute ni validation en jeu.**
L'autorisation de créations modernes est appliquée explicitement : ces quatre
effets sont une **synthèse originale**, pas des enregistrements historiques,
des sons retrouvés ou des extraits d'une autre arme. Les symboles historiques
`FG42_F` / `FG42_R` restent non résolus.

## Génération reproductible

`build_modern_weapon_audio.py` lit uniquement les recettes modernes
`experimental/FG42/modern-audio.json` et
`experimental/GAROTA_AND_ZK383/modern-zk383-audio.json`. Aucun échantillon sonore
ni fichier du jeu n'est lu. Des couches de bruit déterministe filtré et de
tons variables produisent des candidats de tir et de manipulation. Leurs
durées, attaques et événements sont des choix artistiques : aucune unité
d'animation native ou synchronisation de rechargement n'en est déduite.

Format : **PCM mono, 16 bits, 22 050 Hz**, fichiers `.wav.disabled`. Les extrémités
sont nulles, la composante lente est filtrée et les crêtes sont réduites si
nécessaire à environ la moitié de l'amplitude numérique maximale. Cette marge
ne prouve ni une qualité d'écoute ni un équilibre dans le mixage du jeu.

| Effet moderne | Frames audio | Octets WAV | SHA-256 |
|---|---:|---:|---|
| FG42 tir, `MOD_FG42_F` | 13 230 | 26 504 | `38bf541c67b003a9f2f8296f87362b8b6cbe198c6e038d50e611423656547d05` |
| FG42 manipulation, `MOD_FG42_R` | 70 560 | 141 164 | `ae008c53c8d25e69b3d9ccdf6075126c8a43ec1fd3473fb0f3a1e647f4a585a4` |
| ZK-383 tir, `MOD_ZK383_F` | 9 922 | 19 888 | `f34f3b116d99077df3f8200d801a7739bcc0b5ba93170f716c84e00ebed4f2ae` |
| ZK-383 manipulation, `MOD_ZK383_R` | 70 560 | 141 164 | `cd6c9204b654155a2d525df79901e1c10a754a73cf64afa7667c5ae1d44ecd24` |

Les dossiers privés `FG42_ModernAudio_v1` et `ZK383_ModernAudio_v1` contiennent
chacun deux effets et leur manifeste. Les crêtes mesurées sont respectivement
16 384 / 5 751 / 13 312 / 5 511 sur l'échelle PCM signée. Aucun écrêtage.
**Ils n'ont pas été écoutés** : contrôle technique ne signifie pas qualité sonore.

## Ajout réversible dans une copie désactivée

`sound_definition_additive.py` ajoute uniquement des entrées **en fin** des
banques ordonnées 2 et 3. Il préserve les entrées vides, les variantes, les
ordres et tous les octets des entrées existantes. Les tailles des conteneurs
concernés sont recalculées. La section opaque 1050 reste identique, sans
prétendre connaître ou mettre à jour sa résolution symbolique.

Les libellés doivent commencer par `MODERN ` et les fichiers par `MOD_`.
Chemins, conflits insensibles à la casse, indices hors domaine, variantes
mal formées et reçus modifiés sont refusés. Le retrait vérifie l'empreinte
du résultat, les seules entrées de queue attendues, puis reconstruit exactement
les octets de départ. Il ne peut supprimer une entrée intermédiaire.

Le laboratoire `FG42_ZK383_ModernAudioLab_v1` possède **sept fichiers privés** :
quatre WAV originaux désactivés, une définition commerciale dérivée désactivée,
un manifeste et un avertissement de non-distribution. La définition effective
est celle de `Patch.dta`, SHA-256
`ab374c805b6bc663593bfd788f9e437b6998ffe8a3d02e83a393aa201dfd94f3`.
Elle passe de 104 700 à **105 200 octets**, SHA-256
`f857b1c83cc54b4dc4c79c5c55a4565c80fbf2229ce08aa363cad30de19f13e5`.
Ses **539 entrées et 672 variantes préexistantes sont inchangées** ; le retrait
en mémoire retrouve intégralement les 104 700 octets initiaux.

| Nouvelle association privée | Banque | Indice dans cette copie seulement |
|---|---:|---:|
| `MODERN FG42 SHOT` → `MOD_FG42_F.wav` | 2 | 55 |
| `MODERN FG42 RELOAD` → `MOD_FG42_R.wav` | 3 | 85 |
| `MODERN ZK383 SHOT` → `MOD_ZK383_F.wav` | 2 | 56 |
| `MODERN ZK383 RELOAD` → `MOD_ZK383_R.wav` | 3 | 86 |

Ces indices ne sont **ni réservés globalement ni attribués aux anciens symboles**.
Les six paramètres de variante sont adoptés séparément depuis les catégories
existantes `G MP40` et `G MP40 Reload`, avec empreintes et valeurs brutes dans
le manifeste. C'est un choix moderne explicite de réglages, pas un emprunt
de leurs sons ni une preuve de leurs unités physiques. Aucun WAV commercial lu.

L'inventaire examine **onze archives racine** et les fichiers directs de `Sounds` ;
aucun alias candidat en conflit. Pas de définition sonore libre dans l'installation
examinée. Une surcharge libre exige une exclusion explicite ; elle n'est pas
silencieusement composée ou écrasée. Les empreintes d'index ne sont pas présentées
comme des empreintes intégrales d'archives ou une preuve d'ordre de recherche natif.

Les routines natives bornées vérifient **quatre recherches numériques valides**
dans les nouvelles tailles de banques, ainsi que douze insertions synthétiques
ordonnées. **Le chargeur complet de définition, le mixeur et la lecture audio
ne sont pas exécutés.** Le [descripteur FG42 moderne](../FG42/DESCRIPTEUR_ET_TABLES.md)
est ensuite raccordé aux indices 55/85 dans un assemblage désactivé, avec
arguments natifs vérifiés. Le [ZK-383 moderne](../GAROTA_AND_ZK383/DESCRIPTEUR_ZK383_MODERNE.md)
est ensuite raccordé aux indices 56/86, également hors jeu et sans lecture audio.

## Reproduction et suites

```powershell
.\.venv\Scripts\python.exe tools/build_modern_weapon_audio.py --case FG42 --output-name FG42_AudioNeuf
.\.venv\Scripts\python.exe tools/build_modern_weapon_audio.py --case ZK383 --output-name ZK383_AudioNeuf
.\.venv\Scripts\python.exe tools/build_modern_audio_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name AudioLabNeuf
```

Les sorties vont uniquement sous `.analysis/modern-assets/`, avec refus d'un
dossier existant. Le troisième outil nécessite les dépendances privées
d'émulation. Aucun jeu, installateur ou lecteur audio n'est lancé.

**Dix-huit tests sur données inventées** couvrent le générateur, l'ajout/retrait,
les alias et les refus du laboratoire. Restent l'écoute et les retouches sonores,
le chargeur natif complet, le choix de politique symbolique,
les événements de tir/rechargement, les surcharges personnelles et
le déploiement isolé. Les sons ne rendent pas ces armes jouables.
