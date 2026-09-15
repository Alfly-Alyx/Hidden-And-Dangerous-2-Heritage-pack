# Co_Burgundy2 — ambiance animale additive

État : **priorité basse, import de porteurs à préparer**, 14 septembre 2026.
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

- vérifier portée, atténuation, occlusion et spatialisation aux transforms solo ;
- observer au moins cinquante tirages de chaque porteur ;
- tester deux clients proches et un client hors portée ;
- vérifier si l'hôte seul pilote le hasard ou si chaque client double les sons ;
- sauvegarder/reprendre pendant une pause et pendant une lecture ;
- tester cheval visible/invisible indépendamment ;
- refuser la variante en cas de boucle continue, empilement réseau ou son sans
  source spatiale cohérente.

