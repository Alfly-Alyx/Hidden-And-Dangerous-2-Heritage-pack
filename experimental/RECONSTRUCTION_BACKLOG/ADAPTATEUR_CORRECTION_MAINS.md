# Adaptateur de correction après mélange

Implémentation originale C/assembleur, reprise et contrôlée le **10 octobre 2026**.
Elle complète le [calculateur unifié](CORRECTION_MAINS_COMPILEE_UNIFIEE.md), sans
installer de hook, charger une DLL dans Windows, modifier le jeu ou lancer celui-ci.

## Ce qui est réalisé

L'adaptateur correspond aux six octets (trois instructions) du relais de modèle épinglé
à `0x10034bc3` : chargement de la table virtuelle, passage du modèle puis appel
de son rafraîchissement `+0x24`. Il conserve les registres entiers, les indicateurs
et l'état x87 avant d'appeler le correcteur, puis rejoue ces opérations.
**Le point du moteur n'est pas encore intercepté par ce lot.**

Un contexte fourni par l'appelant désigne exactement un modèle et une arène
de nœuds, des offsets, parents, rôles, repos et prises. Après validation des
bornes, le C collecte les poses courantes directement dans cette arène, puis
appelle le préparateur, les deux solveurs et l'application des six rotations.
Le tableau de poses n'est plus préparé par Python à chaque appel de l'adaptateur.
Un autre modèle, un contexte désenregistré ou déjà occupé est ignoré. Une précision
x87 autre que celle contrôlée (`0x27f`) refuse la correction mais conserve l'appel
original de rafraîchissement. Les échecs de calcul laissent l'arène intacte.

Les buffers doivent être distincts, valides et exclusivement possédés par
l'appelant sur un même thread. Le registre d'un contexte est original mais
**ne découvre pas les modèles réels et ne gère pas automatiquement leur durée
de vie**. L'appelant doit désenregistrer avant toute libération ou réutilisation.
Le verrou d'occupation bloque la récursion diagnostique et le désenregistrement
en cours d'appel ; il ne promet aucune synchronisation multithread.

## Contrôles inventés et processeur réel

`tools/build_native_hand_hook.py` construit une nouvelle destination privée à
partir du compilateur local épinglé. L'image désactivée fait 18 432 octets,
sans import système, SHA-256
`80c8524710e0828acf3e09bffbacbf9241db68cd249b24c57b7b410322920fa2`.
Son point d'entrée de chargement refuse toujours un chargement Windows ordinaire.

Le banc exécute :

- seize cas valides : 11 ou 128 nœuds, parents droits ou tournés, puis quatre
  instants avec déplacement du repère dans l'arène existante ;
- dix refus / absences d'action : autre modèle, désenregistrement, occupation,
  précision non prise en charge, contexte invalidé, bras hors portée, dernier
  nœud invalide, callback interdit, quaternion nul et ancien contexte empoisonné
  après désenregistrement ;
- quatre refus d'enregistrement, sans modification de l'état protégé ;
- deux petits programmes console originaux sur le processeur hôte : un aller-retour
  x87 minimal et six cas de l'adaptateur C/assembleur réellement compilé.

Les seize comparaisons de rotations à une référence indépendante ont un écart
maximal de `6,241910278e-8`. Les instantanés C sont identiques aux octets courants
des poses, alors que le buffer source indépendant conserve volontairement les
anciennes positions. Le modèle passé au rafraîchissement est contrôlé.
Les deux programmes console n'utilisent aucun fichier, code ou processus du jeu.

## Limite de l'émulateur, non masquée

Le premier essai a refusé l'adaptateur : après `FRSTOR`, Unicorn 2.1.4 ne restitue
pas les champs d'adresse d'exception x87 `FIP` et `FDP`. Un programme x86 minimal,
indépendant du correcteur, reproduit l'écart ; les autres octets de l'état sauvegardé
restent identiques. Ce contrôle minimal est réexécuté par le banc, qui ne tolère
que les champs effectivement concernés sur l'émulateur courant.

Le banc compare strictement contrôle, état, tags, sélecteurs, opcode et huit
registres de calcul. Il indique explicitement que les deux adresses ne sont
**pas qualifiées dans l'émulateur**. Aucun champ numérique supplémentaire n'est
exempté et aucun seuil du calculateur n'est augmenté.

Sur le processeur hôte, les **108 octets complets** sont identiques avant et après
le test minimal. Les six cas du véritable adaptateur conservent aussi ces 108
octets, avant le rafraîchissement témoin et au retour, y compris quand le correcteur
réussit, refuse ou est ignoré. Cette preuve est séparée du résultat d'émulation.

## Ce qui reste à raccorder

Le rafraîchissement virtuel est ici un témoin explicite, pas le rafraîchissement
d'une scène chargée. Le banc unifié précédent contrôle déjà les palettes et le
rafraîchissement natif, mais les deux preuves ne sont pas présentées comme une
exécution complète du nouveau point d'interception.

Restent : connexion du relais et de l'adaptateur dans le banc natif, découverte
et identification des modèles réels, gestion de leurs créations / destructions,
liaison aux équipements modernes, adaptation des allocations de nœuds du moteur
à l'arène bornée, protections d'installation et restauration du hook, budget par
frame et validation en jeu. Aucun équipement n'est déclaré jouable.

Reproduction privée :
`tools/build_native_hand_hook.py --output-name HandHook_Compiled_v2`.
La destination doit être neuve. Binaire désactivé, programmes console et manifeste
restent sous `.analysis/modern-assets/`, hors du dépôt et de l'installation.
