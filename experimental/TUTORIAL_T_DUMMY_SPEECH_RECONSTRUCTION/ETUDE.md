# Tutorial — reconstruction de `T_dummy_speech`

État : **reconstruction additive spécifiée, position de Talker_02 moderne**, 14
septembre 2026. Aucun fichier de mission n'est modifié et aucun script n'est
rendu actif par cette étude.

## Verdict

La chaîne vocale est suffisamment complète pour un essai contrôlé : le porteur
`T_dummy_speech`, le premier interlocuteur, les deux scripts de personnages, le
script de conversation et les huit ressources vocales subsistent. Il manque
toutefois l'acteur `TUT_Talker_02`, son record d'inventaire et son transform.

Une variante laboratoire peut donc recréer **un seul** second interlocuteur et
réutiliser les scripts officiels sans les modifier. Elle ne doit pas être
qualifiée de restauration fidèle tant qu'une source commerciale ne fournit pas
le corps, l'équipement, le parent et le transform originaux de Talker_02.

## Chaîne officielle conservée

L'audit effectif de Tutorial trouve 114 bindings et 146 scripts disponibles.
`T_dummy_speech.scr` et `TUT_Talker_02.scr` sont non liés ; le premier possède
un frame homonyme libre, le second aucun acteur homonyme.

| Élément | Source commerciale | État |
| --- | --- | --- |
| `T_dummy_speech` | `scene2.bin` | frame présent et sans autre binding |
| `T_dummy_speech.scr` | `Scripts.dta` | conversation complète, non liée |
| `TUT_Talker_01` | `actors.bin`, `items.dat` | acteur et item présents |
| binding 01 | `scripts.dta` | `TUT_Talker_01 -> TUT_Talker_01.scr` actif |
| `TUT_Talker_02.scr` | `Scripts.dta` | script complet, non lié |
| `TUT_Talker_02` | mission effective | absent de `scene2.bin`, `actors.bin`, `sounds.bin` et `items.dat` |

La recherche ciblée dans `missions.dta`, `Patch.dta`, `SabreSquadron.dta` et
`Scripts.dta` ne retrouve le nom `TUT_Talker_02` que dans son script et dans
`T_dummy_speech.scr`. Elle ne fournit donc aucun record de scène ou d'acteur
duquel déduire une position.

## Dialogue et branches

Le porteur déclenche à sept unités et arrête les deux voix lorsque le joueur
sort de dix unités. La variable `goodone` est initialisée à 1 et n'est jamais
modifiée dans le fichier conservé.

| Branche | Ordre des voix | Statut probatoire |
| --- | --- | --- |
| positive | 00990123 sur Talker_01, puis 00990130 et 00990131 sur Talker_02 | **OFFICIEL et atteignable** |
| négative | 00990124, 25, 26 sur Talker_02, puis 00990127 et 28 sur Talker_01 | **OFFICIEL mais dormant** |

Les huit fichiers `Tables\Dabing\*.dat` existent dans `LangEnglish.dta` et les
huit WAV correspondants dans `Sounds.dta`. Leur présence ne prouve pas une
logique de sélection perdue : le prototype minimal conserve `goodone = 1` et
n'ajoute aucun calcul de performance.

## Transforms attestés

Les deux transforms suivants proviennent de la mission commerciale effective :

| Frame | Position `(x, y, z)` | Quaternion `(w, x, y, z)` |
| --- | --- | --- |
| `T_dummy_speech` | `(-58.333748, 1.182707, -4.988830)` | `(0.897916, 0, -0.440166, 0)` |
| `TUT_Talker_01` | `(-55.596886, 1.144970, -5.522693)` | `(0.345661, 0, 0.938359, 0)` |

Leur distance est de 2,79 unités : le premier interlocuteur est déjà bien dans
le volume de déclenchement officiel. Le contrôleur conserve aussi son échelle
commerciale `0.300557` sur les trois axes ; il ne doit être ni déplacé ni
dupliqué.

## Reconstruction minimale

Créer une copie de mission distincte, par exemple
`Tutorial — Talker_02 (test)`, désactivée par défaut. Dans cette copie seulement :

1. copier la structure d'acteur humain et le schéma d'item de `TUT_Talker_01`
   sous le nom exact `TUT_Talker_02` ; ce choix de corps et d'équipement reste
   **MODERNE**, même si le donneur est officiel ;
2. appliquer le script officiel `TUT_Talker_02.scr`, qui impose déjà le visage
   `e_f073` et gère rotation, animation et signal de mort ;
3. ajouter uniquement les bindings `TUT_Talker_02 -> TUT_Talker_02.scr` et
   `T_dummy_speech -> T_dummy_speech.scr` ;
4. conserver sans changement le binding et le script de `TUT_Talker_01` ;
5. utiliser le placement candidat détaillé dans
   [`PLACEMENT_ET_TESTS.md`](PLACEMENT_ET_TESTS.md) ;
6. ne pas activer la branche négative et ne pas ajouter de latch avant d'avoir
   mesuré le comportement de réentrée du script original.

Cette méthode restitue la conversation conservée, pas l'apparence historique
du personnage disparu.

## Risques particuliers

- `TUT_Talker_01` possède déjà d'autres dialogues, notamment après le signal
  20 de `ControlorOne` : un chevauchement audio est possible ;
- les deux talkers envoient le signal 16 à `dummy_objectives` à leur mort ; le
  récepteur met l'objectif 7 en échec, d'où un test obligatoire des deux morts ;
- le script de conversation ne contient pas de monostable persistant : une
  sortie puis une nouvelle entrée peuvent réarmer l'événement ;
- la position candidate se trouve près de plusieurs éléments de décor et doit
  être vérifiée pour le passage, la collision et la ligne de vue ;
- une sauvegarde chargée dans une autre variante ne doit jamais conserver un
  état propre au prototype.

## Sources internes

- `missions.dta : MISSIONS\TUTORIAL\scene2.bin`, `actors.bin`, `items.dat`,
  `scripts.dta` ;
- `Scripts.dta : SCRIPTS\TUTORIAL\T_dummy_speech.scr`,
  `TUT_Talker_01.scr`, `TUT_Talker_02.scr`, `TUT_Objectives.scr` ;
- `LangEnglish.dta : Tables\Dabing\00990123, 24, 25, 26, 27, 28, 30,
  31.dat` ;
- `Sounds.dta` : les huit WAV portant exactement ces identifiants ;
- `.analysis/binding-tutorial-check.json`.
