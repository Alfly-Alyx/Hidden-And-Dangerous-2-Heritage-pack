# Étude expérimentale — `ge_10` et `ge_11` depuis forge24

État : **variante additive désactivée, à traiter en fin de projet**, 15 septembre
2026. Aucun script actif, binding commercial ou installateur n'est modifié et
rien n'est compilé.

## Verdict

`detector_forge24.scr` contient deux intentions commerciales très précises :
`SendSignal (ge10,1)` et `SendSignal (ge11,1)`. Elles sont commentées et le
script ne déclare aucun des deux handles. Les décommenter seuls produirait donc
une copie incomplète.

Les destinataires ne sont pas à recréer : `ge_10` et `ge_11` sont liés à leurs
scripts, possèdent chacun un gestionnaire du signal 1 et disposent de leurs
rondes. En revanche, **l'ajout des déclarations dans forge24 est
reconstructif**, même si les lignes exactes peuvent être copiées depuis
`detector_forge20.scr`. Aucun fichier commercial observé ne prouve que ces
handles ont existé dans forge24 sous une forme exécutable.

La variante proposée est additive : elle ne retire, ne remplace et ne modifie
aucune activation conservée dans forge16 ou forge20. Elle ne devient recevable
qu'après preuve que son signal supplémentaire ne relance pas un garde déjà
activé par un autre détecteur.

## Preuves commerciales

- `detector_forge24.scr` est lié à `detector_forge24`. Il active normalement
  `ge_23`, `ge_24` et `ge_25`, puis conserve les deux envois commentés vers
  `ge10` et `ge11`.
- `detector_forge20.scr` déclare exactement
  `Frame ge10; Frm_FindFrame (ge10,"ge_10");` et son équivalent pour `ge11` ;
  ses deux envois vers ces gardes sont également commentés.
- `detector_forge16.scr` déclare `ge11` et conserve son envoi commenté.
- `detector_forge07.scr` constitue un précédent exécutable : il déclare les
  deux handles et envoie déjà le signal 1 aux deux gardes.
- le registre de mission lie `ge_10 -> ge_10.scr`, `ge_11 -> ge_11.scr` et les
  trois familles de détecteurs forge16, forge20 et forge24 à leurs scripts ;
- `ge_10.scr` et `ge_11.scr` traitent `_SignalReceived(1)`, sortent le soldat de
  suspension, rétablissent ses événements et rejoignent `flakejse` ;
- les checkpoints `ge10_01..08` et `ge11_01..04` existent dans `check2.bin`.

La chaîne destinataire est donc **OFFICIELLE**. L'attribution d'une troisième
source active à forge24 reste une **INFÉRENCE soutenue par un vestige**. Les
deux déclarations ajoutées et le verrou local sont une **CRÉATION MODERNE**.

## Prototype borné

[`PROTOTYPE_DETECTOR_FORGE24.scr.disabled`](PROTOTYPE_DETECTOR_FORGE24.scr.disabled)
reprend le script commercial forge24. Il ajoute les deux déclarations exactes
de forge20 et réactive seulement les deux envois commentés. Un verrou moderne
limite ces nouveaux envois à une fois par chargement ; les signaux commerciaux
vers `ge_23..25` restent hors du verrou et conservent leur comportement.

[`ACTIVATION_CONTRACT.plan.disabled`](ACTIVATION_CONTRACT.plan.disabled) fixe
le profil par défaut, interdit toute substitution de forge16/forge20 et ajoute
forge07 à la matrice de collision. Aucun changement des scripts `ge_10.scr` ou
`ge_11.scr` n'est autorisé pour rendre le prototype artificiellement sûr.

Le verrou local ne prouve pas l'idempotence entre plusieurs détecteurs et ne
persiste pas nécessairement après une sauvegarde. Il réduit seulement les
réémissions propres à forge24 ; il ne justifie pas une intégration.

## Tests et porte de promotion

1. Tracer la baseline commerciale et les profils forge16/forge20 conservés :
   source, ordre et nombre de signaux 1 reçus par chaque garde.
2. Tester forge24 en premier, en dernier et presque simultanément avec
   forge07, forge16 et forge20, chacun séparément puis ensemble.
3. Entrer, sortir et revenir plusieurs fois dans le rayon de 12 unités : les
   deux nouveaux envois de forge24 doivent apparaître une seule fois, tandis
   que `ge_23..25` doivent rester identiques à la baseline.
4. Vérifier pour `ge_10` et `ge_11` : sortie de suspension, alarmes, parcours de
   tous les checkpoints, combat, mort et absence de retour à `flakejse` causé
   par un signal tardif.
5. Sauvegarder avant et après chaque source, puis reprendre dans et hors du
   rayon. Répéter avec plusieurs joueurs si le profil est exposé en réseau.
6. Retirer la copie forge24 et confirmer le retour exact aux activations
   forge16/forge20 sélectionnées et au script commercial.

Porte stricte : promouvoir seulement si un second signal 1 est démontré sans
effet observable sur les deux états et si chaque ordre de déclenchement reste
stable après reprise. Au moindre redémarrage de ronde, blocage, téléportation,
double alarme ou divergence réseau, rejeter l'ajout forge24 ; ne pas neutraliser
les activateurs fidèles et ne pas modifier les récepteurs pour sauver le cas.

## Retour arrière

Restaurer uniquement le binding commercial
`detector_forge24 -> detector_forge24.scr` dans la copie de test. Forge16,
forge20, forge07, `ge_10.scr`, `ge_11.scr`, les acteurs et les checkpoints ne
sont jamais touchés.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forge07.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forge16.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forge20.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forge24.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_10.scr` et `ge_11.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/Scripts.dta`,
  `actors.bin` et `check2.bin`.
