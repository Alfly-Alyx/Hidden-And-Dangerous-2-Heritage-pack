# Co-Libye 3 — étapes manquantes des passagers du half-track

État : deux destinations manquantes isolées, 26 septembre 2026. Routes
commerciales directes intactes, aucun checkpoint créé.

`HAMMER1_SMG_3` et `HAMMER1_LMG_1` sont liés à leurs scripts dans chacun des
deux registres, byte-identiques; ces doubles observations ne prouvent pas
deux affectations simultanées. Ils embarquent au signal 1, respectivement aux
sièges 2 et 4, puis débarquent au signal 2 et rejoignent Action. Chaque signal
est désarmé à sa réception. OnDeath renvoie déjà signal 2 au véhicule.

| Acteur | Première étape commentée, absente | Étape active, présente |
|---|---|---|
| HAMMER1_SMG_3 | HAMMER1_GO4_1 | HAMMER1_GO4_2 |
| HAMMER1_LMG_1 | HAMMER1_GO5_1 | HAMMER1_GO5_2 |

Action règle déjà mode agressif, course/debout et masque 255. OnAlarmDone
rejoint aussi Action : un ajout y serait parcouru **après chaque retour
d'alarme**, pas seulement après le premier débarquement. Cette distinction
doit guider la variante, sans changer les signaux de siège ou de mort.

Les suffixes _1/_2 ne donnent ni coordonnées ni sens de contournement. Relever
les portes de sortie du half-track, obstacles, couvertures et croisements des
deux soldats avant deux points MODERNES distincts. Garder le départ direct
commercial comme option exclusive, jamais lancer deux parcours concurrents.
Tester véhicule encore en mouvement, siège occupé, mort avant sortie, nouvelle
alarme, route bloquée, sauvegarde et nettoyage final.

Sources SabreSquadron.dta :

- SMG_3, 3471 octets, SHA-256
  `cba3f70d0525e904d45e55df7a30242284cb181f65ea8c9edbc0ff4a2bbd324e`;
- LMG_1, 3443 octets, SHA-256
  `d51e7d0130224e8ec21c8c9240a09a18fbc068146c33205712a1f69e03076e9b`;
- missions/co_libye3/check2.bin, 332018 octets, SHA-256
  `62b8177ba59673ce40366a00656e8378e1b4916f09df67c9277a57ea934a3145`.

La recherche de checkpoints est exacte, insensible à la casse et terminée
par NUL; elle ne déduit aucune géométrie. Les variantes de
[propriétaire Opel](../CO_LIBYE3_OPEL_OWNER/ETUDE.md) restent séparées.
