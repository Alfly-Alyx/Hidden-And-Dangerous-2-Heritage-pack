# Czech2 — ancien dialogue déclenché par la porte

État : **alternative exclusive conçue, aucun signal réactivé**, 14 septembre
2026. `cut2.scr` commercial reste actif et inchangé dans Czech2 release.

## Chaîne conservée

L'acteur libre `bigboskecac` existe et son script est l'unique orphelin avec
propriétaire homonyme libre. Après le signal 1, il attend trois secondes puis
fait parler `big_boss` avec 19993810 pendant quatre secondes et 19993811 pendant
quatre secondes.

`doors2.scr`, lié à `dobytcak204`, conserve dans `OnUse()` :

```text
//SendSignal(bigkec,1);
SendSignal(LMswitch,2);
```

La première ligne est le raccord historique exact. Les fichiers
`Tables/Dabing/19993810.dat` et `19993811.dat` existent.

## Remplacement commercial

`bigbossdetector.scr` lance la cinématique 2 lorsque le joueur arrive à une
unité du Big Boss. `cut2.scr`, lié à la frame `cut2`, joue déjà 19993810 et
19993811, puis 19993813, 14 et 15. La cinématique gère également caméra,
duplicata du joueur, musique, ligotage du boss et signal 1 aux objectifs.

`cut2_2.scr`, orphelin, répète la même scène presque à l'identique et ne doit
pas être lancé en parallèle. La répétition des deux premières voix dans le
dialogue de porte puis dans `cut2` indique un ancien déclenchement remplacé.

## Verdict

Réactiver la ligne de porte dans Czech2 produirait deux propriétaires des mêmes
répliques et permettrait des répétitions à chaque usage. Cette restauration
brute est rejetée.

Deux formes additives sont admissibles :

1. **fonction moderne distincte** : la porte déclenche un indice textuel ou un
   état de journal créé pour la variante, sans 19993810/11 ; la cinématique
   release reste intégrale ;
2. **alternative audio exclusive** : une copie de mission arbitre les deux
   répliques entre la porte et une copie explicitement modifiée de `cut2`.

La seconde forme est spécifiée dans `ARBITRAGE_AUDIO.md` sous le nom
`Czech2 [Alternative — dialogue porte]`. Elle ne remplace jamais silencieusement
la cinématique commerciale.

## Tests

- porte avant cinématique, cinématique avant porte et usage simultané ;
- dix usages rapides de la porte ;
- Big Boss mort avant chaque déclencheur ;
- sauvegarde avant la porte, entre les deux voix, puis pendant la cinématique ;
- vérification de 19993810/11 exactement une fois et de 19993813–15 toujours ;
- caméra, duplicata joueur, ligotage, musique et objectif identiques à la
  release ;
- retour à Czech2 release avec `doors2.scr` toujours commenté.

