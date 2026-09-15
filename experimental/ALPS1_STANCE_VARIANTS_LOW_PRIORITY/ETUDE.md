# Alps 1 — variantes de posture à basse priorité

État : **comparaisons séparées, toutes désactivées**, 15 septembre 2026. Ces
lignes sont syntaxiquement complètes mais peuvent remplacer le comportement IA
retenu par la release. Rien n'est compilé.

## Variantes indépendantes

- **ge04 crouch sniper** : ajout commenté après l'arrivée à `ge04_sniper` et
  avant `HUMAN_SetSniper(1,1)`. La release utilise StandFast ; le retour
  d'alarme emploie déjà Crouch.
- **ge14 crouch au signal 1** : ajout commenté avant
  `HUMAN_TurnAtNearestPlayer`. D'autres branches ge14 emploient déjà Crouch,
  sans prouver cette posture d'activation.
- **ge19 crouch après `ge19_02`** : la réaction tir/explosion court actuellement
  vers le point en mode Run/StandFast. Le crouch peut changer navigation et
  temps de réaction.
- **ge19 turn proche** : rotation commentée dans la branche pas à moins de
  quatre unités, juste avant `EndScript()`. À tester séparément du crouch.
- **ge31 crouch/stand au stand** : paire autour du délai de 4,5 secondes à
  `ge31_02`, avant le retour `ge31_01`. Les deux lignes sont atomiques ; activer
  une seule laisserait une posture persistante.
- **ge07 Walk initial**, **ge08 Run initial**, **ge09 Run initial** : modes
  commentés dans l'initialisation. Ils influencent potentiellement toutes les
  rondes et alarmes et sont donc les candidats les plus larges.

La [`VARIANT_MATRIX.md`](VARIANT_MATRIX.md) décrit les baselines. Le
[`SELECTOR.plan.disabled`](SELECTOR.plan.disabled) maintient chaque commutateur
indépendant et OFF par défaut.

## Voix exclues

Les appels directs commentés de ci01/02/03, ge30 et ge36 coexistent avec des
`SendSignal(krik,1)` actifs vers `ci01krik`, `ci02krik`, `ci03krik`,
`ge30krik` et `ge36krik`. Ils sont classés comme mise en scène remplacée. Aucun
profil de posture ne réactive une voix directe ; la branche encore active
14992837 de ci01 reste inchangée.

## Méthode

Tester un seul commutateur pendant au moins dix cycles : marche/course,
occupation des points, visée, couverture, réaction à chaque alarme,
OnAlarmDone, mort et sauvegarde/reprise. Comparer temps de route, détection,
posture finale et animations. Combiner uniquement après validation isolée, et
jamais avec une voix directe.

Rejet : route modifiée, IA moins réactive, posture bloquée, animation cassée,
double voix, différence hôte/client ou impossibilité de retrouver exactement
la baseline.
