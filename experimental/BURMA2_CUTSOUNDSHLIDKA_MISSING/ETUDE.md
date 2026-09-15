# Burma 2 — `CUTSOUNDSHLIDKA.scr` manquant

État : **reconstruction bloquée, aucun prototype**, 15 septembre 2026. Aucun
fichier de mission, registre ou archive n'est modifié.

## Verdict

Le binding commercial est exact :

```text
l_b2str_4 -> CUTSOUNDSHLIDKA.scr
```

Le porteur `l_b2str_4` existe toujours dans `sounds.bin`, mais le script cible
est absent de `Scripts.dta`, `Patch.dta`, `SabreSquadron.dta` et des autres
archives installées vérifiées. Ce n'est pas une réactivation stable.

L'étude prouve la position du porteur, son échantillon, l'événement de
cinématique probable et la règle de nettoyage sûre. Elle ne prouve toutefois
pas **quels porteurs le script pluriel pilotait, dans quel ordre, avec quels
délais et quels arrêts intermédiaires**. Aucun fichier `.scr.disabled` n'est
donc créé. Les conditions de réouverture figurent dans
`REOPEN_GATES.plan.disabled`.

## Nature et position de `l_b2str_4`

`l_b2str_4` n'est ni un quatrième soldat ni une frame visuelle : son nom
n'apparaît pas dans `scene2.bin` ou `actors.bin`. Il s'agit d'un acteur sonore
sérialisé dans `sounds.bin`, à la position monde :

```text
x = -1.398, y = 6.820, z = -26.195
```

Cette position se trouve à environ 1,44 m de `CUThlidka1`/`CUTh1_start`,
3,77 m de `CUThlidka2` et 3,57 m de `CUThlidka3`. Elle justifie un son spatialisé
du groupe de patrouille au début de la cinématique 1.

Correction de l'étude préliminaire : le record `l_b2str_4` référence
**`l_b2str1.wav`**, pas `l_b2str4.wav`. Cet échantillon dure 2,955 s. Le nom de
frame et le numéro du WAV ne constituent donc pas une paire homonyme.

## Pourquoi un script mono-son serait faux

Les cinq acteurs `l_b2str*` forment une disposition cohérente avec les deux
phases de la patrouille :

- `l_b2str_4` et `l_b2str_5` sont proches des trois positions de départ à
  `z ≈ -25` ;
- `l_b2str_2` et `l_b2str_3` sont proches des trois positions atteintes après
  37 s à `z ≈ 21–26` ;
- le porteur racine `l_b2str_` est isolé à `x ≈ 289` et ne permet aucune
  déduction sûre sans contexte de secteur.

Les mappings exacts, positions et durées figurent dans
[`SOUND_POSITION_MATRIX.md`](SOUND_POSITION_MATRIX.md).

Le nom `CUTSOUNDSHLIDKA` est pluriel et le script est attaché à `_4`, premier
porteur proche du chef, mais un script propriétaire peut résoudre et piloter
d'autres frames. Le découpage spatial rend plausible une séquence de plusieurs
cues avant et après le téléport. Réactiver seulement `_4` au temps zéro serait
donc une création moderne arbitraire, même si son WAV propre tient avant la
première voix.

## Contrôleurs de patrouille

`CUTHLIDKA1.scr`, `CUTHLIDKA2.scr` et `CUTHLIDKA3.scr` réagissent tous à
`OnCutscene(1)`. Ils affichent les gardes, les placent sur `CUTh1/2/3_start`,
lancent leurs animations et attendent 37 s. Ils téléportent ensuite le groupe
vers `dummy_VelitelEngZA`, `dummy_engvtab` et `dummy_backman4`, puis changent
d'animation. `OnCutsceneDone(1)` arrête les animations et cache les acteurs.

Le porteur `_4` est donc rattaché sans ambiguïté à la même cinématique. Mais ces
scripts ne lui envoient aucun signal et ne contiennent aucun identifiant
`l_b2str*`. Ils attestent deux phases et une terminaison globale, pas les
timecodes audio internes.

`CUTDABING.scr` commence les voix à 5 s et enchaîne dix-sept répliques jusqu'à
environ 53,5 s. `CUTSCENE.scr` pilote onze plans jusqu'à environ 59,4 s. Le WAV
propre à `_4` pourrait être joué entièrement avant la première voix, mais les
autres WAV associés au groupe durent de 2,307 à 5,817 s ; leur ordre et leur
chevauchement avec le dialogue restent inconnus.

## Comparables commerciaux

Aucun autre fichier `CUTSOUNDS*.scr` ou équivalent exact n'a été retrouvé dans
les scripts commerciaux extraits. Les contrôleurs de cinématique comparables
activent généralement les frames sonores explicitement aux changements de plan
avec `FRM_SetOn(..., true)`, les coupent lors du cue suivant et les forcent à
OFF dans `OnCutsceneDone`. Cette convention justifie une future structure de
nettoyage, mais pas le choix des frames ni des délais Burma 2.

## Données manquantes

Une variante exige encore au moins une source pour chacun des points suivants :

1. liste des `l_b2str*` effectivement pilotés par le script perdu ;
2. délai de départ de chaque cue et ordre avant/après 37 s ;
3. mode one-shot/boucle et moment d'arrêt de chaque porteur ;
4. comportement lors d'un skip ou d'une interruption de cinématique ;
5. preuve que les cues ne doublent pas une ambiance déjà active ni les voix.

La fin globale est justifiable (`OnCutsceneDone(1)` doit tout couper), mais
elle ne compense pas l'absence des quatre premiers contrats. Le statut reste
donc `BLOCKED`.

## Sources internes

- `.analysis/burma2-audit/MISSIONS/BURMA2/scripts.dta` ;
- `.analysis/burma2-audit/MISSIONS/BURMA2/scene2.bin` ;
- `.analysis/burma2-audit/MISSIONS/BURMA2/actors.bin` ;
- `.analysis/burma2-audit/MISSIONS/BURMA2/sounds.bin` ;
- scripts Base Burma 2 `CUTSCENE.scr`, `CUTDABING.scr` et
  `CUTHLIDKA1/2/3.scr` ;
- étude préliminaire conservée sous
  [`BURMA2_MISSING_CUTSOUNDSHLIDKA`](../BURMA2_MISSING_CUTSOUNDSHLIDKA/ETUDE.md).
