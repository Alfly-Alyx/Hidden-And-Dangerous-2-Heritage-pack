# Étude expérimentale — armes et véhicules

État : 14 septembre 2026. Triage statique des archives commerciales de
`D:\Games\Hidden and Dangerous 2`, sans modification du jeu ni compilation.
La présence d'un modèle ne prouve pas à elle seule sa jouabilité passée.

## Règle de classement

Les catégories portent sur une fonction précise. Le Ju 52 est par exemple
utilisable comme décor de scène, mais son pilotage libre reste spéculatif.

1. **Présent et utilisable** : chaîne commerciale livrée ou usage de mission
   directement prouvé.
2. **Présent mais non pilotable/non équipé** : modèle exploitable, sans chaîne
   complète de véhicule ou d'arme joueur.
3. **Données partielles permettant une restauration fidèle bornée** : assez de
   données officielles pour restaurer un aspect précis, pas toute la fonction.
4. **Reconstruction spéculative** : pièce fonctionnelle essentielle à créer
   sans source locale suffisante.

## Synthèse

| Élément et portée | Catégorie | Verdict |
| --- | ---: | --- |
| M1 Garand, Stevens 311, Flak 38 | 1 | faux contenus coupés : chaînes commerciales présentes |
| P08 silencieux, G43, MAS 36, Panzerschreck | 1 | livrés par Sabre Squadron, modèles et chaînes FPV présents |
| Vickers K monté sur jeep SAS | 1 | arme, animation et ancrage de tourelle actifs ; faux positif portatif |
| Ju 52 comme élément de scène | 1 | explicitement appelé dans Africa 1 et présent dans plusieurs variantes Africa |
| Ju 52 comme décor animé réemployable | 3 | modèles, pièces et scripts officiels permettent un usage borné |
| La-5, Aichi, M323, Li-2, Fa 223, Fw 200, DFS 230 | 2 | modèles articulés présents, aucune chaîne pilotable démontrée |
| Li-2 comme ambiance de mission | 3 | quatre scripts sonores Libye 2, sans liaison exacte au modèle prouvée |
| Deux lance-flammes : identité, icônes, munitions, effet | 3 | enveloppe officielle partielle récupérable |
| Deux lance-flammes fonctionnels | 4 | modèles tenu/sol, animations, jet, dégâts et IA absents |
| Benelli M4 : animations, textures, sons et munition | 3 | enveloppe FPV très complète, mais entrée Weapon remplacée et modèle monde absent |
| Benelli M4 comme arme complète | 4 | nouvelle entrée additive et paramètres de tir à reconstruire sans écraser la boussole |
| Pilotage libre des aéronefs | 4 | physique, commandes, dégâts, HUD, IA et réseau non démontrés |
| Garota et ZK-383 | 4 | aucune ressource locale identifiable |
| FG 42 ou MG 34 portative | 4 | vestiges de catalogue, chaîne d'arme portable non démontrée |

## 1 — Présent et utilisable

### Armes rares à exclure du chantier de création

- **M1 Garand** : `models.dta::MODELS\w_garand.4ds` (19 607 octets),
  `w_garandfpv.4ds` (66 942), puis `#FPVGarandAim`, `Arm`, `Shot`, `Reload`
  et `Disarm`. `others.DTA::TABLES\items.sav` contient `M1 Garand`,
  `w_garand` et `AMMO Garand`.
- **Stevens 311 / side-by-side** : `w_sidebyside.4ds` (15 081) et
  `w_sidebysideFPV.4ds` (39 168) ; la table contient sa munition.
- **Flak 38** : `la_flak.4ds` (134 175), `la_flakE`, `la_flak4x38`, modèles
  endommagés et scripts de mission ; les munitions Flak 38/38x4 sont présentes.
- **P08 silencieux** : `SabreSquadron.dta::Models\w_parasil.4ds` (20 134),
  `w_parasil_fpv.4ds` (49 038) et entrée `ParaSil`.
- **G43** : `w_g43.4ds` (43 404), `w_g43fpv.4ds` (118 541), série
  `d_#FPVG43*`, entrées `G43` et `AMMO G43`.
- **MAS 36** : `w_MAS.4ds` (50 553), `w_masfpv.4ds` (113 448), série
  `d_#FPVMAS36*`, entrée `MAS MLE 36` et munition.
- **Panzerschreck** : `w_panschr.4ds` (35 896), `w_pschrek_fpv.4ds`
  (75 912), animations `d_#FPVPanzS*` et entrée balistique `Pschrek`.

Test : vérifier une fois équipement, visée, tir, rechargement, dépôt/retrait et
sauvegarde. Aucun correctif si ce test passe.

### Vickers K : arme montée de la jeep SAS

`w_vickerKFPV.4ds` (26 098 octets) contient `fpv_weapon`, `gunlock`, `base`,
`cock` et `magazine`, avec les textures `w_vickersK.bmp` et
`w_vickersmagazine.tga`. Le modèle `la_Jeepsas.4ds` (328 870 octets) possède
déjà les sièges, caméras, axes `HORT01`/`VERT01`, bouche `BARREL01_00`, point
`SHDUM01`, munitions et culasse nécessaires à son montage. Une mission CMP
installée conserve même la liaison littérale
`la_Jeepsas_01.BARREL01_00 -> w_vickerKFPV`.

Le Vickers K n'est donc pas une arme supprimée à recréer : c'est un composant
fonctionnel du véhicule. Un unique test en jeu de la jeep SAS doit confirmer
tir, orientation, munitions et changement de siège ; aucune version portative
ne sera inférée de cette chaîne montée.

### Ju 52 : usage commercial direct

- `missions.dta::MISSIONS\AFRICA1\scene2.bin` contient `CUTjunkers`,
  `CUTjunkersB` et le modèle `la_Ju52Af` ;
- `Patch.dta::SCRIPTS\AFRICA1\CUT_af1Ju52.scr` anime `CUTjunkers` avec
  `#AF1_junkrcut.i3d`, masque trois hélices et crée deux poussières ;
- `CUT_af1velit.scr` allume ensuite `CUTjunkersB` ;
- `la_Ju52` est aussi présent exactement dans Africa 2 et plusieurs variantes
  Africa 1.

Cela prouve le décor scénarisé, pas le pilotage. Test : rejouer la cinématique
Africa 1 avec/sans Patch et vérifier hélices, poussière, changement d'acteur et
nettoyage après interruption.

## 2 — Modèles présents, pilotage non démontré

Le parseur 4DS local confirme des géométries articulées. Sièges et caméras sont
des points d'ancrage, pas une physique de vol ni une preuve d'entrée joueur.

| Appareil | Preuve exacte dans `models.dta` | Nœuds utiles observés | Conclusion |
| --- | --- | --- | --- |
| Ju 52 | `la_Ju52.4ds`, 142 338 o, 38 nœuds | 3 moteurs/hélices, ailes, gouvernes, roues, `SEAT00`, `streliste` | scène prouvée, pilotage absent |
| La-5 | `la_La-5.4ds`, 162 990 o, 41 nœuds | moteur/hélice, roues, gouvernes, siège, caméras FPV/D | banc monoplace possible |
| Aichi | `la_aici.4ds`, 150 223 o, 47 nœuds | moteur/hélice, roues, gouvernes, 2 sièges/caméras | implantation absente |
| M323 | `LA_M323.4ds`, 257 929 o, 99 nœuds | 6 moteurs/hélices, volets, 6 sièges, caméras, canon | trop complexe comme premier test |
| Li-2 | `la_Li2.4ds`, 323 240 o, 89 nœuds | 2 moteurs/hélices, roues, gouvernes, 5 sièges, caméra FPV | liaison non prouvée |
| Fa 223 | `la_Fa 223.4ds`, 175 680 o, 48 nœuds | 2 rotors/moteurs, gouvernes, 4 sièges/caméras | physique rotor absente |
| Fw 200 | `la_Fw 200.4ds`, 60 102 o, 40 nœuds | 4 moteurs/hélices, gouvernes, `cameraD` | décor seulement au départ |
| DFS 230 | `la_DSF 230.4ds`, 143 402 o, 45 nœuds | roues, gouvernes, 4 sièges, caméra | remorquage/largage absent |

Tous possèdent aussi un modèle simplifié `sla_*`, utile dans le monde mais sans
les systèmes fonctionnels manquants.

### Correction des faux liens de l'inventaire automatique

Une recherche exacte de `la_La-5`, `la_aici`, `LA_M323` et `la_Li2` dans 511
entrées des missions candidates ne trouve aucune correspondance. Les anciens
résultats venaient de sous-chaînes trop courtes :

- `posila5/posila5b` de Czech 1 ne désignent pas le La-5 ;
- `seed_m_palma03M32356/91` et `ob_zm323` ne sont pas `LA_M323.4ds` ;
- le résultat Aichi d'`AFRICA4\scene2.bin` est une suite binaire fortuite ;
- les résultats Li-2 dans `scene2.bin/volumy.bin` sont aussi fortuits.

Conclusion corrigée : **modèles présents, liaison de mission non démontrée**.
Le Ju 52 reste le seul appareil de cette liste relié exactement à une scène.

Tests : instancier chaque modèle dans une mission laboratoire séparée ; vérifier
textures, orientation, échelle, collision et LOD ; bouger seulement ses nœuds
nommés ; rechercher une vraie table de véhicule et un acteur exact avant tout
siège ; puis tester roulage, décollage, décrochage, atterrissage, dommages,
sauvegarde et retour au personnage. Répéter en coopératif avant intégration.

## 3 — Données partielles restaurables fidèlement

### Benelli M4 : enveloppe FPV officielle

Les archives conservent neuf couples 4DS/5DS
`#FPVBeneliAim`, `AimShot`, `Arm`, `Daim`, `Disarm`, `Idle1`, `Jammed`, `Rel`
et `Shot`. `#FPVBeneliAim.4ds` pèse 63 906 octets et contient 45 nœuds, dont
l'arme, les bras, la culasse, la douille et le magasin. Le bloc complet de
`TABLES/FpvAnims.sav`, identique dans Sabre Squadron, est placé entre le Mosin
et le Garand. Les textures `wi_it-benelli.bmp`, `d_benellim4.bmp` et
`d_benellim4paz.bmp`, les sons `f_bene_a.wav` et `bene_r.wav`, leurs
définitions de tir/rechargement, ainsi que la munition 179 subsistent.

Le rang `Weapon` correspondant est toutefois occupé dans la version finale par
l'ID 9 de la boussole. Aucun modèle monde/posé `w_benelli*` ni paramètre
original de capacité, cadence, dégâts ou dispersion n'est retrouvé. La tranche
fidèle se limite donc à préserver et tester les ressources FPV ; toute arme
utilisable doit recevoir une entrée nouvelle, un modèle monde et des valeurs
explicitement reconstruites, sans remplacer la boussole.

### Ju 52 comme décor animé

Le modèle principal, sa variante Africa, les pièces séparées de fuselage, porte,
aile, roue et train, plus les scripts Africa 1 permettent de reproduire la scène
conservée ou un banc d'animation clairement étiqueté. Ils ne permettent pas de
déduire un modèle de vol.

### Li-2 comme ambiance

Sabre Squadron conserve, dans Libye 2 et Co_Libye2, `Li2_SND_bum`,
`Li2_SND_sup`, `Li2_SND_sutr1` et `Li2_SND_sutr2`. Ils ne pilotent pas le
modèle : ils allument aléatoirement `S_bum1..3`, `S_sup1..3` et `S_sutr1..5`.
Le nom donne un contexte, pas une liaison à `la_Li2.4ds`. Il faut observer la
mission et relever l'acteur chargé avant toute annonce de restauration.

### Deux lance-flammes : enveloppe officielle partielle

- `Maps.dta` contient les icônes 64×32 `wi_ge-flmwr35.bmp` et
  `wi_br-flmthr2.bmp`, leurs icônes de munitions et variantes DX1 ;
- `others.DTA::TABLES\items.sav` contient `AMMO Flammewer` et
  `AMMO Flamethrow` avec ces identifiants ;
- `TABLES\effects.def` contient l'effet 25 `plamenomet` avec `d_fire.tga` ;
- `TABLES\IngameSounds.def` conserve `They've Got Flamethrowers` et
  `Aaaa (Flamethrower)` ;
- `models.dta::MODELS\flame1.4ds` ne pèse que 471 octets et ne contient que
  `fire01` : effet, pas arme.

Noms, icônes, munitions et amorce visuelle sont préservables fidèlement. Forme
3D, animations et comportement ne le sont pas. Tester l'effet 25 seul :
création/arrêt, portée visuelle, murs et sauvegarde. Dégâts continus,
consommation et réseau sont des prototypes séparés.

## 4 — Reconstructions spéculatives

### Lance-flammes fonctionnels

Il manque modèles tenu/sol, animations première/troisième personne, réservoir,
jauge, jet continu, collisions/dégâts, allumage, réactions IA, sons de
fonctionnement et réseau. Portée, débit et équilibrage originaux ne sont pas
déductibles : mention obligatoire « reconstruction moderne ».

### Garota et ZK-383

`garrote/garota` et `zk383/zk-383/zk_383` ne produisent aucune entrée locale :
pas de modèle, icône, animation, objet ou script. La Garota exigerait deux
animations synchronisées attaquant/victime. Le ZK-383 pourrait réutiliser une
balistique existante, mais modèle, animations, sons et équilibrage seraient
modernes. Aucun prototype avant une source historique nouvelle et attribuable.

### FG 42 et MG 34 portative

`items.sav` conserve `AMMO FG 42`, `AMMO MG 34` et `Maps.dta` des icônes MG 34.
Aucun modèle nommé FG 42 ou MG 34 portable n'existe dans `models.dta`. Ce sont
des vestiges de catalogue ; la MG 34 montée ne prouve pas une version portable.

### Pilotage libre et armement des aéronefs

Les nœuds `SEAT`, `camera`, `engine`, `vrtule`, `rudder` ou `BARREL` ne
fournissent ni commandes, portance, décrochage, collisions, dégâts, HUD, IA ou
réseau. Tout appareil pilotable resterait un prototype communautaire tant
qu'une chaîne ancienne complète n'est pas retrouvée.

## Ordre recommandé

1. Valider les faux positifs déjà jouables, notamment le Vickers K monté.
2. Construire la Benelli comme entrée additive expérimentale, sans remplacer la boussole.
3. Rejouer et enregistrer la scène Ju 52 d'Africa 1 comme référence.
4. Tester les huit modèles un par un, sans siège joueur inventé.
5. Identifier visuellement la fonction des scripts sonores Li-2.
6. Tester l'effet 25 du lance-flammes sans créer d'arme.
7. Choisir un démonstrateur : Ju 52 décoratif ou comparaison La-5/Aichi.
8. Reporter pilotage, lance-flammes fonctionnels, Garota, ZK-383, FG 42 et MG 34
   portative à la phase spéculative finale.

## Prototypes documentaires associés

- `PROTOTYPE_OFFICIEL.md` borne les deux essais fondés sur une chaîne réellement
  livrée : rejouer le Ju 52 d'Africa 1 sans le copier et tester visuellement
  l'effet 25. Son petit banc d'effet est désactivé et ne contient aucun asset.
- `PROTOTYPE_MODERNE.md` définit les phases d'un lance-flammes fonctionnel et
  d'un laboratoire d'aéronefs. Il exclut toute prétention de restauration et ne
  propose aucun faux prototype pour Garota ou ZK-383.

Ces deux pistes sont volontairement séparées afin qu'une ressource officielle
partielle ne transforme jamais, par glissement de vocabulaire, une mécanique
nouvelle en contenu restauré.

Acceptation d'un décor : chargement stable, bonnes textures/échelle/collisions,
animation déterministe, sauvegarde/reprise et aucun blocage. Un véhicule ajoute
roulage, vol, atterrissage, dommages, sortie, IA et coop. Une arme ajoute
inventaire, FPV, animation, munition, dégâts, IA, sauvegarde et réseau.

## Limites

- Audit statique ; aucun test dans le jeu ou l'éditeur.
- « Non trouvé » n'est pas une preuve absolue d'absence historique.
- Une build alpha/bêta nouvelle pourrait relever certaines catégories.
- Aucun asset commercial, fichier de table, exécutable ou script actif n'a été
  créé. Le seul code associé est un banc générique `.scr.disabled` qui référence
  l'effet 25 sans embarquer sa donnée.
