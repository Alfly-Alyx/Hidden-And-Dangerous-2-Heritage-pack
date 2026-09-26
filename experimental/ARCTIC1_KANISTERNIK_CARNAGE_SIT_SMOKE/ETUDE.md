# Arctic 1 — Kanisternik assis et fumant en Carnage

État : **variante minimale désactivée**, 15 septembre 2026. Le profil release
reste la référence ; la scène 4 restaurée n'est pas modifiée.

## Verdict

`Kanisternik`, le bidon, sa variante physique et `dummy_kanisternik_sit`
existent. La route Carnage des types 3/7 est active : dépôt du bidon, retour par
`Kanisternik_2` et `Kanisternik_3`, rotation vers le bidon, puis
`HUMAN_ACTIVITY_Smoke(true)`. Juste après se trouvent deux lignes commentées :
`HUMAN_ACTIVITY_Sit(sit)` et `HUMAN_SetAnim("%%kourimsed2",...)`.

La primitive `Sit` a de nombreux précédents actifs. Des scripts commerciaux
emploient aussi l'ordre **Sit puis Smoke** et coupent explicitement la fumée à
l'alarme. En revanche, `%%kourimsed2` n'a aucun usage actif dans le corpus ; sa
seule autre occurrence retrouvée est elle aussi commentée. Elle reste bloquée.

## Profils

| Profil | Corps | Statut |
| --- | --- | --- |
| `RELEASE_SMOKE_STANDING` | route et `Smoke(true)` inchangés | défaut |
| `CARNAGE_SIT_AFTER_SMOKE_EXACT` | ajoute seulement `Sit(sit)` à l'emplacement dormant | testable |
| `CARNAGE_SIT_THEN_SMOKE_COMPARABLE` | assise avant fumée, selon les précédents actifs | repli moderne, à comparer |
| `CARNAGE_SIT_KOURIMSED2` | assise + animation nommée | bloqué |

Le premier test doit être le delta exact sans animation nommée. Si `Sit` annule
la fumée, le repli comparable peut être essayé séparément ; les deux ne doivent
jamais être activés ensemble.

## Isolation de la scène 4

Le profil est gardé par le test de type Carnage 3/7. Il ne change pas
`OnSignal(5)`, que le profil release sans caméra et le profil caméra héritage
emploient pour libérer Kanisternik. Il n'ajoute aucun signal à la scène 4 et ne
modifie pas les caméras K4/K4a/K4b.

Si une cutscene 4 survient malgré le mode Carnage, l'activité expérimentale
doit être nettoyée au début et ne doit pas se relancer dans
`OnCutsceneDone(4)`. Le fichier source contient déjà deux emplacements de
handlers vides liés à la cutscene 4 ; leur structure doit être normalisée dans
une copie de test avant toute insertion.

## Interruptions

Le fragment
[`PROTOTYPE_CARNAGE_SIT_SMOKE_DELTA.scr.disabled`](PROTOTYPE_CARNAGE_SIT_SMOKE_DELTA.scr.disabled)
ajoute uniquement le contrat manquant : `Smoke(false)` avant la réaction
d'alarme, retour debout, et même nettoyage à la mort/cutscene. Il ne remplace
aucun mouvement, n'active pas `%%kourimsed2` et n'est pas un script complet.

## Tests

- types 3 et 7 : route, dépôt physique unique du bidon, position d'assise ;
- type normal : comportement strictement identique avec scène 4 release et
  avec `ARCTIC1_GUIDE_CUTSCENES_3_4` ;
- visibilité d'une seule cigarette/fumée, sans posture debout superposée ;
- alarme à chaque étape, arme disponible et fumée coupée ;
- sauvegarde avant le dépôt, pendant la fumée et assis ;
- mort avec/sans bidon en main, sans duplication physique ;
- retrait du profil : retour byte-for-byte au script release de la copie.

## Réalisation du 26 septembre 2026

Deux profils natifs exclusifs sont maintenant reconstructibles :
`arctic1-carnage-sit-after-smoke` et `arctic1-carnage-sit-before-smoke`.
Ils emploient le registre solo d'origine mais portent une qualification
**Carnage**, jamais une validation solo normale implicite. Aucun wrapper de
mission renommée n'est généré pour ce mode.

Le script commercial de 2 123 octets est épinglé, SHA-256
`0f7ed013bb4807e605fc1cf601a1d08857ee73172ac587eec027ec8d54bb3259`.
Les dérivés mesurent respectivement 3 064 et 3 052 octets. Acteur, liaison,
bidon et repère d'assise sont vérifiés dans leurs conteneurs typés. Aucun
nouveau propriétaire ni placement n'est créé.

Les deux variantes sont classées **MODERNE**, car leur protection de cycle de
vie dépasse le seul appel dormant. L'état d'activité n'est armé qu'en types 3/7
et avant le début de la fumée, pour couvrir aussi le délai de 1 450 ms précédant
l'assise historique. L'alarme nettoie la fumée et remet debout; la mort nettoie
sans imposer une posture debout au cadavre. Les routes, le bidon physique et le
signal 5 restent commerciaux.

Les deux handlers vides de cutscene 4 sont regroupés : lorsqu'elle interrompt
l'activité, le nettoyage efface l'état avant ses appels puis quitte vers
`TheEnd`. Une garde empêche toute nouvelle **assise expérimentale** après cette
cutscene; `OnCutsceneDone(4)` reste vide. Si la cutscene précède l'activité, les
gestes commerciaux ultérieurs ne sont pas réécrits : la garde interdit l'assise,
pas la fumée commerciale. Ce cas fait partie du protocole, pas d'un résultat
déjà acquis. Le chemin normal n'arme jamais les nouveaux états.

`%%kourimsed2` reste commenté dans les deux profils. Celui « après » compare
l'ordre dormant; celui « avant » applique le précédent générique avec les mêmes
protections modernes. Aucun des deux n'a été lancé en moteur, ni combiné avec
les caméras Heritage. Leur pose dans les copies d'essai est différée tant qu'un
client du jeu est ouvert.

### Sources internes conservées

- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_Kanisternik.scr` ;
- `.analysis/arctic1-full/MISSIONS/ARCTIC1/scene2.bin` ;
- scripts commerciaux utilisant `HUMAN_ACTIVITY_Sit` et
  `HUMAN_ACTIVITY_Smoke` ;
- [`ARCTIC1_GUIDE_CUTSCENES_3_4`](../ARCTIC1_GUIDE_CUTSCENES_3_4/PROPOSITION.md).
