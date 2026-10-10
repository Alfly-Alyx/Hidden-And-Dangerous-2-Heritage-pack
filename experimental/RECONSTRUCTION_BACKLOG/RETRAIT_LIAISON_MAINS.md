# Retrait explicite de la liaison des mains

Composant original du **10 octobre 2026**, désactivé. Il relie une garde de
durée de vie au registre compilé du [correcteur dispersé](RELAIS_MAINS_DISPERSE.md).
Les événements sont fournis explicitement dans ce premier banc. Le
[raccordement aux entrées natives](NOTIFICATIONS_CYCLE_VIE_NATIVE.md) les livre
maintenant automatiquement dans l'émulateur privé ; leur gestion dans le
client réel n'est **pas encore implémentée**.

## Comportement

Une structure possédée de **20 octets** conserve le contexte, la fonction de
configuration, la génération et les compteurs d'invalidation. Elle doit être
initialement nulle. `Hd2WatchHandContext` appelle le véritable registre compilé,
puis mémorise la liaison uniquement si l'enregistrement a réussi. Une liaison
déjà surveillée ne peut pas être remplacée implicitement. Le réarmement est
toujours explicite et augmente la génération sans bouclage.

`Hd2BeforeHandModelChange` traite trois notifications, avant de transmettre une
opération au moteur : ajout au modèle, retrait du modèle et libération d'objet.
Un changement visant le modèle surveillé ou l'un des nœuds de ses vues provoque
le retrait du registre compilé, puis l'effacement des deux pointeurs de la garde.
Un événement étranger ne modifie rien. Une libération correspondante retire la
liaison même si elle ne devait pas être la dernière référence : c'est un choix
conservateur, pas une qualification du destructeur.

Les identités reçues ne sont jamais déréférencées. La garde compare les adresses
avec les vues possédées ; elle ne lit ni compteur de références, ni parent, ni
transformation de l'objet annoncé. Un événement répété après retrait est neutre.

Si le registre est occupé, le retrait est refusé et tout l'état reste intact.
**L'appelant doit alors empêcher la mutation ou la libération annoncée.**
Ignorer ce retour ne serait pas sûr. Un seul état de garde doit contrôler
exclusivement le registre global de l'adaptateur ; les données et les vues
doivent rester valides jusqu'au retrait réussi. Accès sérialisé obligatoire :
ce n'est ni un verrou multithread ni un système autonome de références.

## Vérifications

L'image de 2 048 octets n'a aucun import système et refuse son initialisation
par un chargement Windows ordinaire. SHA-256 :
`8990a6f58a1d7c96a070117787731b76169fa5506b1042349fad985279486d3f`.
Elle est exécutée avec le vrai registre compilé, pas avec un substitut de sa
fonction de configuration.

- **30 cas de fonctionnement** : onze / 128 nœuds, trois types d'événement,
  modèle, premier / milieu / dernier nœud, ou objet étranger.
- Les pages des objets sont inaccessibles au processeur émulé pendant ces
  notifications, y compris quand leur identité correspond : aucune lecture
  de l'objet n'est nécessaire à la garde.
- **24 vérifications après retrait** : contexte, vues et nœuds deviennent
  inaccessibles ; un appel ultérieur de l'adaptateur ne lance aucune correction
  et conserve son appel de rafraîchissement. Ce dernier est ici un substitut
  explicite, contrairement aux bancs de relais natif.
- Répétition inactive, réarmement explicite et second retrait contrôlés.
- **14 refus** : contrat, tailles, contexte, fonction absente, occupation,
  génération épuisée, événements mal formés, compte modifié et registre occupé.
  État et registre inchangés à chaque refus ; aucune mutation native transmise.

Le type du contexte de correction est maintenant partagé dans un en-tête,
toujours **52 octets**. Sa recompilation reproduit exactement l'empreinte de
l'adaptateur précédent. Ses 32 cas valides, dix refus, quatre refus de registre
et huit sondes console natives ont été rejoués avec succès, dont la préservation
intégrale des 108 octets x87 dans les sondes natives originales.

## Raccordement restant

Les [opérations natives d'appartenance](APPARTENANCE_MODELE_NATIVE.md) ont leurs
effets contrôlés séparément. Les entrées du moteur livrent maintenant leurs
notifications avant mutation dans le banc privé. Il faut encore assurer une
gestion exploitable des refus côté client, étendre les chemins de
[changement de parent](CHANGEMENT_PARENT_NATIF.md) déjà raccordés,
puis qualifier le remplacement complet et la destruction finale.
Le modèle moderne autorisé, ses allocations et son réarmement doivent toujours
être établis. Aucun hook n'est installé et aucun fichier du jeu n'est modifié.

Reproduction : `tools/build_native_hand_lifecycle.py --output-name HandLifecycle_Compiled_v1`
avec `--compiled-hook <adaptateur dispersé désactivé>`, destination neuve.
Manifeste privé sous `.analysis/modern-assets/HandLifecycle_Compiled_v1/`.
