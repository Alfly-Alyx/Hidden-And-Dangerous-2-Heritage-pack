# Africa 4 — transition sur témoin radio Heritage

26 septembre 2026. **Composition expérimentale désactivée, moteur non testé.**

Le profil `africa4-invasion-transition-heritage-radio` ferme le travail de
composition annoncé dans l'étude, sans modifier la paire commerciale existante
`africa4-invasion-transition`. Il s'agit d'une comparaison distincte, exclusivement
native, avec son propre témoin et ses propres empreintes.

## Un seul facteur varie dans la comparaison

| État | Modification du script Patch | Taille / SHA-256 |
| --- | --- | --- |
| Commercial, provenance seulement | Aucune | 3997 / `46bf3adc728550785c65095201720468692360d1b72818d4c87a488d9f41744d` |
| Témoin de cette paire | Retrait du forçage radio, conforme au module Heritage | 3978 / `178ceee9b676000d046a5b7b4461e542c9469a5a9497f0514e62218e2b577179` |
| Variante de cette paire | Même retrait, plus les quatre décommentages de transition | 3970 / `e3fb75147aa74bfdcfa01299424f4a67f1a8a2db26bf09bca2142e5333b223c9` |

Le témoin et la variante respectent tous deux `_LoadGameValue(20)`. Le premier
conducteur n'attend les 20000 supplémentaires que dans la variante; les autres
délais et tous les signaux restent identiques entre les deux branches.

Le retrait reproduit la règle de `Africa4RadioConsequenceInstaller.PatchScript`
sur la source commerciale épinglée. L'empreinte UTF-8 à fins de ligne normalisées
du fichier source du module est
`2736e5f7f928bc4d451f74d1a045bbaabc6af295ceb64a08d2dd91cbf612a1e6`.
Une évolution du module exige une nouvelle revue, pas une acceptation silencieuse.
La source personnelle observée pour l'organisateur possède le même SHA-256 que
le témoin reconstruit, mais elle n'est pas utilisée comme source de confiance.

## Contrat de campagne contrôlé

Les 32 sources de la mission Africa 4 comprennent l'organisateur, sa liaison et
ses propriétaires, le journal, les deux conducteurs, les 18 soldats standards,
deux tankistes et cinq réservistes. La lecture du code actif vérifie :

- chargement de la valeur 20, absence du forçage à 1;
- signaux conducteurs 20/21, soldats et tankistes 1/2;
- espacements des groupes 30000/20000;
- journal 4153/4154 selon la même valeur;
- réservistes 26–30 conditionnés à l'absence d'avertissement et recevant signal 1.

Trois sources externes Africa 3 sont épinglées séparément : script Patch
`af3a_19.scr` (3167 octets), registre et acteurs. Elles prouvent la liaison unique
de l'opérateur `AF3a_19` et ses écritures actives `SaveGameValue(20,0)` et `(20,1)`.
Elles sont **lues seulement**, jamais placées dans la comparaison Africa 4.

Le registre installé d'Africa 3 est une surcharge de 3534 octets, SHA-256
`9734b21869f5b31f5b2ebda1625c2a9d576d05fd9e45cc0fc7ad47d6bc4abddc`,
contre 3498 dans l'archive. Elle est exclue et signalée dans les preuves externes;
ce contrôle ne qualifie donc pas la campagne personnelle modifiée.

Cette preuve de code ne démontre pas qu'une sauvegarde particulière possède la
bonne valeur. Les essais doivent partir de deux progressions réelles d'Africa 3,
radio transmise et non transmise, sans falsification automatique des sauvegardes.

## Limites explicites

La composition porte **uniquement sur la conséquence radio de l'organisateur**.
Elle ne prétend pas combiner tout le pack Heritage. Notamment, les surcharges
personnelles des soldats 27–30 sont exclues au profit des scripts commerciaux
épinglés de cette comparaison. Les éventuelles autres interactions Heritage
restent des essais d'intégration distincts.

Le générateur de laboratoire renommé refuse cette recette : la valeur de campagne
et les chemins d'origine doivent garder leur sens. Le préparateur documentaire
la marque `native_composition_required`, non « dépendance absente ».
Les manifestes natifs distinguent provenance commerciale et référence composée.
Le registre d'essais refuse un résultat associé au mauvais type de témoin.

Les 49 configurations antérieures conservent leurs définitions, fichiers et
protocoles. La paire commerciale et la paire composée sont incompatibles entre
elles; l'outil n'autorise qu'une configuration active à la fois. Ne pas ajouter
l'assaut de proximité à cette comparaison.

## Essais restants

Dans chaque branche 20=0/1 : observer d'abord le témoin Heritage, puis la variante.
Vérifier signaux, journal, réserves, objectifs, ordre et quantité d'émissions.
Mesurer les fondus 200/700, pause 1000 et attente initiale 20000 sans présumer que
les appels de fondu sont bloquants. Tester réutilisation radio, autre cinématique,
interruption et sauvegarde/reprise autour de chaque transition.

Le retour au **témoin de cette paire** conserve le correctif radio. Le retrait
final de l'expérience restaure tous les fichiers initiaux de la copie, selon son
journal. Aucun fichier de l'installation personnelle ni résultat moteur n'est
modifié par la génération.
