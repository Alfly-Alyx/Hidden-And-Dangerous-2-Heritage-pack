# Benelli — banc privé FPV et modèle statique dérivé

État vérifié le **26 septembre 2026** : générateur réalisé, neuf couples lus
intégralement et modèle statique construit. **Aucune arme jouable ni validation
en moteur.** Ce banc est distinct des 50 profils de missions et de leurs essais.

## Réalisation

- `tools/five_ds.py` lit strictement les pistes de transformations 5DS v122 :
  bornes, alignements, offsets, clés ordonnées, valeurs finies et noms uniques.
  Les drapeaux inconnus et pistes de notes sont refusés, jamais ignorés.
- `tools/build_benelli_fpv_lab.py` vérifie **28 sources** contre
  [fpv-sources.json](fpv-sources.json), puis contrôle chaque liaison
  modèle/animation, texture et définition sonore. Il respecte les couches
  Base/LangEnglish/Patch/Sabre auditées. Un remplacement PatchX01 pertinent est
  refusé. Les fichiers libres sont refusés, ou explicitement exclus et tracés
  avec `--archives-only`.
- `tools/benelli_fpv_static.py` conserve les huit éléments de l'arme, enlève
  les 37 articulations, remet `fpv_weapon` à l'origine et recale le chargeur
  indépendant dans ce même repère. La hiérarchie et les transformations sont
  composées, pas seulement additionnées.
- L'inspecteur HTML autonome propose la sélection des neuf poses 4DS, trois
  projections filaires, les repères articulés, les clés 5DS brutes, les quatre
  bitmaps et l'écoute manuelle des deux sons. Aucun serveur ni réseau requis.

L'inspecteur **n'anime pas le modèle** : les canaux ne sont ni interpolés ni
interprétés comme transformations du moteur. Les lignes du graphique relient
seulement les échantillons. Aucun nombre d'images par seconde n'est inventé.
Le maillage commun des mains n'est pas reconstruit à partir des seuls joints.
Le rendu éclairé, les UV, la transparence et les événements restent à qualifier.

## Résultats de lecture des neuf couples

| État | Repère final inclus | Pistes | Clés de canaux |
|---|---:|---:|---:|
| Aim | 10 | 45 | 293 |
| AimShot | 15 | 5 | 100 |
| Arm | 60 | 21 | 1344 |
| Daim | 10 | 45 | 321 |
| Disarm | 20 | 7 | 170 |
| Idle1 | 60 | 45 | 824 |
| Jammed | 20 | 3 | 85 |
| Rel | 146 | 45 | 3248 |
| Shot | 20 | 8 | 180 |

Les neuf fichiers portent des clés au repère final déclaré : `0..60`, par
exemple, et non `0..59`. Toutes les pistes résolvent un nom unique de leur
modèle apparié. Cette vérification ne démontre pas les transitions entre états.

## Modèle de première personne

Ressource dérivée de `models.dta::Models/#FPVBeneliAim.4ds`, distincte du
[modèle extérieur original moderne](MODELE_MODERNE.md) :

- nom local : `PROTOTYPE_HERITAGE_BenelliFPV.4ds.disabled` ;
- 8 nœuds, 4 matériaux, 1 675 sommets, 1 116 triangles, 61 351 octets ;
- SHA-256 : `0c54e499b6b6b434b3bdd02ed78cc2f7f99b304d44e162e11e787d323234300f` ;
- géométrie et octets des matériaux officiels conservés ; transformations
  racines et numéros de parents recalculés, chargement de compagnon 5DS désactivé ;
- provenance **DÉRIVÉ DU JEU**, opération **MODERNE — EXTRACTION ET RECALAGE**.

Ce n'est donc pas une géométrie originale redistribuable. Le résultat et son
inspecteur restent exclusivement dans `.analysis/fpv-labs/`, ignoré par Git.
La référence structurelle est `Patch.dta::Models/w_garandfpv.4ds` (71 146
octets), pas la variante Base de 66 942 octets. Aucun élément Garand n'est copié.
La compatibilité de cette extraction avec l'arme native reste à tester.

## Audio et paramètres historiques

Les deux WAV sont mono PCM16 à 22 050 Hz, décodés et mesurés, **pas écoutés**.

| Son | Octets | Durée PCM | Crête absolue PCM16 | RMS dBFS |
|---|---:|---:|---:|---:|
| `f_bene_a.wav` | 70236 | 1,591655 s | 32768 | −10,4092 |
| `bene_r.wav` | 265818 | 6,026621 s | 32662 | −25,6246 |

Les définitions effectives viennent de **Patch.dta**, offsets 25318 et 34969,
tailles 117 et 122. Le nom du son et son fichier sont vérifiés dans le même
enregistrement structuré, pas par simple proximité de chaînes. Ces preuves ne
qualifient aucun déclencheur ni timing d'animation. Une écoute arrête l'autre ;
changer de pose arrête les deux. Aucun son ne démarre automatiquement.

Correction de l'étude initiale : le record `Benelli` de **135 octets** existe
bien dans `others.DTA::TABLES/item_shoot.tbl`, offsets **1551–1686**, SHA-256
`ce461707bb7551abdb45e165222582201dc90c292d2ff781f684540e38e47fef`.
La [lecture complète du schéma](../RECONSTRUCTION_BACKLOG/TABLES_EDITEUR.md)
corrige l'ancienne fenêtre décalée de quatre octets. Le banc privé `BenelliFPV_v5`
reprend cette preuve sans modifier les géométries ni l'inspecteur.
Sa présence est prouvée, **la signification fonctionnelle de ses champs ne
l'est pas**. Les valeurs brutes 0,3 et 1500 ne sont pas étiquetées cadence ou
dégâts. L'enregistrement actuel de la boussole ne sert jamais de réglage d'arme.

## Utilisation sans modifier le jeu

Audit en mémoire, sans sortie :

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_fpv_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only
```

Construction privée dans un dossier neuf ; un dossier existant est refusé :

```powershell
.\.venv\Scripts\python.exe tools/build_benelli_fpv_lab.py --game 'D:\Games\Hidden and Dangerous 2' --archives-only --output-name BenelliFPV_nouvel_essai --inspector
```

Le manifeste contient les preuves, limites et empreintes des quatre fichiers
produits : modèle désactivé, aperçu, consigne et inspecteur. L'HTML embarque des
données commerciales : **ne pas publier, joindre à une PR ou téléverser**.
Le code générique et les empreintes seules sont versionnés.

Ajouter `--native-assets` fabrique également deux alias courts désactivés,
`PROTOTYPE_BenFPV` et `PROTOTYPE_BenM4`, compatibles avec les vingt octets des
champs de nom des tables. Les [preuves de table](TABLES_ADDITIVES.md) détaillent
cette contrainte. La génération privée `BenelliFPV_v4` avec les deux options a
réussi ; elle contient sept fichiers, manifeste compris.

La génération réelle `BenelliFPV_v3` a réussi. L'aperçu filaire a été inspecté.
La vérification visuelle de l'HTML reste **pending** : le navigateur intégré a
refusé le protocole local `file:` ; aucune autre voie n'a été utilisée pour
contourner cette restriction. Les trois tests JavaScript utilisent exclusivement
des données inventées et un faux DOM, pas un navigateur ou l'HTML commercial.

## Validation et suites

31 nouveaux tests Python synthétiques couvrent lecteur 5DS, transformations,
extraction, provenances, refus, audit sonore et HTML ; trois tests JavaScript
contrôlent les sélecteurs, bornes et absence de lecture automatique.

À qualifier avant l'arme jouable : rendu du banc, écoute, mains/skin, convention
des transformations 5DS, timing FPV, compatibilité du modèle statique, tables
additives et sauvegardes. **Aucun Item n'est créé, aucun numéro n'est réservé,
le slot 9 et la boussole sont intacts.** B0 reste partiel ; les deux ressources
statiques de B1 sont fabriquées mais non validées en moteur ; B2–B4 restent à
construire selon les contrats encore manquants.
