# Systèmes, armes, véhicules, avions et conversion solo

## Armes et équipements

| Ensemble | État et preuves | Décision |
|---|---|---|
| Benelli M4 | Neuf paires FPV entièrement décodées, munition 179 et record `item_shoot` de 135 octets attestés. Modèle extérieur moderne et FPV statique dérivé fabriqués, [banc privé](../BENELLI_M4_ADDITIVE/BANC_FPV.md) réalisé. [Contrat natif](../BENELLI_M4_ADDITIVE/CONTRAT_NATIF.md) : 1 036 descripteurs contrôlés et liaison Item/FPV établie hors moteur. [État/munition](../BENELLI_M4_ADDITIVE/ETAT_ET_MUNITION.md) : 208 associations et état d'objet isolé vérifiés, asymétrie du lecteur conservée comme limite. | Les huit nœuds d'arme sont commerciaux, seul leur extraction/recalage est moderne. Aucun ID réservé : le scan historique de 359 ne suffit pas. Ne jamais écraser l'ID 9. Tables additives, sauvegarde de partie complète et comportement restent à construire/qualifier. |
| Flammenwerfer 35 / No.2 | Enregistrement allemand officiel; vestige britannique remplacé par Flak TMP. Ensembles modernes, tuyaux animés à deux LOD, poses de mains dérivées et [banques FPV au repère corrigé](../FLAMMENWERFER_35_AND_NO2/REPERES_VUE_SUBJECTIVE.md) construits. | Chargement/copie du modèle, cadrage, prises fines, attache dorsale, mapping de tir, événements et son restent à réaliser/qualifier. IDs additifs non réservés ; ne jamais réutiliser Flak TMP. |
| FG42 | Enregistrement `item_shoot` officiel mais ancien emplacement 27 réutilisé par un casque. Extérieur original, banques de mains et [assemblage complet de tables privées](../FG42/DESCRIPTEUR_ET_TABLES.md) construits avec icône, textes, sons modernes et munition historique 196. | Aucune activation. Raccordement client, contacts continus, gestes, cadrage, événements et comportement à compléter ; extérieur et tenue à tester en moteur. Sons numériques modernes distincts des symboles historiques. |
| MG34 portable | Enregistrement officiel mais ancien emplacement 32 réutilisé; munition portable distincte de la munition 211 du montage. [Extérieur original moderne](../MG34_PORTABLE/MODELE_MODERNE.md), 33 pièces, deux LOD, neuf séquences de pièces et banques de mains privées construits. | Contacts continus, gestes, cadrage FPV, événements, comportement et entrée additive à compléter ; extérieur à tester. Ne pas confondre portable et montage de char. |
| MG15 / MG81 | Enregistrements conflictuels/réutilisés. | Laboratoire monté seulement, jamais objet d'inventaire tant que les tables ne sont pas résolues. |
| Vickers K | Déjà actif sur Jeep SAS. | Validation seulement; ne pas en fabriquer une version portable sans ressources. |
| Garota / ZK383 | Aucun ensemble commercial complet démontré. [Deux extérieurs modernes distincts](../GAROTA_AND_ZK383/MODELES_MODERNES.md), 7/33 pièces et deux LOD ; [neuf mouvements de pièces ZK-383](../GAROTA_AND_ZK383/ANIMATIONS_ZK383_MODERNES.md) construits sans géométrie/animation commerciale. | Mains, gestes coordonnés, interaction Garota, événements, comportement et intégration additive restent à réaliser ; aucun slot réservé. |
| `PROLEZACKA_GUARD_AI_TEST` | Neuf scripts seulement; aucune mission, ressource ou entrée de registre. | Laboratoire IA moderne, sans restauration de carte ni ajout menu. |

Les [banques de mouvements FG42/MG34](ANIMATIONS_MODERNES.md) sont maintenant
construites : neuf séquences de pièces par arme, aucun mouvement de mains ni
liaison au personnage. Les animations de personnage et l'intégration fonctionnelle
restent donc à réaliser ; les modèles statiques précédents ne sont pas écrasés.
Les [banques FPV rigides FG42/MG34/ZK-383](BANQUES_FPV_RIGIDES.md) sont ensuite
construites : visuel racine sélectionnable, enfants directs, repère converti,
27 clips recalculés et 1 547 instants comparés. Aucun mouvement de main,
cadrage final ou chargement/copie en scène n'est qualifié par cette étape.

Les [54 clips privés de mains FG42/MG34/ZK-383](MAINS_ARMES_RIGIDES.md) ajoutent
ensuite les deux variantes commerciales de squelette, sans exporter leur
géométrie. Les prises et trajectoires sont des créations modernes explicites.
Six groupes isolés ont transmis 234 demandes natives à 54 chargements
d'animations. Les contrôles de contacts et de poignets conservent leurs
défauts mesurés ; un correcteur Python hors jeu ne remplace pas son
raccordement au client. Les surfaces v7 sont maintenant contrôlées avant et
après correction sur 3 094 poses, sans traversée ; 36 instants natifs gardent
un écart brut de poignet hors seuil. Une candidate ZK-383 distincte passe ses
contrôles numériques mais reste à revoir visuellement. Aucun identifiant
n'est alloué dans le jeu.

La MG34 dispose ensuite d'un [descripteur et de tables privées réversibles](../MG34_PORTABLE/DESCRIPTEUR_ET_TABLES.md),
sans activation. FG42 et ZK-383 ont chacun deux [effets sonores modernes originaux](SONS_MODERNES.md)
et des références numériques ajoutées dans une copie privée ; aucun son
historique absent n'est déclaré retrouvé. Le [descripteur FG42](../FG42/DESCRIPTEUR_ET_TABLES.md)
et trois copies de tables sont maintenant construits, avec icône originale et
munition 196 inchangée. Écoute, descripteur ZK-383, événements et comportement
restent à réaliser/qualifier.

Les lance-flammes disposent maintenant de
[six composants indépendants](../FLAMMENWERFER_35_AND_NO2/COMPOSANTS_MODERNES.md) :
pièce tenue, sac et tuyau statique pour chaque ensemble. Le recentrage et les
raccords au repos sont vérifiés ; attaches au personnage et déformation du
tuyau restent des réalisations nécessaires, pas de simples cases de test.
Leurs [dix-huit mouvements de pièce tenue](../FLAMMENWERFER_35_AND_NO2/ANIMATIONS_PIECES_TENUES.md)
sont créés et contrôlés hors moteur, sans mains ni fonctionnement d'arme.
Les [tuyaux synchronisés déformables](../FLAMMENWERFER_35_AND_NO2/TUYAUX_ANIMES_MODERNES.md)
sont maintenant créés à deux LOD, avec sac fixe. L'attache libre au personnage,
le chargement réel de l'ensemble et les contraintes physiques ne sont pas réalisés.
L'[assemblage en un seul modèle](../FLAMMENWERFER_35_AND_NO2/ASSEMBLAGES_ANIMES.md)
est maintenant construit, avec neuf clips communs aux pièces et au skin.
Les [poses de mains dérivées](../FLAMMENWERFER_35_AND_NO2/PRISES_MAINS_DERIVEES.md)
sont ensuite calculées sur les squelettes commerciaux, sans étirer les bras.
Elles ne sont pas encore une banque native chargée ou une caméra FPV calibrée.
Les [36 clips dérivés privés](../FLAMMENWERFER_35_AND_NO2/ANIMATIONS_MAINS_DERIVEES.md)
sont ensuite construits ; leur format et leurs cibles numériques sont
contrôlés sans les confondre avec le raccordement au modèle chargé.
Les [modèles FPV aplatis](../FLAMMENWERFER_35_AND_NO2/MONTAGE_FPV_MODERNE.md)
placent maintenant tous les nœuds sous le visuel sélectionné ; leurs clips
sont recalculés. Les [associations natives](../FLAMMENWERFER_35_AND_NO2/RESOLUTION_ANIMATIONS_FPV.md)
transmettent les 36 nouveaux alias jusqu'au lecteur d'animations contrôlé.
Ni copie du modèle chargé, ni caméra, ni fonctionnement d'arme ne sont qualifiés.

Le [correcteur de contact](../FLAMMENWERFER_35_AND_NO2/CONTACT_MAINS_ET_TRANSITIONS.md)
résout hors jeu le décalage des poignets après mélange : 704 observations,
écart maximal après correction `1,696e-7` avec palettes natives. Son raccordement
au client reste à réaliser. Les mesures des doigts révèlent des intersections
importantes ; la première proposition de pouces reste un essai non promu.
Les [prises ajustées](../FLAMMENWERFER_35_AND_NO2/PRISES_AJUSTEES_MODERNES.md)
emploient désormais un profil moderne reproductible, des contrôles de triangles
et 36 clips dérivés privés. Les associations natives utilisent des alias
distincts ; cela ne qualifie pas les mélanges, les auto-intersections ou le rendu.

Pour Benelli, les [tables complètes désactivées](../BENELLI_M4_ADDITIVE/TRANSACTION_TABLES.md)
et leur retrait exact sont maintenant construits ; les parcours natifs des
objets et des cellules FPV sont contrôlés en mémoire. Le
[plan des mains](../BENELLI_M4_ADDITIVE/MAINS_ET_CIBLES_FPV.md) conserve les
ressources commerciales retrouvées et 448 correspondances de pistes, sans
qualifier le skin, les poses partielles, la caméra ou l'installation.

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
