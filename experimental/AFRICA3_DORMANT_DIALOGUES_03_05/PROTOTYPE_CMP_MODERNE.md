# Prototype désactivé CMP/MODERNE — conversation 04

Ce prototype teste une seule hypothèse : le candidat CMP de déclenchement à
dix mètres peut-il lancer la conversation 04 une fois, sans concurrencer les
comportements déjà actifs ? Il n'est pas une restauration commerciale.

## Périmètre

- Le rayon 10 provient d'un activator CMP entièrement commenté et non lié.
- La garde 31 et le désarmement avant émission sont des sécurités modernes.
- Le script commercial de conversation et AF3a_05/06 restent inchangés.
- Les signaux gestuels 10/11 restent donc sans handler ; les voix et sous-titres
  constituent le seul résultat attendu de cette phase.
- Le signal 2 du prototype est une entrée d'injection manuelle. Aucun raccord
  automatique entre alarme et conversation 04 n'est revendiqué.
- Les conversations 03 et 05 ne sont ni déclenchées ni modifiées.

## Test d'interruption obligatoire

1. Mesurer la baseline sans prototype : aucun signal 1 vers le dummy 04.
2. Dans une copie de test seulement, lier le fichier désactivé à une frame
   expérimentale et tracer les signaux ; ne modifier aucun fichier stable.
3. Vérifier valeur 31 nulle puis vraie, franchissement du rayon, retour dans la
   zone et sauvegarde/reprise. Une seule émission du signal 1 est permise.
4. Déclencher une alarme pendant une réplique. Si l'audio ou les sous-titres
   continuent, consigner l'échec : l'absence d'émetteur d'abort est confirmée.
5. Refaire l'essai en injectant le signal 2 dans l'activator. Cela valide le
   corps d'abort audio du dialogue, pas son câblage à une alarme réelle.
6. Vérifier qu'AF3a_05/06 suivent toujours leurs routes d'alarme et que le
   synchroniseur 05/06 ne parle jamais en même temps que la conversation.

## Porte de progression

Ne pas ajouter de handlers 10/11/12 tant que le déclenchement unique, la
non-concurrence et une source d'interruption déterministe ne sont pas validés.
Un futur retour 12 devra rester étiqueté CMP/MODERNE : CMP l'ajoute en fin
normale, mais le commercial ne l'atteste pas et CMP ne l'ajoute pas à l'abort.
