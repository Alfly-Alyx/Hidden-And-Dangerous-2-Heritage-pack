# Systèmes, armes, véhicules, avions et conversion solo

## Armes et équipements

| Ensemble | État et preuves | Décision |
|---|---|---|
| Benelli M4 | Neuf paires FPV entièrement décodées, munition 179 et record `item_shoot` de 135 octets attestés. Modèle extérieur moderne et FPV statique dérivé fabriqués, [banc privé](../BENELLI_M4_ADDITIVE/BANC_FPV.md) réalisé. [Contrat natif](../BENELLI_M4_ADDITIVE/CONTRAT_NATIF.md) : 1 036 descripteurs contrôlés et liaison Item/FPV établie hors moteur. | Les huit nœuds d'arme sont commerciaux, seul leur extraction/recalage est moderne. Aucun ID réservé : le scan historique de 359 ne suffit pas. Ne jamais écraser l'ID 9. Tables additives, sauvegarde de partie et comportement restent à construire/qualifier. |
| Flammenwerfer 35 / No.2 | Enregistrement allemand officiel; vestige britannique remplacé par Flak TMP; munitions, icônes et effet 25/flame1 seulement. Modèles, animations, mapping de tir et fonction sonore manquent. | Reconstruction entièrement moderne avec IDs additifs; ne jamais réutiliser Flak TMP. |
| FG42 | Enregistrement `item_shoot` officiel mais ancien emplacement 27 réutilisé par un casque. | Nouvel ID, modèles et animations modernes; conserver la provenance de la munition. |
| MG34 portable | Enregistrement officiel mais ancien emplacement 32 réutilisé; munition portable distincte de la munition 211 du montage. | Nouvel ID; ne pas confondre portable et statique. |
| MG15 / MG81 | Enregistrements conflictuels/réutilisés. | Laboratoire monté seulement, jamais objet d'inventaire tant que les tables ne sont pas résolues. |
| Vickers K | Déjà actif sur Jeep SAS. | Validation seulement; ne pas en fabriquer une version portable sans ressources. |
| Garota / ZK383 | Aucun ensemble commercial complet démontré. | Création moderne clairement étiquetée. |
| `PROLEZACKA_GUARD_AI_TEST` | Neuf scripts seulement; aucune mission, ressource ou entrée de registre. | Laboratoire IA moderne, sans restauration de carte ni ajout menu. |

Dossiers existants : `BENELLI_M4_*`, `FG42`, `MG34_PORTABLE`,
`FLAMMENWERFER_35_AND_NO2`, `GAROTA_AND_ZK383` et
`WEAPONS_VEHICLES_TRIAGE`.

## Avions et appareils décoratifs

| Appareil | Faits | Suite sûre |
|---|---|---|
| Ju 52 | Déjà actif en Africa1/2. Africa2 possède déjà `AF2_actprelet` pour la fumée. | Documenter le script absent sans ajouter une seconde fumée. |
| La-5 / Aichi | Ressources décoratives disponibles, aucune entrée véhicule complète. | Décor d'abord; pilotage seulement après tables et physique. |
| DFS 230, Fa 223, Fw 200, Li-2, Me 323 | Modèles, LOD et structures présents; aucune liaison texte/table véhicule reconnue. | Laboratoires décoratifs. Me 323 armé plus tard; Fa 223/DFS 230 seulement après preuve physique. |
| `AIRCRAFT_DECOR_LAB` | Regroupe les scripts orphelins et les profils de test. | Centraliser les nouveaux essais ici au lieu de multiplier les dossiers concurrents. |

Les dossiers `AICHI_DECOR`, `DFS230_DECOR`, `FA223_DECOR`, `FW200_DECOR`,
`JU52_DECOR_AND_PILOTAGE`, `LA5_DECOR`, `LI2_DECOR` et `ME323_DECOR`
existent déjà.

## Missions multijoueur vers solo

État global : **aucune conversion n'est encore validée**. La matrice existante se
trouve dans `experimental/MP_ONLY_TO_SOLO_MATRIX/`.

Principes de conversion :

- conserver la mission originale et générer un wrapper séparé;
- ne pas confondre une apparition dans le menu avec une mission jouable;
- ne pas annoncer une conversion validée sans les quatre preuves d'exécution :
  menu, apparition du joueur, objectifs, condition de fin;
- tester le chargement/sauvegarde et les différences solo/coop;
- enregistrer les résultats dans un manifeste de validation, pas seulement dans
  une capture ou une note libre.

Cas connus :

- `AFRIKA5_MP` : objectifs manquants;
- `NORMANDY3_MP_ZONE` : contrôleur et objectifs manquants;
- les fiches Alps3, Ardens, London, Normandy2B/3/4 existent mais restent des
  candidats;
- 26 autres cartes détectées ne doivent pas être qualifiées de converties avant
  passage des quatre contrôles d'exécution.

## Politique des identifiants et des ressources

Depuis le 26 septembre 2026, la création de ressources modernes manquantes est
explicitement autorisée : [contrat de provenance](RESSOURCES_MODERNES.md).
Le premier [modèle extérieur Benelli](../BENELLI_M4_ADDITIVE/MODELE_MODERNE.md)
est généré et contrôlé hors moteur. Il ne résout pas encore les animations FPV,
les tables d'arme, les sauvegardes ou les comportements de tir.

1. Scanner à nouveau toutes les tables avant d'attribuer un ID additif.
2. Refuser la construction si l'ID proposé est déjà occupé; aucun ID de repli
   silencieux.
3. Conserver un hash et la taille de chaque enregistrement commercial utilisé
   comme preuve, sans versionner la donnée binaire elle-même.
4. Marquer séparément : `OFFICIEL`, `INFERENCE`, `MODERNE`.
5. Ne jamais transformer un nom de ressource orphelin en preuve de placement ou
   de comportement jouable.
