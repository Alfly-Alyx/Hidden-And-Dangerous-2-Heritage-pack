# Lecture des ressources audio — état du 26 septembre 2026

Le lecteur Python prend désormais en charge le DPCM mono PCM16 des archives
ISD0/ISD1 : sept tables de deltas, types 8/12/16/20/24/28/32, en-tête WAV au
premier bloc, échantillon initial indépendant dans chaque bloc, accumulation
16 bits avec débordement conforme à la référence. Les types non reconnus,
formats stéréo ou en-têtes non canoniques sont refusés, pas approximés.

Référence GPL : M3tox/HD2unpacker, révision
`882ceb8bb2f8473f1295f3a7a8e6c6a038ccf5f6`, ISDM.cpp/ISDM.h, déjà conservée
localement dans `.research/HD2unpacker`. Attribution dans
[THIRD_PARTY.md](../../THIRD_PARTY.md). Les 896 constantes ont été comparées
une à une; empreinte binaire little-endian de la table :
`fcbd0350caeecc42d5373255b5335da50c2423259184a6526bb22d9edf01e2e2`.

## Audit sans export

```powershell
.\.venv\Scripts\python.exe tools\audit_audio_resources.py "D:\Games\Hidden and Dangerous 2\Sounds.dta" --match "*l_Af2pour??.wav" --match "*l_a4palm2.wav"
```

L'[outil](../../tools/audit_audio_resources.py) lit seulement les ressources
sélectionnées, calcule durée/format/empreinte et ne sauvegarde aucun WAV.
L'état du décodeur est local à chaque fichier, y compris lors de lectures
répétées du même fichier. Le lecteur C# et l'installateur ne sont pas modifiés.

| Ressource dans Sounds.dta | Octets | Durée PCM, s | SHA-256 décodé |
|---|---:|---:|---|
| `SOUNDS/l_a4palm2.wav` | 126508 | 2,867664 | `76a6ee13c96d52599ef16c4ed19a87ff86630bab51e05217a7aadfe63b181a68` |
| `SOUNDS/l_Af2pourm1.wav` | 292410 | 6,629615 | `4c88c645cd55321b91c06a6f669e5556f15d7a681f17a40d64464595e2307f7d` |
| `SOUNDS/l_Af2pourm2.wav` | 194092 | 4,400181 | `bba3ad68fd9f85f316ac0fd5ba355213d16e612660cbc6b7f4fc944f0d28f09b` |
| `SOUNDS/l_Af2pourm3.wav` | 143660 | 3,256599 | `846cf2041a338e18050b3f48ca739384aa8c0aa217c042d12dc164f7d4d2c92a` |
| `SOUNDS/l_Af2pourm4.wav` | 192426 | 4,362404 | `faf571cda5effbfac35e331d505401b57d68a1363694eaa0ecc11d67937dc69d` |
| `SOUNDS/l_Af2pourw1.wav` | 166956 | 3,784853 | `4fad88cf57e0092758887e9508419f46ad1525399ffa20bbf7b345a2a28d9a37` |
| `SOUNDS/l_Af2pourw2.wav` | 149676 | 3,393016 | `01087bf944db41812c24ea7e0c6adfb1fbd6ad80670deefb972ccb8a3d55273c` |

Les sept fichiers sont mono, 16 bits, 22050 Hz. Tailles DTA, RIFF et nombre de
trames concordent. Ils ont été décodés en mémoire, **pas écoutés**, et aucun
audio commercial n'est ajouté au dépôt.

## Portée des tests

Dix-sept tests synthétiques couvrent les sept tables, signe/débordement,
changement de table, reprise indépendante de chaque bloc, les deux formats DTA,
réinitialisation entre fichiers, tailles incorrectes, troncatures, stéréo et
formats inconnus refusés, non-régression brut/LZSS et métadonnées PCM.
La suite du projet compte 208 tests réussis après cet ajout.

Ces contrôles ne prouvent ni les secteurs audio du moteur, ni la spatialisation,
ni la synchronisation labiale, ni le comportement de SetOn pendant une lecture.
Une ressource décodée n'autorise pas à relier un contrôleur orphelin ou à diffuser
le fichier hors de l'installation possédée.
