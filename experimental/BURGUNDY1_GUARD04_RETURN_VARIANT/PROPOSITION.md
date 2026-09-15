# Burgundy 1 — retour optionnel de la garde 04

État : **release conservée, variante patrimoniale exclusive**, 14 septembre
2026. Aucun script actif n’est remplacé et aucune compilation n’est effectuée.

## Verdict

Le binding commercial relie bu1_04 à bur1_04.scr. Son signal 1 fait marcher la
garde vers 03_01, ouvrir la barrière, réveiller le chauffeur, attendre 20 s,
refermer la barrière puis écrire SaveGameValue(61,1). Entre la fermeture et
l’écriture subsiste une seule ligne commentée : HUMAN_Move("04_01").

Le checkpoint humain 04_01 existe exactement une fois dans le check2 solo, à
la position -3.038040, 1.779683, 15.901890, avec quatre liens.

Le déplacement est donc techniquement testable, mais pas neutre : HUMAN_Move
est bloquant. La valeur 61 ne passe à 1 qu’après l’arrivée, retardant les six
répliques de bur1_rozhovor_ubrany.scr. Ce dialogue écrit ensuite 61=2, valeur
qui fait partir le chauffeur sur PATH02. Réactiver la ligne change donc aussi
la cadence du convoi.

## Deux variantes exclusives

- **RELEASE_IMMEDIATE_HANDOFF**, sélectionnée par défaut : fermeture de la
  barrière puis 61=1, comportement commercial inchangé ;
- **HERITAGE_RETURN_BEFORE_HANDOFF** : mouvement attesté vers 04_01, puis
  61=1. Cette variante accepte explicitement le retard du dialogue et du convoi.

VARIANT_SELECTOR.scr.disabled conserve les deux corps sous forme neutralisée.
Une copie de mission ne doit en recevoir qu’un. Aucun réglage en cours de partie
et aucun remplacement forcé de la release ne sont proposés.

La variante coopérative est hors périmètre : son bur1_04 écrit directement
61=2 et possède un contrat de conversation différent. Copier le delta solo
modifierait sa synchronisation réseau sans preuve.

## Variante additive écartée

Écrire 61=1 avant HUMAN_Move préserverait le départ du dialogue, mais la garde
prononce deux répliques pendant qu’elle se déplace. Attendre 61=2 dans un nouveau
Whenever ferait courir son retour en même temps que le départ du convoi et
ajouterait un verrou de répétition inédit. Ces solutions modernes restent moins
fidèles que le choix exclusif et ne sont pas prototypées.

## Tests

1. Baseline release : chronométrer fermeture, passage 61=1, six répliques,
   passage 61=2 et départ PATH02.
2. Heritage : mesurer le temps de 03_01 à 04_01 et vérifier que 61 reste à 0
   pendant tout le trajet.
3. Confirmer les deux répliques de bu1_04 seulement après son arrivée.
4. Bloquer le chemin, déclencher alarme/mort pendant le retour et vérifier que
   le convoi ne reste pas définitivement figé.
5. Tester sauvegarde avant fermeture, pendant le mouvement, à 61=1 et 61=2.
6. Vérifier le chemin d’alarme lgv49 et SaveGameValue(70), sans interaction avec
   le retour optionnel.

Retour arrière : sélectionner le corps release ou restaurer bur1_04.scr solo.
Le check2 commercial ne nécessite aucune modification.

