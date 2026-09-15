# Étude expérimentale — roster Base d'Ardens1_Obj

État : seconde entrée proposée, étude seule, mise à jour le 15 septembre 2026. Aucun script,
registre, volume, son ou package jouable n'est créé.

Nom d'affichage demandé pour une future branche :
`Ardennes1 [Prototype Base]`. Cette entrée serait additive et distincte de
`Ardens1_obj`; elle ne remplace jamais la carte Objectifs Sabre.
Sa classification reste explicitement `PROTOTYPE/RECONSTRUCTION` : l'inventaire
Base est attesté, mais son scénario jouable ne l'est pas.

La déclinaison solo exigée est préparée séparément dans
[`VARIANTE_SOLO_RECONSTRUCTION.md`](VARIANTE_SOLO_RECONSTRUCTION.md), sous le
nom de travail `Ardennes1 [Reconstruction Solo — Prototype Base]`.

Sa fiche transversale figure aussi dans
[`MP_ONLY_TO_SOLO_MATRIX`](../MP_ONLY_TO_SOLO_MATRIX/ARDENS1_OBJ/FICHE.md).

## Verdict

La carte Base est une extraction technique complète de son entrée
`Missions.dta` : ses **12 ressources d'archive** sont identifiées. Cette
complétude du conteneur ne signifie toutefois pas que le scénario soit
fonctionnel. La scène est une composition antérieure très proche de la scène
Sabre — l'audit amont mesure 97,1 % de frames communes — mais elle ne conserve
pas les pilotes nécessaires à une partie achevable. Elle contient trois
Sherman et deux Tiger, contre deux Sherman et un Tiger dans Sabre, ainsi que
trois canons nommés différemment et une Jeep.

Son unique script objectif ne conserve aucune action legacy :
`Ardens1_obj.scr` est fonctionnellement identique dans Base et Sabre et fait
seulement ceci :

```text
SetObjectiveStatus(1, 0)
SetObjectiveStatus(2, 0)
SetObjectiveStatus(3, 0)
```

La scène Base n'a qu'un binding `dummy_obj -> Ardens1_obj.scr`, aucun
validateur de canon et aucun `volumy.bin`. `dummy_obj1`, `dummy_obj2` et
`dummy_obj3` sont bien présents dans `actors.bin`, mais aucun script Base ne
les pilote. Aucun script Base ne pilote non plus les deux véhicules
supplémentaires, la Jeep, ni une réussite/condition d'échec associée à ce
roster. La carte ne peut donc pas être publiée par simple copie. Une future
version sera une **création moderne à partir d'un roster et d'une géométrie
commerciaux**, clairement étiquetée prototype.

## Deux compositions distinctes

| Élément | Base | Sabre release |
| --- | --- | --- |
| Sherman jouables/placés | `la_shermanw_`, `_2`, `_3` | `la_shermanw_01`, `_02` |
| Tiger jouables/placés | `la_tigerw_`, `_2` | `la_tigerw_01` |
| canons objectifs | `la_kan17mmw_`, `_2`, `_3` | `la_kan17mmW_01`, `_02`, `_03` |
| Jeep | `la_JeepW_` | `la_JeepW_01` |
| dummies secondaires | `dummy_obj1`, `dummy_obj2`, `dummy_obj3` | aucun pilote équivalent requis par le contrat Sabre |
| bindings | 1 | 4, tous résolus |
| ressources d'archive | 12, extraction Base complète | jeu de ressources Sabre distinct |
| `volumy.bin` | absent | présent |
| `sounds.bin` | présent | présent |
| validation | aucune | trois charges et trois scripts dédiés |

La scène Base mesure 3 549 755 octets ; la scène Sabre 3 552 622 octets. Leur
proximité ne signifie pas que les volumes, noms de frames ou contrats de
destruction soient interchangeables.

## Baseline Sabre à préserver

La release lie chaque canon à un script :

```text
la_kan17mmW_01 -> Ardens1_delo1.scr
la_kan17mmW_02 -> Ardens1_delo2.scr
la_kan17mmW_03 -> Ardens1_delo3.scr
```

Chaque validateur surveille l'état 2 d'une charge `w_explosive_01/02/03`,
active deux dummies d'explosion et une caisse propres à son canon, attend
200 ms, détruit son canon et réussit exactement l'objectif correspondant. Ces
charges, explosifs/caisses et scripts de sabotage existent dans la scène
Sabre et sont absents du contrat Base.

Ce système ne doit pas être injecté dans la scène Base sous les noms Sabre :
les canons, les dummies, les caisses, les volumes d'interaction et leurs
placements ne coïncident pas automatiquement.

## Validation à reconstruire

Deux modèles sont techniquement envisageables, mais **aucun n'est attesté pour
la scène Base** :

### A — mort directe du canon

Un script par canon réussirait son objectif dans `OnDeath`. Cette solution
réutilise les trois canons existants et demande peu d'actifs nouveaux, mais elle
autorise mines, roquettes, chars ou dégâts collatéraux à valider la mission. On
ne sait pas si cette liberté faisait partie du mode Base.

### B — charges inspirées de Sabre

La branche ajouterait trois charges, six dummies d'explosion, trois éléments de
décor et les volumes d'action nécessaires, puis adapterait les validateurs aux
noms Base. Cette solution reproduit le geste de sabotage de la release Sabre,
mais importe dans la composition antérieure un design plus tardif.

Le choix **OnDeath direct contre charges Sabre est spéculatif**. Il doit être
présenté comme règle moderne dans le menu ou la documentation de la carte, pas
comme comportement Base retrouvé. Aucun prototype n'est fourni avant ce choix.

## Architecture additive

| Entrée | Scène | Validation | Statut |
| --- | --- | --- | --- |
| `Ardens1_obj` | roster Sabre 2 Sherman / 1 Tiger + Jeep | charges Sabre | release inchangée |
| `Ardennes1 [Prototype Base]` | roster Base 3 Sherman / 2 Tiger + Jeep | à choisir et étiqueter | nouvelle mission `PROTOTYPE/RECONSTRUCTION` |

La seconde entrée doit posséder son propre répertoire, son propre identifiant
réseau, son `mpscripts.dta`, ses volumes et ses métadonnées. Elle peut partir de
la scène Base commerciale ; elle ne doit jamais écraser `missions/ardens1_obj`.

## Travail requis avant une maquette jouable

1. Choisir et documenter le modèle de destruction des trois canons.
2. Conserver le binding officiel `dummy_obj`, puis créer les seuls bindings
   modernes justifiés pour les trois canons Base ; ne pas donner arbitrairement
   un rôle à `dummy_obj1/2/3`.
3. Recréer `volumy.bin` si le mode choisi demande interaction, zones de spawn,
   limites ou déclencheurs ; ne pas copier celui de Sabre sans comparer les
   repères géométriques.
4. Auditer `sounds.bin` Base, les explosions et les retours audio ; ajouter un
   son seulement si un propriétaire et un moment sont démontrés.
5. Vérifier les textes et conditions de fin des objectifs 1–3.
6. Attribuer des spawns et règles d'occupation aux six véhicules, Jeep
   comprise.

## Roster de véhicules sans pilote de scénario

Le troisième Sherman, le second Tiger et la Jeep sont attestés dans la scène
Base, mais aucun script Base n'explicite leur rôle dans une partie complète.
Les essais devront couvrir : collision au spawn, accès aux sièges, munitions,
réseau, réapparition, abandon, retournement, destruction, chemins praticables
et équilibre entre équipes. Il faudra aussi vérifier les modèles de collision
`cla_*` et les noms de sous-frames propres aux variantes Base.

Le succès des objectifs ne devra dépendre ni du nombre de véhicules encore
vivants ni de leur équipe, sauf règle moderne explicitement ajoutée.

## Critères d'acceptation futurs

- trois objectifs initialisés et réussis une seule fois chacun ;
- destruction simultanée de deux canons déterministe sur hôte et clients ;
- arrivée tardive et changement d'hôte sans perte d'état ;
- six véhicules utilisables sans chevauchement ni avantage involontaire non
  documenté ;
- aucune dépendance aux bindings, valeurs ou volumes de la mission Sabre ;
- installation et suppression de l'entrée prototype sans différence binaire
  dans `Ardens1_obj`.

## Sources internes

- inventaire complet des 12 ressources Base de `Missions.dta` pour
  `missions/ardens1_obj` ;
- entrées release de `SabreSquadron.dta` pour la même mission ;
- scripts Base/Sabre `Ardens1_obj.scr` ;
- scripts Sabre `Ardens1_delo1/2/3.scr` ;
- comparaison de `scene2.bin`, `actors.bin`, `mpscripts.dta`, `sounds.bin` et
  présence/absence de `volumy.bin`.
