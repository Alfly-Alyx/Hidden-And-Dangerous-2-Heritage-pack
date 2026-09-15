# Co-Burgundy 1/3 — porteurs des moniteurs de portes sonores

État : **import additif spécifié, données de scène non générées**, 14 septembre
2026. Les manifestes sont désactivés ; aucune mission n’a été compilée ou
installée.

## Verdict

Les dix moniteurs de portes coop ont été livrés et sont byte-identiques à leurs
versions solo. Les dix portes et dix émetteurs qu’ils recherchent existent dans
les cartes coop. Ce qui manque est uniquement leur propriétaire de script : sept
frames `dummy_snd6..12` dans Co_Burgundy1 et trois frames
`snd_vrabec07..09` dans Co_Burgundy3.

La reconstruction la plus fidèle est additive : copier chaque record de porteur
depuis la mission solo correspondante, conserver son nom, son parent et son
transform complets, puis lui rendre son binding vers le script coop déjà présent.
Les scripts, portes et sons ne sont ni remplacés ni dupliqués.

Un porteur proxy neuf reste une branche de secours moderne si l’import exact du
record échoue. Il ne doit jamais être confondu avec une restauration historique.

## Inventaire des preuves locales

### Co_Burgundy1

| Porteur solo absent | Script coop orphelin | Porte coop présente | Son coop présent |
| --- | --- | --- | --- |
| `dummy_snd6` | `bur1_SND_door1.scr` | `F_dr_door26` | `S_dorcon1` |
| `dummy_snd7` | `bur1_SND_door2.scr` | `F_dr_door00` | `S_dorcon5` |
| `dummy_snd8` | `bur1_SND_door3.scr` | `F_dr_door20` | `S_dorcon2` |
| `dummy_snd9` | `bur1_SND_door4.scr` | `F_dr_door19` | `S_dorcon3` |
| `dummy_snd10` | `bur1_SND_door5.scr` | `F_dr_door18` | `S_dorcon4` |
| `dummy_snd11` | `bur1_SND_door6.scr` | `F_bunk_door_34` | `S_dorcon10` |
| `dummy_snd12` | `bur1_SND_door7.scr` | `F_dr_door17` | `S_dorcon11` |

L’audit coop compte les sept scripts parmi les fichiers non liés, sans acteur
homonyme libre. Chaque paire solo/coop possède la même taille et le même SHA-256.

### Co_Burgundy3

| Porteur solo absent | Script coop orphelin | Porte coop présente | Son coop présent |
| --- | --- | --- | --- |
| `snd_vrabec07` | `bur3_snd_door1.scr` | `F_door_wood01` | `S_door02` |
| `snd_vrabec08` | `bur3_snd_door2.scr` | `F_door_wood00` | `S_door03` |
| `snd_vrabec09` | `bur3_snd_door3.scr` | `F_door_wood02` | `S_door04` |

Les trois scripts sont également non liés sans acteur homonyme, byte-identiques
au solo. Les `sounds.bin` solo et coop de Burgundy3 sont eux-mêmes identiques ;
aucun import sonore n’est requis.

### Logique commune préservée

Chaque script initialise son émetteur à `False`, surveille l’état de la porte et
active le son pour les états 1, 2 ou 3. Lorsque l’état revient à 0, il coupe le
son et réarme le test d’ouverture. Aucun script ne lit son propre frame : le
porteur ne sert qu’à maintenir la durée de vie et le binding du moniteur.

## Données manquantes et hypothèses

- **Prouvé** : noms des porteurs, bindings solo, scripts coop, portes, sons et
  logique des états.
- **Prouvé** : transforms arrondis des trois porteurs Burgundy3, déjà inventoriés
  dans `CO_BURGUNDY3_REMOVED_AMBIENT_CONTROLLERS` ; l’import doit reprendre les
  champs binaires, pas ressaisir ces valeurs.
- **Manquant** : export structuré complet des sept records `dummy_snd6..12`,
  notamment parent, identifiant interne, flags et transform.
- **Manquant** : preuve dynamique que le parent solo de chaque porteur existe et
  conserve le même cycle de vie dans la carte coop.
- **Hypothèse faible** : le transform n’influence pas la spatialisation, puisque
  les scripts pilotent des frames `S_*` distinctes.
- **Hypothèse moyenne** : importer le record solo complet suffit sans adaptation
  d’autorité réseau.

## Niveaux de spéculation

- **Faible** : les dix bindings manquent à cause du retrait des dix porteurs ;
  toutes les autres pièces concordent.
- **Faible** : branche A, copie exacte du record solo quand son parent existe en
  coop.
- **Moyenne** : rattacher le record exact à un parent coop équivalent si son
  parent solo manque.
- **Forte** : branche B, créer un proxy à un nouvel emplacement ; fonctionnelle
  en théorie, mais architecture moderne.
- **Exclue** : attacher les scripts directement aux portes ou aux émetteurs, qui
  peuvent déjà avoir leur propre binding.

## Branches additives

### A — import exact, préférée

Les manifestes `PROTOTYPE_CO_BURGUNDY1_EXACT.plan.disabled` et
`PROTOTYPE_CO_BURGUNDY3_EXACT.plan.disabled` ordonnent un import record par
record depuis les scènes solo. Aucun nom ni transform n’est inventé. Cette
branche doit être tentée dans un éditeur capable de préserver tous les champs.

### B — proxies modernes, secours seulement

`PROTOTYPE_PROXY_OWNERS.plan.disabled` prévoit dix nouveaux dummies inertes avec
des noms `lab_*`. Chaque proxy reçoit un seul script existant. Cette branche est
réversible, mais elle n’est recevable qu’après échec documenté de l’import exact
et comparaison prouvant que parent/transform n’affectent pas le moniteur.

Les branches A et B sont mutuellement exclusives pour une même porte.

## Activation et désactivation

1. Dupliquer séparément Co_Burgundy1 et Co_Burgundy3.
2. Importer et lier un seul porteur, tester sa porte, puis passer au suivant.
3. Conserver `mpscripts.dta` coop comme autorité ; ajouter une seule paire
   propriétaire-script, sans copier le corps du script.
4. Co_Burgundy3 : ne pas activer simultanément ces trois porteurs et la variante
   complète `CO_BURGUNDY3_REMOVED_AMBIENT_CONTROLLERS`, qui importe déjà
   `snd_vrabec07..09`.
5. Désactivation A : retirer les bindings ajoutés et les records importés.
6. Désactivation B : retirer les bindings et proxies `lab_*`.
7. Les dix portes, dix émetteurs, scripts coop et sons doivent rester
   byte-identiques à la baseline après réversion.

## Risques

- parent solo absent ou durée de vie différente dans la mission coop ;
- collision d’identifiant ou de nom lors de l’import ;
- double moniteur si une restauration ambiante Burgundy3 est déjà active ;
- son multiplié par le nombre de clients ;
- script persistant après destruction/changement de secteur du porteur ;
- proxy moderne chargé à un moment différent du record solo ;
- son bloqué actif lors d’une sauvegarde sur état 1/2/3.

## Protocole de test en jeu

1. Baseline de cinq minutes : ouvrir/fermer les dix portes et confirmer l’absence
   des moniteurs reconstruits.
2. Pour chaque porteur seul : ouvrir lentement, fermer, rouvrir, interrompre aux
   états 1, 2 et 3, puis revenir à 0.
3. Vérifier un seul émetteur actif, le bon son et la coupure complète à l’état 0.
4. Tester deux puis toutes les portes simultanément ; aucune paire ne doit être
   croisée.
5. Sauvegarder/reprendre porte fermée, en mouvement et ouverte ; répéter après
   changement de secteur.
6. Tester hôte, un client proche et un client éloigné ; compter les
   déclenchements et comparer le volume.
7. Pour la branche B seulement, comparer à A sur la même porte avant d’autoriser
   d’autres proxies.
8. Retirer la variante et refaire la baseline ; aucun frame ou binding fantôme.

Critères d’arrêt : mauvais son, boucle persistante, doublon, divergence réseau,
collision de binding, mauvais cycle de chargement ou réversion incomplète.

## Sources internes

- `docs/CREATIONS_EXPERIMENTALES.md`, entrée CO-BURG-DOORS (consultée, non
  modifiée) ;
- `experimental/CO_BURGUNDY3_REMOVED_AMBIENT_CONTROLLERS/ETUDE.md` ;
- `experimental/CO_BURGUNDY3_REMOVED_AMBIENT_CONTROLLERS/MATRICE_OWNER_SCRIPT.md` ;
- scripts `Scripts/BURGUNDY1`, `Scripts/Co_Burgundy1`, `Scripts/BURGUNDY3` et
  `Scripts/Co_Burgundy3` de `SabreSquadron.dta` ;
- `scene2.bin`, `actors.bin`, `sounds.bin` et `mpscripts.dta` des deux missions
  coop dans `SabreSquadron.dta`.
