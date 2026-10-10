# Relais natif de correction des mains

État du **10 octobre 2026** : connexion réalisée dans un émulateur privé, sur
des objets et une animation inventés. Aucun hook installé dans un processus,
aucune DLL chargée sous Windows et aucun fichier du jeu modifié.

## Chaîne raccordée

Le relais de modèle épinglé `0x10034ba0` appelle son contrôleur d'animation
`0x10020150`, puis le rafraîchissement virtuel `+0x24`. Six octets à
`0x10034bc3` sont remplacés **uniquement dans la mémoire de l'émulateur** par
un appel relatif de l'[adaptateur compilé](ADAPTATEUR_CORRECTION_MAINS.md) et
une instruction sans effet. L'adaptateur exécute le calcul C, puis rejoue le
rafraîchissement natif `0x1001e610`.

Le même objet modèle sert à l'attachement natif, à la mise à jour et au contexte
de correction. Les propriétaires d'animation pointent sur les mêmes nœuds que
le collecteur C ; aucun tableau de poses n'est injecté entre animation et
correction. La mise à jour récursive utilise les tables virtuelles natives du
modèle et des joints. Les indicateurs de transformation, compteurs et caches
de joints sont comparés à une référence indépendante.

Le patch exige les six octets et les deux adresses exactes examinées. Sa remise
en place et son retrait invalident le cache de traduction de l'émulateur.
Après chaque séquence, y compris lors d'un échec, l'intégralité de l'image native
émulée est comparée à son état initial. Ce mécanisme n'est **pas** un installateur
de hook Windows et ne valide ni protection mémoire ni concurrence d'un jeu actif.

## Résultats du banc

Seize séquences combinent parents droits / tournés, patch absent / présent,
contexte désenregistré / enregistré et contrôleur absent / présent. Chaque
séquence contient un modèle initialement sans animation, un attachement, des
avancées, des pauses à delta nul, un poids nul puis rétabli, un détachement complet
et un réattachement.

- 208 étapes de mise à jour du modèle ;
- 72 appels du contrôleur natif, 112 calculs natifs de poses ;
- 36 passages dans l'adaptateur, dont 18 corrections complètes ;
- 72 rafraîchissements natifs, sans substitut de rafraîchissement ;
- écart maximal de pose avant correction : `9,319978792e-17` ;
- écart maximal de rotation corrigée : `7,386094425e-8`.

Le relais n'appelle ni contrôleur, ni adaptateur, ni rafraîchissement lorsque
le contrôleur manque ou que sa liste de propriétaires est vide. Un delta nul
avec des propriétaires conservés atteint en revanche l'adaptateur, même si
aucune nouvelle pose n'a été calculée. Cette distinction est contrôlée, elle
n'est pas assimilée au comportement du précédent banc qui appelait directement
le contrôleur à chaque étape.

Les registres entiers sont comparés avant le rafraîchissement natif, les registres
préservés et la pile au retour du relais. Les limites x87 de l'émulateur restent
[explicitement séparées de la preuve sur processeur hôte](ADAPTATEUR_CORRECTION_MAINS.md#limite-de-lémulateur-non-masquée).
La référence de poses corrigées est transportée indépendamment entre les étapes.

## Limites et suite

Les onze joints, leurs parents et l'enregistrement sont fournis par le banc.
Le propriétaire visuel est un enregistrement diagnostique séparé : sa boîte
englobante, sa géométrie, le skin et le rendu ne sont pas exécutés. Les nœuds
restent dans une arène contiguë dans ce banc. La [variante dispersée](RELAIS_MAINS_DISPERSE.md)
relie maintenant le même enchaînement à des allocations séparées ; la durée de vie
des modèles réellement chargés reste à gérer. L'animation inventée ne prouve
pas les transitions d'armes décidées par le client, ni le comportement en jeu.

Restent notamment le raccordement aux équipements modernes et aux vrais modèles,
les gardes de chargement / destruction, le budget par frame et l'intégration
désactivable dans une copie de test. Aucun équipement n'est déclaré jouable.

Reproduction privée : `tools/hand_relay_audit.py`, avec `--library` pointant sur
LS3DF 1.12 épinglé, `--compiled-hook` sur l'image désactivée de l'adaptateur et
`--json-output` sur un rapport neuf. Le rapport de cette exécution est
`.analysis/native-hand-relay-v1-20261010.json`, exclu du dépôt ; il ne contient
aucune géométrie ni clé d'animation commerciale.
