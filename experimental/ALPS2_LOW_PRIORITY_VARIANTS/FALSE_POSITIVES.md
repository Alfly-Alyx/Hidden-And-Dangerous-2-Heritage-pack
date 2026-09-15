# Faux positifs — ne jamais réactiver

Ces lignes sont des doublons, raccourcis de développement ou anciennes
branches rendues incompatibles par le flux actif. Elles ne sont pas des
variantes proposées.

| Fichier / vestige | Décision | Motif |
| --- | --- | --- |
| `AL2_16.scr` — `//SetWhenever(odbrany,0)` | verrouillé OFF | couperait le handler encore utilisé au lieu d'ajouter un comportement |
| `egg.scr` — `//goto eee` | verrouillé OFF | saute le chemin initial actif et change le déclenchement de l'easter egg |
| `AL2_cutscene1.scr` — `//goto end` en première ligne | verrouillé OFF | court-circuite toute la cutscene |
| `AL2_playerinstore.scr` — `//SendSignal(obj,2)` | verrouillé OFF | ancien envoi objectif ; le flux actif notifie `AL2_03,1` |
| `AL2_dokumenty.scr` — `//SendSignal(obj,5)` | verrouillé OFF | ancien raccord objectif ; le flux actif envoie `agent,3` |
| `objectives_carn.scr` — ancien `//SetObjectiveStatus(8,0)` | verrouillé OFF | l'objectif 8 possède déjà une progression active et une activation Carnage |

La présence de variantes actives autour de ces lignes ne les rend pas
réactivables. Tout futur examen doit partir du graphe de signaux courant, pas
du simple marqueur de commentaire.
