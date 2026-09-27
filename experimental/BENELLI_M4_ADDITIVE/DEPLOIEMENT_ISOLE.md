# Transaction de fichiers Benelli dans une copie indépendante

**27 septembre 2026.** Le plan de fichiers et la transaction réversible sont
réalisés. Le paquet personnel désactivé est préparé dans les trois copies
d'essai ; un cycle complet sur l'hôte a retrouvé tous les fichiers initiaux.
**Ce contrôle ne lance pas le jeu et ne rend pas l'arme validée ou jouable.**

**Actualisation :** les trois préparations utilisent maintenant le paquet
`BenelliTables_Personal_v4`, après [correction des rotations](../RECONSTRUCTION_BACKLOG/ROTATIONS_NATIVES.md).
Les préparations antérieures sont archivées dans `retired-presets/`, leurs
contenus et sauvegardes conservés. Les anciens modèles ne peuvent plus être
appliqués ; une ancienne transaction reste restaurable.

## Douze cibles, pas quatorze

| Cibles | Nombre | Traitement |
|---|---:|---|
| Models/PROTOTYPE_BenFPV.4ds et Models/PROTOTYPE_BenM4.4ds | 2 | Création uniquement ; présence préalable refusée |
| Tables/items.sav et Tables/FpvAnims.sav | 2 | Ajout sur l'instantané vérifié, personnalisations conservées |
| Text/<langue>/TEXTY_DD.txt | 8 | Préfixes d'origine intacts, ajout moderne vérifié |

Les deux fichiers `PROTOTYPE_Benelli.item.disabled` et
`PROTOTYPE_Benelli.fpvgroup.disabled` sont des preuves d'assemblage. Ils restent
hors du jeu. Aucun exécutable, menu, sauvegarde, profil ou autre fichier ne peut
devenir une cible via le manifeste de ce paquet.

`tools/benelli_trial_payload.py` vérifie les quatorze contenus désactivés,
leurs empreintes, l'inverse des tables et des textes, l'absence des deux
modèles modernes et les instantanés avant modification. Il prépare les douze
couples avant/après entièrement en mémoire. Son rapport privé est
`.analysis/benelli-trial-file-plan-20260927.json`.

## Préparation et protections

`tools/benelli_trial_deploy.py` n'accepte qu'une session munie du manifeste
d'une copie indépendante, sous `.analysis/reconstruction-sandboxes/`. Il refuse
l'installation personnelle, les liens, les clients ouverts et les modifications
des archives ou de l'exécutable épinglés. Le contrôle des ressources est refait
avant toute pose ; son résultat doit correspondre à la préparation.

Le nouveau `BENELLI_TRIAL.json` conserve un plan immuable, la preuve du
laboratoire, les contenus désactivés et les sauvegardes dans le magasin privé.
Sa préparation ne modifie aucun fichier du jeu copié.

La transaction partage **active.json** et le verrou d'opération avec les essais
de missions : aucun chevauchement d'expériences. Elle journalise tous les
originaux avant la première écriture, vérifie chaque fichier après remplacement
et conserve l'historique. Une interruption déclenche le retrait des changements
déjà effectués. Une modification ultérieure de l'utilisateur ou une sauvegarde
manquante provoque un refus, pas un écrasement.

Au retrait, les deux modèles créés sont déplacés dans `retired/`, avec suffixe
`.disabled`, et restent récupérables. Seuls les répertoires créés par cette
transaction et toujours vides peuvent être supprimés. Les originaux personnels
et les fichiers hors périmètre restent intacts.

## Contrôle obtenu sur les copies réelles

- Paquet de douze cibles préparé sur l'hôte et les deux clients, sans activation
  laissée en place.
- Sur l'hôte : pose, lecture de contrôle et retrait des douze fichiers réussis.
- La comparaison globale retrouve **24 385 fichiers**, aucun contenu changé et
  aucun fichier supplémentaire dans le jeu copié.
- Rapport privé : `BENELLI_OFFLINE_REHEARSAL.json` dans la session hôte.
  L'historique de cette répétition est
  `history/c74763a7691241ee8e917b1ba02375dc.json`.
- **21 tests synthétiques nouveaux** : dix sur le plan, onze sur les opérations
  réelles de fichiers fictifs, les collisions, l'interruption et la restauration.
- Zéro essai moteur ; aucun lancement de jeu, installateur ou migration de
  sauvegarde. Les registres de comportement ne sont pas marqués réussis.

## Commandes et limites

Trois cycles supplémentaires sur la version corrigée sont terminés : hôte,
client 1 et client 2 retrouvent chacun leurs **24 385 fichiers initiaux**, sans
modification ni fichier supplémentaire. Leurs nouveaux rapports privés
`BENELLI_OFFLINE_REHEARSAL_rotations-v2.json` préservent le rapport historique.
Les historiques sont respectivement `b3d39234592f49c9895c5f85c9da4f69`,
`1cd5478ae52f4a0e9d5215cbc6ae70eb` et `17b8f3060a8f41beada111dcf71a0d8f`.
Aucune activation n'est laissée en place. Quatre tests synthétiques de plus
couvrent le renouvellement, le refus des anciens modèles, la restauration
historique et la conservation des rapports.

Pour une nouvelle préparation ou répétition, adapter les noms aux dossiers
neufs. Les commandes historiques ci-dessous ne sont pas une invitation à
réappliquer l'ancien modèle :

```powershell
.\.venv\Scripts\python.exe tools/benelli_trial_deploy.py prepare --session '.analysis/reconstruction-sandboxes/native-trials-20260926' --lab '.analysis/item-table-labs/BenelliTables_Personal_v1'
.\.venv\Scripts\python.exe tools/benelli_trial_deploy.py rehearse --session '.analysis/reconstruction-sandboxes/native-trials-20260926'
```

Ces commandes ont déjà été effectuées ; un preset ou rapport existant n'est pas
écrasé. `apply` maintient une pose expérimentale sans lancer le jeu, et `restore`
retire cette pose. Ils restent confinés à une copie indépendante vérifiée.

`refresh --lab <laboratoire-corrigé>` renouvelle uniquement une préparation
inactive et vérifiée, en archivant l'ancienne avant remplacement atomique.
`rehearse --report-name BENELLI_OFFLINE_REHEARSAL_nom-neuf.json` conserve un
nouveau résultat sans effacer les précédents ; chemins libres refusés.

Les manifestes historiques du laboratoire conservent leurs exigences au moment
de la construction ; la preuve de transaction se trouve dans le rapport de
répétition, pas dans une réécriture de ces sources. Les consommateurs de l'action
secondaire, le skin, les poses partielles, la caméra, les événements, la liberté
globale d'identifiant et les sauvegardes complètes restent à qualifier. Les
formats effectivement choisis par le moteur ne sont pas déduits de ce test de
fichiers. Il ne s'agit pas encore d'une option activée dans l'installateur public.
