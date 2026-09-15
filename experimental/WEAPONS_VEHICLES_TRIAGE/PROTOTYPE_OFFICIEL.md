# Prototype OFFICIEL borné — références installées uniquement

État : proposition non intégrée, 14 septembre 2026. « OFFICIEL » signifie ici
que l'élément observé est livré par le jeu commercial. Le banc qui l'isole est
expérimental ; il n'est pas présenté comme un script original retrouvé.

## Frontière de redistribution

Ce dossier ne contient et ne doit contenir aucun modèle 4DS/5DS, animation I3D,
texture, icône, son, table ou scène extrait du jeu. Les essais résolvent les
ressources depuis l'installation que possède le testeur. Un paquet publiable ne
doit embarquer que le code original du banc, cette documentation et, si besoin,
des assets entièrement nouveaux.

## Prototype O1 — référence Ju 52 d'Africa 1

### Portée officielle

La seule liaison exacte démontrée pour les aéronefs triés est celle du Ju 52 :

- la scène Africa 1 contient `CUTjunkers`, `CUTjunkersB` et `la_Ju52Af` ;
- `CUT_af1Ju52.scr` applique `#AF1_junkrcut.i3d`, masque les trois hélices et
  gère deux particules de poussière ;
- `CUT_af1velit.scr` allume ensuite `CUTjunkersB`.

Le prototype OFFICIEL consiste d'abord à **rejouer cette scène inchangée** et à
enregistrer son comportement de référence. Il ne faut ni extraire ces fichiers
dans `experimental/`, ni transposer leur script avant d'avoir la baseline.

### Mesures

1. relever le moment d'apparition, la durée d'animation et le passage de
   `CUTjunkers` à `CUTjunkersB` ;
2. vérifier l'état des trois hélices et des deux poussières avant, pendant et
   après la cinématique ;
3. interrompre la scène, sauvegarder/reprendre avant son départ et confirmer le
   nettoyage ;
4. consigner modèle, animation et frames par leur nom seulement, sans copier les
   données binaires.

Acceptation : la référence est reproductible et documentée. Elle autorise un
décor Ju 52 animé fondé sur des ressources installées ; elle n'autorise ni
pilotage, ni armement, ni physique de vol.

## Prototype O2 — effet 25 du lance-flammes

### Portée officielle

`effects.def` nomme l'effet 25 `plamenomet`. Un banc minimal peut vérifier cet
effet indépendamment de toute arme. Le fichier
`PROTOTYPE_OFFICIEL_EFFECT25.scr.disabled` référence uniquement l'index 25 et
une frame de laboratoire fictive `EXP_FlameEmitter`; il ne redistribue aucune
donnée commerciale.

Contrat du banc :

| Signal | Action du banc |
| ---: | --- |
| 1 | créer une seule instance indexée de l'effet 25 |
| 2 | demander sa fin normale |
| 3 | destruction de secours pour interruption de test |

### Mesures

1. créer localement une mission laboratoire privée avec une frame vide nommée
   `EXP_FlameEmitter` ;
2. tester création, durée, orientation, taille, extinction et destruction ;
3. placer la frame près d'un mur, du sol, d'un humain et d'un véhicule ;
4. constater séparément visibilité et dégâts : aucun dommage ne doit être
   attribué à l'effet sans mesure ;
5. tester signaux répétés, sauvegarde/reprise et nettoyage à l'interruption.

Acceptation : aucun doublon ou résidu de particule, et une description purement
visuelle de l'effet. Ce test ne constitue pas un lance-flammes fonctionnel.

## Ressources partielles qui ne deviennent pas un prototype OFFICIEL

- Les icônes et munitions `Flammewer`/`Flamethrow` prouvent une enveloppe de
  catalogue, pas une arme utilisable.
- `flame1.4ds` ne contient que `fire01` et ne remplace pas un modèle tenu/sol.
- Les sons de dialogue mentionnant un lance-flammes ne sont pas des sons de
  fonctionnement.
- Les scripts `Li2_SND_*` ne lient pas le modèle `la_Li2.4ds`.
- La-5, Aichi, M323 et Li-2 n'ont aucune liaison exacte de mission retrouvée.
- Garota et ZK-383 n'ont aucune ressource locale identifiable.

Aucun prototype OFFICIEL n'est donc proposé pour ces fonctions.

## Sources référencées, non recopiées

- installation commerciale : Africa 1, `scene2.bin`, `CUT_af1Ju52.scr`,
  `CUT_af1velit.scr` et `#AF1_junkrcut.i3d` ;
- installation commerciale : `TABLES/effects.def`, entrée 25 ;
- `ETUDE.md` pour l'inventaire, les tailles et la correction des faux positifs.
