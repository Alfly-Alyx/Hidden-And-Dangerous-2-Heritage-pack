# Étude expérimentale — ventilateur physique d'Africa 5

État : **variante désactivée**, 15 septembre 2026. Aucune compilation ni
modification de mission commerciale.

## Verdict

Le premier ventilateur possède un bloc de proximité entièrement commenté qui
convertit son frame en objet physique de masse 5. Le réactiver tel quel ferait
probablement tomber le ventilateur quand un joueur passe à moins de trois
unités, sans intention claire, sans verrou de répétition et sans équivalent sur
le jumeau. Ce comportement ne convient pas au lot stable.

La variante recommandée remplace la proximité automatique par une utilisation
explicite et monostable. Une seconde variante conserve le déclencheur historique
comme expérience comparative, mais le désarme avant toute conversion. Les deux
sont exclusives et ne ciblent jamais le second ventilateur.

## Preuves

| Élément | Constat commercial |
| --- | --- |
| ventilateur 1 | `m_AF5_vetrak.Rectangle07 -> AF4_vetrak.scr` dans `scripts.dta` |
| animation 1 | rotation Y `108000, 360`, puis délai 8000 en boucle |
| vestige 1 | `_PlayerInRange(3)` puis `FRM_CreatePhysicalObject(this, 5)`, entièrement commenté |
| ventilateur 2 | `m_AF5_vetrak2.Rectangle07 -> AF4_vetrak02.scr` |
| animation 2 | rotation Y `108000, 90`, délai 8000 ; aucun bloc physique |
| géométrie | `scene2.bin` contient les parents `m_AF5_vetrak` et `m_AF5_vetrak2`; les chemins complets sont résolus par les bindings actifs |

Le binding prouve que le moteur trouve les frames pour la rotation. Il ne
prouve pas que `Rectangle07` constitue un solide autonome adapté à la physique :
son pivot, sa collision, sa masse effective et ses liens au plafond doivent
être inspectés en éditeur et en jeu.

## Variantes exclusives

### `RELEASE`

Conserver les deux scripts commerciaux. Les ventilateurs tournent et aucun ne
devient physique.

### `ON_USE_ONESHOT` — recommandée pour le laboratoire

[`PROTOTYPE_ONUSE_ONESHOT.scr.disabled`](PROTOTYPE_ONUSE_ONESHOT.scr.disabled)
conserve la rotation du premier ventilateur. `OnUse()` exige une portée de trois
unités, place le verrou avant la conversion physique, puis termine le script.
Le choix d'une interaction est une **création moderne**, pas une restauration.

### `PIR_ONESHOT` — comparaison du vestige

[`PROTOTYPE_PIR_ONESHOT.scr.disabled`](PROTOTYPE_PIR_ONESHOT.scr.disabled)
garde le rayon commercial, mais désarme le `Whenever` et pose son verrou avant
la conversion. Cette branche mesure l'effet supposé du code commenté ; elle
n'est pas recommandée comme comportement de jeu.

Ne jamais charger les deux variantes à la fois, convertir le jumeau par symétrie
ou démarrer un second contrôleur sur le même frame.

## Porte géométrie/physique

1. Inspecter hiérarchie, pivot, volume de collision et parentage de
   `m_AF5_vetrak.Rectangle07` ; refuser si le frame entraîne plafond ou décor.
2. Capturer la transformation et la rotation release avant conversion.
3. Dans une copie laboratoire, convertir une seule fois et observer chute,
   rebonds, traversée du plafond/sol, sommeil physique et persistance.
4. Tester contact joueur/IA, grenades, tirs, sauvegarde/reprise et limites de
   zone. Aucun dégât n'est ajouté tant qu'un mécanisme commercial contrôlé n'a
   pas été identifié et validé.
5. Vérifier que le verrou est posé avant l'appel physique et qu'aucun second
   appel n'apparaît sous spam d'utilisation ou présence prolongée dans le rayon.
6. Contrôler le jumeau pendant tout le test : rotation `90`, absence de chute,
   binding et géométrie strictement inchangés.

Critères d'arrêt : géométrie liée au bâtiment, pivot aberrant, appel multiple,
désynchronisation, objet persistant après rechargement, blocage de navigation
ou dommage non maîtrisé.

## Retour arrière

Restaurer `AF4_vetrak.scr` commercial dans la copie d'essai. Aucun nouveau
frame, binding ou asset n'est nécessaire ; `AF4_vetrak02.scr` n'est jamais
modifié.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_vetrak.scr` et
  `AF4_vetrak02.scr` ;
- copies Patch homonymes ;
- `missions.dta : MISSIONS/AFRICA5/scene2.bin`, `scripts.dta` ;
- précédents physiques commerciaux sous Africa1, Alps2 et Czech3, utilisés
  seulement comme preuve de l'API, pas comme preuve de masse ou de collision.
