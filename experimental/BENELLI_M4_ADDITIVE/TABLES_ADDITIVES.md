# Benelli — lecture des tables et préparation additive

État du **26 septembre 2026** : lecteurs stricts réalisés, huit sources
centrales vérifiées, aucun fichier du jeu modifié. **Pas encore d'entrée Weapon
additive** : cet audit de tables seul ne valide ni sauvegarde, ni liaison FPV,
ni mécanique. Le [contrôle natif distinct](CONTRAT_NATIF.md) établit maintenant
la liaison des identifiants et la lecture des descripteurs hors moteur.

## Ce que l'audit démontre

`tools/benelli_table_audit.py` vérifie tailles/empreintes des couches Base,
Patch, Sabre et PatchX01 avant toute interprétation. Il conserve séparément
les objets, les groupes FPV et leurs numéros : un même nombre dans deux tables
n'est pas automatiquement une liaison.

| Source `items.sav` | Capacité | Entrées présentes | Vides | Octets sérialisés | Fin 0xCD |
|---|---:|---:|---:|---:|---:|
| others.DTA | 255 | 246 | 9 | 125004 | 3516 |
| Patch.dta | 255 | 246 | 9 | 125004 | 3516 |
| SabreSquadron.dta | 500 | 272 | 228 | 139088 | 112912 |
| PatchX01.dta | 500 | 272 | 228 | 139088 | 112912 |

Le lecteur parcourt exactement la capacité dérivée de la taille allouée
(`capacité × 504`). Chaque emplacement contient un marqueur 32 bits : zéro
occupe quatre octets ; un est suivi de 504 octets de données. Le reste doit
être exclusivement `0xCD`. Les noms sont des chaînes terminées par zéro dans
des champs de vingt octets. Les numéros de texte ne sont pas les numéros de
slots. Tous les autres champs non qualifiés restent opaques.

Les [notes de recherche historiques de Corporal Desola](https://hidden-and-dangerous.net/board/viewtopic.php?t=957)
ont servi de piste, mais leur découpage en records de 508/512/516 octets ne
conserve pas les emplacements vides dans les fichiers possédés. L'interprétation
ci-dessus est établie par lecture complète des quatre fichiers et contrôles
croisés, pas par adoption de cette heuristique. Aucun code du forum n'est copié.

PatchX01 ne contient ici que `Tables/items.sav`, SHA-256
`10fa461d6116c7463fcdb46c404c67af495585b82a574656a72e85f37964b20c`.
Par rapport à Sabre, seuls des octets des entrées MP 44 (26) et BAR (28)
diffèrent. Leur sens n'est pas réinterprété et leurs données ne sont pas écrasées.

## Numéro 359 : candidat, pas allocation

Un [premier descripteur moderne complet](DESCRIPTEUR_MODERNE.md) est désormais
assemblé et contrôlé hors moteur, avec fragment FPV isolé et ressources verrouillées.
Il ne constitue toujours pas une entrée additive installée : texte non alloué,
contrats de comportement et transaction des tables encore incomplets.

Complément du **27 septembre 2026** :
[18 colonnes de tir projetées](../RECONSTRUCTION_BACKLOG/PARAMETRES_TIR.md)
sur les octets consommés de l'action native. Les 40 témoins Base/Patch
concordent ; les écarts Sabre/PatchX01 sont conservés. La projection Benelli
couvre 85 octets sur 88, mais n'est pas un descripteur d'arme complet.

- Hors de la capacité Base/Patch ; une intégration 359 ne peut donc pas être
  annoncée compatible Base sans autre mécanisme.
- Vide dans Sabre/PatchX01 : marqueur de quatre octets à l'offset **138524**.
- Le scan distinct des missions a relu 80 catalogues commerciaux, 146 locaux,
  149 573 enregistrements et 7 135 déclarations de maplist : aucune occurrence
  d'objet 359, dix avertissements de formats conservés. Il ne décode pas les
  sauvegardes ni toutes les tables centrales.
- Les deux tables libres de l'installation personnelle ont été inspectées
  séparément et laissées intactes. Leur slot 359 est également vide, mais elles
  ne sont pas un témoin commercial et sont exclues des constructions archivées.
- **Aucune liberté de slot globale ni compatibilité de sauvegarde n'est
  revendiquée.** Le rapport renvoie toujours `allocation_allowed: false`.

Le slot 9 reste `KOMPAS`, type 2, texte 1009. La munition 179 est `AMMO Beneli`,
type 0, texte 1179, icône `ii_br-side-m`, modèle `w_ammo`. Ces éléments sont
attestés dans les quatre couches. Le [contrôle natif de munition](ETAT_ET_MUNITION.md)
établit séparément le consommateur et la quantité 7,0, avec une association
synthétique seulement : aucune fiche commerciale d'arme Benelli n'est inventée.

## Associations FPV structurées

`tools/fpv_table.py` décode entièrement les conteneurs Base (255 groupes) et
Sabre (277 groupes), avec bornes et unicité des propriétaires. Le groupe
**109**, offset 6550, taille 784, est identique dans les deux versions :
SHA-256 `b9e781eeb849241616f9598ef5d4e9d9c4b5df16bf033784370fadd697e0bd24`.

| Identifiant d'état | Ressource du canal 3000 |
|---|---|
| 2000, 2001 | `#FPVBeneliIdle1.I3D` |
| 2002, 2003 | `#FPVBeneliShot.I3D` |
| 2004, 2005 | `#FPVBeneliAimShot.I3D` |
| 2006 | `#FPVBeneliRel.I3D` |
| 2007 | `#FPVBeneliJammed.I3D` |
| 2008 | `#FPVBeneliArm.I3D` |
| 2009, 2010 | `#FPVBeneliDisarm.I3D` |
| 2011 | `#FPVBeneliAim.I3D` |
| 2012 | `#FPVBeneliDaim.I3D` |

Chaque association est suivie de la valeur brute 100 ; les canaux 3001–3003
sont vides. Le rôle moteur de ces canaux et nombres n'est pas inventé.
Le groupe numérique 359 existe dans Sabre, mais ce n'est **pas** une preuve
qu'il corresponde à l'objet 359. Le contrôle natif distinct confirme désormais
« groupe = objet + 100 » jusqu'au calcul du consommateur : l'objet candidat 359
exige 459, absent. Les canaux sont consommés dans l'ordre du fichier, et la
valeur 100 est un seuil de sélection. L'audit de tables seul garde ces preuves
natives hors de son périmètre ; aucune animation n'est validée en jeu.

## Noms courts construits pour les modèles

Les noms descriptifs longs des laboratoires ne tiennent pas dans les champs
natifs. L'option `--native-assets` du [banc FPV](BANC_FPV.md) produit donc,
sans tronquer ni toucher aux tables :

| Nom sans extension | Provenance | Ressource |
|---|---|---|
| `PROTOTYPE_BenFPV` | dérivé du jeu, recalage moderne | modèle de première personne |
| `PROTOTYPE_BenM4` | création moderne originale | modèle extérieur |

Les deux copies sont `.4ds.disabled`, leurs octets restent identiques aux
modèles déjà contrôlés. Le manifeste inscrit séparément leur provenance et
leur champ nominal de vingt octets. Ces alias courts sont une exception
documentée au préfixe descriptif `PROTOTYPE_HERITAGE_`, pas un contenu officiel.
Le lot privé **BenelliFPV_v5** contient les deux alias et l'inspecteur local,
avec la [preuve de ligne TBL corrigée](../RECONSTRUCTION_BACKLOG/TABLES_EDITEUR.md).

## Reproduire les lectures

```powershell
.\.venv\Scripts\python.exe tools/benelli_table_audit.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only
.\.venv\Scripts\python.exe tools/item_id_collision_audit.py 'D:\Games\Hidden and Dangerous 2' --candidate 359
```

Sans `--archives-only`, les tables libres font refuser le premier audit. Ce refus
est attendu : ni remplacement silencieux ni confusion avec la dernière couche
archivée. Un export JSON doit employer un nouveau chemin et ne contient pas
les octets des records commerciaux.

18 tests synthétiques supplémentaires couvrent capacités, marqueurs vides,
champs, noms courts, hiérarchie FPV, couches, surcharges, non-allocation et les
deux alias générés. Avant B2 restent à établir : sauvegardes complètes et
interprétation des paramètres. La liaison munition et l'état d'un objet isolé
sont maintenant contrôlés séparément, avec une asymétrie native documentée.
La liaison numérique arme/FPV est établie sans chargement de scène.
Les recettes d'intégration ne sont pas fabriquées à partir d'un record Garand
copié ou d'une boussole réaffectée.
