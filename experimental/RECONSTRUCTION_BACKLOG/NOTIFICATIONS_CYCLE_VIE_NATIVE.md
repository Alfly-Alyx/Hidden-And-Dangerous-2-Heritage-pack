# Notifications natives avant changement de modèle

Composant original du **10 octobre 2026**, désactivé. Les entrées natives
d'ajout, de retrait et de libération transmettent maintenant leurs événements
à la [garde de liaison](RETRAIT_LIAISON_MAINS.md) **dans l'émulateur privé**.
Les notifications ne sont plus injectées séparément par le scénario Python.
Ce n'est pas un dispositif installé dans le jeu ni un hook de production.

## Ordre et limites

Trois petites dérivations remplacent des instructions entières dans la copie
mémoire vérifiée de LS3DF 1.12 : ajout `100341c0`, retrait `10034260`, libération
`1001c370`. Elles sauvegardent registres et indicateurs, normalisent le drapeau
de direction pour le code C, appellent la garde, puis restaurent l'état et
rejouent exactement le prologue remplacé. La garde et le registre ne touchent
pas à l'état flottant. Les 26 reprises vérifiées conservent les registres,
indicateurs et tous les champs x87 exposés par le processeur émulé.

Le retrait du véritable registre compilé doit avoir réussi **avant la première
mutation originale**. Lors d'un transfert, l'ajout externe retire la liaison
avant que le moteur n'entre dans ses retraits et libérations imbriqués.
Les vues utilisées sont la sortie directe du collecteur C sur ces mêmes objets.

Un refus provoque une instruction d'arrêt diagnostique `UD2`, interceptée par
le banc avant le prologue natif. **Ce mécanisme ne fournit pas une gestion
d'erreur utilisable dans le client réel.** Il ne faut pas installer ces
dérivations dans un processus. Un état surveillé actif ne peut être remplacé
ou déconnecté sans retrait préalable ; accès sérialisé et propriété exclusive
du registre restent des obligations de l'appelant.

## Résultats privés

Deux scénarios, onze et 128 nœuds :

- ajout dans le même modèle, retrait, transfert vers un autre modèle ;
- libération d'une référence non finale, conservant une référence explicite ;
- retrait refusé pendant l'occupation du correcteur, sans mutation native ;
- réarmements explicites, générations et registres contrôlés ;
- **28 notifications compilées**, **26 reprises de prologue** et **deux arrêts
  pour occupation**, avec restauration exacte de toute l'image native ;
- aucune correction de pose exécutée dans ce banc de durée de vie, aucun
  allocateur ou destructeur appelé, aucun jeu lancé ou modifié.

Les objets sont diagnostiques et les vecteurs préalloués. Les changements de
parent, la destruction finale, le remplacement complet côté client, la
reconnaissance d'un équipement moderne autorisé et la gestion d'un refus en
production restent à raccorder ou qualifier. Ces vérifications ne démontrent
pas la durée de vie d'un modèle effectivement chargé dans le jeu.

L'image originale compilée de 3 072 octets, sans import système, refuse son
initialisation par un chargement Windows ordinaire. SHA-256 :
`1d4c52aec99a023f957680f42a88343bb9c2150a7497273a06c34551dc7fe3a2`.

Reproduction : `tools/build_native_hand_lifecycle_hooks.py`, avec destination
neuve `--output-name HandLifecycleHooks_Compiled_v1`, bibliothèque native
vérifiée `--library`, collecteur `--compiled-collection` et adaptateur dispersé
`--compiled-hook`. Manifeste privé dans
`.analysis/modern-assets/HandLifecycleHooks_Compiled_v1/` ; neuf tests unitaires
publics couvrent notamment les refus avant accès au processeur et aux fichiers.
