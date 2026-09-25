# Arctic 4 — destination d'alarme de Static Guard 3

État : première reconstruction **expérimentale et désactivée**, 25 septembre
2026. Le profil commercial demeure la référence. Cette étude ne modifie ni la
mission installée ni l'installateur du Heritage Pack.

## Constat commercial

La mission `arctic4` contient 124 liaisons de script. La liaison exacte
`Static_Guard_3` → `R_Arc3_static_guard_3.scr` est présente. Le script actif
reçoit l'alarme, interrompt la conversation des deux gardes, coupe la cigarette,
arrête le mouvement courant, règle course/IA zombie/portées, attend deux
secondes puis termine son gestionnaire. Une seule ligne placée entre ces deux
dernières opérations est commentée :

```text
//  HUMAN_Move("StaticGuard3_5");
```

`StaticGuard3_5` existe dans `check2.bin`, au même titre que les points 1 à 4
de la ronde et les points 6/K de la conversation. Aucun script de surcharge
pour ce garde n'a été trouvé dans `Patch.dta`; l'exécutable commercial utilise
le script de `Scripts.dta`. L'audit de fermeture d'Arctic 4 trouve zéro script
affecté manquant et zéro checkpoint manquant pour les appels actifs.

## Deux profils exclusifs

| Profil | Opération à l'alarme | État |
|---|---|---|
| `release_free_combat` | La ligne reste commentée; la réaction commerciale est inchangée. | Défaut. |
| `legacy_alarm_destination` | La seule ligne `HUMAN_Move("StaticGuard3_5")` est réactivée à sa place d'origine. | Prototype désactivé. |

Le choix s'effectue sur une **copie du script** dans une variante de mission,
avec l'unique liaison de `Static_Guard_3`. Il ne faut pas ajouter un second
propriétaire, un deuxième gestionnaire `OnAlarm` ou un nouveau signal. La ligne
réactivée est **OFFICIELLE** en tant que vestige textuel et le checkpoint est
**OFFICIEL**; l'affirmation qu'elle reproduirait un comportement final voulu
par les développeurs reste une **INFÉRENCE**. La géométrie et le trajet exact
du checkpoint ne sont pas encore contrôlés en moteur.

La séquence de conversation `OnSignal(1)` est distincte : elle utilise les
points 6/K et attend le signal 2 du contrôleur de dialogue. Le profil d'alarme
ne touche ni ces points ni les signaux. Le garde 2 pointe vers le garde 3 pour
ce dialogue; le garde 3 signale les deux snipers à sa mort. Ces interactions
doivent survivre dans les deux profils.

## Fabrication contrôlée du prototype local

Depuis la racine du dépôt :

```powershell
.\.venv\Scripts\python.exe experimental\ARCTIC4_STATIC_GUARD3_ALARM_POST_ADDITIVE\build_variant.py --game "D:\Games\Hidden and Dangerous 2"
```

L'outil lit l'archive commerciale légitime, vérifie l'empreinte du script,
l'unique liaison et le checkpoint, puis écrit une copie
`.analysis/generated/arctic4-guard3-fixed-post.scr.disabled`. Ce chemin est
ignoré par Git. Il refuse un fichier de sortie existant, une archive différente
ou une surcharge commerciale inattendue. Il n'installe rien dans le jeu.

Exécution du 25 septembre 2026 : 2 506 octets générés, SHA-256
`6e1a366e75794249aa437b3577b50c45c32376409ddde197f9b57a306c17817c`.
Le diff avec l'extraction commerciale ne comporte que la suppression des deux
caractères `//` devant `HUMAN_Move("StaticGuard3_5")`.

## Contrôles encore nécessaires

1. Mesurer le point 5 et les collisions autour dans un éditeur ou en moteur;
   la seule présence du nom dans `check2.bin` ne suffit pas à prouver un chemin
   praticable.
2. En solo, comparer l'alarme lorsque le garde fume, se déplace, parle au
   garde 2 et se trouve loin du point 5. Consigner position finale, durée et
   réaction de combat.
3. Déclencher mort et alarme simultanément, puis vérifier le contrôleur de
   dialogue et les signaux vers Sniper 1/2.
4. Reprendre une sauvegarde avant et pendant l'alarme; vérifier que le profil
   commercial redevient identique après retrait de la variante.
5. Tester les modes Carnage et coopération uniquement s'ils utilisent la même
   mission et la même liaison, sans présumer que le script solo s'y applique.

Tant que ces essais ne sont pas documentés, le prototype reste désactivé et
aucune intégration dans l'installateur n'est autorisée par cette étude.

## Provenance vérifiée

- `Scripts.dta::SCRIPTS/ARCTIC4/R_Arc3_static_guard_3.scr` : 2 508 octets,
  SHA-256 `73e72535024bedf65787ae3fda305724ab1386c6941c9809ea786fbe9a41208b`;
- `missions.dta::MISSIONS/ARCTIC4/actors.bin` : 16 359 octets,
  SHA-256 `280aa09645a1610db10c2708263f4d1dc7b35694f99d48872388039c7f77fdfb`;
- `missions.dta::MISSIONS/ARCTIC4/check2.bin` : 138 281 octets,
  SHA-256 `8fae6ee23121e58f8cb95628f6a20069e7243488a0ef9b6f4484eaf937b4da9f`;
- registre `missions.dta::MISSIONS/ARCTIC4/Scripts.dta` : liaison exacte du
  garde au script;
- position initiale du garde dans `actors.bin` :
  `(-58.356277, 11.104563, -47.424149)`; cette position ne donne pas la
  position du checkpoint 5.

Méthode de reproduction : `tools/dta_archive.py`,
`tools/script_binding_audit.py`, `tools/mission_closure_audit.py` et
`tools/scene_frame_position_audit.py`.
