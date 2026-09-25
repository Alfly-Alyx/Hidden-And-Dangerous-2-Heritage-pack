# Libye 3 — déplacement de German15 vers l'alarme

État : **prototype reproductible désactivé**, 25 septembre 2026.

`Li3_German_15` est lié à `Li3_German_15.scr` dans Sabre Squadron. L'acteur
existe à `(195.397003, -13.78614, 75.459534)`. Le signal 1 le réveille et
lance sa ronde `GE15_x1`/`GE15_x2`; les noms sérialisés des checkpoints sont
`Ge15_x1`/`Ge15_x2` (casse différente dans le script commercial lui-même).

Au déclenchement de l'alarme, l'appel `HUMAN_MoveToAlarm()` est commenté avant
les réglages accroupi/course/IA agressive. Le profil
`libye3-german15-move-to-alarm` réactive uniquement cet appel. Les signaux,
la ronde, les réglages et les gestionnaires de fin d'alarme/mort restent intacts.
L'ancien appel est **OFFICIEL** en tant que vestige, pas en tant que
comportement historiquement validé sur la version finale.

La destination de `MoveToAlarm` dépend de l'événement; les checkpoints de ronde
ne prouvent pas que ce déplacement sera praticable. Aucun nouveau checkpoint
ni cible arbitraire n'est créé. Le profil commercial sans déplacement reste le
défaut; sélection exclusive du script d'une future copie laboratoire avant
chargement, sans second acteur ni nouveau canal de signal.

Le [catalogue](../reconstruction-variants.json) verrouille quatre ressources.
La [fabrication commune](../RECONSTRUCTION_BACKLOG/VARIANTES_REPRODUCTIBLES.md)
a produit et vérifié une copie de 1342 octets, hors de l'installation.

## Tests restants

- Comparer les alarmes par vue, tir, explosion et blessure, depuis les deux
  points de ronde et pendant le déplacement.
- Vérifier l'arme antichar, la capacité à engager le véhicule du joueur et le
  délai avant engagement : l'appel est placé avant les modes de combat.
- Tester alarme sans destination accessible, mort et fin d'alarme en chemin.
- Sauvegarder/reprendre avant le signal 1 et au milieu du déplacement.
- Revenir au script commercial sur une partie neuve; ne pas transposer à
  Co_Libye3 sans vérifier séparément sa liaison et ses événements.

Aucune validation en moteur n'est encore enregistrée. Le prototype reste
`.scr.disabled`; aucun fichier du jeu ni de l'installateur n'est modifié.
