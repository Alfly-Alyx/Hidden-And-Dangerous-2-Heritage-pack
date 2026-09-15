# Arctic 1 — ancien sélecteur `Rebel_Test`

État : **seconde autorité rejetée, aucun prototype**, 15 septembre 2026.

## Verdict

`R_Arc1A_Rebel_Test.scr` n'a aucun binding ni acteur propriétaire. Il mémorise
un état binaire via le signal 3 puis, au signal 1, envoie 10 (marais) ou 11
(route) à `Rebel`. Aucun émetteur commercial de ses signaux 1/3 n'est démontré.

La release a déjà intégré le choix dans `R_Arc1A_rebel.scr`. `swampYesNo`
commence à 1, passe à 0 sur alarme réelle ou signal 17, puis l'acteur s'envoie
exactement un signal 10 ou 11 après le dialogue d'accueil. Les deux handlers
complets, les voix, les trajets, les objectifs et les retours sont actifs.

Réactiver `Rebel_Test` créerait un second sélecteur asynchrone, fondé sur un état
des gardes d'avion différent de l'alarme/détection release. Il pourrait choisir
une autre branche, envoyer trop tôt ou faire traiter successivement 10 et 11.

## Contrat de préservation

[`SELECTOR_CONTRACT.plan.disabled`](SELECTOR_CONTRACT.plan.disabled) réserve
l'autorité de dispatch à `Rebel` :

- les handlers 10 et 11 restent tous deux intacts ;
- le point de choix release reste après le dialogue d'accueil ;
- `Rebel_Test` n'est ni lié ni recréé ;
- aucun acteur auxiliaire ne peut envoyer directement 10/11.

Une future variante historique ne serait admissible qu'en tant que **source
d'entrée sélectionnée** pour la variable interne, jamais comme second
dispatcher. Elle exigerait les émetteurs exacts 1/3 et la sémantique du statut
des gardes d'avion. Ces preuves manquent, donc même ce profil reste bloqué.

## Tests si le dossier est rouvert

Les parcours silencieux et alarmés doivent chacun atteindre leur branche
release, puis terminer objectifs, scène 3/4 et retour du guide. Un journal de
test doit prouver un seul dispatch et l'impossibilité d'exécuter les deux
handlers dans une partie.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_Rebel_Test.scr` ;
- `.analysis/scripts/base/SCRIPTS/ARCTIC1/R_Arc1A_rebel.scr` ;
- `.analysis/arctic1-full/MISSIONS/ARCTIC1/scripts.dta`.
