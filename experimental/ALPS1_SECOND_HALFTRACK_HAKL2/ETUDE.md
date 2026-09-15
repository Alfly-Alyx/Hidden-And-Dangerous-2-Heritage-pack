# Étude expérimentale — second half-track `hakl_na`

État : **correction couplée désactivée**, 15 septembre 2026. Le cas n'est pas
une ligne à décommenter ; aucun script actif, véhicule, binding ou installateur
n'est modifié et rien n'est compilé.

## Verdict

À la fin de la route de `ge_12.scr`, le vestige
`//sendsignal (hakl2,1);` vise bien la frame `hakl_na`. Or `hakl2.scr` ne traite
que le signal 11. Il rend alors le véhicule visible et appelle
`FRM_TeleportNearCheckpoint(me,"h1"," h2")`.

Deux défauts doivent être résolus ensemble avant tout essai :

1. utiliser le signal 11 attendu par le récepteur survivant, au lieu de
   décommenter le signal 1 sans effet ;
2. remplacer la destination inexistante avec espace et mauvaise casse
   `" h2"` par le nom commercial exact `"H2"`.

Cette paire est la reconstruction minimale techniquement cohérente. Elle reste
une **INFÉRENCE**, car aucune autre copie de `hakl2.scr` ni aucun émetteur Alps 1
du signal 11 vers `hakl_na` ne confirme le protocole historique.

## Chaîne commerciale

- `ge_12.scr` déclare `hakl2` comme `hakl_na`, puis conduit le half-track
  principal jusqu'à `hakl_11` ;
- après l'arrêt, la ligne commentée précède un délai de deux secondes, le
  téléport du véhicule principal `hakl` entre `h3` et `h4`, puis le masquage du
  proxy `haklbum` ;
- le registre lie `hakl_na -> hakl2.scr` ; ce contrôleur met son carburant à
  zéro et le masque au chargement ;
- son unique `OnSignal(11)` le réaffiche et le téléporte ;
- `check2.bin` contient exactement `h1`, `H2`, `h3` et `h4`. Il ne contient pas
  de checkpoint nommé avec un espace initial ;
- `ge_12_car.scr` conserve la déclaration de `hakl_na`, mais n'envoie aucun
  signal, ce qui confirme une branche abandonnée sans résoudre son contrat.

Le véhicule, le binding, le handler et les quatre points sont **OFFICIELS**.
Le choix de relier la fin de route au signal 11 et l'interprétation “second
véhicule de remplacement” restent des **INFÉRENCES**.

## Prototype atomique

[`PROTOTYPE_GE12_END_ROUTE.scr.disabled`](PROTOTYPE_GE12_END_ROUTE.scr.disabled)
remplace le vestige par `SendSignal(hakl2,11)` exactement au même emplacement.
[`PROTOTYPE_HAKL2.scr.disabled`](PROTOTYPE_HAKL2.scr.disabled) conserve le
handler 11 et corrige seulement la seconde borne en `H2`.

Le contrat [`PAIR_CONTRACT.plan.disabled`](PAIR_CONTRACT.plan.disabled)
interdit de tester un seul des deux deltas. Aucun alias `OnSignal(1)` n'est
ajouté : il serait plus invasif et ne possède aucune preuve indépendante.

## Tests et porte de décision

1. Baseline : relever visibilité, transform, carburant, collision et occupant
   de `hakl_na`, `hakl`, `haklbum` avant et après la route de ge12.
2. Dans une copie isolée, appliquer les deux deltas simultanément. Vérifier un
   unique signal 11 et la résolution exacte de `h1`/`H2` sans erreur de frame.
3. Contrôler l'ordre : arrêt du véhicule principal, apparition de `hakl_na`,
   délai, téléport du principal entre `h3`/`h4`, puis masquage du proxy.
4. Tester intersections, physique, visibilité à distance, absence de conducteur,
   carburant nul, destruction anticipée et objectif du half-track.
5. Sauvegarder avant le signal, pendant les deux secondes et après les
   téléports ; vérifier qu'aucun véhicule ne se duplique ou ne réapparaît.
6. Comparer le mode carnage et retirer les deux deltas ensemble.

Critères d'arrêt : checkpoint non résolu, apparition dans la géométrie,
collision entre véhicules, objectif perturbé, second signal nécessaire ou rôle
du véhicule impossible à distinguer d'un simple décor. La réussite technique ne
suffit pas à présenter cette branche comme restauration historique certaine.

## Retour arrière

Restaurer ensemble `ge_12.scr` et `hakl2.scr` commerciaux dans la copie de test.
Ne supprimer ni déplacer `hakl_na`, `hakl`, `haklbum`, `h1`, `H2`, `h3` ou
`h4`.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_12.scr` et `ge_12_car.scr` ;
- `.analysis/scripts/base/SCRIPTS/ALPS1/hakl2.scr` ;
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/Scripts.dta`,
  `actors.bin` et `check2.bin` ;
- `experimental/ALPS1_GE12_HAKL_NA/ETUDE.md`.
