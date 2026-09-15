# Arctic 1 — faux positifs verrouillés

État : **ne jamais reconstruire**, 15 septembre 2026.

| Élément | Preuve | Décision |
| --- | --- | --- |
| `R_Arc1a_print_objective.scr` | commentaire « help script », trois `printf` d'objectifs console, aucun binding | outil de développement |
| `save game value.scr` | écrit la taille de l'équipe dans la valeur 1, aucun binding | test de développement |
| `tree01.scr` | affiche des valeurs aléatoires, masque/réaffiche un porteur ; ni binding ni acteur `tree01` | test sans propriétaire |
| anciens `HUMAN_UseInv(99)` / `%%dalekohled` des gardes mer | remplacés dans les deux scripts par `HUMAN_ACTIVITY_Binoculars()` et `BinocularsEnd()` actifs | mécanisme release supérieur |
| téléports des deux gardes souterrains | commentés ; `HUMAN_Move("UnDoor_1/2")` et rotation sont actifs au retour d'alarme | route release conservée |
| ancien choix externe `Rebel_Test` | second sélecteur face à `swampYesNo` | rejeté dans son dossier dédié |
| `R_Arc1A_ohen_LMP.scr` brut | boucle sans délai et sans propriétaire | interdit ; étude dédiée bloquée |
| CUDLIK radio Arctic 1 | mécanisme stable déjà traité par le principal | hors lot, ne pas dupliquer |

Les cinq premiers scripts/vestiges ne sont pas des options esthétiques
désactivées. Leur contenu et/ou leur remplacement actif expliquent leur absence
du registre. Aucun dossier futur ne doit les reclasser sur la seule présence du
fichier source.
