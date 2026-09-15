# Protocole — coordination moderne 22/23

Ce protocole n'autorise pas encore une intégration. Il sert à réfuter ou valider
un concept explicitement moderne dans une copie de mission.

## Phase 0 — baseline

1. Observer séparément 22 et 23 depuis le chargement jusqu'à leur boucle
   stable, sans joueur proche.
2. Refaire l'observation en entrant dans les rayons de 30 et 20 unités utilisés
   par leurs scripts respectifs.
3. Déclencher chaque famille d'alarme, puis le signal 20, et journaliser
   animations, positions, suspension, optimisation et détection des morts.
4. Confirmer que la conversation 14/15 se joue intégralement sans intervention
   des deux bindings manquants.

## Phase 1 — contrôleur seul

Installer le nouveau propriétaire près du point milieu, sans signal sortant.
Vérifier pendant dix minutes, puis après sauvegarde/reprise, qu'il ne change ni
IA, animation, objectif, alarmes ni conversation. Toute différence invalide le
choix du propriétaire ou de son autorité réseau.

## Phase 2 — un cycle coordonné

Dans les copies expérimentales des scripts d'acteur :

- attendre que les deux acteurs soient vivants, non alertés et encore dans la
  zone de travail ;
- jouer une seule paire `%%mina`/`%%mina2` avec départ commun ;
- rendre ensuite à chaque acteur son chemin release ;
- sur mort, alarme, proximité hostile ou signal 20, arrêter le cycle et prendre
  immédiatement le chemin release correspondant ;
- ne jamais réarmer le cycle après son achèvement dans la même partie.

Les signaux, délais et éventuels drapeaux sont tous **MODERNES** et doivent être
journalisés comme tels.

## Matrice d'essais

| Cas | Résultat exigé |
| --- | --- |
| joueur absent | aucun cycle déclenché sans la condition choisie |
| approche par 22 puis 23 | un seul départ commun |
| approche inverse | résultat identique |
| mort de 22 avant départ | 23 conserve son comportement release |
| mort de 23 pendant le cycle | 22 abandonne et passe au comportement release |
| alarme pendant chaque animation | arrêt sans posture figée ni signal perdu |
| signal 20 simultané | le combat a priorité |
| sauvegarde avant/pendant/après | aucune répétition ni acteur suspendu |
| conversation 14/15 simultanée | voix et animations 14/15 inchangées |
| variante désactivée | trace fonctionnelle identique à la baseline |

## Critères d'arrêt

Arrêter l'essai si une animation devient non interruptible, si un acteur reste
suspendu, si une alarme est retardée, si la conversation 14/15 change, si une
sauvegarde réarme le cycle ou si la coordination exige d'inventer un dialogue,
un objectif ou une route. Sans source du script disparu, un résultat jouable
reste une mise en scène moderne.
