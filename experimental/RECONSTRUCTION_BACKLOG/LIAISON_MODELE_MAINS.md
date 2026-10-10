# Liaison compilée des nœuds de mains

Implémentation originale du **10 octobre 2026**, désactivée. Elle identifie et
ordonne une collection de nœuds natifs nommés fournie par l'appelant, puis produit
directement les tables utilisées par le correcteur. Elle ne découvre pas encore
seule les modèles vivants du client et ne qualifie pas leur durée de vie.

## Contrat

`Hd2BuildHandModelBinding` reçoit une identité de modèle, onze à 128 vues de
nœuds et des plages de noms valides possédées par l'appelant. Le pointeur de nom
présent dans chaque nœud doit correspondre à la plage fournie. Les noms sont
ASCII imprimables, terminés, de 63 caractères au maximum et sans doublon,
y compris avec une différence de casse seulement.

Le C retrouve la hiérarchie à partir des pointeurs de parents réellement présents
dans les nœuds. Il refuse parent externe ou cycle, puis effectue un tri stable
par parcours répétés, avec chaque parent avant ses enfants. Les onze rôles du
correcteur sont recherchés par nom exact : racine `fpv_weapon`, deux repères
modernes, coudes et six articulations. Les chaînes épaule / avant-bras / main,
leurs clavicules, les types de joints et le rattachement des repères à la racine
sont contrôlés.

Avant publication du résultat, les pointeurs de parent et de nom ainsi que les
types sont relus. Un refus laisse toute la sortie intacte. Aucun nœud natif n'est
écrit. La sortie fait **1 588 octets** et le travail privé **3 636 octets**.
Les plages de données doivent rester valides, distinctes et exclusivement
possédées pendant l'appel : il ne s'agit pas d'une protection contre une
libération concurrente ni d'un contrôle de pages mémoire d'un jeu actif.

L'image de 5 120 octets ne comporte aucun import système et refuse un chargement
Windows ordinaire, SHA-256
`fd5cee2af99f7f76f52221ae4bf2be9afdf54543a5157fbc5e27441430a5a688`.

## Contrôles et raccordement

Seize cas valides combinent onze / 128 nœuds, quatre ordres d'énumération et
deux alignements. Vingt-trois refus couvrent l'ABI, les plages, les recouvrements,
les parents, les noms, les rôles et trois mutations explicites de métadonnées
avant la dernière vérification. Les sorties refusées, les pages de nœuds, les
noms et les gardes sont contrôlés intégralement. Les trois mutations du banc
sont distinguées de toute écriture du programme C.

La liaison est ensuite exécutée sur les nœuds du
[relais à allocations dispersées](RELAIS_MAINS_DISPERSE.md), énumérés à l'envers.
Le contexte de correction pointe **directement** sur les vues, parents et rôles
produits par le C, dont la page devient en lecture seule. Python ne recrée pas
des tables de substitution. Le collecteur doit suivre l'ordre C lorsqu'il lit
les poses animées ; la référence numérique conserve son propre ordre et ses
propres poses entre les étapes.

Les seize séquences raccordées passent : 208 mises à jour, 72 appels du contrôleur,
112 calculs natifs de pose, 36 passages dans l'adaptateur, 18 corrections complètes
et 72 rafraîchissements natifs. Écarts maximaux inchangés : `9,319978792e-17`
avant correction et `7,386094425e-8` pour les rotations corrigées. Les deux bancs
précédents, contigu et dispersé sans liaison automatique, ont également été
rejoués avec les noms explicites et conservent ces résultats.

## Ce qui reste

La [collecte compilée du vecteur du modèle](COLLECTE_MODELE_MAINS.md) est maintenant
raccordée à cette liaison, sur des plages dont la propriété reste fournie par le banc.

Les objets et leurs plages de noms sont encore construits par le banc. Il reste
à collecter le modèle réellement assemblé, assurer la propriété de ses
allocations, associer son équipement moderne et traiter les créations,
remplacements et destructions. La présence de noms connus seule n'autorise pas
l'activation sur n'importe quel modèle. Skin, rendu, boîte englobante, budget par
frame et validation en jeu restent non qualifiés.

Reproduction privée :

- `tools/build_native_hand_model_binding.py --output-name HandModelBinding_Compiled_v1`
  dans une destination neuve ;
- `tools/hand_relay_audit.py --scattered --compiled-binding <image désactivée>`,
  avec les arguments de bibliothèque, adaptateur et rapport neuf habituels.

Rapport : `.analysis/native-bound-hand-relay-v1-20261010.json`. Binaire, manifeste
et rapports restent sous `.analysis/`, exclus du dépôt et de l'installation.
