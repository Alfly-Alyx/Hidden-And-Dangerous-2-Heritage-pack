# Collecte compilée du vecteur de modèle

Implémentation originale du **10 octobre 2026**, toujours désactivée. Le
collecteur utilise désormais la liste de nœuds déclarée par le modèle natif,
puis alimente directement la [liaison nommée](LIAISON_MODELE_MAINS.md).
L'appelant doit encore garantir la validité et la propriété des plages mémoire.

## Contrat et limites

`Hd2CollectHandModelBinding` reçoit les plages connues du modèle et de son
vecteur, ainsi que onze à 128 vues possédées de nœuds et de leurs noms. Il vérifie
le type de modèle `9` dans le mot bas à `+f8`, l'identité du vecteur à `+120`,
son nombre à `+128` et la capacité réellement fournie. Chaque entrée doit
correspondre exactement à une vue, et chaque vue doit apparaître une seule fois.
Un pointeur étranger n'est pas déréférencé.

L'ordre initial vient du vecteur du modèle, pas de l'ordre des vues fournies.
Le lieur C effectue ensuite le tri parents / enfants et l'identification des
rôles dans une sortie privée provisoire. Après cela, le collecteur relit le
type complet, l'identité du vecteur, le nombre et toutes les entrées. Il ne
publie les **1 588 octets** de résultat que si tout est encore cohérent.
Le travail privé fait **8 296 octets**. Un refus laisse la sortie intacte ;
aucun modèle, nœud, nom ou vecteur natif n'est modifié par le programme C.

Les données doivent être distinctes, valides et possédées exclusivement pendant
l'appel. Ces relectures ne constituent pas un verrou contre les changements
concurrents ni une garantie de durée de vie. Le collecteur ne recherche pas
des adresses arbitraires dans un processus et n'autorise pas l'activation par
la seule présence de noms connus.

L'image de 7 168 octets n'a aucun import système et son initialisation refuse
un chargement Windows ordinaire. SHA-256 :
`05bfa7667cfb0adc7bf61662930ad0f46c94620ca4b29fba16c45522c2d5b7a9`.

## Vérifications réalisées

- **32 cas valides** : onze / 128 nœuds, quatre ordres du vecteur, deux ordres
  indépendants des vues possédées, alignements quatre / huit octets. Les deux
  valeurs diagnostiques du mot haut de type restent intactes.
- **28 refus** : tailles, alignements, débordement, type, identité et capacité
  du vecteur, objets étrangers, doublons, vues manquantes, erreurs de liaison,
  puis quatre mutations explicitement injectées avant la dernière relecture.
- Comparaison intégrale des pages de données, noms, gardes et sorties refusées.
  Les mutations injectées par le banc sont distinguées des écritures C.
- Raccordement à l'objet modèle utilisé par l'attachement, l'animation et le
  rafraîchissement natifs, sur le même processeur émulé : **16 séquences / 208
  mises à jour**, 72 appels du contrôleur, 112 calculs de pose, 36 passages dans
  l'adaptateur, 18 corrections et 72 rafraîchissements natifs.

Le contexte pointe directement dans la sortie C devenue en lecture seule.
Les poses ne sont pas réinjectées entre les étapes. Les écarts maximaux restent
`9,319978792e-17` avant correction et `7,386094425e-8` sur les rotations corrigées.
Le code commercial n'est exécuté qu'en émulation privée ; le jeu n'est pas lancé.

## Suite nécessaire

Le [relais sur mains / MG34 complètes](RELAIS_MAINS_EQUIPEMENT_COMPLET.md) utilise
maintenant 78 nœuds et les deux variantes commerciales de mains. Ses objets
restent des joints diagnostiques et ne qualifient pas le chargement de scène.

Les [ajouts, retraits et transferts natifs](APPARTENANCE_MODELE_NATIVE.md) sont
désormais examinés sur vecteurs préalloués et références conservées. Ils ne
modifient pas automatiquement la hiérarchie des parents ; le collecteur refuse
les transferts devenus incohérents avec celle-ci.

Les allocations du modèle et des nœuds restent des objets diagnostiques du banc.
Il faut encore établir leur propriété dans le client, reconnaître l'équipement
moderne, retirer la liaison avant remplacement / destruction et qualifier les
modèles complets, le rendu et le coût d'exécution. Aucun contenu n'est promu ni
installé dans le jeu personnel.

Reproduction privée, avec destinations neuves :

- `tools/build_native_hand_model_collect.py --output-name HandModelCollect_Compiled_v1`
- `tools/hand_relay_audit.py --scattered --compiled-collection <image désactivée>`,
  avec bibliothèque, adaptateur et rapport comme dans les bancs précédents.

Rapport : `.analysis/native-collected-hand-relay-v1-20261010.json`.
Images, manifests et rapports dérivés restent sous `.analysis/`, hors dépôt.
