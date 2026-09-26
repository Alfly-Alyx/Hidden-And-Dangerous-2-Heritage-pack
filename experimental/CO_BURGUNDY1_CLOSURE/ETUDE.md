# Co-Burgundy 1 — ambiance et fermeture des vestiges

État : comparaison binaire d'ambiance construite et désactivée, autres cas
séparés, 26 septembre 2026. Aucune installation ni validation moteur.

## Douze porteurs d'ambiance reconstruits

Le registre solo contient 105 liaisons, la coop 91. Les douze propriétaires
`dummy_snd1..12` et leurs liaisons sont absents de la coop, mais leurs douze
scripts existent et sont identiques aux versions solo. Les **21 frames sonores**
et les **sept portes** visées existent dans les sources coop vérifiées.

Le profil `co-burgundy1-ambience` de
[`build_burgundy_ambient_patch.py`](../../tools/build_burgundy_ambient_patch.py)
copie leurs records dummy de type 6 sans changer un seul champ de transform,
parent, échelle ou bornes. Neuf records font 166 octets, trois 167 : ajout total
1995 octets. Le groupe de scène passe de 6632 à 6644 records. Les douze paires
de registre sont également copiées brutes, portant `mpscripts.dta` de 91 à 103
liaisons; aucune paire existante n'est modifiée.

| Porteur | Script coop conservé |
|---|---|
| `dummy_snd1` | `bur1_SND_bird1.scr` |
| `dummy_snd2` | `bur1_SND_bird2.scr` |
| `dummy_snd3` | `bur1_SND_bird3.scr` |
| `dummy_snd4` | `bur1_SND_bird4.scr` |
| `dummy_snd5` | `bur1_SND_bird6.scr` |
| `dummy_snd6` | `bur1_SND_door1.scr` |
| `dummy_snd7` | `bur1_SND_door2.scr` |
| `dummy_snd8` | `bur1_SND_door3.scr` |
| `dummy_snd9` | `bur1_SND_door4.scr` |
| `dummy_snd10` | `bur1_SND_door5.scr` |
| `dummy_snd11` | `bur1_SND_door6.scr` |
| `dummy_snd12` | `bur1_SND_door7.scr` |

Le saut de `bird4` à `bird6` est commercial : aucun `bird5` inventé. Le fichier
`sounds.bin` entier diffère entre solo et coop, contrairement à Burgundy 3 :
il n'est donc ni copié ni remplacé. Les sons et leurs propriétés coop restent
inchangés. L'audit des cent scripts coop ne trouve aucune autre référence
littérale à ces 21 sons.

## Sources et sorties contrôlées

Huit fichiers de mission sont épinglés, les cent scripts coop sont vérifiés par
empreinte composée, et les douze scripts solo sont comparés : **120 sources**
consignées dans le rapport local. Le fichier de scène source fait 8053475 octets,
SHA-256 `ef50a34d146a2f7f38d197002aa7c6b6c530e1c9b3b27b9647205f726f3c2eb6`.
La scène coop témoin fait 7551923 octets, SHA-256
`20b520c6570cfacaf137cd15b10890a36cc390e75f598a40bbe91782b6837180`.

| Sortie variante locale | Octets | SHA-256 |
|---|---:|---|
| `scene2.bin.disabled` | 7553918 | `ff54bd0663ebd7be0f4be7be91f91a30402762627f544315942b984d747bd480` |
| `mpscripts.dta.disabled` | 3883 | `f068541902daba474c1b770e7723cbeee8e15cc6ce412cd7191d28a24cc4c442` |

Le ZIP sous `.analysis/scene-patches/` contient les deux témoins, les deux
variantes et un rapport, tous désactivés. Il n'a pas de manifeste activable,
de menu ou de scénario solo; aucun dérivé commercial complet n'entre dans Git.
Les deux surcharges installées `bu1_objective_05.scr` et `bur1_04.scr` ne sont pas
touchées : mode strict refusé, ou exclusion explicite et empreintée en mode archives.

```powershell
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --profile co-burgundy1-ambience --archives-only
.\.venv\Scripts\python.exe tools\build_burgundy_ambient_patch.py --game "D:\Games\Hidden and Dangerous 2" --profile co-burgundy1-ambience --archives-only --build
```

Le second appel refuse une sortie existante. Les 21 tests communs couvrent
notamment la matrice non consécutive, l'absence d'import de personnage et la
conservation des exigences propres aux deux autres missions Burgundy.

## Les autres vestiges ne sont pas intégrés à ce profil

- **John Ashley et chien** : les acteurs et bindings sont absents. L'étude
  [existante](../CO_BURGUNDY1_REMOVED_SOLO_ACTORS/ETUDE.md) impose la comparaison
  des items, affiliations, inventaires et transforms dans l'éditeur avant tout
  delta. Cette barrière demeure; aucun personnage ou trajet n'est importé ici.
- **Explosion 05** : `a_explosion_05` est retrouvée et activée dans le contrôleur
  lié `dummy_obj2_detector -> bu1_objective_02.scr`, avec explosion 07, objectifs
  et valeur 52. Ce n'est pas un effet attendant un nouveau propriétaire. Source
  Sabre : 3171 octets, SHA-256
  `03a91d8de5bd81c37ad635c26dd0f78c52f6d29f09b7f6578a2341fb0a2041bc`.
- **Regard ambiant** : les seuls commentaires `HUMAN_LookAround(3)` trouvés dans
  les scripts coop sont ceux de `bur1_07` et `bur1_36`; ils sont identiques dans
  les deux versions. Ce n'est pas une suppression spécifique à la coop. Une
  activité alternative reste possible, mais ne serait pas une restitution
  prouvée par cette comparaison et n'est pas ajoutée à l'ambiance sonore.

## Essais requis

Dans une copie coop explicitement isolée : un porteur à la fois, puis les douze,
portes ouvertes/fermées, plusieurs clients, joueur hors portée, sauvegarde/reprise,
comparaison de cadence et retour aux témoins. Mesurer qui exécute les scripts
aléatoires et vérifier qu'aucun son n'est multiplié par le nombre de clients.
Progression, explosion 05 et fin de mission doivent rester identiques. La fidélité
des records ne prouve ni l'autorité réseau ni le rendu; le ZIP reste inerte.

## Préparation d'un essai dans la mission d'origine — 26 septembre 2026

La fermeture complète du registre coop, examinée pour préparer un déploiement
réversible, révèle deux dépendances absentes **dans le témoin comme dans la
variante** : `dummy_diary -> bu1_diary.scr` et
`F_sloup03 -> bur1_obj_carnage.scr`. Le registre commercial fait 3376 octets,
SHA-256 `1714d8b87f29be8755cb50fb3b2b77a802d357aa28ab3b62bcc24ddd937b315c`.
Les douze ajouts d'ambiance ne créent ni ne résolvent ces deux absences.

Le préparateur d'essais natifs conserve la mission `co_burgundy1`, tous ses
fichiers commerciaux et ces deux liaisons. Il ne fabrique pas de scripts vides
et ne transforme pas la comparaison en laboratoire déclaré complet. Seul le
témoin peut être déployé avant observation du jeu; la variante reste verrouillée
tant qu'une preuve réelle du témoin natif n'est pas inscrite au registre.
Toute autre dépendance manquante ou modification des sources est refusée.

Avant d'essayer l'ambiance, vérifier le chargement coop, les objectifs et la
progression du témoin. Si l'absence empêche le fonctionnement commercial, arrêter
la comparaison et consigner cet échec : elle n'autorise pas à inventer le journal
ou un contrôleur Carnage. Ces observations restent à effectuer en moteur.
