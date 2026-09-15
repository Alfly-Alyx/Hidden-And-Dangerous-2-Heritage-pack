# Étude expérimentale — propriétaire de la fumée du Junkers d'Africa 2

État : liaison manquante classée comme résidu remplacé, 14 septembre 2026.
Aucun fichier substitut, handler ou effet supplémentaire n'est créé.

## Correction du constat de binding

Le registre effectif contient bien la liaison cassée :

```text
HoriciJunkers.engine_l00 -> AF2_particle_junkers.scr
```

Le fichier cible est absent de toutes les couches de scripts inventoriées.
En revanche, `AF2_hidejunkers.scr` n'est **pas** non relié : le même registre
contient `HideJunkers -> AF2_hidejunkers.scr`. Son détecteur positionnel est
donc actif, même si sa gestion de particule est incohérente.

## Propriétaire actif et cycle complet

`dummy_turnat -> AF2_actprelet.scr` possède déjà tout le cycle de la fumée :

1. il résout `HoriciJunkers.engine_l00` ;
2. il y crée `FRM_CreateIndexedParticle(16, part01, dymzkridla)` ;
3. il joue la séquence aérienne pendant environ 19 secondes ;
4. il masque le Junkers et les autres avions ;
5. il termine exactement l'index qu'il a créé avec
   `FRM_FinishIndexedParticle(dymzkridla)`.

Le créateur et le destructeur partagent ainsi la même variable locale et la
même exécution. C'est un propriétaire complet, actif dans Base et Patch.

## Le cas `AF2_hidejunkers.scr`

Ce script surveille l'arrivée du Junkers à moins de cinq unités de sa propre
frame `HideJunkers`, puis masque l'avion et réveille AF2_05/06. Il déclare lui
aussi un entier local `dymzkridla` et appelle
`FRM_FinishIndexedParticle(dymzkridla)`, mais ne crée jamais de particule et ne
reçoit jamais l'index produit par `AF2_actprelet`.

Sauf sémantique globale non documentée des index, cette valeur locale non
initialisée ne peut pas désigner de manière fiable la fumée créée dans l'autre
script. La ligne est vraisemblablement un reste de l'ancien partage de
responsabilité. Elle ne prouve pas qu'une seconde fumée doive être créée.

## Résidu remplacé ou effet distinct ?

Les indices en faveur d'un remplacement sont forts :

- le fichier manquant porte un nom générique de particule Junkers ;
- son binding vise exactement la frame utilisée par `AF2_actprelet` ;
- le script actif crée déjà la particule 16 sur cette frame et la termine ;
- aucun émetteur, signal ou autre identifiant de particule ne décrit un second
  effet ;
- Base et Patch conservent le même cycle actif.

L'hypothèse d'un effet distinct reste abstraitement possible — autre type de
fumée, durée continue avant ou après la séquence — mais aucune source n'en fixe
le type, le moment ou l'arrêt. Créer un fichier substitut sur le binding actuel
risquerait au minimum deux particules superposées pendant la séquence aérienne.

## Verdict et porte de réouverture

Classer `AF2_particle_junkers.scr` comme **ancien propriétaire remplacé par
`AF2_actprelet.scr`**, avec binding de registre resté pendant. Ne pas combler
le fichier absent et ne pas ajouter une seconde création de particule.

Une maquette ne deviendrait recevable qu'avec une source révélant un effet
différent de l'index 16 ou une fenêtre temporelle exclusive. Elle devrait alors
désactiver explicitement le propriétaire actif pendant cette fenêtre, tracer
les deux index et prouver l'absence de double fumée après sauvegarde/reprise.

## Tests de constat recommandés

- tracer la création et la fin de l'index par `AF2_actprelet` ;
- relever le moment exact où le detector `HideJunkers` devient vrai ;
- vérifier l'effet réel de son appel de fin sur l'index local non initialisé ;
- confirmer qu'AF2_05/06 reçoivent leurs signaux même si cette ligne est sans
  effet ;
- sauvegarder/reprendre avant, pendant et après la séquence aérienne et vérifier
  qu'aucune fumée ne persiste.

Ces tests servent à nettoyer la compréhension du flux actif, pas à autoriser
le script manquant.

## Sources internes

- registre effectif `missions/africa2/scripts.dta`
- scripts Base/Patch `AF2_actprelet.scr` et `AF2_hidejunkers.scr`
- inventaire des scripts effectifs confirmant l'absence de
  `AF2_particle_junkers.scr`
