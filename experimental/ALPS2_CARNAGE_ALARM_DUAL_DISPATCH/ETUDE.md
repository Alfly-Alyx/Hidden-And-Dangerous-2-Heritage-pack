# Alps 2 — double dispatch de l'alarme Carnage

État : **deux routes conservées comme profils exclusifs**, 15 septembre 2026.
Le dispatch Carnage release reste inchangé.

## Les deux branches ne sont pas équivalentes

Dans `AL2_alarm_carn.scr`, l'ancien bloc envoie le signal 3 aux trois frames
`detectoral204_1`, `_2` et `_3`. Ces frames et leurs bindings existent ; `_1`
utilise `detectoral204.scr`, tandis que `_2` et `_3` partagent
`detectoral204_2.scr`.

Le signal 3 ne réveille pas directement les personnages. Il désactive le
détecteur de présence pacifique et arme un détecteur de proximité « alarme ».
Quand le joueur entre à trois unités, chacun de ces scripts envoie alors
`AL2_04,2`. Avant l'alarme, leurs branches pacifiques peuvent aussi envoyer
`AL2_04,1`, `AL2_31,5`, `AL2_05,1` et, pour `_1`, `AL2_33,1`.

Le bloc Carnage actif contourne ces volumes et envoie immédiatement :

```text
SendSignal(al2_04, 2);
SendSignal(al2_05, 3);
SendSignal(al2_31, 4);
```

Activer les six lignes ensemble doublerait au minimum `AL2_04,2` lorsque le
joueur touche les volumes. Les signaux 3 et 4 directs vers 05/31 n'ont en outre
pas d'équivalent dans les branches d'alarme des détecteurs. La route détecteur
n'est donc ni un simple délai ni une copie fonctionnelle de la route directe.

## Profils

- `DIRECT_CARNAGE_RELEASE` — défaut ; conserve les trois envois directs et les
  trois lignes détecteur commentées ;
- `DETECTOR_CARNAGE_LEGACY_TEST` — essai historique exclusif : active les
  détecteurs et supprime, dans cette copie seulement, les trois envois directs ;
- `DUAL_DEDUP_CARNAGE` — bloqué. Il nécessiterait de modifier les trois
  contrôleurs de volume, définir un propriétaire unique pour `AL2_04,2` et
  prouver les intentions de 05/31. Aucun tel contrat n'est attesté.

Les deux branches sont ainsi préservées dans le pack expérimental, mais jamais
émises simultanément. Carnage ne doit pas hériter silencieusement du dispatch
normal.

## Tests d'acceptation

- instrumenter chaque couple destinataire/signal et compter ses réceptions ;
- tester les trois volumes séparément puis leurs zones de recouvrement ;
- entrer dans la salle avant l'alarme, après l'alarme et pendant la cascade ;
- vérifier les états de `AL2_04`, `AL2_05`, `AL2_31` et `AL2_33` ;
- vérifier mort et sauvegarde/rechargement entre armement et proximité ;
- comparer le rythme de combat et les objectifs à Carnage release ;
- refuser toute promotion si un acteur reçoit deux fois le même signal de
  transition ou si 05/31 restent pacifiques dans le profil détecteur.
