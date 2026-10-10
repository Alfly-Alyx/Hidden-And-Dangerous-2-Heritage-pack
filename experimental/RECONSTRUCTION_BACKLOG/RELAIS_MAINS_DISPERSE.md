# Relais de mains à allocations dispersées

État au **10 octobre 2026** : le collecteur dispersé est maintenant branché sur
un contexte enregistré et sur le relais natif dans le banc privé. Aucun hook
installé dans un jeu actif, aucun chargement Windows du binaire désactivé,
aucune installation personnelle modifiée.

## Implémentation

`hand_scatter_hook.c` associe exactement un modèle à ses vues de nœuds, à la
hiérarchie, aux rôles, au repos, aux prises et au travail fourni par l'appelant.
L'enregistrement vérifie la forme du contexte ; les plages de nœuds et leurs
liaisons sont contrôlées lors de chaque correction. Un autre modèle, un contexte
désenregistré ou occupé n'est pas corrigé. Un contexte invalidé ou une précision
x87 différente de celle examinée refuse le calcul, mais conserve le rafraîchissement.
Le désenregistrement d'un contexte occupé est refusé.

Le code assembleur conserve l'état avant correction, appelle le collecteur C,
puis rejoue les instructions du rafraîchissement. L'image désactivée fait
20 480 octets, sans import système, SHA-256
`1f123fb2de5ae8c222aa4bf3191ec417c5507d3b77dbab0d0787410bf5ed91d9`.
Les sources du collecteur et du calculateur sont partagées avec les bancs précédents.

## Contrôles réalisés

Le banc autonome de l'adaptateur exécute 32 corrections : onze / 128 nœuds,
parents droits / tournés, alignement seize / quatre octets et quatre instants
successifs dans les mêmes allocations. Dix cas de refus ou d'absence d'action
et quatre refus d'enregistrement complètent ces contrôles. Les octets non ciblés,
les entrées et les gardes restent inchangés. Écart maximal de rotation par
rapport au calcul indépendant : `6,241910278e-8`.

Un programme console original vérifie ensuite **huit cas sur le processeur hôte**,
avec onze allocations séparées du tas, des tailles variées et des gardes.
Il conserve les **108 octets x87 complets**, transmet le bon modèle au
rafraîchissement témoin et respecte les refus. Il ne lit et n'exécute aucun fichier
du jeu. Les champs d'adresse d'exception `FIP` / `FDP` restent explicitement
non qualifiés dans Unicorn, indépendamment de cette preuve sur processeur hôte.

Le second banc branche cet adaptateur sur le relais de modèle original et le
rafraîchissement récursif original. Les nœuds sont placés dans des pages séparées,
à des adresses non monotones et alignées sur quatre octets, avec une page non
mappée entre allocations. Le modèle utilisé par les attachements, le relais et
le contexte C est identique. Aucune pose n'est réinjectée entre les étapes.

Les seize séquences produisent 208 mises à jour, 72 appels du contrôleur,
112 calculs de pose, 36 passages dans l'adaptateur, 18 corrections complètes et
72 rafraîchissements natifs. Les absences de contrôleur / propriétaires,
désenregistrements, pauses, poids nuls et réattachements suivent les mêmes règles
que le [relais contigu](RELAIS_NATIF_CORRECTION_MAINS.md). Écart maximal de pose :
`9,319978792e-17` ; de rotation : `7,386094425e-8`.

Le relais contigu a été rejoué après mutualisation du banc : ses 208 mises à jour
conservent les mêmes résultats. Chaque séquence retire le patch émulé et compare
intégralement l'image native à son état initial. Le registre, les entrées, les
gardes et les plages d'écriture sont contrôlés par phase.

## Limites maintenues

Les adresses, tailles d'allocation et durées de vie sont encore **fournies par le
banc**, pas découvertes dans une scène chargée. L'appelant doit désenregistrer
avant libération ou réutilisation et sérialiser toutes les opérations. Les tests
de changement tardif ne remplacent pas cette propriété exclusive. Le propriétaire
visuel est diagnostique ; skin, rendu, boîte englobante et budget par frame ne
sont pas exécutés ou qualifiés. Aucune arme n'est déclarée jouable.

La suite porte sur la collecte des modèles réellement assemblés, leur identité,
leurs créations / remplacements / destructions et leur association aux équipements
modernes, avant toute activation dans une copie de test.

Reproduction privée :

- `tools/build_native_hand_scatter_hook.py --output-name HandScatterHook_Compiled_v2`
  avec une destination neuve ;
- `tools/hand_relay_audit.py --scattered`, avec la bibliothèque 1.12 épinglée,
  l'adaptateur désactivé et un rapport neuf.

Rapport de relais : `.analysis/native-scattered-hand-relay-v1-20261010.json`.
Les programmes, manifestes et rapports restent privés sous `.analysis/`.
