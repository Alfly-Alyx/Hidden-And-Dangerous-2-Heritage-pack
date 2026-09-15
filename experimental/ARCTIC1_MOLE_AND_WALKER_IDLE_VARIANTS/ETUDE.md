# Arctic 1 — variantes d'idle du garde du quai et des walkers

État : **animation validation required, aucun prototype**, 15 septembre 2026.

## Constat

Le garde du quai conserve, après `Mole_2`, deux appels commentés :

```text
HUMAN_ACTIVITY_SpotRight(800)
HUMAN_ACTIVITY_SpotLeft(800)
```

Walker 1 conserve quatre points de variation pilotés par son compteur :
`!strazny02` aux tours 2 et 8, `!strazny01` au tour 6 et `!strazny03` au tour
10. Walker 2 conserve `!strazny02` au début de `DeAlarm`. Toutes ces lignes
sont commentées.

La recherche dans l'ensemble du corpus commercial extrait ne trouve aucun
appel actif à `SpotRight`, `SpotLeft`, `!strazny01`, `!strazny02` ou
`!strazny03`. Leur nom ne prouve ni l'existence de l'animation finale, ni sa
compatibilité avec le squelette, l'arme ou les déplacements release.

## Verdict par groupe

| Groupe | Intention lisible | Risque principal | Verdict |
| --- | --- | --- | --- |
| Mole `SpotRight/Left` | observation au bout du quai | primitive non attestée, deux appels contigus | bloqué |
| Walker 1 `!strazny*` | variation périodique d'arme/posture | boucle/durée inconnue avant reprise de route | bloqué |
| Walker 2 `!strazny02` | idle de garde après retour | peut rester actif pendant toute la ronde | bloqué |

Les changements actifs de `WeaponOnArm` autour des lignes Walker sont
conservés par la release et ne constituent pas une preuve que les animations
commentées se terminaient correctement.

## Ordre de validation

Le protocole complet figure dans
[`VALIDATION_GATES.plan.disabled`](VALIDATION_GATES.plan.disabled). Il commence
sur un acteur isolé, une animation à la fois, puis vérifie déplacement, alarme,
mort et sauvegarde. Une animation qui boucle, déplace la racine, exige un objet
ou ne se nettoie pas est rejetée.

Aucune variante de mission n'est proposée avant ces essais. Si validation il y
a, chaque idle aura son propre sélecteur ; `SpotRight` et `SpotLeft` ne seront
pas activés ensemble au même arrêt.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_mole_guard.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_walker1.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_walker2.scr` ;
- recherche exacte dans `.analysis/scripts/base/SCRIPTS`.
