# Étude expérimentale — branche retirée `ge_12` vers `hakl_na`

État : continuation véhicule/décor retirée, 14 septembre 2026. Aucun prototype
n'est proposé et aucun script commercial n'est modifié.

## Verdict

La ligne commentée `//sendsignal (hakl2,1);` ne peut pas être restaurée seule.
La frame `hakl2` désigne `hakl_na`, relié à `hakl2.scr`, mais ce contrôleur ne
gère que le signal 11. Décommenter l'envoi 1 resterait donc sans effet. Aucun
émetteur 11 vers cet acteur n'est conservé.

Le cas est classé **architecture alternative retirée, coupée des deux côtés** :
pas une faute locale dont le numéro pourrait être corrigé sans autre preuve.

## Séquence officielle de `ge_12`

Dans la branche normale, ge_12 conduit l'acteur véhicule `hakl` le long de
`hakl_001`, `hakl_01` à `_09`, puis `_07`, `_08` et `_11`. À l'arrivée :

```text
HUMAN_Drive("",0);
//sendsignal (hakl2,1);
Delay(2000);
FRM_TeleportNearCheckpoint(haklx,"h3", "h4");
FRM_SetOn(hakl,0);
```

Les noms locaux sont trompeurs :

- `haklx` est la frame `hakl`, le véhicule effectivement conduit et téléporté ;
- `hakl` est la frame `haklbum`, un proxy/élément visuel ensuite masqué ;
- `hakl2` est `hakl_na`, le véhicule alternatif.

`hakl2.scr` met `hakl_na` sans carburant et invisible au démarrage. Son unique
récepteur 11 le rend visible et le téléporte entre `h1` et `h2`. Il n'est pas
appelé par `ge_12.scr` ni par un autre script Alps 1 conservé.

La variante carnage `ge_12_car.scr` déclare les mêmes trois frames, mais ne
référence jamais `hakl2`; elle téléporte seulement le véhicule actif vers les
checkpoints carnage. Elle confirme que la déclaration a survécu à plusieurs
branches après l'abandon de sa consommation.

## Interprétation

Le montage le plus plausible est une ancienne substitution de véhicule ou de
décor en fin de trajet : déplacer le véhicule conduit hors de sa position,
masquer un proxy, puis faire apparaître `hakl_na` ailleurs. Mais les traces ne
donnent pas :

- si l'envoi devait être 1 ou 11 ;
- si `hakl_na` remplaçait le véhicule, le doublait ou préparait une séquence
  ultérieure ;
- l'ordre historique entre apparition, téléportation et masquage ;
- la raison du carburant à 0 et la propriété future du véhicule.

Le handler 11 est une preuve de fonctionnalité autonome, pas une autorisation à
changer le numéro commenté. Inversement, ajouter un alias 1 à `hakl2.scr`
modifierait un protocole dont aucun autre utilisateur n'est connu.

## Décision et porte de test

Ne pas décommenter l'envoi, ne pas le convertir en 11 et ne pas ajouter de
handler 1. Une réouverture exige une ancienne copie de `ge_12.scr` ou de
`hakl2.scr`, ou une scène/binding montrant l'ordre de substitution.

À défaut, un constat laboratoire non intégré peut seulement relever : position
et visibilité de `hakl`, `haklbum` et `hakl_na` avant/après la fin du trajet,
occupation du véhicule, objectif du hakl, sauvegarde/reprise, puis comparaison
avec le mode carnage. Aucun de ces tests ne choisit à lui seul le signal exact.

## Sources internes

- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_12.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/ge_12_car.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/hakl2.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/obj_hakl.scr`
- `.analysis/scripts/base/SCRIPTS/ALPS1/detector_forhakl.scr`
- `.analysis/mission-assets/alps1/base/MISSIONS/ALPS1/Scripts.dta`
