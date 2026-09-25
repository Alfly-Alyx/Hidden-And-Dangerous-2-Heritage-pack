# Co_Burgundy2 — ambiance animale additive

État : **comparaison scène/registre construite et désactivée**, 25 septembre 2026.
La coop release n'est pas modifiée.

## Correction de l'inventaire

Les scripts `Br2_SND_kun.scr` et `Br2_SND_prase.scr` sont bien orphelins en
coop. Les porteurs `zwukkun`, `zwukprase` et le cheval `d_horse_` sont absents.
En revanche, l'audit binaire trouve encore dans
`Co_Burgundy2/sounds.bin` les frames `S_kun1`, `S_kun2` et `S_prase`, avec les
références suivantes :

- `S_kun1` → `L_BR3KUN1.WAV` ;
- `S_kun2` → `L_BR3KUN2.WAV` ;
- `S_prase` → `L_BR3PIG.WAV`.

Les trois WAV existent dans `LangEnglish.dta`; `L_BR3KUN3.WAV` existe aussi,
mais n'est pas demandé par les deux scripts. Copier de nouveaux sons par-dessus
les frames coop serait donc inutile et risquerait un doublon.

## Variante proposée

Nom : `Co_Burgundy2 [Ambiance animale — Reconstruction]`.

Dans la copie coop :

1. copier depuis Burgundy2 les deux porteurs de scène `zwukkun` et
   `zwukprase`, avec leurs transforms exacts ;
2. les lier aux deux scripts coop déjà livrés ;
3. réutiliser les trois frames sonores déjà présentes dans la coop ;
4. copier `d_horse_` avec son item et son transform solo seulement si le test
   d'écoute confirme que l'image sonore sans cheval visible est incohérente ;
5. ne raccorder l'animal à aucun objectif ni compteur.

Le cheval est un décor officiel du solo, mais son import visuel reste une
option indépendante des porteurs sonores. Aucun cochon acteur distinct n'est
prouvé par les données citées ; ne pas en inventer un.

## Cadences officielles et garde moderne

Le cheval choisit un des deux sons puis attend aléatoirement 6,5 à 11,5 s. Le
cochon attend 8 à 17 s puis active `S_prase`. Les scripts utilisent
`FRM_SetOn(..., true)` sans extinction explicite ; la durée du son doit donc
ramener la frame à un état rejouable.

Une garde anti-boucle ne sera ajoutée qu'après observation d'un chevauchement.
Ce serait une correction `MODERNE`, pas une partie de l'import fidèle.

## Tests réseau et audio

### Import exact local réalisé

Le profil binaire `co-burgundy2-animal-ambience` de
[`build_burgundy_ambient_patch.py`](../../tools/build_burgundy_ambient_patch.py)
copie uniquement les deux records dummy `zwukkun` (163 octets) et `zwukprase`
(165 octets). Leurs positions, quaternions, échelles, parent `Primary sector` et
bornes sont repris octet pour octet. Le groupe passe de 2910 à 2912 records.
Le registre coop **`mpscripts.dta`** passe de 127 à 129 paires, les anciennes
paires restant identiques. Aucune duplication de script, son, cheval ou cochon.

L'outil contrôle huit fichiers de mission épinglés, l'ensemble des **122 scripts
coop** par empreinte composée, et les deux scripts solo de comparaison :
**132 sources** sont consignées. Toute collision de nom/liaison, source différente,
record non dummy ou transform parental non trivial est refusé. Retirer les
ajouts et rétablir les seules longueurs doit retrouver exactement les témoins.

Deux différences importantes avec Burgundy 3 interdisent une assimilation :

- `Br2_SND_prase.scr` est identique solo/coop, mais le cheval ne l'est pas.
  Le solo fait 421 octets, SHA-256
  `cc1cdc83b2057cc9a3f5ed053422340b6405f61f6ab17c6b1cab0f4d4a7ef6e3`;
  la coop 329 octets, SHA-256
  `a1418cb289f131aa8d9c0c41334b2a61ad355188e8a34764350c89782d4ea9a8`.
  La coop a retiré `Whenever ticho(_SignalReceived(1))`, qui met les deux frames
  sonores à zéro. **Le script coop est conservé**, sans réintroduire ce handler.
  La seule exception d'identité autorisée est cette paire d'empreintes exacte.
- `sounds.bin` n'est pas identique. Le record `S_prase` l'est; `S_kun1/2`
  inversent l'ordre des références de secteur `Primary sector` et
  `sector Rectangle18` dans leur bloc 0x4060. Les autres champs de ces deux
  records sont identiques. Aucune équivalence moteur n'est supposée pour cet
  ordre : les données coop sont réutilisées **sans réécriture ni normalisation**.

| Sortie variante locale | Octets | SHA-256 |
|---|---:|---|
| `scene2.bin.disabled` | 13278572 | `f84ad6e5a8481d1b4642ea7b8f2ba2d6cf97c093302839e2974d0b35d2719048` |
| `mpscripts.dta.disabled` | 5341 | `80cf0349c282758b152fccee433420191bf71839cd9a72056a8311b25c905261` |

La comparaison se trouve uniquement dans
`.analysis/scene-patches/co-burgundy2-animal-ambience.scene-patch.zip.disabled`.
Elle contient deux témoins, deux variantes et un rapport désactivés : **pas une
mission activable, pas une conversion solo, pas un installateur**. Aucun fichier
commercial complet n'entre dans Git. Les surcharges préexistantes `ge_cesticka.scr`
et `gumak.scr` sont refusées en mode strict, ou exclues et empreintées avec
`--archives-only`; elles ne sont pas modifiées.

```powershell
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --profile co-burgundy2-animal-ambience --archives-only
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --profile co-burgundy2-animal-ambience --archives-only --build
```

Les 19 tests communs vérifient les garde-fous binaires, l'exception de script
strictement bornée et le maintien des exigences d'identité de Burgundy 3.
Les sorties Burgundy 3 ont été recalculées : leurs octets n'ont pas changé.

### Essais restant obligatoires

- vérifier portée, atténuation, occlusion et spatialisation aux transforms solo ;
- observer au moins cinquante tirages de chaque porteur ;
- tester deux clients proches et un client hors portée ;
- vérifier si l'hôte seul pilote le hasard ou si chaque client double les sons ;
- sauvegarder/reprendre pendant une pause et pendant une lecture ;
- tester cheval visible/invisible indépendamment ;
- refuser la variante en cas de boucle continue, empilement réseau ou son sans
  source spatiale cohérente.
