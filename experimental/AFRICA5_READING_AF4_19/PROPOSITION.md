# Africa 5 — lecture d’archives par AF4_19

État : **API historique non éprouvée, repli release sûr**, 14 septembre 2026.
Le prototype est désactivé ; aucune mission n’a été compilée ou installée.

## Verdict

Le script et les objets nécessaires ont survécu, mais les trois opérations qui
feraient réellement manipuler et lire le dossier sont commentées. Le commentaire
indique lui-même que `read` devait être complété « quand cela fonctionnera ».
La reconstruction fidèle est donc testable, pas présumée fonctionnelle.

La variante API réactive exactement l’intention locale : prendre `book`, lancer
la lecture, arrêter la lecture et lâcher l’objet. Si le compilateur ou le moteur
refuse une seule de ces opérations, le repli sûr est le comportement release :
`HUMAN_Investigate(archive)`, changement de posture et temporisation, sans objet
attaché à la main.

## Inventaire des preuves

| Élément | Constat | Portée |
| --- | --- | --- |
| registre de mission | `AF4_19` est lié à `AF4_19.scr` | propriétaire vérifié |
| `archive` | cadre `m_AF5_slozky01b14`, présent dans `scene2.bin` | cible d’inspection attestée |
| `book` | cadre `m_AF5_slozky01a7`, présent dans `scene2.bin` | objet prévu pour la lecture |
| activité release | `HUMAN_Investigate(archive)` est actif | repli moteur éprouvé localement |
| manipulation | `HUMAN_PickObject(book, 1)` et le `HUMAN_DropObject()` de la boucle sont commentés | intention locale, API de prise non éprouvée ici |
| lecture | `HUMAN_ACTIVITY_Read(1, book)` et `(0, book)` sont commentés avec la note d’attente | API explicitement inachevée |
| corpus effectif | aucune occurrence active de `HUMAN_ACTIVITY_Read` dans les scripts Base/Patch inspectés ; seules les deux lignes commentées d’AF4_19 existent | aucun précédent d’exécution |
| alarme | `OnAlarm()` appelle déjà `HUMAN_DropObject()`, réveille l’acteur, restaure son mode et termine le script | échappatoire importante à conserver |
| reprise | `OnAlarmDone()` restaure les alarmes et retourne à `ACTIVATE` | chaîne de reprise existante |

Les copies Base et Patch ont la même logique utile sur cette séquence ; la copie
Patch doit servir de base au laboratoire puisqu’elle est la couche effective.

## Niveaux de spéculation

- **Faible** : AF4_19 devait examiner puis lire le dossier nommé `book`.
- **Moyenne** : `HUMAN_PickObject` et `HUMAN_DropObject` acceptent ces paramètres
  dans cette mission ; aucun appel actif de prise n’a été trouvé.
- **Forte** : `HUMAN_ACTIVITY_Read` compile et reste interruptible. Il n’existe
  aucun analogue actif dans le corpus inspecté.
- **Faible** : conserver `HUMAN_Investigate(archive)` comme repli. C’est déjà le
  comportement effectif.

## Variante de laboratoire et repli

`PROTOTYPE_READ_API.scr.disabled` remplace uniquement le corps de la boucle
`ACTIVITY` dans une copie Patch d’AF4_19. Il ne change ni `OnSignal(1)`, ni
`OnAlarm`, ni `OnAlarmDone`, ni `OnDeath`.

Le fichier `PROTOTYPE_INVESTIGATE_FALLBACK.scr.disabled` formalise le repli. Il
n’ajoute aucune API : c’est une boucle finie d’inspection et de posture fondée
sur le code release. Elle sert à vérifier que le retour arrière restaure bien la
mission même si la variante API ne se charge pas.

L’alarme reste prioritaire. Aucun `DisableAlarms`, `DisableSignals` ou attente
infinie n’est ajouté autour de la lecture.

## Activation et retour arrière

1. Dupliquer Africa 5 et partir de la copie Patch effective d’AF4_19.
2. Remplacer seulement la boucle `ACTIVITY` par la variante API.
3. Lancer d’abord un contrôle de chargement/compilation de la mission de test.
4. Si `HUMAN_PickObject` ou `HUMAN_ACTIVITY_Read` est refusé, ne pas essayer de
   masquer l’erreur par une autre animation : remettre immédiatement la boucle
   de repli.
5. Pour désactiver, restaurer la copie Patch originale ; aucun acteur, registre
   ou objet de scène ne doit avoir été ajouté.

## Risques

- symbole `HUMAN_ACTIVITY_Read` absent du moteur final ou signature différente ;
- `book` décoratif, non saisissable malgré son cadre valide ;
- objet restant attaché après une alarme, une mort ou une sauvegarde ;
- activité bloquante retardant `OnAlarm()` ;
- répétition de la boucle dupliquant ou faisant disparaître le dossier ;
- collision visuelle entre le personnage, `book` et `archive`.

## Protocole de test en jeu

1. Baseline : envoyer le signal 1, observer l’inspection release, puis déclencher
   une alarme pendant chaque posture et vérifier la reprise.
2. Charger la variante API seule. Un échec de compilation/chargement suffit à
   la rejeter et à rétablir le repli.
3. Observer au moins trois cycles : prise unique, lecture, arrêt, dépôt, puis
   nouvelle inspection.
4. Déclencher une alarme avant la prise, objet en main, lecture active et juste
   après l’arrêt ; AF4_19 doit abandonner l’objet et rejoindre sa chaîne d’alerte.
5. Tuer AF4_19 à chacun de ces stades et vérifier qu’aucun dossier ne reste
   attaché ou dupliqué.
6. Sauvegarder/reprendre avant le signal 1, pendant la lecture et après une
   alarme terminée.
7. Réactiver le repli et confirmer le comportement release, notamment les
   alarmes et la réentrée par `ACTIVATE`.

Critères d’arrêt : crash, symbole inconnu, animation non interruptible, objet
orphelin, alarme retardée ou différence de progression de mission.

## Sources internes

- `.analysis/scripts/patch/SCRIPTS/AFRICA5/AF4_19.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA5/AF4_19.scr` ;
- `.analysis/scripts/base/SCRIPTS/AFRICA2/AF2_14.scr` pour un
  `HUMAN_DropObject()` actif ;
- `Missions/AFRICA5/scene2.bin` et `Scripts.dta` de `missions.dta`.
