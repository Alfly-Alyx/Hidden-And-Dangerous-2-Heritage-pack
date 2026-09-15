# Libye3 — objectifs 4 et 6

État : **objectif 4 reconstructible sous forme désactivée ; objectif 6 classé
résiduel**, 14 septembre 2026. Aucun catalogue, registre ou script actif n'est
modifié.

## Verdict

Le catalogue Sabre de Libye3 contient six entrées :

| N° | Texte | Libellé anglais | Contrôleur release |
| ---: | ---: | --- | --- |
| 1 | 15530 | `Destroy the wreck of the Liberator.` | actif |
| 2 | 15531 | `Destroy the second section of the equipment.` | actif |
| 3 | 15532 | `Assemble at the planned location with a functional vehicle.` | actif |
| 4 | 15534 | `All members of the unit must survive.` | absent |
| 5 | 15533 | `Eliminate all enemies.` | actif en modes 3/7 |
| 6 | 15533 | `Eliminate all enemies.` | absent, doublon exact du n°5 |

Le n°4 est un objectif optionnel de survie cohérent avec Libye1 et Libye2. Son
point de validation naturel subsiste : `dummy_exitpoint` n'envoie le signal 3
qu'après rassemblement de tous les joueurs avec un véhicule admis, et
`dummy_objectives.scr` réussit alors l'objectif 3. Une réussite conditionnelle
du n°4 à cet endroit est fortement justifiable.

Le n°6 ne possède aucune fonction distincte. Le n°5 affiche déjà le même texte,
s'active seulement en 3/7 et se valide avec le compteur Carnage. **Aucun
prototype n'est créé pour le n°6.**

## Chaîne release complète

Les 73 scripts Libye3 sont tous liés ; aucun propriétaire ou fichier manquant
ne peut cacher un second contrôleur d'objectifs. Dans
`dummy_objectives.scr` :

- l'objectif 1 est actif au départ ;
- le signal 1, issu de `Li3_Liberator.scr`, réussit le n°1 et active le n°2 ;
- le signal 2, issu de `Li3_Cargo.scr`, réussit le n°2 et active le n°3 ;
- le signal 3, issu de `dummy_exitpoint.scr`, réussit le n°3 ;
- en types 3/7, le n°5 est activé et le Whenever `AID` surveille
  `_GetCountOfCarnageEnemies() == 0` avant de le réussir ;
- aucun appel `SetObjectiveStatus` ne vise 4 ou 6 ;
- aucune recherche `_IsTeamMemberDead()` n'existe dans les scripts Libye3.

Le nombre de membres est lu uniquement pour choisir le texte de journal de fin.
Il ne constitue pas une gestion cachée de la survie.

## Objectif 4 — survie de l'unité

### Preuve par les missions voisines

Libye1 possède un objectif optionnel « tous doivent survivre » au n°6. Lors de
la sortie, son contrôleur vérifie explicitement `_IsTeamMemberDead()`, ignore ce
bonus en type 2 et marque le n°6 réussi avant l'objectif principal de sortie.

Libye2 possède le même objectif au n°4, texte 15524. Une fois tous les joueurs
rassemblés avec un véhicule fonctionnel, son contrôleur effectue la même
vérification, ignore également le type 2, réussit le n°4 puis l'objectif de
rassemblement.

Ces deux exemples prouvent que le moteur ne valide pas la survie à partir du
seul catalogue. Ils donnent aussi le moment et la garde attendus. Libye3 possède
le même événement de rassemblement avec véhicule, au signal 3.

### Reconstruction minimale

`PROTOTYPE_OBJECTIVE4_SURVIVAL.scr.disabled` décrit le fragment à insérer dans
une copie laboratoire de `dummy_objectives.scr`, au début de son `OnSignal(3)` :

1. si le type de partie n'est pas 2 ;
2. si aucun membre d'équipe n'est mort ;
3. réussir l'objectif 4 ;
4. poursuivre ensuite le corps release et réussir l'objectif 3.

Comme dans les voisins, aucun échec explicite n'est inventé si un membre est
mort : le bonus reste simplement non réussi. Aucun nouveau texte, signal,
compteur ou état sauvegardé n'est ajouté. La position précise dans le signal 3
est une **INFÉRENCE FORTE**, pas un fragment local archivé.

## Objectif 6 — doublon Carnage

Les objectifs 5 et 6 utilisent exactement le même identifiant 15533. Le
contrôleur initialise uniquement le n°5 en 3/7 et le valide via `AID`. Créer un
second Whenever ou écrire le n°6 doublerait l'affichage et la réussite sans
nouvelle condition de jeu.

Classification : **résidu de catalogue**, fidélité 4/4 pour le constat,
reconstruction 0/4. Le n°6 reste intact et sans écriture. Une source future ne
justifierait sa réouverture que si elle fournit un libellé distinct et une
condition distincte, pas seulement un autre compteur « tous les ennemis morts ».

## Comparaison coop et CMP

La mission commerciale `Co_Libye3` possède huit objectifs différents. Ses
slots 4 et 6 signifient respectivement détruire le Tiger enterré et détruire
une partie de l'équipement du Liberator ; ils appartiennent à une progression
multijoueur propre et ne restituent ni la survie solo ni un second Carnage.

Les variantes CMP `Co_Libye3N` et `Co_Libye3N3` écrivent elles aussi les huit
slots 1 à 8 et conservent cette architecture coopérative. Elles ne fournissent
aucun analogue du couple solo 4/6.

Sources CMP consultées :

- [Co_Libye3N — Objectives.scr](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Co_Libye3N/Objectives.scr) ;
- [Co_Libye3N3 — Objectives.scr](https://github.com/ehylla93/had2-cmp/blob/main/Scripts/Co_Libye3N3/Objectives.scr).

## Protocole de test de l'objectif 4

1. Baseline : terminer Libye3 sans mort et confirmer que seul le n°3 réussit à
   la sortie.
2. Variante, équipe intacte : au signal 3, réussir le n°4 puis le n°3, une fois
   chacun.
3. Perdre un membre avant le Liberator, entre les objectifs 1/2 et juste avant
   la sortie : le n°4 reste non réussi, le n°3 demeure atteignable.
4. Type 2 : aucune écriture du n°4.
5. Types 3/7 : vérifier que le n°5 Carnage reste l'unique objectif « Eliminate
   all enemies » et que le n°6 ne change jamais.
6. Tester chaque véhicule accepté par `dummy_exitpoint`, véhicule détruit,
   joueur hors du rayon 55 et tous les joueurs présents.
7. Sauvegarder/reprendre avant le signal 2, après activation de la sortie et au
   moment du signal 3.
8. Désactiver la variante et retrouver la trace release 1→2→3, avec 5 en
   Carnage et aucune écriture 4/6.

Critères d'arrêt : réussite 4 en type 2, échec de l'objectif principal après une
mort, seconde ligne Carnage, écriture du n°6, double signal de sortie ou
divergence selon le véhicule choisi.

## Sources internes

- `.analysis/metadata/sabre/GameData/Gamedata01.gdt` ;
- `.analysis/scripts/sabre/Scripts/libye3/dummy_objectives.scr` ;
- `.analysis/scripts/sabre/Scripts/libye3/dummy_exitpoint.scr` ;
- `.analysis/scripts/sabre/Scripts/libye3/Li3_Liberator.scr` ;
- `.analysis/scripts/sabre/Scripts/libye3/Li3_Cargo.scr` ;
- `.analysis/scripts/sabre/Scripts/libye1/AF1_objective.scr` ;
- `.analysis/scripts/sabre/Scripts/libye2/AF2_objective.scr` ;
- `.analysis/scripts/sabre/Scripts/co_libye3/Objectives.scr` ;
- `output/audit/full-game-audit.json`.
