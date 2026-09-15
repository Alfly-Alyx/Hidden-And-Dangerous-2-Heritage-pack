# Arctic 1 — son de mort du guide

État : **chaîne fonctionnelle, asset sonore non identifié**, 14 septembre 2026.
Aucun prototype sonore n’est créé ; aucune mission n’a été compilée ou installée.

## Verdict

Le commentaire demande bien de « revoir et compléter le son du guide mort »,
mais la logique de mort elle-même est complète : le guide coupe son animation et
sa voix, neutralise la suite du doublage, puis fait échouer l’objectif 1 avec le
sous-titre 01990209. Ce qui manque est uniquement un son additionnel dont
l’identifiant et la nature ne sont pas conservés.

Réutiliser une réplique, le sous-titre d’échec ou le son 2/5 des dummies qui
abattent Albert fabriquerait une association sans preuve. La proposition sûre
est donc **aucun changement** tant qu’un test en jeu ou un registre sonore ne
fournit pas un asset exact.

## Inventaire des preuves

| Maillon | Comportement effectif | Conclusion |
| --- | --- | --- |
| `R_arc1A_objectives.scr` | commentaire `Zrevidovat a DOPLNIT snd na dead pruvodce` lors de l’initialisation | intention directe, sans ID |
| `R_Arc1A_rebel.scr::OnDeath()` | arrête la morphologie vocale et l’animation, envoie 15 à `dummy_rebel_dabing`, désactive `Near`, puis envoie 9 à `objectives` | chaîne de mort active |
| `R_Arc1A_Rebel_Dabing.scr::OnSignal(15)` Patch | désactive les signaux, appelle `FRM_MorphSpeech(Rebel, 0, 0, 0)`, coupe les sous-titres et termine le script | aucune réplique ne doit survivre à la mort |
| `R_arc1A_objectives.scr` signal 9 | désactive la réussite, écrit `SetObjectiveStatus(1, 3)`, affiche 01990209 pendant 4 s | conséquence de mission complète |
| archives audio | aucun nom d’entrée `01990209` dans `LangEnglish.dta`, `Sounds.dta` ou `Patch.dta` | l’ID du sous-titre n’atteste pas un son |
| `R_Arc1A_kill_him*.scr` | joue trois fois `PlaySound(2, 5)` autour de `HUMAN_Kill(Albert)` | contexte compatible avec des tirs, pas preuve d’un cri de mort |

La variante Patch de `R_Arc1A_Rebel_Dabing.scr` modifie plusieurs timings de
dialogue mais conserve exactement le récepteur de mort 15. Les propriétaires
`Rebel`, `dummy_rebel_dabing` et `objectives` ainsi que leurs signaux sont donc
cohérents entre la base et la couche effective.

## Niveaux de spéculation

- **Faible** : un son lié à la mort a été envisagé ; le commentaire est explicite.
- **Faible** : la chaîne voix 15 / objectif 9 est déjà active et ne doit pas être
  remplacée.
- **Moyenne** : le moteur joue peut-être déjà un cri générique de mort pour
  Albert. Seule une écoute en jeu peut le confirmer.
- **Forte et écartée** : 01990209 serait aussi un fichier vocal jouable.
- **Forte et écartée** : `PlaySound(2, 5)` serait le son manquant ; son usage
  répété autour d’une exécution suggère plutôt les coups de feu.

## Proposition et variantes

### Variante 0 — baseline, recommandée

Ne rien ajouter. Vérifier d’abord si le moteur produit déjà un cri générique,
un impact ou un autre retour sonore lors de la mort normale du guide. Si le
retour est audible et la voix en cours est bien interrompue, le commentaire peut
décrire une vérification restée sans correction nécessaire.

### Variante future — uniquement sur preuve d’asset

Un prototype ne deviendrait recevable que si une source relie explicitement un
cadre sonore ou une paire `PlaySound(groupe, index)` à la mort d’Albert. L’appel
unique serait alors ajouté dans une copie de `R_Arc1A_rebel.scr::OnDeath()`,
après la coupure de parole et avant le signal 9, sans délai et sans réplique.

Faute de cette preuve, aucun `.scr.disabled` n’est fourni : même désactivé, un
exemple avec un ID choisi au hasard ferait passer une invention pour une piste
archéologique.

## Activation et retour arrière

Il n’y a rien à activer dans l’état actuel. Pour un futur essai documenté :

1. dupliquer Arctic 1 et partir de la couche de scripts effective ;
2. ajouter un seul appel sonore à `OnDeath()` sans modifier l’ordre des signaux
   15 et 9 ;
3. conserver 01990209 comme sous-titre seulement ;
4. désactiver en restaurant le script release, sans toucher au doublage ni au
   contrôleur d’objectifs.

## Risques

- doubler un cri de mort déjà joué automatiquement par l’acteur humain ;
- jouer un coup de feu ou une réplique à la place d’un son de mort ;
- relancer une voix que le signal 15 cherche précisément à interrompre ;
- retarder le signal 9 et créer une fenêtre de réussite concurrente ;
- faire échouer l’objectif après sa réussite dans une phase tardive : c’est un
  comportement release à observer, pas à modifier dans cette étude sonore.

## Protocole de test en jeu

1. Enregistrer une baseline audio avec musique et voix séparément réglables.
2. Tuer Albert au repos, pendant chacun des blocs de dialogue, pendant la marche
   et après la réussite de l’objectif de guidage.
3. Pour chaque cas, relever : cri humain automatique, impact, coupure immédiate
   de la phrase, disparition des sous-titres de dialogue, apparition de 01990209
   et passage de l’objectif 1 à l’échec.
4. Déclencher aussi la mort par `dummy_Albert_killer` afin de distinguer le son
   2/5 des tirs du son propre de l’acteur mourant.
5. Tester mort instantanée, dégâts progressifs, friendly fire et reprise d’une
   sauvegarde pendant une phrase.
6. Si un asset exact est ultérieurement prouvé, comparer A/B avec la baseline et
   rejeter tout doublon, retard, réplique ou lecture hors position.

Critères d’arrêt : dialogue post-mortem, son joué deux fois, ID non sourcé,
retard de l’échec, ou altération de la chaîne signal 15 puis signal 9.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_arc1A_objectives.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_rebel.scr` ;
- `.analysis/scripts/patch/SCRIPTS/ARCTIC1/R_Arc1A_Rebel_Dabing.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_kill_him.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_kill_him2.scr` ;
- index d’entrées de `LangEnglish.dta`, `Sounds.dta` et `Patch.dta`.
