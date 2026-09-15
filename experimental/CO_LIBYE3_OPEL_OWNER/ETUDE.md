# Co_Libye3 — propriétaire perdu de `Opel.scr`

État : **ambiguïté réduite mais non levée, aucun binding activé**, 14 septembre
2026. Co_Libye3 commerciale reste intacte.

## Verdict

Le meilleur candidat de provenance est `la_OpelAfK_`, le camion cargo : cet
acteur est propre à la scène coop, tout comme le script orphelin. L'Opel FlaK
`la_OpelFAf_1` existait déjà dans Libye3 solo avec un rôle de canon servi et
aucun équivalent de `Opel.scr`.

Ce faisceau n'est pas une preuve de binding. Le rôle coop de la FlaK est celui
d'une batterie fixe, ce qui rend également plausible un carburant nul pour
empêcher le joueur de déplacer le poste. La décision reste donc : **ne rien
attacher à Co_Libye3 release** et tester deux copies mutuellement exclusives.

## Script et registre

Le script complet tient en trois opérations :

```text
Frame opel;
FRM_GetMyFrame(opel);
Car_SetFuel(opel, 0);
```

L'audit trouve 148 bindings uniques dans les deux registres coop identiques,
149 scripts disponibles et un seul orphelin, `Opel.scr`. Aucun acteur `Opel`
homonyme ne survit et Libye3 solo ne possède ni ce script ni un contrôleur
équivalent.

## Position et rôle des candidats

Les positions ci-dessous sont extraites des champs de transformation
d'`actors.bin` ; les distances sont euclidiennes dans le même repère de scène.

### A — `la_OpelAfK_`, cargo du village

- position : `(177.094, -13.868, 136.371)` ;
- `bedny` à 5,21 unités ; `w_explosive_2` à 5,63 ;
- soldats `VILLAGE_RIF_2`, `VILLAGE_WALK_2/3` à 7,68–9,66 ;
- aucune référence textuelle à ce véhicule dans les scripts coop ;
- acteur absent de Libye3 solo.

Cette proximité place le camion dans l'ensemble village/caisses/explosif. Elle
ne dit pas s'il devait être une cible immobile, un décor ou un véhicule joueur.

### B — `la_OpelFAf_1`, Opel FlaK du checkpoint

- position : `(-164.631, 3.112, -4.287)` ;
- `OPEL_GUNNER` à 3,67 unités ; `OPEL_GUARD1..3` à 9,57–14,55 ;
- le gunner embarque explicitement au siège `1,2`, puis tire sur dix repères ;
- les renforts 3 et 4 se déplacent vers le checkpoint et se tournent vers la
  FlaK ;
- le contrôleur d'objectifs réveille le gunner après la défense du checkpoint ;
- un Opel FlaK du même nom existe en solo et y reçoit aussi un servant, sans
  script de carburant nul.

La voiture n'a aucune route de déplacement coop : son rôle observé est un poste
de tir. Le carburant nul protégerait ce rôle, mais aucun script ne l'affirme.

## Pondération de preuve

| Indice | Cargo | FlaK |
| --- | ---: | ---: |
| script et acteur tous deux propres à la coop | fort | faible |
| nom générique `Opel.scr` | moyen | moyen |
| rôle explicitement stationnaire | faible | fort |
| dépendances qui casseraient si le véhicule bouge | aucune connue | fortes |
| précédent solo sans verrouillage | sans objet | contre-indice |

Conclusion : **cargo 3/4 comme candidat de provenance ; FlaK 2/4 comme candidat
fonctionnel ; propriétaire prouvé 0/4**.

Les deux variantes et leurs critères discriminants figurent dans
`MATRICE_VARIANTES_DE_TEST.md`.

## Porte de réouverture

Seuls un ancien `scripts.dta`, une scène éditable conservant l'assignation ou un
test en jeu montrant une incompatibilité nette peut autoriser un binding. La
position seule ne le peut pas. Aucun `.scr.disabled` n'est ajouté : le script
officiel existe déjà et seule son assignation manque.

