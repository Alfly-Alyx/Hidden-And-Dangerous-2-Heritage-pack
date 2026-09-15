# Étude expérimentale — voix du garde de toit AF1_12

État : **identifiants audio non résolus, test désactivé**, 15 septembre 2026.
Aucun son n'est activé et rien n'est compilé.

## Verdict

Le script Africa 1 d'AF1_12 conserve deux appels commentés à des emplacements
précis :

- `PlaySound(9, 53)` au signal 20, avant le déplacement vers `af1_12_01` ;
- `PlaySound(9, 50)` après le déplacement et l'embarquement sur
  `w_mg42Crouch_01` dans `OnAlarm()`.

Aucun autre script commercial Base/Patch n'emploie ces couples exacts. Il
n'existe donc pas d'analogue permettant de conclure au locuteur, au texte, au
volume ou à la disponibilité de ces entrées.

## Vérification de banque

`Sounds.dta` est présent et lisible, et l'API `PlaySound(9, ...)` est utilisée
ailleurs. L'inventaire des archives ne fournit toutefois pas de table locale
reliant directement le couple `(banque 9, index 50/53)` à un nom de fichier
auditable. Les recherches de noms évidents `900050/900053` ne donnent pas de
ressource correspondante.

La banque ne peut donc être validée que par une table moteur supplémentaire ou
par audition contrôlée en jeu. La simple absence d'erreur ne suffit pas : il
faut confirmer qu'une voix correcte, spatialisée sur AF1_12 et adaptée au
contexte est réellement entendue.

## Prototype minimal

[`PROTOTYPE_VOICE_CALLS.scr.disabled`](PROTOTYPE_VOICE_CALLS.scr.disabled)
documente les deux insertions sans déplacer aucune commande. Les essais se font
séparément : 53 seul, puis 50 seul, puis les deux uniquement si chacun est
validé.

Les deux chemins protégés sont :

- signal 20 : désactivation des signaux, station debout, mouvement, arme,
  portée de vue et sortie ;
- alarme : arrêt, course, réveil, signal `dummy_alert`, mouvement vers le point
  MG42, embarquement puis `EndScript()`.

Aucun délai, garde `if(!atpos)`, boarding, signal, alarme ou destination n'est
modifié.

## Test audio et fonctionnel

1. Capturer une baseline de chaque branche sans son.
2. Activer 53 seul dans une copie : vérifier absence d'erreur, contenu vocal,
   langue, locuteur, durée, volume, spatialisation et répétition.
3. Déclencher signal 20 plusieurs fois et pendant une alarme ; le son ne doit
   pas bloquer la route ni masquer une alerte prioritaire.
4. Revenir à la baseline, puis tester 50 seul juste après l'embarquement MG42.
   Vérifier que la voix provient du garde et que le servant reste opérationnel.
5. Tester mort, MG42 occupée/détruite, alarme répétée, distance, murs,
   sauvegarde/reprise et différentes langues installées.
6. Comparer les deux branches instruction par instruction hors PlaySound.

Critères d'arrêt : silence ambigu, mauvais locuteur/langue, son global au lieu
de spatial, répétition abusive, boarding retardé, route changée ou erreur
d'index. Sans identification positive, laisser les lignes commentées.

## Retour arrière

Remettre les deux lignes en commentaire dans la copie expérimentale. Aucun
asset, frame, binding ou banque n'est ajouté au dépôt.

## Sources internes

- scripts Base/Patch `AFRICA1/AF1_12.scr` ;
- corpus Base/Patch pour la recherche exacte des deux appels ;
- `D:/Games/Hidden and Dangerous 2/Sounds.dta` et inventaire
  `.analysis/langenglish-list.json`, consultés sans extraction audio.
