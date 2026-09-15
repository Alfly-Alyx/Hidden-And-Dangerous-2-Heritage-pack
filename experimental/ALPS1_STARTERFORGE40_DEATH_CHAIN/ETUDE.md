# Étude expérimentale — chaîne de morts `starterforge40`

État : **variante 2-sur-3 désactivée**, 15 septembre 2026. Aucun script actif,
binding ou installateur n'est modifié et rien n'est compilé.

## Verdict

La lecture la plus cohérente des traces survivantes est : **les deux premiers
morts parmi `ge_01`, `ge_02` et `ge_03` ouvrent pendant dix secondes la fenêtre
dans laquelle l'alarme de `ge_40` peut lancer la relève**.

Ce n'est pas une restauration certaine de trois lignes identiques :

- l'envoi de `ge_01` est conservé textuellement mais commenté ;
- les envois de `ge_02` et `ge_03` sont absents et doivent être reconstruits ;
- les trois scripts déclarent pourtant `starterforge40`, forment le triplet de
  valeurs 21/22/23 et effacent leur valeur respective à la mort ;
- `starterforge40.scr` compte des signaux anonymes, teste `a>1` et son
  commentaire indique que les « premiers 2 » doivent mourir. Il ne peut donc
  pas distinguer un couple fixe ge01/ge02 d'une combinaison quelconque.

Ajouter un émetteur aux trois gardes et conserver le seuil commercial est plus
cohérent que choisir arbitrairement deux noms. Le profil fixe ge01+ge02 reste
non retenu : aucune trace n'exclut ge03.

## Chaîne aval officielle

`starterforge40` commence avec son écoute du signal 2 désactivée. À la première
mort, il incrémente `a`. À partir de la deuxième, il active cette écoute pendant
dix secondes. `ge_40.scr`, lorsqu'il reçoit une alarme, lui envoie le signal 2.
Le contrôleur réveille alors `ge_41` par le signal 1 et remplace le script de
ge40 par `ge_40akce`.

`ge_40akce.scr` et `ge_41.scr` contiennent les déplacements et alarmes de la
relève. Les acteurs et bindings de `GE_01..03`, `ge_40`, `ge_41` et
`starterforge40` existent. La moitié aval n'est donc pas à recréer.

Une limite subsiste : ge40 commence suspendu avec ses événements désactivés,
mais conserve un `OnAlarm()`. Le moteur doit démontrer en jeu que l'alarme peut
bien produire le signal 2 pendant la fenêtre ; l'analyse statique ne le prouve
pas.

## Prototype minimal

[`PROTOTYPE_ONDEATH_DELTAS.scr.disabled`](PROTOTYPE_ONDEATH_DELTAS.scr.disabled)
documente trois remplacements bornés de `OnDeath()` :

- ge01 : réactivation de la ligne commerciale à son emplacement exact ;
- ge02 et ge03 : ajout reconstructif de la même émission avant leurs écritures
  et sorties existantes.

Toutes les commandes actuelles restent dans le même ordre : signal `piskac` de
ge01, valeurs 21/22/23 et `EndScript()`. Le contrôleur commercial n'est pas
remplacé, son seuil, son délai de dix secondes, le signal 2 de ge40, le réveil
de ge41 et l'assignation `ge_40akce` restent intacts.

Le contrat [`CHAIN_CONTRACT.plan.disabled`](CHAIN_CONTRACT.plan.disabled)
impose les six permutations de deux morts. La troisième mort peut rouvrir une
fenêtre avec le contrôleur survivant ; ce comportement doit être tracé avant
toute promotion, pas masqué par un nouveau verrou sans preuve.

## Tests et porte de promotion

1. Capturer la baseline : états de ge40/ge41, signaux 1/2, valeurs 21/22/23 et
   réactions aux tirs avant toute mort.
2. Tester séparément les couples 01+02, 01+03 et 02+03, dans les deux ordres.
   Le premier décès ne doit rien lancer ; le second doit ouvrir une fenêtre de
   dix secondes.
3. Provoquer l'alarme de ge40 avant, pendant et après cette fenêtre. Seul le cas
   pendant doit réveiller ge41 et assigner `ge_40akce` à ge40.
4. Tuer le troisième garde pendant puis après la première fenêtre et déterminer
   si sa réouverture est volontaire, inoffensive ou dangereuse.
5. Vérifier que le signal `piskac` de ge01 et les valeurs utilisées par
   `uniformer.scr` restent identiques à la baseline.
6. Tester tirs multiples, mort quasi simultanée, ge40/ge41 morts en avance,
   sauvegarde/reprise et plusieurs joueurs.

Critères d'arrêt : un couple ne fonctionne pas, signal 2 impossible depuis
ge40, double assignation, seconde relève, compteur perdu après reprise, valeur
21/22/23 incorrecte ou nécessité de remplacer un comportement actuel.

## Retour arrière

Restaurer les trois `OnDeath()` commerciaux. Ne modifier ni
`starterforge40.scr`, ni `ge_40.scr`, ni `ge_40akce.scr`, ni `ge_41.scr`.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_01.scr`, `ge_02.scr`, `ge_03.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/starterforge40.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_40.scr`, `ge_40akce.scr`,
  `ge_41.scr` et `uniformer.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/Scripts.dta` et
  `actors.bin`.
