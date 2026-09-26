# Co_Burgundy3 — fermeture des scripts et références du dépôt

État au 26 septembre 2026 : **preuve structurelle complétée, pas de nouveau
correctif de jeu**. La comparaison d'ambiance reste dans son
[dossier séparé](../CO_BURGUNDY3_REMOVED_AMBIENT_CONTROLLERS/ETUDE.md).

## Verdict

- **OFFICIEL** : 57 liaisons dans `mpscripts.dta`, 57 scripts accessibles sur
  67 disponibles, aucune dépendance littérale manquante. Les dix non accessibles
  sont exactement les scripts d'ambiance déjà étudiés.
- **OFFICIEL** : 94 appels Move/Drive, 80 noms de checkpoint distincts, tous
  présents comme tokens terminés dans `check2.bin`. Cela ne prouve pas les trajets
  physiques, collisions ou comportements après interruption.
- **OFFICIEL** : six barils sont des nœuds du modèle du dépôt, pas des acteurs
  supprimés. Ne créer ni faux checkpoint ni copie de baril.
- **INFERENCE** : le signal 1 commenté chez le maquis est un protocole abandonné,
  pas un raccord nécessaire au comportement coop actuel. Aucun décommentage.
- **MODERNE** : seul l'outil d'audit est ajouté; aucun script de jeu ne change.

## Le signal 1 ne désigne pas le même destinataire

Le maquis `maquis01` est lié à `bur3_maquis01.scr`. Son `OnSignal(1)` est
commenté, mais son **OnAlarm actif rejoint déjà DESTROY**. Cette branche désactive
les signaux entrants, attaque `BUR3_vybuch` pendant 300 ms, lui envoie signal 1,
puis fuit par `maquis_escape` et se suspend.

`BUR3_vybuch` est un dummy réel de la scène, lié à `bur3_vybuch.scr`. Son
**OnSignal(1) est actif** : explosion, six particules sur les barils et mort
conditionnelle des gardes 22/23 à distance strictement inférieure à 16.
Ne pas confondre ce protocole avec la variante solo à distance 15 en cinématique.

Aucun des 67 scripts coop ne contient de recherche littérale de `maquis01`
ni d'appel actif `_SignalPistolFired()`. Cette absence est une preuve de source,
pas une preuve absolue sur les événements moteur ou d'éventuels alias dynamiques.

La version solo du maquis, 1274 octets, SHA-256
`44a90a52b6be9a57d6ca39c245616bfef3adf808bb268f41260af5b3bc088ac0`, attend
`_SignalPistolFired()` **ou `_SignalReceived(22)`**, pas le signal 1.
Elle enregistre la valeur 70, attaque le dépôt réel, attend 1 s et peut forcer
son état à zéro; la cinématique 4 assure ensuite la route sonore. Copier cette
logique en coop ajouterait un protocole différent, pas une ligne oubliée.

### Réentrance à observer, pas à corriger aveuglément

Le maquis désactive les signaux, mais ce fait ne démontre pas que l'événement
OnAlarm ne peut jamais le réinterrompre. Le récepteur d'explosion ne contient
pas de verrou explicite `DisableSignals(true)` ni de drapeau anti-rejeu.
Cela constitue un **risque à tester**, pas un défaut reproduit. Ne pas ajouter
d'émetteur, de second accès par fusée ou de verrou sans mesure des événements.

## Les éléments de géométrie sont retrouvés

Neuf références de l'ensemble des scripts sont des nœuds exacts du
`scene.4ds` commercial : trois poutres `F_b_p_tram301/303/304`, les trois portes
`F_door_wood00/01/02`, `f_b_door_00`, `f_b_door_05` et `f_b_futra_06`.
Leur ascendance est décodée, pas déduite d'une recherche de sous-chaîne.

Dans `actors.bin`, `la_bu3_FuelStorage_01` est un **record typé modèle 9** dont
la ressource 0x2012 est `la_bu3_FuelStorage`. Le record lightmap séparé
`la_bu3_FuelStorage_01.Mesh05` ne constitue pas un second acteur.

| Cible suffixe du dépôt | Index 4DS | Parent |
|---|---:|---|
| `f_Sud34` | 37 | 1, `Mesh05` |
| `f_Sud30` | 33 | 1, `Mesh05` |
| `F_SudB07` | 83 | 1, `Mesh05` |
| `F_SudB14` | 90 | 1, `Mesh05` |
| `F_SudB19` | 95 | 1, `Mesh05` |
| `F_SudB27` | 103 | 1, `Mesh05` |

Les six sont des frames visuelles de type 1. Le modèle provient de
`SabreSquadron.dta`, pas de `models.dta`; il fait 54457 octets, SHA-256
`b24bdeb7b0af5b8dbe4e0bb95a904b2cec5dff1fa78ff717c64f7ef0802a0385`.
La résolution moteur du nom instance.nœud et les positions monde ne sont pas
validées par cette seule présence structurelle.

## Audit reproductible et provenance

```powershell
.\.venv\Scripts\python.exe tools\audit_co_burgundy3_closure.py --game "D:\Games\Hidden and Dangerous 2" --archives-only
```

L'[audit](../../tools/audit_co_burgundy3_closure.py) lit **73 sources** : 67
scripts, cinq fichiers de mission et un modèle. Il rapporte chaque provenance,
taille et empreinte sans écrire de fichier. Le registre coop est sélectionné
explicitement; aucun registre solo n'est fusionné avec lui. Les références de
modèle ambiguës, cycles/parents absents, surcharges PatchX01 et modèle modifié
sont refusés. Le générateur de variantes garde ses restrictions de chemins.

| Source, toutes dans SabreSquadron.dta | Octets | SHA-256 |
|---|---:|---|
| `mpscripts.dta` | 2029 | `78e1ae06d70ee4e587d633c196f07d1b9942314cb7fe5d136376b4c79207fe82` |
| `actors.bin` | 20767 | `b5a16eac58352fb9cce5fd614fb53d5046dfcfe5e651d191de11457d66487751` |
| `scene.4ds` | 2699031 | `2493ebbb26c31fcf9497cd8d0d0988ae541b83ae8775f526067388561c6ea798` |
| `scene2.bin` | 5006340 | `4e0b3b14f4d6e14d331585a869f254b1a07c57a29a45c3330eca4c39b10ddf25` |
| `check2.bin` | 167246 | `27865b651bf20141eb17fca2a3e89d5cbee3ee096815985ed18f470a7899bd9a` |
| `bur3_maquis01.scr` | 805 | `f115b65f88eabcffef044366e2c7b9abbe7dbbe64e8ac5d482d8cf994b418c1a` |
| `bur3_vybuch.scr` | 1408 | `0b9edab91007478c444c25d3ab691e2d37e900f1a9a21f9a47c779d53db05c6c` |

Le mode strict refuse les surcharges Heritage préexistantes de `bur3_obj3.scr`
et `bur3_objectives.scr`. `--archives-only` les exclut en consignant leurs
empreintes, sans modifier les corrections de prisonniers/objectifs déjà installées.

Quatorze tests synthétiques couvrent les distinctions modèle/lightmap/parent,
noms exacts, doublons, ascendance, commentaires, sélection de registre, provenance
et surcharges. Suite complète : **222 tests réussis**.

## Suite en environnement de test isolé

1. Observer l'alarme initiale, la fuite et l'explosion commerciales.
2. Compter signaux/explosions pendant plusieurs alarmes et sur hôte/clients.
3. Vérifier les six ancrages de particules et les deux gardes à 16 unités.
4. Sauvegarder/reprendre avant/après l'alarme et pendant la fuite.
5. Préserver les objectifs Heritage; tester l'ambiance dans sa variante séparée.

Aucune validation de mission jouable ou conversion solo n'est revendiquée ici.
