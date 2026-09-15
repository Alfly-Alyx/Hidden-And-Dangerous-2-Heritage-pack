# Alps 2 — variantes de très basse priorité

État : **documentation et mocks désactivés seulement**, 15 septembre 2026.
Aucune de ces lignes n'est nécessaire à la mission release.

## Critère d'inclusion

Une ligne dormante n'est retenue que si ses ressources sont attestées par le
script effectif, la scène ou un usage moteur actif. Même alors, elle reste une
option de test isolée. Aucun groupe de lignes n'est réactivé en bloc.

## Candidats retenus

- `AL2_05` : les checkpoints `AL2_05_03` et `AL2_05_04` sont chacun utilisés
  par un `HUMAN_Move` actif dans le même script. Le téléport commenté entre les
  deux est donc testable, mais il peut masquer un défaut de navigation ;
- `AL2_07` : `HUMAN_SETMODE_Walk()` est commenté après le mode Guard. L'API
  d'allure est largement active ; l'effet local sur la ronde doit être mesuré ;
- `AL2_22` normal et Carnage : les points `cumzadl` et
  `cumpredsebeveskladu` sont résolus et utilisés activement ailleurs dans les
  mêmes scripts. Les deux tours commentés sont testables un par un ;
- `AL2_40` : le siège `al240sit` existe dans la scène et est utilisé par
  `HUMAN_ACTIVITY_Sit`. `%%sedimtak` est actif dans d'autres missions et
  conservé exactement ici, mais sa disponibilité Alps 2 doit encore être
  confirmée au runtime.

`MOCK_DELTAS.scr.disabled` conserve les lignes exactes. Chaque ligne correspond
à un profil séparé ; le fichier n'est pas un patch cumulatif.

## Règles de test

- partir de la release et activer un seul candidat ;
- comparer position/orientation avant et après sauvegarde ;
- tester l'alarme pendant le mouvement ou l'animation ;
- vérifier l'absence de collision et de saut visible ;
- pour `AL2_05`, refuser le téléport si le Move réussit déjà sans blocage ;
- pour `AL2_22`, tester normal et Carnage séparément ;
- pour `AL2_40`, refuser la promotion si l'animation n'est pas résolue dans le
  pack Alps 2 chargé.

Les faux positifs explicitement exclus sont consignés dans
`FALSE_POSITIVES.md`.
