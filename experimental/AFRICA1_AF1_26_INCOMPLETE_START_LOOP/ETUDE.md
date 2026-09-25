# Africa 1 — sortie de la boucle incomplète AF1_26

État du 25 septembre 2026 : variante **MODERNE**, désactivée, validation moteur
en attente. Aucun trajet historique n'est revendiqué ou inventé.

## Preuve commerciale et diagnostic

`Patch.dta::Scripts/africa1/AF1_26.scr` contient 1752 octets, SHA-256
`864019f2264626732713ba796df742b90d7867a0768c92445f096ba345123dc2`.
Le registre commercial lie une seule fois `AF1_26` à ce script et le propriétaire
est sérialisé dans `Patch.dta::Missions/africa1/actors.bin`.

Le gestionnaire `OnAlarmDone` rétablit les alarmes, la portée de vue 80 et
l'optimisation, puis saute à `START`. Ce label ne contient que le commentaire
`doplnit` et un retour immédiat à lui-même : aucune attente ni activité.
C'est une boucle vide attestée; son coût exact et l'ordonnancement du moteur
restent à observer, pas un gel du jeu déjà démontré.

## Modification minimale

Le profil `africa1-af126-safe-idle` change seulement le retour interne de cette
boucle en `goto END`, vers le label terminal déjà utilisé par l'initialisation,
l'activation de proximité et le chemin d'alarme non terminal.

Ce choix moderne conserve les réglages de fin d'alarme, la réaction de proximité,
l'animation assise initiale, les branches d'alarme et `OnDeath`. Il n'ajoute ni
trajet, ni checkpoint, ni signal, ni objectif; il n'appelle pas `EndScript()` et
ne réarme pas le détecteur de proximité désactivé par l'alarme. Revenir à
`ACTIVATE` aurait imposé une remise en posture assise non justifiée après combat.

Le [catalogue](../reconstruction-variants.json) verrouille les trois empreintes
commerciales et l'ancre exacte. Une boucle déjà enrichie par un autre mod est
refusée. La surcharge libre Africa 1 doit être exclue explicitement pour cette
expérience; elle n'est ni remplacée ni déclarée compatible.

## Isolation et validation

Utiliser les générateurs de [variantes](../RECONSTRUCTION_BACKLOG/VARIANTES_REPRODUCTIBLES.md)
et de [laboratoires](../RECONSTRUCTION_BACKLOG/LABORATOIRES_DESACTIVES.md), avec
le profil ci-dessus. La copie témoin reste commerciale; la copie variante ne
change que ce script. Ne pas cumuler cette expérience avec celle de l'officier 21
avant les mesures individuelles.

Tests moteur encore requis :

1. Observer le même démarrage et la même activation à 100 m dans les deux copies.
2. Déclencher une alarme non 32 puis sa fin; vérifier une sortie vers l'attente,
   sans occupation anormale et sans retour spontané en position assise.
3. Vérifier une nouvelle alarme après cette sortie, puis la mort du propriétaire.
4. Vérifier séparément la branche d'alarme 32, inchangée.
5. Sauvegarder/recharger avant alarme, pendant le déplacement et après sa fin.
6. Finir la mission : aucun objectif, voix ou événement ne doit être doublé.

Abandonner la promotion si le label terminal ne laisse pas les événements
fonctionnels, si l'IA devient inactive ou si la reprise change le comportement.
Retrait : supprimer uniquement l'entrée de laboratoire isolée; aucun fichier
commercial n'a besoin d'être restauré lors de la simple génération.
