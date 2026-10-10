# Relais natif sur les mains et l'équipement complets

Raccordement du **10 octobre 2026**, désactivé. Les mains commerciales privées
et la banque moderne MG34 passent maintenant par le [collecteur compilé du
modèle](COLLECTE_MODELE_MAINS.md), l'animation native, l'adaptateur appelé depuis
le relais du moteur, puis le rafraîchissement natif.

## Ce qui change

Le banc n'est plus limité à onze nœuds inventés et deux repères animés. Il utilise
les **37 nœuds de chaque variante de mains** et les 41 nœuds de l'équipement
MG34 moderne, soit **78 nœuds** répartis sur des pages distinctes. Les neuf clips
privés dérivés sont vérifiés par leur manifeste et leurs empreintes. Les sources
commerciales et les poses dérivées restent hors dépôt.

Le relais prend en charge les clips et créneaux multiples, les poids lors de
l'attachement et les changements de poids par créneau. La référence conserve
ses propres poses corrigées ; aucune pose native n'est réinjectée entre les
opérations. Le contexte lit directement les vues, parents et rôles construits
par le collecteur C, sur le vecteur utilisé par l'attachement natif.

Les enregistrements demeurent **tous des joints diagnostiques**. En particulier,
les racines visuelles ne sont pas présentées comme des visuels réellement
chargés par le moteur. Cela permet de qualifier ce chemin d'animation et de
correction sans confondre cette preuve avec le chargement d'une scène complète.

## Résultats MG34

Pour chaque variante : treize transitions, trois phases de départ, une séquence
de maintien / temps nul / poids nul / détachement, puis trois parcours témoins
(patch absent, contexte non enregistré, contrôleur absent).

| Mesure consolidée | Résultat |
| --- | ---: |
| Séquences | 86 |
| Mises à jour | 620 |
| Appels natifs du contrôleur | 598 |
| Calculs natifs de pose | 39 000 |
| Passages dans l'adaptateur | 584 |
| Corrections complètes | 570 |
| Rafraîchissements natifs | 598 |
| Mises à jour sans correction, conformément aux conditions | 50 |
| Écart maximal des poses avant correction | 0 |
| Écart maximal des rotations corrigées | `8,330791257e-8` |
| Écart maximal de poignet avant correction | `0,009477951937` |
| Écart maximal de poignet après correction | `1,616424799e-7` |

Les écarts de poignet sont mesurés par un calcul indépendant des transformations,
dans les unités des données. La tolérance du banc est `5e-6`. Le calcul natif de
palette, le skin et le rendu ne sont pas exécutés dans ce relais ; leurs anciens
bancs séparés ne sont pas assimilés à cette exécution.

Les deux précédents parcours de onze nœuds, contigu et collecté, ont été rejoués
après la généralisation. Ils conservent chacun leurs 16 séquences, 208 mises à
jour et mêmes écarts. Neuf tests Python supplémentaires couvrent les entrées,
les rapports, les conditions de correction et les refus de résultats incomplets.

## Encore non qualifié

Ces transitions sont des scénarios diagnostiques, pas une preuve que le client
les sélectionne toutes dans cet ordre. Restent notamment les objets réellement
chargés, leur propriété et leur durée de vie, les racines visuelles, le skin et
le rendu combinés, les contacts naturels des doigts, la caméra, les événements,
les sons, la mécanique d'arme et le budget d'exécution. Aucun équipement n'est
installé ni déclaré jouable sur cette seule base.

Reproduction privée : `tools/equipment_hand_relay_audit.py`, avec `--case MG34`,
`--bank-suffix HandFPV_v10`, le profil `modern-rigid-hand-grips-mg34-linear.json`,
les chemins de jeu / banque privée, les images désactivées de l'adaptateur et
du collecteur, `--archives-only` et un rapport neuf.

Rapport : `.analysis/equipment-hand-relay-mg34-v1-20261010.json`.
Régressions : `.analysis/native-hand-relay-v4-20261010.json` et
`.analysis/native-collected-hand-relay-v2-20261010.json`.
