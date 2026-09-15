# Registre — campagnes et prototypes sans carte complète

L'inventaire des archives ne trouve **aucun dossier de mission** nommé England,
Castle1, Castle2, Bristol/Gary, Allemagne/Germany, Dunkerque/Dunkirk, Urban,
Warehouse ou Train. Seuls `Scripts/ENGLAND`, `Scripts/CASTLE1` et
`Scripts/CASTLE2` existent comme ensembles nommés. Les autres mentions sont
documentaires ou des frames/scripts non attribuables à une carte autonome.

| Concept | Vestige local vérifié | Variante autorisée | Statut |
| --- | --- | --- | --- |
| England | 14 scripts de mission utiles, 7 chemins, pas de carte | `Prototype — reconstruction — England demonstrator` sur petite scène créée | faisabilité, création 3/3 |
| Castle1 | 60 scripts, 41 frames référencées, 203 chemins, objectifs 1–3 | `Test — reconstruction — Castle1 logic` sur banc de scripts | suspendu sans topologie |
| Castle2 | 55 scripts, 72 frames, 63 chemins, quatre objectifs + objectif 5 commenté | `Prototype — reconstruction — Castle2 vertical slice` | meilleur candidat, carte créée |
| Gary | `Norway/R_nor_Gary.scr` vide ; aucun acteur Gary | `Test — reconstruction — Gary character` | suspendu sans rôle/placement |
| Gary Bristol | éléments biographiques dans les sources d'époque, pas d'asset local attribuable | étude narrative séparée | aucune mission |
| Allemagne | campagne annoncée, aucun dossier/lot de scripts homonyme | étude de faisabilité | aucune base de carte |
| Dunkerque | passé de Bristol annoncé, aucun dossier/lot homonyme | étude de faisabilité | aucune base de carte |
| urbain / entrepôt / pont-train | images et descriptions anciennes, aucun paquet local attribuable ; `Burma1/bu1_bridge.scr` n'est pas une preuve du train | diorama créé, jamais « restauré » | identité non vérifiée |

## Tranches autorisées

### England

Le démonstrateur peut matérialiser les 14 frames et sept chemins des scripts,
puis tester ennemis, otage, appels HELP, sniper et détecteurs de tranchée. La
géométrie, les placements, le briefing, les items, les sons, les objectifs et
la fin sont entièrement créés. Aucun lien avec `London_mp` n'est admis sans
correspondance spatiale démontrée.

### Castle1

Créer seulement un banc logique sans décor historique : chaque script reçoit
une frame factice et ses chemins sont testés par grappes. Une mission jouable
est différée tant qu'aucune topologie ne réduit les 203 placements possibles.

### Castle2

Construire une aile moderne limitée au contact Aika/Salter, aux documents, au
dépôt d'armes et à la sortie. Initialiser les objectifs 1–5, tester récupération
anticipée des armes, mort de l'agent, deux apparitions, alarme, quatre caméras et
sauvegarde. Tout mur, placement, son et raccord de checkpoint reste `CRÉATION`.

## Règle pour Bristol, Allemagne, Dunkerque et décors

Une mention historique n'autorise ni acteur, ni carte, ni chronologie inventée.
Ces concepts ne passent en prototype qu'après découverte d'un asset local
attribuable ou après décision explicite de produire une création inspirée. Le
nom d'affichage doit alors commencer par `Test — reconstruction`, jamais par
« restauration ».

