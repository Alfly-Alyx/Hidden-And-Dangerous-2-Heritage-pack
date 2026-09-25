# Arctic 4 — échec historique après destruction de la radio

État : **documenté, bloqué sur le propriétaire destructible**, 25 septembre 2026.
Aucun générateur ni script activable n'est créé pour ce cas.

## Chaîne réellement présente

Le registre lie `m_AF5_stul_4.Box17` à `R_Arc3_fail.scr`. Ce script possède
`OnHit`, pas un événement de destruction, et son seul `SendSignal(OBJ, 4)` est
commenté. Le destinataire recherché est `dummy_objectives`.

Le contrôleur d'objectifs n'a pas de liaison directe dans le registre :
`dummy_KRVEPROLITI` exécute `R_Arc3_KRVEPROLITI.scr`, qui affecte dynamiquement
`R_Arc3_Objectives` à `dummy_objectives`. En Carnage 3/7, il affecte aussi le
contrôleur Carnage à un autre dummy. Le script d'objectifs effectif vient du
Patch; il utilise `m_AF5_prisj_2` pour l'interaction radio, pas la table Box17.

Son ancien gestionnaire du signal 4 est intégralement commenté, avec une note
indiquant que la radio est indestructible. Il prévoyait l'échec de l'objectif 6
et le sous-titre 04990822. Les interactions commerciales actuelles activent puis
valident cet objectif via l'état de la radio et la synchronisation du dialogue.

## Pourquoi deux décommentages ne suffisent pas

Un coup reçu par le propriétaire Box17 ne prouve ni un coup sur la radio ni sa
destruction. Réactiver cette chaîne ferait échouer une transmission sur un
événement mal attribué. Le texte dormant ne démontre pas non plus que les
branches de succès et d'échec sont mutuellement exclusives lors d'une reprise
ou d'une transmission déjà engagée.

Le vestige et les liaisons sont **OFFICIELS**. Un proxy destructible, son
placement, sa santé et ses règles seraient **MODERNES** jusqu'à découverte de
données commerciales correspondantes. Rien ne justifie de faire de la table un
tel proxy.

## Conditions d'un prototype futur

1. Identifier un véritable propriétaire radio destructible, sa transformation,
   ses collisions et son événement terminal; sinon concevoir un proxy moderne
   propre à une copie laboratoire.
2. Sélectionner cette mission avant chargement; garder la radio indestructible
   commerciale comme défaut.
3. Définir un état terminal unique qui arbitre transmission en cours, succès et
   destruction; ne pas ajouter un second gestionnaire concurrent de l'objectif.
4. Choisir un canal dédié après audit des signaux, sans réutiliser aveuglément 4.
5. Tester tirs sur table seule, tirs sur radio, dégâts non létaux, destruction,
   répétition, transmission simultanée, sauvegarde/reprise et Carnage.

Abandonner l'activation si le dommage à la radio ne peut pas être distingué du
dommage à la table. Le script commercial et ses objectifs restent alors intacts.

## Provenance reproductible

| Archive et entrée | Octets | SHA-256 |
|---|---:|---|
| `missions.dta::missions/arctic4/scripts.dta` | 6073 | `618dbf08b27f3d58ffe5b67b6f515da3f3c17672a8d42ffa1e0f6f2396d64d57` |
| `Scripts.dta::scripts/arctic4/r_arc3_fail.scr` | 105 | `c5482f2dd64a960242b12eb04f5e87928a402e15732f572492bfe37dd03de510` |
| `Scripts.dta::scripts/arctic4/r_arc3_krveproliti.scr` | 261 | `fb6efc81e6efe3a211e6b98244fa17fb43ad3cf8abea5975198c69b6c3770706` |
| `Patch.dta::scripts/arctic4/r_arc3_objectives.scr` | 9629 | `2a6bec68315ea201a8a8f28b385e2db69745f9b6fa81d95045a915db960e18c7` |

Vérification : lecture des archives par `tools/dta_archive.py`, décodage du
registre par `tools/script_binding_audit.py`, suivi de `ScriptAssign` puis lecture
du gestionnaire Patch. Aucune preuve d'exécution n'est revendiquée.
